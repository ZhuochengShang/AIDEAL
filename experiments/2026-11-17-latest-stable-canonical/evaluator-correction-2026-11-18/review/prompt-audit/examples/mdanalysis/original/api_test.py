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
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/qualified/runs/original/mdanalysis/mdanalysis/execution/output"

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
    import MDAnalysis.lib.distances as distances
    import numpy as np

    # Use the preloaded 'atoms' AtomGroup.
    # We will calculate the distance between the first two atoms in the group.
    # Since calc_bonds expects two arrays of coordinates, we slice the AtomGroup.
    ag1 = atoms[:2]
    ag2 = atoms[1:3]

    # Calculate bond lengths between pairs (ag1[0]-ag2[0], ag1[1]-ag2[1])
    bond_lengths = distances.calc_bonds(ag1, ag2)

    # Verify the result shape matches the number of pairs
    assert bond_lengths.shape == (2,)
    assert isinstance(bond_lengths, np.ndarray)

    # Verify that the calculated distance is non-negative and finite
    assert np.all(bond_lengths >= 0)
    assert np.all(np.isfinite(bond_lengths))

    print(f"__CHECK__ python:MDAnalysis.lib.distances.calc_bonds {bond_lengths.shape}")
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
