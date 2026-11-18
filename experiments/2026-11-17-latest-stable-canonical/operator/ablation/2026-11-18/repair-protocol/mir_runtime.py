"""Select and verify an isolated mir_eval source before running an audience program."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('program', nargs='?')
    args = parser.parse_args()
    record = json.loads(args.binding.read_text())
    root = Path(record['source']).resolve(strict=True)
    if any(x == 'mir_eval' or x.startswith('mir_eval.') for x in sys.modules):
        raise ValueError('Select condition source before importing mir_eval')
    for item in record['files']:
        p = Path(item['path']).resolve(strict=True)
        if not p.is_relative_to(root) or hashlib.sha256(p.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Condition source changed: ' + str(p))
    sys.path.insert(0, str(root))
    import mir_eval.transcription as module
    if Path(module.__file__).resolve() != root / 'mir_eval/transcription.py':
        raise ValueError('Wrong mir_eval source loaded')
    if args.smoke:
        import numpy as np
        intervals = np.array([[0., .5], [.5, 1.]])
        pitches = np.array([440., 550.])
        assert module.validate(intervals, pitches, intervals, pitches) is None
        try:
            module.validate(intervals, pitches[:1], intervals, pitches)
        except ValueError as exc:
            assert str(exc) == record['trigger_message'], str(exc)
        else:
            raise AssertionError('Expected native length error')
        try:
            module.validate(intervals, pitches, intervals, pitches[:1])
        except ValueError as exc:
            assert str(exc) == 'Estimated intervals and pitches have different lengths.'
        else:
            raise AssertionError('Expected unrelated length error')
        print(json.dumps({'status': 'verified', 'condition': record['condition'],
            'loaded_source': str(Path(module.__file__).resolve()),
            'source_files': len(record['files']), 'valid_call': True,
            'native_trigger': record['trigger_message'], 'unrelated_error_unchanged': True}))
        return
    if not args.program:
        parser.error('program is required unless --smoke is selected')
    program = Path(args.program).resolve(strict=True)
    sys.argv = [str(program)]
    runpy.run_path(str(program), run_name='__main__')


if __name__ == '__main__':
    main()
