PATH='/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/coordinates/test_topology.pdb'
import MDAnalysis as mda
u=mda.Universe(PATH)
assert len(u.atoms)>0
print(len(u.atoms))
