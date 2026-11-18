PATH='/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/test.xvg'
from MDAnalysis.auxiliary.XVG import XVGReader
r=XVGReader(PATH)
assert len(r)>0
print(len(r))
r.close()
