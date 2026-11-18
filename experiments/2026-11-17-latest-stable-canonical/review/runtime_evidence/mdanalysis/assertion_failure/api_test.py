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
    psf_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures/adk.psf"
    dcd_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures/adk_dims.dcd"
    pdb_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures/adk_open.pdb"
    gro_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures/adk_oplsaa.gro"
    xtc_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures/adk_oplsaa.xtc"
    mdanalysis_fixture_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures"
    output_dir = r"/home/zshan011/apps/aideal/checks/2026-11-17-latest-stable-runtime/scientific-native-controls/mdanalysis/assertion_failure/execution/output"

    # pre-loaded typed inputs (comprehension.execute.preamble)
    MDAnalysis = mda  # type: module
    numpy = np  # type: module
    universe = mda.Universe(psf_path, dcd_path)  # type: MDAnalysis.Universe
    atoms = universe.atoms  # type: MDAnalysis.core.groups.AtomGroup
    protein = universe.select_atoms("protein")  # type: MDAnalysis.core.groups.AtomGroup
    backbone = universe.select_atoms("protein and backbone")  # type: MDAnalysis.core.groups.AtomGroup
    trajectory = universe.trajectory  # type: MDAnalysis.coordinates.base.ReaderBase
    timestep = trajectory[0]  # type: MDAnalysis.coordinates.base.Timestep
    _aideal_os.makedirs(output_dir, exist_ok=True)

    # TODO API_TEST_START
    import MDAnalysis as _checked_package
    from pathlib import Path as _CheckedPath
    import sys as _checked_sys
    import json as _checked_json
    assert _CheckedPath(_checked_package.__file__).resolve().parent == _CheckedPath('/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable/lib/python3.12/site-packages/MDAnalysis').resolve()
    assert _checked_package.__version__ == '2.11.0'
    assert _CheckedPath(_checked_sys.prefix).resolve() == _CheckedPath('/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable').resolve()
    print("__IDENTITY__ " + _checked_json.dumps({"module": _checked_package.__name__, "file": _checked_package.__file__, "version": _checked_package.__version__, "python": _checked_sys.executable}))
    from MDAnalysis.analysis.rms import rmsd as _selected_target
    from MDAnalysis.lib import c_distances as _checked_extension
    assert _CheckedPath(_checked_extension.__file__).resolve().is_relative_to(_CheckedPath('/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable/lib/python3.12/site-packages/MDAnalysis').resolve())
    _checked_universe = _checked_package.Universe(psf_path, dcd_path)
    assert len(_checked_universe.atoms) == 3341 and len(_checked_universe.trajectory) == 98
    _positions = _checked_universe.atoms.positions.copy()
    assert np.isclose(_selected_target(_positions, _positions), 0.0)
    assert np.isclose(_selected_target(_positions, _positions + 1.0), np.sqrt(3.0), atol=1e-5)
    print("__CHECK__ rmsd selected exact-owner positive and negative numerical controls")
    assert False, 'AIDEAL_EXPECTED_ASSERTION_FAILURE'
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
