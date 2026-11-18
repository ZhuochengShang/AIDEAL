"""Shared infrastructure-only scaffold for tslearn's frozen canonical API study.

This exact infrastructure file is shared by all study conditions. It intentionally imports no
tested tslearn API because discovering the public import is part of the
audience task in every cell.
"""

from pathlib import Path
import sys
import traceback

import numpy as np


def run():
    # Typed repository fixture path and condition-specific output directory:
    trace_npz = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/tslearn/tslearn/.cached_datasets/Trace.npz"
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/tslearn/execution/output"

    # pre-loaded typed inputs (comprehension.execute.preamble)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    _trace = np.load(trace_npz)
    _balanced = np.array([0, 4, 1, 17, 3, 13, 2, 5], dtype=int)
    X = _trace["X_train"][_balanced, :40, :]  # type: balanced time-series dataset ndarray (8, 40, 1)
    X2 = _trace["X_test"][:4, :32, :]  # type: second dataset ndarray (4, 32, 1)
    s1 = X[0].ravel()  # type: 1-D series ndarray (40,)
    s2 = X[1].ravel()  # type: 1-D series ndarray (40,)
    y = _trace["y_train"][_balanced]  # type: four balanced labels, two examples per class
    tiny_matrix = np.arange(12.0).reshape(3, 4)  # type: deterministic numeric matrix

    # Keep audience imports local so they cannot shadow fixture construction.
    def api_test():
        # TODO API_TEST_START
        from tslearn.metrics import dtw
        import numpy as np

        # Use the provided 1D series s1 and s2
        # dtw expects (sz, d) or (sz,)
        # s1 and s2 are (40,) which is valid for univariate DTW
        dist = dtw(s1, s2)

        # Verify the result is a float and non-negative
        assert isinstance(dist, float)
        assert dist >= 0.0

        # Compute a small witness: DTW of a series with itself should be 0.0
        dist_self = dtw(s1, s1)
        assert np.isclose(dist_self, 0.0), f"DTW(s, s) should be 0, got {dist_self}"

        # Compute with Sakoe-Chiba constraint
        dist_constrained = dtw(s1, s2, global_constraint="sakoe_chiba", sakoe_chiba_radius=5)
        assert isinstance(dist_constrained, float)
        assert dist_constrained >= 0.0

        print(f"__CHECK__ python:tslearn.metrics._dtw.dtw {dist:.4f}")
        # TODO API_TEST_END
        pass

    api_test()


if __name__ == "__main__":
    try:
        run()
        print("__DONE__")
    except Exception as exc:  # noqa: BLE001 - execution boundary
        sys.stderr.write("__RUN_ERR__ " + type(exc).__name__ + ": " + str(exc) + "\n")
        traceback.print_exc()
        raise SystemExit(1)
