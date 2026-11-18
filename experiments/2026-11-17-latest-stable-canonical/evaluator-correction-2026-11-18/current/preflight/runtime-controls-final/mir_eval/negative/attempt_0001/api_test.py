import sys
import traceback

import numpy as np
import mir_eval
from mir_eval import alignment, beat, chord, display, hierarchy, io, key
from mir_eval import melody, multipitch, onset, pattern, segment, separation
from mir_eval import sonify, tempo, transcription, transcription_velocity, util


def run():
    beat_reference_file = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/ref00.txt"
    beat_estimate_file = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/est00.txt"
    chord_reference_file = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/chord/ref00.lab"
    melody_reference_file = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/melody/ref00.txt"
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/current/preflight/runtime-controls-final/mir_eval/negative/attempt_0001/output"

    # pre-loaded typed inputs (comprehension.execute.preamble)
    times = np.array([0.0, 0.5, 1.0, 1.5, 2.0])  # type: numpy.ndarray event/frame times
    ref_events = np.array([0.0, 0.5, 1.0, 1.5])  # type: numpy.ndarray reference events
    est_events = np.array([0.02, 0.48, 1.03, 1.52])  # type: numpy.ndarray estimated events
    ref_intervals = np.array([[0.0, 0.5], [0.5, 1.0], [1.0, 1.5], [1.5, 2.0]])  # type: numpy.ndarray reference intervals
    est_intervals = np.array([[0.0, 0.48], [0.48, 1.02], [1.02, 1.48], [1.48, 2.0]])  # type: numpy.ndarray estimated intervals
    ref_labels = ["C:maj", "G:maj", "A:min", "F:maj"]  # type: list[str] reference labels
    est_labels = ["C:maj", "G:maj", "A:min", "F:maj"]  # type: list[str] estimated labels
    ref_freqs = np.array([440.0, 440.0, 0.0, 523.25, 523.25])  # type: numpy.ndarray reference frequencies
    est_freqs = np.array([442.0, 438.0, 0.0, 525.0, 520.0])  # type: numpy.ndarray estimated frequencies
    ref_sources = np.vstack([np.sin(2*np.pi*3*times), np.cos(2*np.pi*2*times)])  # type: numpy.ndarray reference sources
    est_sources = ref_sources + 0.001  # type: numpy.ndarray estimated sources

    def api_test(*, alignment=alignment, beat=beat, beat_estimate_file=beat_estimate_file, beat_reference_file=beat_reference_file, chord=chord, chord_reference_file=chord_reference_file, display=display, est_events=est_events, est_freqs=est_freqs, est_intervals=est_intervals, est_labels=est_labels, est_sources=est_sources, hierarchy=hierarchy, io=io, key=key, melody=melody, melody_reference_file=melody_reference_file, mir_eval=mir_eval, multipitch=multipitch, np=np, onset=onset, output_dir=output_dir, pattern=pattern, ref_events=ref_events, ref_freqs=ref_freqs, ref_intervals=ref_intervals, ref_labels=ref_labels, ref_sources=ref_sources, segment=segment, separation=separation, sonify=sonify, sys=sys, tempo=tempo, times=times, traceback=traceback, transcription=transcription, transcription_velocity=transcription_velocity, util=util):
        # TODO API_TEST_START

        from mir_eval.alignment import absolute_error
        import numpy as np
        median_error, mean_error = absolute_error(ref_events, est_events)
        expected = np.abs(ref_events - est_events)
        assert np.isclose(median_error, np.median(expected) + 1.0)
        assert np.isclose(mean_error, np.mean(expected))
        print(f"__CHECK__ python:mir_eval.alignment.absolute_error {median_error} {mean_error}")
        # TODO API_TEST_END
        pass

    api_test()


if __name__ == "__main__":
    try:
        run()
        print("__DONE__")
    except Exception as exc:
        sys.stderr.write(f"__RUN_ERR__ {type(exc).__name__}: {exc}\n")
        traceback.print_exc()
        sys.exit(1)
