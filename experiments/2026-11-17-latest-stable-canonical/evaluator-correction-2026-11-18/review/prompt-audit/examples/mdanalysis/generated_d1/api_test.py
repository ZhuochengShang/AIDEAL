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
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/mdanalysis/execution/output"

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
    import MDAnalysis.lib.distances as dists
    import numpy as np

    # Use the first two atoms of the protein to calculate a single bond length
    ag1 = protein[:1]
    ag2 = protein[1:2]

    # Calculate bond length
    bond_length = dists.calc_bonds(ag1, ag2)

    # Verify the result is a scalar float64 as per documentation
    assert isinstance(bond_length, np.float64)
    assert bond_length > 0.0

    # Calculate bond lengths for a subset of the backbone
    ag_a = backbone[:10]
    ag_b = backbone[1:11]
    bond_lengths = dists.calc_bonds(ag_a, ag_b)

    # Verify the shape matches the number of pairs
    assert bond_lengths.shape == (10,)
    assert np.all(bond_lengths > 0.0)

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
