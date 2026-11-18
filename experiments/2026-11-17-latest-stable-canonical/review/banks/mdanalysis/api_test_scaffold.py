import sys
import traceback

def run():
    # Imports are local so snippets may use either conventional aliases or full
    # package names without Python's local-name analysis breaking the preamble.
    import MDAnalysis as mda
    import numpy as np
    import os as _aideal_os

    MDAnalysis = mda
    numpy = np
    output_dir = "/tmp/aideal_mdanalysis_default_out"
    # AIDEAL_DATA_BINDINGS
    _aideal_os.makedirs(output_dir, exist_ok=True)

    # TODO API_TEST_START
    # TODO API_TEST_END
    pass


if __name__ == "__main__":
    try:
        run()
        print("__DONE__")
    except Exception as exc:
        sys.stderr.write(f"__RUN_ERR__ {type(exc).__name__}: {exc}\n")
        traceback.print_exc()
        sys.exit(1)
