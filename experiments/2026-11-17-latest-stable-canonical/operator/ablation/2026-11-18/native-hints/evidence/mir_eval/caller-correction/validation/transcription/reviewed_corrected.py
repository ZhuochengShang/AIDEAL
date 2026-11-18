import mir_eval
import numpy as np

# ref_intervals shape (n, 2) must match ref_pitches shape (n,)
ref_intervals = np.array([[0.0, 0.5], [0.5, 1.0]])
ref_pitches = np.array([440.0, 523.25])
est_intervals = np.array([[0.0, 0.48], [0.48, 1.02]])
est_pitches = np.array([442.0, 525.0])

mir_eval.transcription.validate(ref_intervals, ref_pitches, est_intervals, est_pitches)

witness = ref_intervals.shape[0] + est_intervals.shape[0]
assert ref_intervals.shape[0] == 2 and est_intervals.shape[0] == 2
print(f"__CHECK__ python:mir_eval.transcription.validate {witness}")