PATH='/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/inputs/test.fasta'
from Bio import AlignIO
a=AlignIO.read(PATH,"fasta")
assert len(a)>=2
print(len(a),a.get_alignment_length())
