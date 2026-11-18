import sys
import traceback

def run(*, sys=sys, traceback=traceback):
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
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/current/preflight/runtime-controls/mdanalysis/final1519-d8ba3815cf95/negative/attempt_0001/output"

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
    from MDAnalysis.lib.distances import calc_bonds
    import numpy as np
    first = atoms[:2].positions.copy()
    second = atoms[1:3].positions.copy()
    observed = calc_bonds(first, second, backend="serial")
    expected = np.linalg.norm(first.astype(float) - second.astype(float), axis=1)
    assert np.allclose(observed, expected + 1.0, rtol=1e-6, atol=1e-6)
    print(f"__CHECK__ python:MDAnalysis.lib.distances.calc_bonds {observed.tolist()}")
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
