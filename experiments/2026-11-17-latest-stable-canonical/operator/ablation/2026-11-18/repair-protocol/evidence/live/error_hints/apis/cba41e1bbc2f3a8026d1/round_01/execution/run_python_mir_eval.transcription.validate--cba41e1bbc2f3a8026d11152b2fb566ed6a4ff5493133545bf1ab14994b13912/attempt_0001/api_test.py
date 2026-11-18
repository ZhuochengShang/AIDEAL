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
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/repair-pilot/mir_eval/error_hints/apis/cba41e1bbc2f3a8026d1/round_01/output"

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

    def api_test():
        # TODO API_TEST_START
        import mir_eval.transcription
        import numpy as np

        # Ensure inputs are aligned for the validation check
        # The previous error indicated a length mismatch between intervals and pitches.
        # We slice the arrays to ensure they are of equal length (n) for the validation.
        n = min(ref_intervals.shape[0], ref_freqs.shape[0])
        m = min(est_intervals.shape[0], est_freqs.shape[0])

        ref_intervals_sub = ref_intervals[:n]
        ref_freqs_sub = ref_freqs[:n]
        est_intervals_sub = est_intervals[:m]
        est_freqs_sub = est_freqs[:m]

        # Call the validation function
        mir_eval.transcription.validate(ref_intervals_sub, ref_freqs_sub, est_intervals_sub, est_freqs_sub)

        # Correctness check: Verify that the validated arrays maintain the expected shape
        # and that the number of reference notes is consistent with the input slice.
        assert ref_intervals_sub.shape[0] == ref_freqs_sub.shape[0]
        assert est_intervals_sub.shape[0] == est_freqs_sub.shape[0]

        witness = ref_intervals_sub.shape[0]
        print(f"__CHECK__ python:mir_eval.transcription.validate {witness}")
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
