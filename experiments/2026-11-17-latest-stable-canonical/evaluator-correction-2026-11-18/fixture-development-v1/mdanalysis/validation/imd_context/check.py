ROOT='/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis'
TRR='/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/coordinates/test.trr'
import sys,json,numpy as np
sys.path.insert(0,ROOT)
from imd_stream_fixture import imd_stream
from MDAnalysis.coordinates.IMD import IMDReader
from MDAnalysis.coordinates.TRR import TRRReader
with TRRReader(TRR) as trajectory: expected=[ts.positions.copy() for ts in trajectory]
for attempt in range(2):
 with imd_stream(TRR) as fixture:
  with IMDReader(fixture['imd_url'],n_atoms=fixture['imd_n_atoms']) as reader:
   actual=[reader.ts.positions.copy()]
   while True:
    try:actual.append(next(reader).positions.copy())
    except (StopIteration,EOFError):break
   np.testing.assert_allclose(actual,expected)
   assert len(actual)==5
print(json.dumps({'status':'passed','independent_connections':2,'frames_each':5,'atoms':5}))
