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
    psf_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures/adk.psf"
    dcd_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures/adk_dims.dcd"
    pdb_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures/adk_open.pdb"
    gro_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures/adk_oplsaa.gro"
    xtc_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures/adk_oplsaa.xtc"
    mdanalysis_fixture_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/libraries/mdanalysis/fixtures"
    tng_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/coordinates/test.tng"
    h5md_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/coordinates/test.h5md"
    mmcif_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/mmcif/1YJP.cif"
    gsd_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/example_bonds.gsd"
    tpr_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/tprs/Linear_Angle.tpr"
    edr_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/test.edr"
    xvg_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/test.xvg"
    fasta_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/test.fasta"
    imd_trr_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/coordinates/test.trr"
    small_pdb_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/coordinates/test_topology.pdb"
    dna_pdb_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/dna_bdl084.pdb"
    fixture_catalog_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/upstream_data_catalog.json"
    chemfiles_trajectory_path = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/coordinates/test.trr"
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/current/preflight/native-controls/mdanalysis/d8ba3815cf95/original/imd_positive/execution/run_python_MDAnalysis.coordinates.IMD.IMDReader--59ed171dbc037d3cbfef98e9d0c574063a4c9b5abd80fc7c145857869954dbb5/attempt_0001/output"

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
        def api_test(*, MDAnalysis=MDAnalysis, _AidealExitStack=_AidealExitStack, _AidealPath=_AidealPath, _aideal_api=_aideal_api, _aideal_importlib=_aideal_importlib, _aideal_json=_aideal_json, _aideal_os=_aideal_os, _aideal_target=_aideal_target, atoms=atoms, backbone=backbone, chemfiles_trajectory_path=chemfiles_trajectory_path, dcd_path=dcd_path, dna_pdb_path=dna_pdb_path, edr_path=edr_path, fasta_path=fasta_path, fixture_catalog_path=fixture_catalog_path, gro_path=gro_path, gsd_path=gsd_path, h5md_path=h5md_path, imd_host=imd_host, imd_n_atoms=imd_n_atoms, imd_port=imd_port, imd_trr_path=imd_trr_path, imd_url=imd_url, mda=mda, mdanalysis_fixture_dir=mdanalysis_fixture_dir, mmcif_path=mmcif_path, np=np, numpy=numpy, output_dir=output_dir, pdb_path=pdb_path, protein=protein, psf_path=psf_path, small_pdb_path=small_pdb_path, sys=sys, timestep=timestep, tng_path=tng_path, tpr_path=tpr_path, traceback=traceback, trajectory=trajectory, universe=universe, x3dna_executable=x3dna_executable, x3dna_root=x3dna_root, xtc_path=xtc_path, xvg_path=xvg_path):
            # TODO API_TEST_START
            from MDAnalysis.coordinates.IMD import IMDReader
            assert imd_url.startswith('imd://127.0.0.1:')
            with IMDReader(imd_url,n_atoms=imd_n_atoms) as reader:
             count=1
             while True:
              try:next(reader);count+=1
              except (StopIteration,EOFError):break
            assert count == 5
            print(f"__CHECK__ python:MDAnalysis.coordinates.IMD.IMDReader {count}")
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
