def validate(ref_intervals, ref_pitches, est_intervals, est_pitches):
    validate_intervals(ref_intervals, est_intervals)
    if not ref_intervals.shape[0] == ref_pitches.shape[0]:
        raise ValueError("Reference intervals and pitches have different lengths. Ensure the number of rows in the interval array matches the number of elements in the pitch array.")
    if not est_intervals.shape[0] == est_pitches.shape[0]:
        raise ValueError("Estimated intervals and pitches have different lengths. Ensure the number of rows in the interval array matches the number of elements in the pitch array.")
    if ref_pitches.size > 0 and np.min(ref_pitches) <= 0:
        raise ValueError("Reference contains at least one non-positive pitch value")
    if est_pitches.size > 0 and np.min(est_pitches) <= 0:
        raise ValueError("Estimate contains at least one non-positive pitch value")