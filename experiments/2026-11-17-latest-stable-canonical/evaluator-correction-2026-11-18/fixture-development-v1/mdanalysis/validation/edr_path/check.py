PATH='/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/test.edr'
from MDAnalysis.auxiliary.EDR import EDRReader
r=EDRReader(PATH)
assert len(r)>0
print(len(r))
r.close()
