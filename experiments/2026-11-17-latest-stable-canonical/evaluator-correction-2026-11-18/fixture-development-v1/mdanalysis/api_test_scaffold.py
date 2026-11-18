"""Shared MDAnalysis execution scaffold with versioned format/stream fixtures.

Only fixture provision and lifecycle live here. Audience code still invokes the
real selected API. Both documentation conditions use this exact scaffold.
"""
import sys
import traceback


def run():
    import MDAnalysis as mda
    import numpy as np
    import os as _aideal_os
    import json as _aideal_json
    import importlib.util as _aideal_importlib
    from pathlib import Path as _AidealPath
    from contextlib import ExitStack as _AidealExitStack

    MDAnalysis = mda
    numpy = np
    output_dir = "/tmp/aideal_mdanalysis_default_out"
    # AIDEAL_DATA_BINDINGS
    _aideal_os.makedirs(output_dir, exist_ok=True)

    _aideal_target = _aideal_json.loads(
        _AidealPath(__file__).with_name("requested_target.json").read_text())
    _aideal_api = _aideal_target.get("api_id") or _aideal_target["qualified_name"]
    _aideal_api = _aideal_api.removeprefix("python:")
    imd_url = imd_host = imd_port = imd_n_atoms = None
    x3dna_executable = "/home/zshan011/apps/aideal/external/2026-11-18-x3dna-v2.4/bin/x3dna_ensemble"
    x3dna_root = "/home/zshan011/apps/aideal/external/2026-11-18-x3dna-v2.4"
    if _aideal_api.startswith("MDAnalysis.analysis.legacy.x3dna."):
        _aideal_os.environ["X3DNA"] = x3dna_root
        _aideal_os.environ["PATH"] = x3dna_root + "/bin" + _aideal_os.pathsep + _aideal_os.environ.get("PATH", "")

    with _AidealExitStack() as _aideal_stack:
        if (_aideal_api.startswith("MDAnalysis.coordinates.IMD.") or
                _aideal_api.startswith("MDAnalysis.coordinates.base.StreamReaderBase")):
            _aideal_spec = _aideal_importlib.spec_from_file_location(
                "aideal_imd_fixture",
                "/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/imd_stream_fixture.py")
            _aideal_fixture = _aideal_importlib.module_from_spec(_aideal_spec)
            _aideal_spec.loader.exec_module(_aideal_fixture)
            _aideal_stream = _aideal_stack.enter_context(_aideal_fixture.imd_stream(imd_trr_path))
            imd_url = _aideal_stream["imd_url"]
            imd_host = "127.0.0.1"
            imd_port = int(imd_url.rsplit(":", 1)[1])
            imd_n_atoms = _aideal_stream["imd_n_atoms"]

        # The evaluator captures surrounding input bindings as keyword defaults.
        # This prevents snippet imports/reassignments from shadowing fixtures.
        def api_test():
            # TODO API_TEST_START
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
