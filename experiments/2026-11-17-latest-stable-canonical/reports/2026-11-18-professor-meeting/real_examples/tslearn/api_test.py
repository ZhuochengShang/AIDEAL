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
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/explicit-inputs-r0/continuation/tslearn/generated_d1/execution/run_python_tslearn.metrics._dtw.dtw--1030f6652ac41edcbb4e216b7eeb1c69a54f12c8b6a7ac83287e9655cc75932b/attempt_0001/output"

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
    def api_test(*, Path=Path, X=X, X2=X2, _balanced=_balanced, _trace=_trace, np=np, output_dir=output_dir, s1=s1, s2=s2, sys=sys, tiny_matrix=tiny_matrix, trace_npz=trace_npz, traceback=traceback, y=y):
        # TODO API_TEST_START
        from tslearn.metrics import dtw
        import numpy as np

        # Use the provided 1D series s1 and s2
        # DTW distance between identical series should be 0.0
        dist_identical = dtw(s1, s1)
        assert dist_identical == 0.0, f"Expected 0.0 for identical series, got {dist_identical}"

        # Compute DTW with Sakoe-Chiba constraint
        # Using a small radius on a subset of the provided data
        s1_sub = s1[:10]
        s2_sub = s2[:10]
        dist_constrained = dtw(s1_sub, s2_sub, global_constraint="sakoe_chiba", sakoe_chiba_radius=2)

        # Verify the result is a non-negative float
        assert isinstance(dist_constrained, float), "Result must be a float"
        assert dist_constrained >= 0.0, "Distance must be non-negative"

        # Verify against a known simple case: distance between [0, 1] and [0, 2]
        # Path: (0,0) -> (1,1) => sqrt((0-0)^2 + (1-2)^2) = 1.0
        dist_simple = dtw([0, 1], [0, 2])
        assert np.isclose(dist_simple, 1.0), f"Expected 1.0, got {dist_simple}"

        print(f"__CHECK__ python:tslearn.metrics._dtw.dtw {dist_constrained:.4f}")
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
