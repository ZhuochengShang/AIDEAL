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
    # AIDEAL_DATA_BINDINGS

    # Keep audience imports local so they cannot shadow fixture construction.
    def api_test():
        # TODO API_TEST_START
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
