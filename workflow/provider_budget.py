"""POSIX-locked, atomic cost reservations for one shared Codex pilot budget."""
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid

MODEL = 'gpt-5.3-codex'
PRICES = {'input': 1750, 'cached_input': 175, 'output': 14000}  # Nanodollars/token.
FRAMING_TOKENS = 4096


class BudgetError(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _integer(value):
    return type(value) is int and value >= 0


class BudgetLedger:
    def __init__(self, path, max_cost_usd='5'):
        self.path = Path(path).expanduser().resolve()
        try:
            cap = Decimal(str(max_cost_usd)) * 1_000_000_000
            if not cap.is_finite() or cap <= 0 or cap > 5_000_000_000 or cap != cap.to_integral_value():
                raise ValueError
            cap = int(cap)
        except (InvalidOperation, ValueError):
            raise BudgetError('Budget must be positive, at most $5, and precise to nanodollars') from None
        self.identity = {'schema_version': 1, 'model': MODEL, 'max_cost_nanousd': cap,
                         'prices_nanousd_per_token': PRICES, 'framing_tokens': FRAMING_TOKENS}

    def _save(self, data):
        fd, name = tempfile.mkstemp(prefix=self.path.name + '.', suffix='.tmp', dir=self.path.parent)
        try:
            with os.fdopen(fd, 'w') as output:
                json.dump(data, output, indent=2, allow_nan=False)
                output.write('\n')
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, self.path)
            directory = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def _validate(self, data, marker):
        if not isinstance(data, dict):
            raise BudgetError('Invalid ledger document; refusing to spend')
        if any(data.get(key) != value for key, value in self.identity.items()):
            raise BudgetError('Ledger model, prices, cap or schema changed; automatic reset is forbidden')
        if not marker or data.get('ledger_id') != marker or not isinstance(data.get('records'), list):
            raise BudgetError('Ledger identity or records are invalid')
        seen = set()
        for row in data['records']:
            if (not isinstance(row, dict) or not isinstance(row.get('id'), str)
                    or row['id'] in seen or row.get('state') not in ('reserved', 'uncertain', 'settled')
                    or not _integer(row.get('reserved_nanousd'))
                    or not _integer(row.get('charged_nanousd'))
                    or not _integer(row.get('input_upper_tokens'))
                    or not _integer(row.get('max_output_tokens'))):
                raise BudgetError('Invalid ledger record; refusing to spend')
            expected = row['input_upper_tokens'] * PRICES['input'] + row['max_output_tokens'] * PRICES['output']
            if row['reserved_nanousd'] != expected:
                raise BudgetError('Ledger reservation is inconsistent')
            if row['state'] != 'settled' and row['charged_nanousd'] != expected:
                raise BudgetError('Unresolved reservation must remain fully charged')
            if row['state'] == 'settled' and row['charged_nanousd'] != self._actual(row.get('usage')):
                raise BudgetError('Settled ledger usage is inconsistent')
            seen.add(row['id'])

    @contextmanager
    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.path) + '.lock', os.O_RDWR | os.O_CREAT, 0o600)
        with os.fdopen(fd, 'r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            marker = lock.read().strip()
            if self.path.exists():
                try:
                    data = json.loads(self.path.read_text())
                except (ValueError, OSError):
                    raise BudgetError('Cannot read budget ledger; refusing to reset it') from None
            else:
                if marker:
                    raise BudgetError('Budget ledger was removed; automatic recreation is forbidden')
                marker = uuid.uuid4().hex
                data = {**self.identity, 'ledger_id': marker, 'records': []}
                self._save(data)
                lock.write(marker)
                lock.flush()
                os.fsync(lock.fileno())
            self._validate(data, marker)
            yield data
            self._save(data)

    def reserve(self, system, prompt, max_output_tokens, request_sha256, settings_sha256):
        if not isinstance(system, str) or not isinstance(prompt, str):
            raise BudgetError('Only text requests can be reserved')
        if type(max_output_tokens) is not int or max_output_tokens <= 0:
            raise BudgetError('Output limit must be a positive integer')
        if any(not isinstance(value, str) or len(value) != 64
               or any(char not in '0123456789abcdef' for char in value)
               for value in (request_sha256, settings_sha256)):
            raise BudgetError('Request and settings hashes are required')
        bound = len(system.encode('utf-8')) + len(prompt.encode('utf-8')) + FRAMING_TOKENS
        amount = bound * PRICES['input'] + max_output_tokens * PRICES['output']
        with self._locked() as data:
            used = sum(row['charged_nanousd'] for row in data['records'])
            if data.get('blocked_reason') or used + amount > self.identity['max_cost_nanousd']:
                raise BudgetError('Shared budget cannot cover this request; no provider call permitted')
            row = {'id': uuid.uuid4().hex, 'state': 'reserved', 'created_at': _now(),
                   'request_sha256': request_sha256, 'settings_sha256': settings_sha256,
                   'input_upper_tokens': bound, 'max_output_tokens': max_output_tokens,
                   'reserved_nanousd': amount, 'charged_nanousd': amount}
            data['records'].append(row)
        return row['id']

    @staticmethod
    def _actual(usage):
        if not isinstance(usage, dict):
            return None
        incoming, cached, outgoing = (usage.get(key) for key in
                                      ('input_tokens', 'cached_input_tokens', 'output_tokens'))
        if not all(_integer(value) for value in (incoming, cached, outgoing)) or cached > incoming:
            return None
        return (incoming - cached) * PRICES['input'] + cached * PRICES['cached_input'] + outgoing * PRICES['output']

    def finish(self, reservation_id, *, usage=None, response_id=None, status=None, failure=None):
        """Only complete, final usage releases a reservation; uncertain calls stay charged."""
        violation = False
        with self._locked() as data:
            row = next((row for row in data['records'] if row['id'] == reservation_id), None)
            if row is None or row['state'] != 'reserved':
                raise BudgetError('Reservation is missing or already finalized')
            row.update(finished_at=_now(), response_id=response_id, response_status=status)
            amount = self._actual(usage) if status in ('completed', 'incomplete', 'failed', 'cancelled') else None
            if amount is None:
                row.update(state='uncertain', failure=failure or {'type': 'MissingFinalUsage'})
            else:
                row.update(state='settled', charged_nanousd=amount, usage=usage)
                violation = (amount > row['reserved_nanousd'] or
                             usage['input_tokens'] > row['input_upper_tokens'] or
                             usage['output_tokens'] > row['max_output_tokens'])
                if violation:
                    data['blocked_reason'] = 'Provider usage exceeded the conservative reservation'
            receipt = {'reservation_id': row['id'], 'state': row['state'],
                       'reserved_nanousd': row['reserved_nanousd'],
                       'charged_nanousd': row['charged_nanousd'],
                       'total_committed_nanousd': sum(item['charged_nanousd'] for item in data['records']),
                       'max_cost_nanousd': self.identity['max_cost_nanousd']}
        if violation:
            raise BudgetError('Provider usage exceeded reservation; ledger is blocked for review')
        return receipt
