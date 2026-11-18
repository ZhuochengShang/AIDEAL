"""Conservative static forwarding proofs for source-bound Java declarations.

No compiler or subject executes. This intentionally recognizes only same-owner,
static methods with unchanged primitive parameters, unchanged explicit defaults,
matching returns, and a single direct call. It does not resolve virtual dispatch,
Scala implicit conversions, instance/field receivers, callbacks or coercions.
"""
import hashlib
from pathlib import Path
import re

VERSION = 'same_owner_static_primitive_forwarding_v1'
PRIMITIVES = {'boolean','byte','short','int','long','char','float','double'}
_SIMPLE_BODY = re.compile(r'([^{}]*)\{\s*(return\s+)?([A-Za-z_$][A-Za-z_$0-9]*)\s*\(([^()]*)\)\s*;\s*\}', re.S)


def bound_source(root, row):
    root = Path(root).resolve()
    path = (root / row['path']).resolve(strict=True)
    if not path.is_relative_to(root):
        raise ValueError('Forwarding evidence escapes source root')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != row['source_sha256']:
        raise ValueError('Forwarding source file hash changed')
    start, end = row['start'], row['end']
    if any(isinstance(n, bool) or not isinstance(n, int) for n in (start, end)) or not 0 <= start < end:
        raise ValueError('Invalid forwarding source span')
    units = raw.decode('utf-8').encode('utf-16-le')
    if end * 2 > len(units):
        raise ValueError('Forwarding source span exceeds file')
    body = units[2 * start:2 * end].decode('utf-16-le')
    if hashlib.sha256(body.encode()).hexdigest() != row['source_span_sha256']:
        raise ValueError('Forwarding source span hash changed')
    return body


def static_header(header):
    # Deprecated is a documented compile-time migration marker. Other annotations
    # are outside this limited proof, as are synchronization and native methods.
    header = re.sub(r'@(?:java\.lang\.)?Deprecated\b', '', header).strip()
    return ('@' not in header and bool(re.search(r'\bstatic\b', header))
            and not re.search(r'\b(?:synchronized|native)\b', header)
            and '<' not in header and '>' not in header)


def header_matches_record(header, row):
    """Recheck the limited signature directly, not only the ledger's type text."""
    header = re.sub(r'@(?:java\.lang\.)?Deprecated\b', '', header).strip()
    match = re.fullmatch(r'(?:(?:public|protected|private|static|final)\s+)*'
                         r'([A-Za-z_$][\w.$]*)\s+([A-Za-z_$][\w$]*)\s*\(([^()]*)\)\s*', header)
    if match is None:
        return False
    returns, name, parameter_text = match.groups()
    if name != row['name'] or returns != row.get('returns'):
        return False
    actual = []
    for text in parameter_text.split(',') if parameter_text.strip() else []:
        param = re.fullmatch(r'\s*(?:final\s+)?([A-Za-z]+)\s+([A-Za-z_$][\w$]*)\s*', text)
        if param is None or param[1] not in PRIMITIVES:
            return False
        actual.append((param[2], param[1]))
    declared = row.get('params', [])
    return (len(actual) == row.get('parameter_count')
            and actual == [(p['name'], p['type'].strip()) for p in declared]
            and all(p.get('default') in (None, '') for p in declared))


def prove_forwarding(root, row, all_records, retained_ids):
    """Return (proof, reason); rejected candidates remain in the API inventory."""
    text = bound_source(root, row)
    if row['language'] != 'Java':
        return None, 'language_requires_typed_receiver_or_implicit_resolution'
    if row['kind'] != 'method':
        return None, 'constructor_or_nonmethod_contract'
    match = _SIMPLE_BODY.fullmatch(text.strip())
    if match is None:
        return None, 'body_not_single_unqualified_call'
    header, returns, called, argument_text = match.groups()
    if not static_header(header):
        return None, 'receiver_dispatch_or_method_modifier_not_proven'
    if not header_matches_record(header, row):
        return None, 'source_signature_outside_proof_or_differs_from_ledger'
    params = row.get('params', [])
    args = [arg.strip() for arg in argument_text.split(',')] if argument_text.strip() else []
    names = [p['name'] for p in params]
    if (called in names or len(args) != len(names) or len(set(args)) != len(args)
            or set(args) != set(names)):
        return None, 'arguments_not_unchanged_formal_parameters'
    if any(param['type'].strip() not in PRIMITIVES for param in params):
        return None, 'parameter_type_resolution_outside_proof'
    targets = [t for t in all_records if t['language']=='Java' and t['kind']=='method'
               and t.get('owner') == row.get('owner') and t['name'] == called]
    if len(targets) != 1:
        return None, 'same_owner_target_not_unique'
    target = targets[0]
    if target['site_id'] == row['site_id'] or target['site_id'] not in retained_ids:
        return None, 'target_not_distinct_retained_implementation'
    if target['path'] != row['path']:
        return None, 'declaring_lexical_context_differs'
    target_text = bound_source(root, target)
    target_header = target_text.split('{', 1)[0]
    if not static_header(target_header):
        return None, 'target_dispatch_or_method_modifier_not_proven'
    if not header_matches_record(target_header, target):
        return None, 'target_source_signature_outside_proof_or_differs_from_ledger'
    target_params = target.get('params', [])
    if len(target_params) != len(params) or target.get('parameter_count') != row.get('parameter_count'):
        return None, 'arity_differs'
    source_by_name = {p['name']: p for p in params}
    for name, target_param in zip(args, target_params):
        source_param = source_by_name[name]
        if source_param['type'].strip() != target_param['type'].strip():
            return None, 'forwarded_parameter_type_differs'
        if (source_param.get('default') or None) != (target_param.get('default') or None):
            return None, 'parameter_default_differs'
    if row.get('returns') != target.get('returns') or bool(returns) != (row.get('returns') != 'void'):
        return None, 'return_contract_differs'
    return {'relation':'direct_forwarder','target_site_id':target['site_id'],
            'argument_map':[{'source_parameter':name,'target_parameter':param['name']}
                            for name,param in zip(args,target_params)],
            'semantics_preserved':True,'source_span_sha256':row['source_span_sha256'],
            'target_source_span_sha256':target['source_span_sha256'],
            'evidence':{'method':VERSION,'language':'Java','owner':row['owner'],
                        'source_path':row['path'],'source_file_sha256':row['source_sha256'],
                        'call':'same_owner_static','arguments':'unchanged_primitive_parameters',
                        'defaults':'identical','return':'same_declared_type',
                        'scope':'direct invocation behavior; not reflective API metadata or stack-trace identity'}}, 'proven_same_owner_static_forwarding'
