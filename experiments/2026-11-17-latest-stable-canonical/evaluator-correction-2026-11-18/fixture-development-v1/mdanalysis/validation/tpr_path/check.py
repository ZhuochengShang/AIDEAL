PATH='/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/tprs/Linear_Angle.tpr'
from MDAnalysis.topology.TPRParser import TPRParser
t=TPRParser(PATH).parse()
assert t.n_atoms>0
print(t.n_atoms)
