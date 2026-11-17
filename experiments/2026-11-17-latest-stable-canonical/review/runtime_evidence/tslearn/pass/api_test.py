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
    output_dir = r"/home/zshan011/apps/aideal/checks/2026-11-17-latest-stable-runtime/scientific-native-controls/tslearn/pass/execution/output"

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
        import tslearn as _checked_package
        from pathlib import Path as _CheckedPath
        import sys as _checked_sys
        import json as _checked_json
        assert _CheckedPath(_checked_package.__file__).resolve().parent == _CheckedPath('/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable/lib/python3.12/site-packages/tslearn').resolve()
        assert _checked_package.__version__ == '0.10.0'
        assert _CheckedPath(_checked_sys.prefix).resolve() == _CheckedPath('/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable').resolve()
        print("__IDENTITY__ " + _checked_json.dumps({"module": _checked_package.__name__, "file": _checked_package.__file__, "version": _checked_package.__version__, "python": _checked_sys.executable}))
        from tslearn.metrics._dtw import dtw as _selected_target
        assert X.shape == (8,40,1) and X2.shape == (4,32,1)
        assert np.load(trace_npz)["X_train"].shape == (100,275,1)
        assert _selected_target([1.,2.,3.], [1.,2.,3.]) == 0.0
        assert _selected_target([1.,2.,3.], [4.,5.,6.]) > 0.0
        print("__CHECK__ dtw selected exact-owner positive and negative numerical controls")
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
