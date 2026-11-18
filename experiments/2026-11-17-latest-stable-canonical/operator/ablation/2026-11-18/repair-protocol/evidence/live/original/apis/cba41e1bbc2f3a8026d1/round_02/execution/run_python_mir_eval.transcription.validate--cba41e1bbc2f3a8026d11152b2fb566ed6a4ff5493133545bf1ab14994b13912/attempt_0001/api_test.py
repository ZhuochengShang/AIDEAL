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
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/repair-pilot/mir_eval/original/apis/cba41e1bbc2f3a8026d1/round_02/output"

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

        # Filter inputs to ensure positive frequencies as required by the validation contract
        # The previous error indicated non-positive pitch values.
        ref_mask = ref_freqs > 0
        est_mask = est_freqs > 0

        ref_intervals_clean = ref_intervals[ref_mask]
        ref_freqs_clean = ref_freqs[ref_mask]
        est_intervals_clean = est_intervals[est_mask]
        est_freqs_clean = est_freqs[est_mask]

        # Call the validation function with cleaned data
        mir_eval.transcription.validate(ref_intervals_clean, ref_freqs_clean, est_intervals_clean, est_freqs_clean)

        # Correctness check: Verify that the validated arrays maintain their expected shape
        # and that the number of reference notes is consistent with the filtered input.
        assert ref_intervals_clean.shape[0] == ref_freqs_clean.shape[0]
        assert est_intervals_clean.shape[0] == est_freqs_clean.shape[0]
        assert np.all(ref_freqs_clean > 0)
        assert np.all(est_freqs_clean > 0)

        witness = ref_intervals_clean.shape[0]
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
