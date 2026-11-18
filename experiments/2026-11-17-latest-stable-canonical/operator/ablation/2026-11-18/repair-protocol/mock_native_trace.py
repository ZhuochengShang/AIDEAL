#!/usr/bin/env python3
"""Exercise real pinned mir_eval execution with three scripted model answers.

No provider calls occur. Use a dedicated spec with mode=offline_mock and a fresh
output directory. Its result is software-validation evidence, not an LLM result.
"""
import argparse
import json
from pathlib import Path
import matched_repairs as protocol

SNIPPETS = [
    'from mir_eval.transcription import validate\n'
    'validate(ref_intervals, ref_freqs, est_intervals, est_freqs)\n',
    'from mir_eval.transcription import validate\n'
    'validate(ref_intervals, ref_freqs[:4], est_intervals, est_freqs[:4])\n',
    'from mir_eval.transcription import validate\n'
    'ref_pitch = np.array([440.0, 440.0, 523.25, 523.25])\n'
    'est_pitch = np.array([442.0, 438.0, 525.0, 520.0])\n'
    'value = validate(ref_intervals, ref_pitch, est_intervals, est_pitch)\n'
    'assert value is None\n'
    'print("__CHECK__ python:mir_eval.transcription.validate valid note arrays")\n',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    args = parser.parse_args()
    spec = protocol.read(args.spec)
    if (spec.get('mode') != 'offline_mock'
            or spec['api_ids'] != ['python:mir_eval.transcription.validate']):
        raise ValueError('Require an explicitly marked mir transcription mock spec')
    if (Path(spec['output']) / 'result.json').exists():
        raise ValueError('Use a fresh mock output; test requires all three scripted calls')
    engine = protocol.load_engine(spec)
    with engine.ownership(Path(spec['output'])):
        spec, cfg, receipt, aliases = protocol.prepare(args.spec, engine)
        import aideal.llm as llm
        actual, calls = llm.invoke_text, []
        def mock(model, system, user):
            number = len(calls)
            if number >= len(SNIPPETS):
                raise AssertionError('Unexpected extra model request')
            calls.append({'logical_round': number, 'system': system, 'user': user})
            return SNIPPETS[number]
        llm.invoke_text = mock
        try:
            status = protocol.run(spec, cfg, receipt, aliases, engine)
        finally:
            llm.invoke_text = actual
        result = protocol.read(Path(spec['output']) / 'result.json')
        if status or len(calls) != 3 or result['cumulative_passes'] != {'R0': 0, 'R1': 0, 'R2': 1}:
            raise AssertionError('Real executor did not produce the required fail/fail/pass chain')
        assert SNIPPETS[0].strip() in json.loads(
            protocol.read(Path(spec['output']) / 'apis' / protocol.digest(spec['api_ids'][0].encode())[:20]
                          / 'round_01/ROUND.json')['context'])['previous_complete_snippet']
        assert 'different lengths' in calls[1]['user']
        assert 'positive' in calls[2]['user'].lower()
        if spec['condition'] == 'error_hints':
            assert '[AIDEAL fix:interval_pitch_length_match]' in calls[1]['user']
            assert '[AIDEAL fix:interval_pitch_length_match]' not in calls[2]['user']
        engine.atomic_json(Path(spec['output']) / 'MOCK_VALIDATION.json', {
            'status': 'pass', 'mode': 'offline_mock', 'actual_model_calls': 0,
            'scripted_answers': 3, 'native_outcomes': ['fail', 'fail', 'pass'],
            'repair_context_verified': True, 'result': protocol.bind(Path(spec['output']) / 'result.json')})
        print(json.dumps({'status': 'pass', 'mode': 'offline_mock', 'actual_model_calls': 0}))


if __name__ == '__main__':
    main()
