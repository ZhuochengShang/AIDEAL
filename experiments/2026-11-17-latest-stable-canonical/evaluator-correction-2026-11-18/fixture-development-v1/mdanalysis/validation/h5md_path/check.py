PATH='/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/coordinates/test.h5md'
from MDAnalysis.coordinates.H5MD import H5MDReader
with H5MDReader(PATH) as r: assert r.n_atoms>0; print(r.n_atoms,len(r))
