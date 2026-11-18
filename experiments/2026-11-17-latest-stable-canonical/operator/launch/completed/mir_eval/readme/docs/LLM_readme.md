# mir_eval — LLM_readme

LLM-facing API documentation. Generated from the API surface, project profile, and distilled docs.

## API Test: `python:mir_eval.alignment.absolute_error`

### Signature
```python
def absolute_error(reference_timestamps, estimated_timestamps)
```
_Source: source/mir_eval/alignment.py:115_

_Source doc:_ Compute the absolute deviations between estimated and reference timestamps,
and then returns the median and average over all events

Examples
--------
>>> reference_timestamps = mir_eval.io.load_events('reference.txt')
>>> estimated_timestamps = mir_eval.io.load_events('estimated.txt')
>>> mae, aae = mir_eval.align.absolute_error(reference_onsets, estimated_timestamps)

Parameters
----------
reference_timestamps : np.ndarray
    reference timestamps, in seconds
estimated_timestamps : np.ndarray
    estimated timestamps, in seconds

Returns
-------
mae : float
    Median absolute error
aae: float
    Average absolute error

### Goal
Computes the median and average absolute deviation between a set of estimated timestamps and ground-truth reference timestamps to evaluate alignment accuracy.

### Parameters
- `reference_timestamps`: A 1D `np.ndarray` containing ground-truth event timestamps in seconds.
- `estimated_timestamps`: A 1D `np.ndarray` containing the estimated event timestamps in seconds.

### Input
- **Data Format:** Both inputs must be 1D `np.ndarray` objects representing time in seconds.
- **Preconditions:** Inputs should be sorted by time. The arrays must contain the same number of events to compute a direct correspondence.

### Output
Returns a tuple `(mae, aae)`:
- `mae` (float): The median of the absolute differences between the reference and estimated timestamps.
- `aae` (float): The arithmetic mean of the absolute differences between the reference and estimated timestamps.

### Valid Call Patterns
```python
import mir_eval
# Assuming reference_timestamps and estimated_timestamps are loaded via mir_eval.io.load_events
mae, aae = mir_eval.alignment.absolute_error(reference_timestamps, estimated_timestamps)
```

### LLM Instruction Prompt
- When calling `mir_eval.alignment.absolute_error`, ensure both `reference_timestamps` and `estimated_timestamps` are 1D NumPy arrays of floats representing time in seconds.
- Ensure the arrays are sorted chronologically before passing them to the function.
- Note that the function expects a direct mapping between the two arrays; ensure the number of elements matches.

### Prompt Snippet
```text
# Example usage of absolute_error for alignment evaluation
mae, aae = mir_eval.alignment.absolute_error(ref_times, est_times)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays of different lengths will result in a `ValueError` during the subtraction operation.
- **Unsorted Input:** If the input arrays are not sorted by time, the computed errors will not reflect the intended temporal alignment.
- **Unit Mismatch:** Providing timestamps in samples rather than seconds will lead to incorrect metric values.

### Fix Code Hint
```python
import numpy as np
# Ensure inputs are sorted and of equal length
ref_sorted = np.sort(reference_timestamps)
est_sorted = np.sort(estimated_timestamps)
if len(ref_sorted) == len(est_sorted):
    mae, aae = mir_eval.alignment.absolute_error(ref_sorted, est_sorted)
```

## API Test: `python:mir_eval.alignment.evaluate`

### Signature
```python
def evaluate(reference_timestamps, estimated_timestamps, **kwargs)
```
_Source: source/mir_eval/alignment.py:312_

_Source doc:_ Compute all metrics for the given reference and estimated annotations.

Examples
--------
>>> reference_timestamps = mir_eval.io.load_events('reference.txt')
>>> estimated_timestamps = mir_eval.io.load_events('estimated.txt')
>>> duration = max(np.max(reference_timestamps), np.max(estimated_timestamps)) + 10
>>> scores = mir_eval.align.evaluate(reference_onsets, estimated_timestamps, duration)

Parameters
----------
reference_timestamps : np.ndarray
    reference timestamp locations, in seconds
estimated_timestamps : np.ndarray
    estimated timestamp locations, in seconds
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of alignment evaluation metrics by comparing reference and estimated timestamp annotations.

### Parameters
- `reference_timestamps`: A 1D `np.ndarray` containing the ground-truth event timestamps in seconds.
- `estimated_timestamps`: A 1D `np.ndarray` containing the estimated event timestamps in seconds.
- `kwargs`: Optional keyword arguments passed to underlying metric or preprocessing functions.

### Input
- **Data Format:** Inputs must be 1D `np.ndarray` objects.
- **Preconditions:** Timestamps must be provided in seconds. For most metrics, input arrays must be sorted by time.
- **Validation:** It is recommended to use `mir_eval.alignment.validate()` prior to evaluation to ensure input arrays conform to expected shapes and constraints.

### Output
Returns `scores` (dict): A dictionary mapping metric names (str) to their corresponding scalar values (float).

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Standard usage pattern
scores = mir_eval.alignment.evaluate(reference_timestamps, estimated_timestamps)
```

### LLM Instruction Prompt
- When calling `mir_eval.alignment.evaluate`, ensure that both `reference_timestamps` and `estimated_timestamps` are 1D NumPy arrays containing values in seconds.
- Always verify that the arrays are sorted chronologically before passing them to the function.
- Use this function to obtain a complete dictionary of alignment metrics rather than calculating individual metrics manually.

### Prompt Snippet
```text
# Example of calling the alignment evaluation
scores = mir_eval.alignment.evaluate(ref_events, est_events)
# Accessing a specific metric
f_measure = scores['Precision']
```

### Common Failure Modes
- **Unsorted Inputs:** Providing unsorted timestamp arrays will lead to incorrect metric calculations.
- **Unit Mismatch:** Providing timestamps in samples instead of seconds will result in invalid evaluation scores.
- **Empty Arrays:** Passing empty arrays may cause errors in metric computation; ensure inputs are validated using `mir_eval.alignment.validate()` first.

### Fix Code Hint
```python
# Ensure inputs are sorted and validated
reference_timestamps = np.sort(reference_timestamps)
estimated_timestamps = np.sort(estimated_timestamps)
mir_eval.alignment.validate(reference_timestamps, estimated_timestamps)
scores = mir_eval.alignment.evaluate(reference_timestamps, estimated_timestamps)
```

## API Test: `python:mir_eval.alignment.karaoke_perceptual_metric`

### Signature
```python
def karaoke_perceptual_metric(reference_timestamps, estimated_timestamps)
```
_Source: source/mir_eval/alignment.py:269_

_Source doc:_ Metric based on human synchronicity perception as measured in the paper
"User-centered evaluation of lyrics to audio alignment" [#lizemasclef2021]

The parameters of this function were tuned on data collected through a user Karaoke-like
experiment
It reflects human judgment of how "synchronous" lyrics and audio stimuli are perceived
in that setup.
Beware that this metric is non-symmetrical and by construction it is also not equal to 1 at 0.

Examples
--------
>>> reference_timestamps = mir_eval.io.load_events('reference.txt')
>>> estimated_timestamps = mir_eval.io.load_events('estimated.txt')
>>> score = mir_eval.align.karaoke_perceptual_metric(reference_onsets, estimated_timestamps)

Parameters
----------
reference_timestamps : np.ndarray
    reference timestamps, in seconds
estimated_timestamps : np.ndarray
    estimated timestamps, in seconds

Returns
-------
perceptual_score : float
    Perceptual score, averaged over all timestamps

### Goal
Computes a perceptual synchronicity score for lyrics-to-audio alignment based on human judgment models derived from karaoke-style user experiments.

### Parameters
- `reference_timestamps`: A 1D `np.ndarray` containing the ground-truth event timestamps in seconds.
- `estimated_timestamps`: A 1D `np.ndarray` containing the estimated event timestamps in seconds.

### Input
- **Data Format:** Both inputs must be 1D NumPy arrays of floats representing time in seconds.
- **Preconditions:** Inputs should be sorted by time. Use `mir_eval.io.load_events` to load data from standard delimited text files.

### Output
Returns `perceptual_score` (float): The average perceptual synchronicity score across all provided timestamps.

### Valid Call Patterns
```python
import mir_eval
# Assuming reference.txt and estimated.txt contain event timestamps
reference_timestamps = mir_eval.io.load_events('reference.txt')
estimated_timestamps = mir_eval.io.load_events('estimated.txt')
score = mir_eval.alignment.karaoke_perceptual_metric(reference_timestamps, estimated_timestamps)
```

### LLM Instruction Prompt
- When calling `mir_eval.alignment.karaoke_perceptual_metric`, ensure both arguments are 1D `np.ndarray` objects containing timestamps in seconds.
- Note that this metric is non-symmetrical; swapping `reference_timestamps` and `estimated_timestamps` will yield different results.
- Do not assume the score will be 1.0 when the difference between timestamps is 0.0.

### Prompt Snippet
```text
# Example usage of karaoke_perceptual_metric
score = mir_eval.alignment.karaoke_perceptual_metric(ref_array, est_array)
```

### Common Failure Modes
- **Non-Symmetry:** Expecting the metric to be symmetric; it is not, and the order of arguments matters significantly.
- **Input Format:** Passing lists instead of `np.ndarray` objects, which may cause errors in internal array operations.
- **Unsorted Data:** Providing unsorted timestamps, which violates the implicit requirement for temporal alignment evaluation.

### Fix Code Hint
```python
import numpy as np
# Ensure inputs are sorted numpy arrays
ref = np.sort(np.array(reference_data))
est = np.sort(np.array(estimated_data))
score = mir_eval.alignment.karaoke_perceptual_metric(ref, est)
```

## API Test: `python:mir_eval.alignment.percentage_correct`

### Signature
```python
def percentage_correct(reference_timestamps, estimated_timestamps, window=0.3)
```
_Source: source/mir_eval/alignment.py:144_

_Source doc:_ Compute the percentage of correctly predicted timestamps. A timestamp is predicted
correctly if its position doesn't deviate more than the window parameter from the ground
truth timestamp.

Examples
--------
>>> reference_timestamps = mir_eval.io.load_events('reference.txt')
>>> estimated_timestamps = mir_eval.io.load_events('estimated.txt')
>>> pc = mir_eval.align.percentage_correct(reference_onsets, estimated_timestamps, window=0.2)

Parameters
----------
reference_timestamps : np.ndarray
    reference timestamps, in seconds
estimated_timestamps : np.ndarray
    estimated timestamps, in seconds
window : float
    Window size, in seconds
    (Default value = .3)

Returns
-------
pc : float
    Percentage of correct timestamps

### Goal
Computes the accuracy of timestamp alignment by calculating the percentage of estimated events that fall within a specified temporal tolerance window of the ground-truth reference events.

### Parameters
- `reference_timestamps`: A 1D NumPy array containing the ground-truth event times in seconds.
- `estimated_timestamps`: A 1D NumPy array containing the estimated event times in seconds.
- `window`, default `0.3`: The tolerance threshold in seconds; an estimated timestamp is considered correct if its absolute deviation from a reference timestamp is less than or equal to this value.

### Input
- **Data Format:** Both `reference_timestamps` and `estimated_timestamps` must be 1D NumPy arrays of floats representing time in seconds.
- **Preconditions:** Inputs should be sorted by time. Use `mir_eval.io.load_events` to load data from standard text files.

### Output
Returns `float` — The proportion of estimated timestamps that are correctly aligned, expressed as a value between 0.0 and 1.0.

### Valid Call Patterns
```python
import mir_eval
# Using the pattern from the documentation
pc = mir_eval.alignment.percentage_correct(reference_timestamps, estimated_timestamps, window=0.3)
```

### LLM Instruction Prompt
- When calling `mir_eval.alignment.percentage_correct`, ensure both input arrays are 1D NumPy arrays containing time values in seconds.
- Always specify the `window` parameter if the default 0.3 seconds is not appropriate for the specific alignment task requirements.
- Ensure inputs are sorted chronologically before passing them to the function.

### Prompt Snippet
```text
# Example usage:
pc = mir_eval.alignment.percentage_correct(ref_array, est_array, window=0.1)
```

### Common Failure Modes
- **Unsorted Inputs:** Providing unsorted arrays may lead to incorrect matching logic.
- **Unit Mismatch:** Providing timestamps in samples instead of seconds will result in invalid evaluation scores.
- **Empty Arrays:** Passing empty arrays may result in unexpected behavior; ensure inputs are validated using task-specific `validate()` functions if available.

### Fix Code Hint
```python
import numpy as np
# Ensure arrays are sorted
ref_sorted = np.sort(reference_timestamps)
est_sorted = np.sort(estimated_timestamps)
pc = mir_eval.alignment.percentage_correct(ref_sorted, est_sorted, window=0.3)
```

## API Test: `python:mir_eval.alignment.percentage_correct_segments`

### Signature
```python
def percentage_correct_segments(reference_timestamps, estimated_timestamps, duration: Optional[float]=None)
```
_Source: source/mir_eval/alignment.py:175_

_Source doc:_ Calculate the percentage of correct segments (PCS) metric.

It constructs segments out of predicted and estimated timestamps separately
out of each given timestamp vector and calculates the percentage of overlap between correct
segments compared to the total duration.

WARNING: This metrics behaves differently depending on whether "duration" is given!

If duration is not given (default case), the computation follows the MIREX lyrics alignment
challenge 2020. For a timestamp vector with entries (t1,t2, ... tN), segments with
the following (start, end) boundaries are created: (t1, t2), ... (tN-1, tN).
After the segments are created, the overlap between the reference and estimated segments is
determined and divided by the total duration, which is the distance between the
first and last timestamp in the reference.

If duration is given, the segment boundaries are instead (0, t1), (t1, t2), ... (tN, duration).
The overlap is computed in the same way, but then divided by the duration parameter given to
this function.
This method follows the original paper [#fujihara2011] more closely, where the metric was
proposed.
As a result, this variant of the metrics punishes cases where the first estimated timestamp
is too early or the last estimated timestamp is too late, whereas the MIREX variant does not.
On the other hand, the MIREX metric is invariant to how long the eventless beginning and end
parts of the audio are, which might be a desirable property.

Examples
--------
>>> reference_timestamps = mir_eval.io.load_events('reference.txt')
>>> estimated_timestamps = mir_eval.io.load_events('estimated.txt')
>>> pcs = mir_eval.align.percentage_correct_segments(reference_timestamps, estimated_timestamps)

Parameters
----------
reference_timestamps : np.ndarray
    reference timestamps, in seconds
estimated_timestamps : np.ndarray
    estimated timestamps, in seconds
duration : float
    Optional. Total duration of audio (seconds). WARNING: Metric is computed differently
    depending on whether this is provided or not - see documentation above!

Returns
-------
pcs : float
    Percentage of time where ground truth and predicted segments overlap

### Goal
Calculates the Percentage of Correct Segments (PCS) metric to evaluate the temporal alignment accuracy of estimated event timestamps against ground truth.

### Parameters
- `reference_timestamps`: A 1D `np.ndarray` of ground-truth event timestamps in seconds.
- `estimated_timestamps`: A 1D `np.ndarray` of estimated event timestamps in seconds.
- `duration` (`Optional[float]`), default `None`: The total duration of the audio in seconds. If provided, the metric includes segments from the start of the audio to the first timestamp and from the last timestamp to the end of the duration.

### Input
- **Data Format:** Expects 1D `np.ndarray` objects containing timestamps in seconds.
- **Preconditions:** Timestamps should be sorted in ascending order.
- **Loading:** Typically loaded using `mir_eval.io.load_events`.

### Output
Returns `float`: The percentage of time (0.0 to 1.0) where the ground truth and predicted segments overlap, relative to the total duration (either defined by the first/last timestamp or the `duration` parameter).

### Valid Call Patterns
```python
# Default MIREX 2020 behavior
pcs = mir_eval.alignment.percentage_correct_segments(reference_timestamps, estimated_timestamps)

# Original paper behavior with explicit duration
pcs = mir_eval.alignment.percentage_correct_segments(reference_timestamps, estimated_timestamps, duration=120.5)
```

### LLM Instruction Prompt
- When calling `percentage_correct_segments`, ensure `reference_timestamps` and `estimated_timestamps` are 1D NumPy arrays sorted by time.
- Explicitly decide whether to provide `duration`: use `None` for MIREX-style evaluation (invariant to start/end silence) or provide a float for the original paper's method (punishes early/late boundary errors).

### Prompt Snippet
```text
# Example usage of percentage_correct_segments
import mir_eval
pcs = mir_eval.alignment.percentage_correct_segments(ref_ts, est_ts, duration=audio_duration)
```

### Common Failure Modes
- **Unsorted Input:** Providing unsorted timestamp arrays will lead to incorrect segment construction.
- **Duration Mismatch:** Providing a `duration` shorter than the last timestamp in the arrays may lead to unexpected behavior or invalid segment calculations.
- **Empty Arrays:** Passing empty arrays may result in division by zero or undefined behavior; ensure inputs are validated.

### Fix Code Hint
```python
import numpy as np
# Ensure inputs are sorted
ref_ts = np.sort(reference_timestamps)
est_ts = np.sort(estimated_timestamps)
pcs = mir_eval.alignment.percentage_correct_segments(ref_ts, est_ts, duration=duration)
```

## API Test: `python:mir_eval.alignment.validate`

### Signature
```python
def validate(reference_timestamps: np.ndarray, estimated_timestamps: np.ndarray)
```
_Source: source/mir_eval/alignment.py:59_

_Source doc:_ Check that the input annotations to a metric look like valid onset time
arrays, and throws helpful errors if not.

Parameters
----------
reference_timestamps : np.ndarray
    reference timestamp locations, in seconds
estimated_timestamps : np.ndarray
    estimated timestamp locations, in seconds

### Goal
Validates that reference and estimated timestamp arrays conform to the expected format for alignment evaluation, ensuring they are suitable for metric computation.

### Parameters
- `reference_timestamps` (`np.ndarray`): A 1D NumPy array containing ground-truth timestamp locations in seconds.
- `estimated_timestamps` (`np.ndarray`): A 1D NumPy array containing estimated timestamp locations in seconds.

### Input
- **Data Format:** Both inputs must be 1D `np.ndarray` objects.
- **Preconditions:** Timestamps must be provided in seconds. While not explicitly enforced by this function, most downstream `mir_eval` metrics require these arrays to be sorted by time.

### Output
Returns `None` if the inputs are valid. If the inputs are invalid (e.g., incorrect dimensions or types), it raises an exception with a descriptive error message.

### Valid Call Patterns
```python
import numpy as np
import mir_eval

# Example inferred from signature
ref = np.array([0.0, 1.0, 2.0])
est = np.array([0.1, 1.1, 2.1])
mir_eval.alignment.validate(ref, est)
```

### LLM Instruction Prompt
- Always ensure `reference_timestamps` and `estimated_timestamps` are 1D `np.ndarray` objects before passing them to `mir_eval.alignment.validate`.
- Use this function as a pre-computation check to ensure data integrity before calling evaluation functions in the `mir_eval.alignment` module.

### Prompt Snippet
```text
# Validate alignment inputs before evaluation
mir_eval.alignment.validate(reference_timestamps, estimated_timestamps)
```

### Common Failure Modes
- **Dimension Mismatch:** Passing multi-dimensional arrays instead of 1D arrays will trigger a validation error.
- **Type Errors:** Passing lists or other non-NumPy array types will cause the validation to fail.
- **Unsorted Data:** While `validate` checks format, it may not catch unsorted timestamps; ensure arrays are sorted chronologically to avoid errors in subsequent metric calculations.

### Fix Code Hint
```python
import numpy as np
# Ensure inputs are 1D arrays and sorted
reference_timestamps = np.sort(np.array(reference_timestamps).flatten())
estimated_timestamps = np.sort(np.array(estimated_timestamps).flatten())
mir_eval.alignment.validate(reference_timestamps, estimated_timestamps)
```

## API Test: `python:mir_eval.beat.cemgil`

### Signature
```python
def cemgil(reference_beats, estimated_beats, cemgil_sigma=0.04)
```
_Source: source/mir_eval/beat.py:177_

_Source doc:_ Cemgil's score, computes a gaussian error of each estimated beat.
Compares against the original beat times and all metrical variations.

Examples
--------
>>> reference_beats = mir_eval.io.load_events('reference.txt')
>>> reference_beats = mir_eval.beat.trim_beats(reference_beats)
>>> estimated_beats = mir_eval.io.load_events('estimated.txt')
>>> estimated_beats = mir_eval.beat.trim_beats(estimated_beats)
>>> cemgil_score, cemgil_max = mir_eval.beat.cemgil(reference_beats,
                                                    estimated_beats)

Parameters
----------
reference_beats : np.ndarray
    reference beat times, in seconds
estimated_beats : np.ndarray
    query beat times, in seconds
cemgil_sigma : float
    Sigma parameter of gaussian error windows
    (Default value = 0.04)

Returns
-------
cemgil_score : float
    Cemgil's score for the original reference beats
cemgil_max : float
    The best Cemgil score for all metrical variations

### Goal
Computes the Cemgil score for beat tracking evaluation by calculating the Gaussian error of estimated beats relative to reference beats, accounting for both the original timing and potential metrical variations.

### Parameters
- `reference_beats`: A 1D `np.ndarray` containing ground-truth beat timestamps in seconds.
- `estimated_beats`: A 1D `np.ndarray` containing the estimated beat timestamps in seconds.
- `cemgil_sigma`, default `0.04`: A float representing the standard deviation (sigma) of the Gaussian error window used to weight the proximity of estimated beats to reference beats.

### Input
- **Data Format:** Both `reference_beats` and `estimated_beats` must be 1D `np.ndarray` objects containing timestamps in seconds.
- **Preconditions:** Inputs should be sorted by time. It is recommended to use `mir_eval.beat.trim_beats` on both arrays prior to evaluation to ensure consistent alignment and duration.

### Output
Returns a tuple of two floats:
- `cemgil_score`: The score calculated against the original reference beat sequence.
- `cemgil_max`: The maximum score achieved across all considered metrical variations (e.g., double-time, half-time, or off-beat shifts).

### Valid Call Patterns
```python
# Standard usage with default sigma
cemgil_score, cemgil_max = mir_eval.beat.cemgil(reference_beats, estimated_beats)

# Usage with custom sigma
cemgil_score, cemgil_max = mir_eval.beat.cemgil(reference_beats, estimated_beats, cemgil_sigma=0.05)
```

### LLM Instruction Prompt
- When calling `mir_eval.beat.cemgil`, ensure that both `reference_beats` and `estimated_beats` are 1D NumPy arrays of floats representing time in seconds.
- Always apply `mir_eval.beat.trim_beats` to the input arrays before passing them to this function to ensure the evaluation is robust to leading/trailing silence.
- The function returns two values; ensure both are captured in the assignment.

### Prompt Snippet
```text
# Ensure inputs are trimmed before evaluation
ref = mir_eval.beat.trim_beats(reference_beats)
est = mir_eval.beat.trim_beats(estimated_beats)
score, max_score = mir_eval.beat.cemgil(ref, est)
```

### Common Failure Modes
- **Unsorted Inputs:** Providing unsorted arrays may lead to incorrect matching or unexpected behavior in the Gaussian error calculation.
- **Empty Arrays:** Passing empty arrays may result in errors or undefined scores; ensure inputs are validated using `mir_eval.beat.validate` if the source is untrusted.
- **Unit Mismatch:** Providing timestamps in samples instead of seconds will cause the metric to fail or produce meaningless results.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure inputs are sorted and in seconds
reference_beats = np.sort(reference_beats)
estimated_beats = np.sort(estimated_beats)

# Trim beats to remove non-beat segments
ref = mir_eval.beat.trim_beats(reference_beats)
est = mir_eval.beat.trim_beats(estimated_beats)

# Compute score
score, max_score = mir_eval.beat.cemgil(ref, est)
```

## API Test: `python:mir_eval.beat.continuity`

### Signature
```python
def continuity(reference_beats, estimated_beats, continuity_phase_threshold=0.175, continuity_period_threshold=0.175)
```
_Source: source/mir_eval/beat.py:410_

_Source doc:_ Get metrics based on how much of the estimated beat sequence is
continually correct.

Examples
--------
>>> reference_beats = mir_eval.io.load_events('reference.txt')
>>> reference_beats = mir_eval.beat.trim_beats(reference_beats)
>>> estimated_beats = mir_eval.io.load_events('estimated.txt')
>>> estimated_beats = mir_eval.beat.trim_beats(estimated_beats)
>>> CMLc, CMLt, AMLc, AMLt = mir_eval.beat.continuity(reference_beats,
                                                      estimated_beats)

Parameters
----------
reference_beats : np.ndarray
    reference beat times, in seconds
estimated_beats : np.ndarray
    query beat times, in seconds
continuity_phase_threshold : float
    Allowable ratio of how far is the estimated beat
    can be from the reference beat
    (Default value = 0.175)
continuity_period_threshold : float
    Allowable distance between the inter-beat-interval
    and the inter-annotation-interval
    (Default value = 0.175)

Returns
-------
CMLc : float
    Correct metric level, continuous accuracy
CMLt : float
    Correct metric level, total accuracy (continuity not required)
AMLc : float
    Any metric level, continuous accuracy
AMLt : float
    Any metric level, total accuracy (continuity not required)

### Goal
Computes beat tracking accuracy metrics that evaluate the continuity of the estimated beat sequence relative to a ground-truth reference.

### Parameters
- `reference_beats`: A 1D NumPy array of ground-truth beat timestamps in seconds.
- `estimated_beats`: A 1D NumPy array of estimated beat timestamps in seconds.
- `continuity_phase_threshold`, default `0.175`: The maximum allowable ratio of the inter-beat interval for the phase deviation between estimated and reference beats.
- `continuity_period_threshold`, default `0.175`: The maximum allowable relative difference between the estimated inter-beat interval and the reference inter-annotation interval.

### Input
- **Data Format:** Both `reference_beats` and `estimated_beats` must be 1D NumPy arrays of floats representing time in seconds.
- **Preconditions:** Inputs should be sorted by time. It is recommended to use `mir_eval.beat.trim_beats` on both arrays prior to evaluation to ensure consistent temporal alignment.

### Output
Returns a tuple of four floats: `(CMLc, CMLt, AMLc, AMLt)`.
- `CMLc`: Correct Metric Level, continuous accuracy.
- `CMLt`: Correct Metric Level, total accuracy (continuity not required).
- `AMLc`: Any Metric Level, continuous accuracy.
- `AMLt`: Any Metric Level, total accuracy (continuity not required).

### Valid Call Patterns
```python
CMLc, CMLt, AMLc, AMLt = mir_eval.beat.continuity(reference_beats, estimated_beats)
```

### LLM Instruction Prompt
- Always ensure `reference_beats` and `estimated_beats` are 1D NumPy arrays of floats.
- Always apply `mir_eval.beat.trim_beats` to both input arrays before passing them to this function to ensure valid evaluation.
- The function returns four distinct float values; ensure the caller unpacks all four.

### Prompt Snippet
```text
# Example usage:
CMLc, CMLt, AMLc, AMLt = mir_eval.beat.continuity(ref_beats, est_beats)
```

### Common Failure Modes
- **Unsorted Inputs:** Passing unsorted arrays will lead to incorrect metric calculations; ensure arrays are sorted by time.
- **Unit Mismatch:** Providing timestamps in samples instead of seconds will result in invalid accuracy scores.
- **Empty Arrays:** Passing empty arrays may cause errors; validate inputs using `mir_eval.beat.validate` if necessary.

### Fix Code Hint
```python
import mir_eval
import numpy as np

# Ensure inputs are sorted and trimmed
ref = np.sort(reference_beats)
est = np.sort(estimated_beats)
ref = mir_eval.beat.trim_beats(ref)
est = mir_eval.beat.trim_beats(est)

# Compute continuity
CMLc, CMLt, AMLc, AMLt = mir_eval.beat.continuity(ref, est)
```

## API Test: `python:mir_eval.beat.evaluate`

### Signature
```python
def evaluate(reference_beats, estimated_beats, **kwargs)
```
_Source: source/mir_eval/beat.py:715_

_Source doc:_ Compute all metrics for the given reference and estimated annotations.

Examples
--------
>>> reference_beats = mir_eval.io.load_events('reference.txt')
>>> estimated_beats = mir_eval.io.load_events('estimated.txt')
>>> scores = mir_eval.beat.evaluate(reference_beats, estimated_beats)

Parameters
----------
reference_beats : np.ndarray
    Reference beat times, in seconds
estimated_beats : np.ndarray
    Query beat times, in seconds
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of standard beat-tracking evaluation metrics by comparing estimated beat timestamps against ground-truth reference annotations.

### Parameters
- `reference_beats`: A 1D NumPy array containing the ground-truth beat timestamps in seconds.
- `estimated_beats`: A 1D NumPy array containing the estimated beat timestamps in seconds.
- `kwargs`: Optional keyword arguments passed directly to underlying metric or preprocessing functions (e.g., for adjusting tolerances).

### Input
- **Data Format:** Both `reference_beats` and `estimated_beats` must be 1D NumPy arrays of floats representing time in seconds.
- **Preconditions:** Arrays must be sorted by time. It is recommended to use `mir_eval.beat.trim_beats` on both inputs prior to evaluation to ensure consistent temporal boundaries.

### Output
Returns a `dict` where keys are strings representing the names of the computed metrics (e.g., F-measure, Cemgil, Continuity) and values are `float` scores.

### Valid Call Patterns
```python
import mir_eval
# Load data
reference_beats = mir_eval.io.load_events('reference.txt')
estimated_beats = mir_eval.io.load_events('estimated.txt')
# Optional: trim beats to consistent range
reference_beats = mir_eval.beat.trim_beats(reference_beats)
estimated_beats = mir_eval.beat.trim_beats(estimated_beats)
# Evaluate
scores = mir_eval.beat.evaluate(reference_beats, estimated_beats)
```

### LLM Instruction Prompt
- Always ensure input arrays are 1D NumPy arrays of floats.
- Remind the user to sort timestamps chronologically and consider using `mir_eval.beat.trim_beats` to ensure the reference and estimated sets are comparable.
- Note that `mir_eval` uses 4-decimal point rounding and bipartite matching, which may differ from legacy MIREX scripts.

### Prompt Snippet
```text
# Example of calling mir_eval.beat.evaluate
scores = mir_eval.beat.evaluate(ref_beats, est_beats)
```

### Common Failure Modes
- **Unsorted Input:** Passing unsorted arrays will lead to incorrect metric calculations; ensure arrays are sorted by time.
- **Empty Arrays:** Passing empty arrays may cause errors in metric computation; validate inputs using `mir_eval.beat.validate` if necessary.
- **Unit Mismatch:** Providing inputs in samples or milliseconds instead of seconds will result in invalid scores.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure inputs are sorted and in seconds
ref = np.sort(reference_beats)
est = np.sort(estimated_beats)

# Validate before evaluation
mir_eval.beat.validate(ref, est)
scores = mir_eval.beat.evaluate(ref, est)
```

## API Test: `python:mir_eval.beat.f_measure`

### Signature
```python
def f_measure(reference_beats, estimated_beats, f_measure_threshold=0.07)
```
_Source: source/mir_eval/beat.py:136_

_Source doc:_ Compute the F-measure of correct vs incorrectly predicted beats.
"Correctness" is determined over a small window.

Examples
--------
>>> reference_beats = mir_eval.io.load_events('reference.txt')
>>> reference_beats = mir_eval.beat.trim_beats(reference_beats)
>>> estimated_beats = mir_eval.io.load_events('estimated.txt')
>>> estimated_beats = mir_eval.beat.trim_beats(estimated_beats)
>>> f_measure = mir_eval.beat.f_measure(reference_beats,
                                        estimated_beats)

Parameters
----------
reference_beats : np.ndarray
    reference beat times, in seconds
estimated_beats : np.ndarray
    estimated beat times, in seconds
f_measure_threshold : float
    Window size, in seconds
    (Default value = 0.07)

Returns
-------
f_score : float
    The computed F-measure score

### Goal
Computes the F-measure for beat tracking evaluation by determining the proportion of estimated beat times that fall within a specified temporal window of reference beat times.

### Parameters
- `reference_beats`: A 1D `np.ndarray` containing ground-truth beat timestamps in seconds.
- `estimated_beats`: A 1D `np.ndarray` containing the estimated beat timestamps in seconds.
- `f_measure_threshold`, default `0.07`: A float representing the tolerance window (in seconds) around each reference beat; an estimated beat is considered "correct" if it falls within this window.

### Input
- **Data Format:** Both `reference_beats` and `estimated_beats` must be 1D NumPy arrays of floats.
- **Preconditions:** Inputs should be sorted by time. It is recommended to use `mir_eval.beat.trim_beats` on both arrays prior to evaluation to ensure consistent temporal alignment.

### Output
Returns `f_score` (float): The calculated F-measure, representing the harmonic mean of precision and recall for the beat detection task.

### Valid Call Patterns
```python
import mir_eval
# Assuming reference_beats and estimated_beats are pre-loaded 1D np.ndarrays
f_score = mir_eval.beat.f_measure(reference_beats, estimated_beats)

# With custom threshold
f_score = mir_eval.beat.f_measure(reference_beats, estimated_beats, f_measure_threshold=0.1)
```

### LLM Instruction Prompt
- When calling `mir_eval.beat.f_measure`, ensure both input arrays are 1D NumPy arrays containing timestamps in seconds.
- Always verify that inputs are sorted chronologically.
- Use `mir_eval.beat.trim_beats` on both inputs before passing them to the function to ensure the evaluation is performed on the same temporal range.

### Prompt Snippet
```text
# Example usage of mir_eval.beat.f_measure
f_score = mir_eval.beat.f_measure(reference_beats, estimated_beats, f_measure_threshold=0.07)
```

### Common Failure Modes
- **Unsorted Inputs:** Passing unsorted arrays may lead to incorrect matching logic.
- **Mismatched Units:** Providing inputs in milliseconds instead of seconds will result in invalid scores.
- **Empty Arrays:** Passing empty arrays may cause errors; ensure inputs are validated using `mir_eval.beat.validate` if the source of the data is untrusted.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure inputs are sorted and trimmed
ref = np.sort(reference_beats)
est = np.sort(estimated_beats)
ref = mir_eval.beat.trim_beats(ref)
est = mir_eval.beat.trim_beats(est)

score = mir_eval.beat.f_measure(ref, est, f_measure_threshold=0.07)
```

## API Test: `python:mir_eval.beat.goto`

### Signature
```python
def goto(reference_beats, estimated_beats, goto_threshold=0.35, goto_mu=0.2, goto_sigma=0.2)
```
_Source: source/mir_eval/beat.py:230_

_Source doc:_ Calculate Goto's score, a binary 1 or 0 depending on some specific
heuristic criteria

Examples
--------
>>> reference_beats = mir_eval.io.load_events('reference.txt')
>>> reference_beats = mir_eval.beat.trim_beats(reference_beats)
>>> estimated_beats = mir_eval.io.load_events('estimated.txt')
>>> estimated_beats = mir_eval.beat.trim_beats(estimated_beats)
>>> goto_score = mir_eval.beat.goto(reference_beats, estimated_beats)

Parameters
----------
reference_beats : np.ndarray
    reference beat times, in seconds
estimated_beats : np.ndarray
    query beat times, in seconds
goto_threshold : float
    Threshold of beat error for a beat to be "correct"
    (Default value = 0.35)
goto_mu : float
    The mean of the beat errors in the continuously correct
    track must be less than this
    (Default value = 0.2)
goto_sigma : float
    The std of the beat errors in the continuously correct track must
    be less than this
    (Default value = 0.2)

Returns
-------
goto_score : float
    Either 1.0 or 0.0 if some specific criteria are met

### Goal
Calculates the Goto score, a binary metric that evaluates beat tracking performance based on heuristic criteria regarding the mean and standard deviation of beat errors within a continuously correct track.

### Parameters
- `reference_beats`: A 1D NumPy array of ground-truth beat timestamps in seconds.
- `estimated_beats`: A 1D NumPy array of estimated beat timestamps in seconds.
- `goto_threshold`, default `0.35`: The maximum allowable beat error (in seconds) for an individual beat to be considered "correct."
- `goto_mu`, default `0.2`: The maximum allowable mean of beat errors within the identified continuously correct track.
- `goto_sigma`, default `0.2`: The maximum allowable standard deviation of beat errors within the identified continuously correct track.

### Input
- **Data Format:** Both `reference_beats` and `estimated_beats` must be 1D NumPy arrays containing floats representing time in seconds.
- **Preconditions:** Inputs should be sorted by time. It is recommended to use `mir_eval.beat.trim_beats` on both arrays prior to evaluation to ensure consistent temporal alignment.

### Output
Returns a `float` representing the `goto_score`, which is either `1.0` (criteria met) or `0.0` (criteria not met).

### Valid Call Patterns
```python
import mir_eval
# Assuming reference_beats and estimated_beats are pre-loaded and trimmed
goto_score = mir_eval.beat.goto(reference_beats, estimated_beats)
```

### LLM Instruction Prompt
- When calling `mir_eval.beat.goto`, ensure that both `reference_beats` and `estimated_beats` are 1D NumPy arrays of floats.
- Always perform `mir_eval.beat.trim_beats` on input arrays before passing them to this function to ensure valid evaluation.
- The function returns a binary float (1.0 or 0.0); do not expect a continuous probability score.

### Prompt Snippet
```text
# Example usage of mir_eval.beat.goto
import mir_eval
# reference_beats and estimated_beats must be 1D np.ndarray of seconds
score = mir_eval.beat.goto(reference_beats, estimated_beats, goto_threshold=0.35)
```

### Common Failure Modes
- **Unsorted Inputs:** Providing unsorted beat arrays will lead to incorrect error calculations.
- **Empty Arrays:** Passing empty arrays may result in errors or unexpected behavior; ensure inputs are validated using `mir_eval.beat.validate` if necessary.
- **Unit Mismatch:** Providing timestamps in samples instead of seconds will cause the heuristic thresholds to fail.

### Fix Code Hint
```python
# Ensure inputs are sorted and trimmed
reference_beats = np.sort(reference_beats)
estimated_beats = np.sort(estimated_beats)
reference_beats = mir_eval.beat.trim_beats(reference_beats)
estimated_beats = mir_eval.beat.trim_beats(estimated_beats)
score = mir_eval.beat.goto(reference_beats, estimated_beats)
```

## API Test: `python:mir_eval.beat.information_gain`

### Signature
```python
def information_gain(reference_beats, estimated_beats, bins=41)
```
_Source: source/mir_eval/beat.py:586_

_Source doc:_ Get the information gain - K-L divergence of the beat error histogram
to a uniform histogram

Examples
--------
>>> reference_beats = mir_eval.io.load_events('reference.txt')
>>> reference_beats = mir_eval.beat.trim_beats(reference_beats)
>>> estimated_beats = mir_eval.io.load_events('estimated.txt')
>>> estimated_beats = mir_eval.beat.trim_beats(estimated_beats)
>>> information_gain = mir_eval.beat.information_gain(reference_beats,
                                                      estimated_beats)

Parameters
----------
reference_beats : np.ndarray
    reference beat times, in seconds
estimated_beats : np.ndarray
    query beat times, in seconds
bins : int
    Number of bins in the beat error histogram
    (Default value = 41)

Returns
-------
information_gain_score : float
    Entropy of beat error histogram

### Goal
Computes the information gain of a beat tracking system by calculating the Kullback-Leibler (K-L) divergence between the beat error histogram and a uniform distribution.

### Parameters
- `reference_beats`: A 1D `np.ndarray` containing ground-truth beat timestamps in seconds.
- `estimated_beats`: A 1D `np.ndarray` containing the estimated beat timestamps in seconds.
- `bins`, default `41`: An integer specifying the number of bins used to construct the beat error histogram.

### Input
- **Data Format:** Both `reference_beats` and `estimated_beats` must be 1D NumPy arrays of floats representing time in seconds.
- **Preconditions:** Inputs should be sorted by time. It is recommended to use `mir_eval.beat.trim_beats` on both arrays prior to evaluation to ensure they are within a comparable range.

### Output
Returns a `float` representing the information gain score, which quantifies the entropy of the beat error histogram.

### Valid Call Patterns
```python
import mir_eval
# Assuming reference_beats and estimated_beats are pre-loaded np.ndarrays
score = mir_eval.beat.information_gain(reference_beats, estimated_beats)
```

### LLM Instruction Prompt
- When calling `mir_eval.beat.information_gain`, ensure that both `reference_beats` and `estimated_beats` are 1D NumPy arrays of timestamps in seconds. Always apply `mir_eval.beat.trim_beats` to the inputs before passing them to this function to ensure consistent evaluation boundaries.

### Prompt Snippet
```text
# Example usage for information gain calculation
reference_beats = mir_eval.io.load_events('reference.txt')
estimated_beats = mir_eval.io.load_events('estimated.txt')
# Trim beats to ensure alignment
ref_trimmed = mir_eval.beat.trim_beats(reference_beats)
est_trimmed = mir_eval.beat.trim_beats(estimated_beats)
ig_score = mir_eval.beat.information_gain(ref_trimmed, est_trimmed)
```

### Common Failure Modes
- **Unsorted Inputs:** Providing arrays that are not sorted by time will lead to incorrect error calculations.
- **Mismatched Units:** Passing timestamps in samples instead of seconds will result in invalid metric values.
- **Empty Arrays:** Passing empty arrays may cause errors or return non-meaningful results; ensure inputs are validated using `mir_eval.beat.validate` if necessary.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure inputs are sorted and trimmed
reference_beats = np.sort(reference_beats)
estimated_beats = np.sort(estimated_beats)
reference_beats = mir_eval.beat.trim_beats(reference_beats)
estimated_beats = mir_eval.beat.trim_beats(estimated_beats)

score = mir_eval.beat.information_gain(reference_beats, estimated_beats)
```

## API Test: `python:mir_eval.beat.p_score`

### Signature
```python
def p_score(reference_beats, estimated_beats, p_score_threshold=0.2)
```
_Source: source/mir_eval/beat.py:330_

_Source doc:_ Get McKinney's P-score.
Based on the autocorrelation of the reference and estimated beats

Examples
--------
>>> reference_beats = mir_eval.io.load_events('reference.txt')
>>> reference_beats = mir_eval.beat.trim_beats(reference_beats)
>>> estimated_beats = mir_eval.io.load_events('estimated.txt')
>>> estimated_beats = mir_eval.beat.trim_beats(estimated_beats)
>>> p_score = mir_eval.beat.p_score(reference_beats, estimated_beats)

Parameters
----------
reference_beats : np.ndarray
    reference beat times, in seconds
estimated_beats : np.ndarray
    query beat times, in seconds
p_score_threshold : float
    Window size will be
    ``p_score_threshold*np.median(inter_annotation_intervals)``,
    (Default value = 0.2)

Returns
-------
correlation : float
    McKinney's P-score

### Goal
Computes McKinney's P-score, a metric for evaluating beat tracking accuracy based on the autocorrelation of reference and estimated beat sequences.

### Parameters
- `reference_beats`: A 1D NumPy array of ground-truth beat timestamps in seconds.
- `estimated_beats`: A 1D NumPy array of estimated beat timestamps in seconds.
- `p_score_threshold`, default `0.2`: A float determining the window size for the P-score calculation, defined as the product of this threshold and the median inter-annotation interval of the reference beats.

### Input
- **Data Format:** Both `reference_beats` and `estimated_beats` must be 1D NumPy arrays containing timestamps in seconds.
- **Preconditions:** Inputs should be sorted by time. It is recommended to use `mir_eval.beat.trim_beats` on both arrays prior to evaluation to ensure consistent temporal alignment.

### Output
Returns a `float` representing the P-score, which quantifies the correlation between the reference and estimated beat sequences.

### Valid Call Patterns
```python
import mir_eval
# Assuming reference_beats and estimated_beats are pre-loaded and trimmed
score = mir_eval.beat.p_score(reference_beats, estimated_beats)
```

### LLM Instruction Prompt
- When calling `mir_eval.beat.p_score`, ensure that both `reference_beats` and `estimated_beats` are 1D NumPy arrays of floats representing time in seconds.
- Always apply `mir_eval.beat.trim_beats` to both input arrays before passing them to the function to ensure valid evaluation.
- The `p_score_threshold` is optional; only override the default `0.2` if specific research requirements necessitate a different window size.

### Prompt Snippet
```text
# Example usage for P-score calculation
reference_beats = mir_eval.io.load_events('ref.txt')
estimated_beats = mir_eval.io.load_events('est.txt')
# Trim beats to ensure valid input
ref_trimmed = mir_eval.beat.trim_beats(reference_beats)
est_trimmed = mir_eval.beat.trim_beats(estimated_beats)
score = mir_eval.beat.p_score(ref_trimmed, est_trimmed)
```

### Common Failure Modes
- **Unsorted Inputs:** Providing unsorted arrays will lead to incorrect autocorrelation results.
- **Inconsistent Units:** Passing timestamps in samples instead of seconds will cause the metric to fail or produce invalid scores.
- **Empty Arrays:** Passing empty arrays may result in errors during the median calculation of inter-annotation intervals.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure inputs are sorted and trimmed
ref = np.sort(reference_beats)
est = np.sort(estimated_beats)
ref = mir_eval.beat.trim_beats(ref)
est = mir_eval.beat.trim_beats(est)

score = mir_eval.beat.p_score(ref, est)
```

## API Test: `python:mir_eval.beat.trim_beats`

### Signature
```python
def trim_beats(beats, min_beat_time=5.0)
```
_Source: source/mir_eval/beat.py:57_

_Source doc:_ Remove beats before min_beat_time.  A common preprocessing step.

Parameters
----------
beats : np.ndarray
    Array of beat times in seconds.
min_beat_time : float
    Minimum beat time to allow
    (Default value = 5.)

Returns
-------
beats_trimmed : np.ndarray
    Trimmed beat array.

### Goal
Removes beat event timestamps that occur before a specified threshold time to facilitate preprocessing of beat tracking evaluation data.

### Parameters
- `beats`: A 1D NumPy array containing beat timestamps in seconds.
- `min_beat_time`, default `5.0`: A float representing the minimum time threshold in seconds; any beat occurring at a time less than this value will be removed.

### Input
- **Data:** A 1D `np.ndarray` of floats representing time in seconds.
- **Preconditions:** The input `beats` array should be sorted by time, as is standard for `mir_eval` event arrays.

### Output
Returns a 1D `np.ndarray` containing only the beat timestamps that are greater than or equal to `min_beat_time`.

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example from project documentation
reference_beats = mir_eval.io.load_events('reference.txt')
reference_beats = mir_eval.beat.trim_beats(reference_beats, min_beat_time=5.0)
```

### LLM Instruction Prompt
- When calling `mir_eval.beat.trim_beats`, ensure the input `beats` is a 1D NumPy array of timestamps in seconds.
- Always provide `min_beat_time` as a float if the default of 5.0 is not appropriate for the specific audio file duration or evaluation requirements.
- Use this function as a preprocessing step before passing beat arrays to `mir_eval.beat.evaluate`.

### Prompt Snippet
```text
# Preprocess beat arrays by removing initial segments
beats = mir_eval.beat.trim_beats(beats, min_beat_time=5.0)
```

### Common Failure Modes
- **Input Type:** Passing a list instead of a `np.ndarray` may cause errors in downstream `mir_eval` functions that expect NumPy arrays.
- **Empty Output:** If `min_beat_time` is set higher than the latest beat in the array, the function will return an empty array, which may cause errors in subsequent evaluation metrics.
- **Unsorted Input:** While the function filters by time, downstream evaluation functions (like `mir_eval.beat.evaluate`) require the input arrays to be sorted; ensure the input is sorted before or after trimming.

### Fix Code Hint
```python
import numpy as np
# Ensure input is a sorted numpy array
beats = np.sort(np.array(beats))
trimmed_beats = mir_eval.beat.trim_beats(beats, min_beat_time=5.0)
```

## API Test: `python:mir_eval.beat.validate`

### Signature
```python
def validate(reference_beats, estimated_beats)
```
_Source: source/mir_eval/beat.py:77_

_Source doc:_ Check that the input annotations to a metric look like valid beat time
arrays, and throws helpful errors if not.

Parameters
----------
reference_beats : np.ndarray
    reference beat times, in seconds
estimated_beats : np.ndarray
    estimated beat times, in seconds

### Goal
Validates that beat time arrays conform to the expected format and constraints required for beat evaluation metrics.

### Parameters
- `reference_beats`: A 1D NumPy array containing the ground-truth beat timestamps in seconds.
- `estimated_beats`: A 1D NumPy array containing the estimated beat timestamps in seconds.

### Input
- **Data Format:** Both inputs must be 1D `np.ndarray` objects.
- **Preconditions:** Time values must be represented in seconds. While not explicitly enforced by `validate`, most downstream `mir_eval.beat` metrics require these arrays to be sorted by time.

### Output
Returns `None` if the inputs are valid. If the inputs do not conform to the expected format (e.g., incorrect dimensions or types), it raises an exception with a descriptive error message.

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example inferred from signature
ref = np.array([1.0, 2.0, 3.0])
est = np.array([1.1, 2.1, 3.1])
mir_eval.beat.validate(ref, est)
```

### LLM Instruction Prompt
- Always ensure `reference_beats` and `estimated_beats` are 1D NumPy arrays before passing them to `mir_eval.beat.validate`.
- Use this function as a pre-computation check to ensure data integrity before calling `mir_eval.beat.evaluate`.

### Prompt Snippet
```text
# Validate beat arrays before evaluation
mir_eval.beat.validate(reference_beats, estimated_beats)
scores = mir_eval.beat.evaluate(reference_beats, estimated_beats)
```

### Common Failure Modes
- **Dimension Mismatch:** Passing multi-dimensional arrays instead of 1D arrays will trigger a validation error.
- **Unsorted Data:** While `validate` checks format, downstream metrics may fail if the arrays are not sorted by time; ensure arrays are sorted prior to evaluation.
- **Non-numeric types:** Passing lists or arrays containing non-numeric types will cause the validation to fail.

### Fix Code Hint
```python
# Ensure arrays are 1D and sorted
reference_beats = np.sort(np.array(reference_beats).flatten())
estimated_beats = np.sort(np.array(estimated_beats).flatten())
mir_eval.beat.validate(reference_beats, estimated_beats)
```

## API Test: `python:mir_eval.chord.InvalidChordException`

### Signature
```python
class InvalidChordException(Exception)
```
_Source: source/mir_eval/chord.py:113_

_Source doc:_ Exception class for suspect / invalid chord labels

### Goal
Provides a specialized exception class raised by the `mir_eval.chord` module when encountering malformed or unrecognized chord labels during evaluation or validation.

### Parameters
- `message`, default `''`: A descriptive string explaining the nature of the validation error.
- `chord_label`, default `None`: The specific chord label string that triggered the exception.

### Input
The caller does not provide input directly to this class; it is instantiated internally by `mir_eval.chord` functions (such as `validate()` or `evaluate()`) when processing chord label annotations that do not conform to the expected syntax (e.g., `C:maj`).

### Output
Returns `mir_eval.chord.InvalidChordException` — An exception object that signals a failure in chord label parsing or validation.

### Valid Call Patterns
```python
# This exception is typically raised by the library, but can be manually raised:
raise mir_eval.chord.InvalidChordException(message="Invalid chord syntax", chord_label="C:unknown")
```

### LLM Instruction Prompt
- Use `mir_eval.chord.InvalidChordException` to handle or catch errors specifically related to chord label parsing.
- Do not attempt to instantiate this class unless you are implementing custom validation logic that mirrors the `mir_eval.chord` module's requirements.
- Ensure that any chord labels passed to the `chord_label` parameter are strings.

### Prompt Snippet
```text
# Example of catching the exception during chord evaluation
try:
    scores = mir_eval.chord.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
except mir_eval.chord.InvalidChordException as e:
    print(f"Chord validation failed: {e}")
```

### Common Failure Modes
- **Malformed Labels:** Passing chord labels that do not follow the standard `mir_eval` syntax (e.g., missing root or quality components).
- **Uncaught Exceptions:** Failing to wrap `mir_eval.chord` operations in a `try-except` block when processing user-provided or unverified annotation files, leading to program termination.
- **Incorrect Label Format:** Providing non-string types as chord labels, which may cause the underlying validation logic to fail before this exception is even raised.

### Fix Code Hint
```python
# Ensure labels are cleaned or validated against the expected vocabulary before evaluation
import mir_eval
# If a label is invalid, catch the exception and log the problematic label
try:
    mir_eval.chord.validate_labels(labels)
except mir_eval.chord.InvalidChordException:
    # Handle or filter out the invalid labels
    pass
```

## API Test: `python:mir_eval.chord.directional_hamming_distance`

### Signature
```python
def directional_hamming_distance(reference_intervals, estimated_intervals)
```
_Source: source/mir_eval/chord.py:1358_

_Source doc:_ Compute the directional hamming distance between reference and
estimated intervals as defined by [#harte2010towards]_ and used for MIREX
'OverSeg', 'UnderSeg' and 'MeanSeg' measures.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> overseg = 1 - mir_eval.chord.directional_hamming_distance(
...     ref_intervals, est_intervals)
>>> underseg = 1 - mir_eval.chord.directional_hamming_distance(
...     est_intervals, ref_intervals)
>>> seg = min(overseg, underseg)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2), dtype=float
    Reference chord intervals to score against.
estimated_intervals : np.ndarray, shape=(m, 2), dtype=float
    Estimated chord intervals to score against.

Returns
-------
directional hamming distance : float
    directional hamming distance between reference intervals and
    estimated intervals.

### Goal
Computes the directional Hamming distance between two sets of chord intervals to facilitate the calculation of segmentation-based metrics like OverSeg and UnderSeg.

### Parameters
- `reference_intervals`: An $N \times 2$ NumPy array of floats representing the ground-truth chord start and end times in seconds.
- `estimated_intervals`: An $M \times 2$ NumPy array of floats representing the estimated chord start and end times in seconds.

### Input
- **Data Format:** Intervals must be provided as $N \times 2$ NumPy arrays where each row is `[start, end]`.
- **Preconditions:** Intervals must be sorted by time. It is recommended to use `mir_eval.util.adjust_intervals` to ensure estimated intervals span the same total duration as reference intervals before evaluation.

### Output
Returns a `float` representing the directional Hamming distance between the two sets of intervals.

### Valid Call Patterns
```python
overseg = 1 - mir_eval.chord.directional_hamming_distance(ref_intervals, est_intervals)
underseg = 1 - mir_eval.chord.directional_hamming_distance(est_intervals, ref_intervals)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.directional_hamming_distance`, ensure both `reference_intervals` and `estimated_intervals` are NumPy arrays of shape `(n, 2)` and `(m, 2)` respectively.
- Always perform the calculation in both directions (ref vs est, and est vs ref) if you intend to derive MIREX-style segmentation metrics like OverSeg or UnderSeg.

### Prompt Snippet
```text
# Example of calculating segmentation metrics
overseg = 1 - mir_eval.chord.directional_hamming_distance(ref_intervals, est_intervals)
underseg = 1 - mir_eval.chord.directional_hamming_distance(est_intervals, ref_intervals)
```

### Common Failure Modes
- **Unsorted Intervals:** Passing unsorted interval arrays will lead to incorrect distance calculations; ensure arrays are sorted by start time.
- **Mismatched Durations:** If the total duration of the reference intervals differs significantly from the estimated intervals, the resulting distance may not be meaningful; use `mir_eval.util.adjust_intervals` to normalize.
- **Input Shape:** Passing 1D arrays or lists instead of $N \times 2$ NumPy arrays will raise a `ValueError`.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure intervals are sorted and properly shaped
ref_intervals = np.sort(ref_intervals, axis=0)
est_intervals = np.sort(est_intervals, axis=0)

# Calculate distance
dist = mir_eval.chord.directional_hamming_distance(ref_intervals, est_intervals)
```

## API Test: `python:mir_eval.chord.encode`

### Signature
```python
def encode(chord_label, reduce_extended_chords=False, strict_bass_intervals=False)
```
_Source: source/mir_eval/chord.py:470_

_Source doc:_ Translate a chord label to numerical representations for evaluation.

Parameters
----------
chord_label : str
    Chord label to encode.
reduce_extended_chords : bool
    Whether to map the upper voicings of extended chords (9's, 11's, 13's)
    to semitone extensions.
    (Default value = False)
strict_bass_intervals : bool
    Whether to require that the bass scale degree is present in the chord.
    (Default value = False)

Returns
-------
root_number : int
    Absolute semitone of the chord's root.
semitone_bitmap : np.ndarray, dtype=int
    12-dim vector of relative semitones in the chord spelling.
bass_number : int
    Relative semitone of the chord's bass note, e.g. 0=root, 7=fifth, etc.

### Goal
Translates a string-based chord label into a standardized numerical representation (root, semitone bitmap, and bass note) suitable for quantitative comparison in MIR chord recognition tasks.

### Parameters
- `chord_label`: A string representing the chord (e.g., "C:maj", "G#:min7").
- `reduce_extended_chords`, default `False`: If `True`, simplifies complex extensions (9ths, 11ths, 13ths) into their corresponding semitone intervals within the octave.
- `strict_bass_intervals`, default `False`: If `True`, enforces that the specified bass note must exist within the chord's constituent intervals; otherwise, it allows non-chord tones in the bass.

### Input
- **Format:** A single string following standard chord syntax (e.g., `Root:Suffix`).
- **Preconditions:** The input string must be a valid chord label recognized by the library's parser.

### Output
Returns a tuple containing:
- `root_number` (int): The absolute semitone of the root (0-11, where 0=C).
- `semitone_bitmap` (np.ndarray): A 12-element binary vector (dtype=int) where 1 indicates the presence of a semitone relative to the root.
- `bass_number` (int): The relative semitone of the bass note (0-11, relative to the root).

### Valid Call Patterns
```python
# Inferred from signature
root, bitmap, bass = mir_eval.chord.encode("C:maj7", reduce_extended_chords=True)
```

### LLM Instruction Prompt
- Always pass `chord_label` as a string.
- Use `reduce_extended_chords` and `strict_bass_intervals` as boolean flags to control the granularity of the encoding.
- Ensure the returned `semitone_bitmap` is treated as a 12-dimensional NumPy array.

### Prompt Snippet
```text
# Example of encoding a chord label
import mir_eval
root, bitmap, bass = mir_eval.chord.encode("C:maj7")
```

### Common Failure Modes
- **InvalidChordException:** Raised if the `chord_label` string does not conform to the expected syntax.
- **Type Errors:** Passing non-boolean values to `reduce_extended_chords` or `strict_bass_intervals`.
- **Bass Mismatch:** If `strict_bass_intervals=True` and the provided bass note is not part of the chord's interval set, the function may raise an error or fail to validate the label.

### Fix Code Hint
```python
# Ensure labels are stripped of whitespace and follow standard syntax
try:
    root, bitmap, bass = mir_eval.chord.encode(label.strip())
except mir_eval.chord.InvalidChordException:
    # Handle or log invalid labels
    pass
```

## API Test: `python:mir_eval.chord.encode_many`

### Signature
```python
def encode_many(chord_labels, reduce_extended_chords=False)
```
_Source: source/mir_eval/chord.py:522_

_Source doc:_ Translate a set of chord labels to numerical representations for sane
evaluation.

Parameters
----------
chord_labels : list
    Set of chord labels to encode.
reduce_extended_chords : bool
    Whether to map the upper voicings of extended chords (9's, 11's, 13's)
    to semitone extensions.
    (Default value = False)

Returns
-------
root_number : np.ndarray, dtype=int
    Absolute semitone of the chord's root.
interval_bitmap : np.ndarray, dtype=int
    12-dim vector of relative semitones in the given chord quality.
bass_number : np.ndarray, dtype=int
    Relative semitones of the chord's bass notes.

### Goal
Translates a collection of string-based chord labels into standardized numerical representations (root, interval bitmap, and bass) to facilitate consistent and reproducible chord evaluation.

### Parameters
- `chord_labels`: A list of strings representing chord labels (e.g., `['C:maj', 'D:min7']`).
- `reduce_extended_chords`, default `False`: A boolean flag; if `True`, upper extensions (9ths, 11ths, 13ths) are mapped down to their corresponding semitone intervals within the octave.

### Input
- **Data:** A list of strings.
- **Format:** Labels must follow standard syntax (e.g., `C:maj`, `G:7`).
- **Preconditions:** Labels must be valid according to the library's chord parser; invalid labels will raise an `InvalidChordException`.

### Output
Returns a tuple of three `np.ndarray` objects:
1. `root_number`: An array of integers representing the absolute semitone of the root (0-11).
2. `interval_bitmap`: An $N \times 12$ array of integers representing the presence of relative semitones in the chord quality.
3. `bass_number`: An array of integers representing the relative semitone of the bass note.

### Valid Call Patterns
```python
import mir_eval
# Example inferred from signature
labels = ['C:maj', 'D:min7', 'E:7']
roots, bitmaps, basses = mir_eval.chord.encode_many(labels, reduce_extended_chords=True)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.encode_many`, ensure the input is a list of strings.
- Always unpack the three returned NumPy arrays into distinct variables (`root_number`, `interval_bitmap`, `bass_number`).
- Use `reduce_extended_chords=True` if the evaluation task requires collapsing complex jazz voicings into standard triad/seventh-based interval bitmaps.

### Prompt Snippet
```text
# Example usage:
roots, bitmaps, basses = mir_eval.chord.encode_many(chord_labels_list, reduce_extended_chords=True)
```

### Common Failure Modes
- **InvalidChordException:** Occurs if a string in `chord_labels` does not conform to the expected chord syntax.
- **Type Mismatch:** Passing a single string instead of a list of strings will cause the function to iterate over characters or fail during processing.
- **Empty Input:** Passing an empty list may result in empty NumPy arrays, which can cause downstream indexing errors if not handled.

### Fix Code Hint
```python
# Ensure labels are valid and in a list
try:
    roots, bitmaps, basses = mir_eval.chord.encode_many(my_labels)
except mir_eval.chord.InvalidChordException as e:
    print(f"Check your chord label syntax: {e}")
```

## API Test: `python:mir_eval.chord.evaluate`

### Signature
```python
def evaluate(ref_intervals, ref_labels, est_intervals, est_labels, **kwargs)
```
_Source: source/mir_eval/chord.py:1524_

_Source doc:_ Compute weighted accuracy for all comparison functions for the given
reference and estimated annotations.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> scores = mir_eval.chord.evaluate(ref_intervals, ref_labels,
...                                  est_intervals, est_labels)

Parameters
----------
ref_intervals : np.ndarray, shape=(n, 2)
    Reference chord intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
ref_labels : list, shape=(n,)
    reference chord labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
est_intervals : np.ndarray, shape=(m, 2)
    estimated chord intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
est_labels : list, shape=(m,)
    estimated chord labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of weighted accuracy metrics for chord recognition by comparing estimated chord labels and intervals against ground-truth reference annotations.

### Parameters
- `ref_intervals`: A NumPy array of shape `(n, 2)` containing start and end times (in seconds) for each reference chord.
- `ref_labels`: A list of `n` strings representing the ground-truth chord labels (e.g., `C:maj`).
- `est_intervals`: A NumPy array of shape `(m, 2)` containing start and end times (in seconds) for each estimated chord.
- `est_labels`: A list of `m` strings representing the estimated chord labels.
- `kwargs`: Optional keyword arguments passed to underlying metric or preprocessing functions.

### Input
- **Data Format:** Intervals must be provided as `(n, 2)` NumPy arrays (start, end). Labels must be provided as lists of strings.
- **Preconditions:** Reference and estimated intervals should be sorted by time.
- **Compatibility:** Use `mir_eval.util.adjust_intervals` to ensure estimated intervals span the same duration as reference intervals before evaluation.
- **Chord Syntax:** Labels must follow standard syntax (e.g., `C:maj`). Invalid labels will raise an `InvalidChordException`.

### Output
Returns a `dict` where keys are metric names (strings) and values are the corresponding accuracy scores (floats).

### Valid Call Patterns
```python
scores = mir_eval.chord.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
```

### LLM Instruction Prompt
- Always ensure `ref_intervals` and `est_intervals` are `np.ndarray` objects of shape `(n, 2)` and `(m, 2)` respectively.
- Ensure `ref_labels` and `est_labels` are lists of strings.
- If intervals are not aligned, use `mir_eval.util.adjust_intervals` before calling this function.
- Do not invent metrics; the function returns a dictionary of pre-defined chord evaluation metrics.

### Prompt Snippet
```text
# Example of chord evaluation
import mir_eval
ref_intervals, ref_labels = mir_eval.io.load_labeled_intervals('ref.lab')
est_intervals, est_labels = mir_eval.io.load_labeled_intervals('est.lab')
scores = mir_eval.chord.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
```

### Common Failure Modes
- **Invalid Labels:** Providing chord labels that do not conform to the expected syntax (e.g., `C:maj`) will raise an `InvalidChordException`.
- **Unsorted Intervals:** Passing intervals that are not sorted by start time can lead to incorrect metric calculations.
- **Mismatched Durations:** If the total duration of estimated intervals does not match the reference, the evaluation may be biased; use `mir_eval.util.adjust_intervals` to normalize.

### Fix Code Hint
```python
# Ensure intervals are sorted and adjusted before evaluation
import mir_eval
ref_intervals, ref_labels = mir_eval.util.adjust_intervals(ref_intervals, ref_labels, t_min=0, t_max=duration)
est_intervals, est_labels = mir_eval.util.adjust_intervals(est_intervals, est_labels, t_min=0, t_max=duration)
scores = mir_eval.chord.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
```

## API Test: `python:mir_eval.chord.join`

### Signature
```python
def join(chord_root, quality='', extensions=None, bass='')
```
_Source: source/mir_eval/chord.py:435_

_Source doc:_ Join the parts of a chord into a complete chord label.

Parameters
----------
chord_root : str
    Root pitch class of the chord, e.g. 'C', 'Eb'
quality : str
    Quality of the chord, e.g. 'maj', 'hdim7'
    (Default value = '')
extensions : list
    Any added or absent scaled degrees for this chord, e.g. ['4', '\*3']
    (Default value = None)
bass : str
    Scale degree of the bass note, e.g. '5'.
    (Default value = '')

Returns
-------
chord_label : str
    A complete chord label.

### Goal
Constructs a standardized chord label string from individual components (root, quality, extensions, and bass) to ensure consistency in MIR chord annotation workflows.

### Parameters
- `chord_root`: The root pitch class of the chord (e.g., 'C', 'Eb', 'F#').
- `quality`, default `''`: The quality of the chord (e.g., 'maj', 'min', 'hdim7').
- `extensions`, default `None`: A list of strings representing added or absent scale degrees (e.g., ['4', '*3']).
- `bass`, default `''`: The scale degree of the bass note (e.g., '5').

### Input
The function accepts string and list inputs. While there are no strict file-format preconditions, the resulting labels must conform to the syntax expected by other `mir_eval.chord` functions. Note that invalid chord labels generated or provided to other evaluation functions in this module may raise an `InvalidChordException`.

### Output
Returns a `str` representing the complete, formatted chord label (e.g., 'C:maj7/5').

### Valid Call Patterns
```python
import mir_eval
# Example of joining components into a full chord label
label = mir_eval.chord.join('C', 'maj', ['7'], '5')
# Result: 'C:maj7/5'
```

### LLM Instruction Prompt
- When generating chord labels for `mir_eval` evaluation, use `mir_eval.chord.join` to ensure the output string adheres to the library's expected syntax.
- Ensure `chord_root` is a valid pitch class string.
- If `extensions` are provided, ensure they are passed as a list of strings.

### Prompt Snippet
```text
# Use mir_eval.chord.join to construct labels
label = mir_eval.chord.join(chord_root='C', quality='min', extensions=['7'], bass='b3')
```

### Common Failure Modes
- Passing non-string types for `chord_root`, `quality`, or `bass`, which may result in malformed label strings.
- Providing `extensions` as a single string instead of a list, which will cause the function to iterate over the characters of the string rather than the intended degrees.
- Generating labels that do not match the expected syntax of the `mir_eval.chord` evaluation metrics, leading to `InvalidChordException` during later processing.

### Fix Code Hint
```python
# Ensure extensions are always a list
extensions = ['7'] if extensions is None else extensions
label = mir_eval.chord.join(root, quality, extensions, bass)
```

## API Test: `python:mir_eval.chord.majmin`

### Signature
```python
def majmin(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:1106_

_Source doc:_ Compare chords along major-minor rules. Chords with qualities outside
Major/minor/no-chord are ignored.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.majmin(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
comparison_scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0], or -1 if the comparison is out of
    gamut.

### Goal
Computes a chord-wise comparison score based on major/minor quality equivalence, ignoring chords that fall outside the Major, minor, or no-chord categories.

### Parameters
- `reference_labels`: A list of ground-truth chord labels (strings) corresponding to the intervals being evaluated.
- `estimated_labels`: A list of estimated chord labels (strings) corresponding to the intervals being evaluated.

### Input
- **Data Format:** Labels must follow standard chord syntax (e.g., `C:maj`).
- **Preconditions:** Inputs must be aligned and of equal length. It is standard practice to use `mir_eval.util.merge_labeled_intervals` to ensure reference and estimated labels are synchronized over the same time intervals before calling this function.
- **Validation:** Invalid chord labels will raise an `InvalidChordException`.

### Output
Returns a `np.ndarray` of shape `(n,)` containing float scores. A value of `1.0` indicates a match, `0.0` indicates a mismatch, and `-1.0` indicates that the comparison is out of the major/minor gamut (i.e., one or both labels are not Major, minor, or no-chord).

### Valid Call Patterns
```python
comparisons = mir_eval.chord.majmin(ref_labels, est_labels)
```

### LLM Instruction Prompt
- When evaluating chord performance, always ensure labels are synchronized using `mir_eval.util.merge_labeled_intervals` before passing them to `majmin`.
- Use the returned `comparison_scores` with `mir_eval.chord.weighted_accuracy` to compute a duration-weighted score.
- Remember that `majmin` ignores complex qualities; ensure the user understands that labels outside the Major/minor/no-chord set will result in a `-1` score.

### Prompt Snippet
```text
# Ensure labels are aligned before comparison
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.majmin(ref_labels, est_labels)
```

### Common Failure Modes
- **Length Mismatch:** Passing lists of different lengths will cause errors; always merge intervals first.
- **Invalid Syntax:** Providing non-standard chord strings will raise an `InvalidChordException`.
- **Gamut Misinterpretation:** Treating `-1` as a zero-score rather than an "out of gamut" indicator, which can skew accuracy metrics if not handled by `weighted_accuracy`.

### Fix Code Hint
```python
# If labels are not aligned, use merge_labeled_intervals:
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
# Then compute scores:
comparisons = mir_eval.chord.majmin(ref_labels, est_labels)
```

## API Test: `python:mir_eval.chord.majmin_inv`

### Signature
```python
def majmin_inv(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:1171_

_Source doc:_ Compare chords along major-minor rules, with inversions. Chords with
qualities outside Major/minor/no-chord are ignored, and the bass note must
exist in the triad (bass in [1, 3, 5]).

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.majmin_inv(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
comparison_scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0], or -1 if the comparison is out of
    gamut.

### Goal
Computes a chord-wise comparison score between reference and estimated labels based on major-minor quality and inversion constraints.

### Parameters
- `reference_labels`: A list of ground-truth chord labels (strings) corresponding to the intervals being evaluated.
- `estimated_labels`: A list of estimated chord labels (strings) corresponding to the intervals being evaluated.

### Input
- **Data Format:** Labels must follow standard chord syntax (e.g., `C:maj`).
- **Preconditions:** Inputs must be aligned in time. It is standard practice to use `mir_eval.util.merge_labeled_intervals` to ensure the reference and estimated labels correspond to the same time intervals before calling this function.
- **Constraints:** Chords with qualities other than Major, minor, or no-chord are ignored. The bass note must be a member of the triad (1, 3, or 5).

### Output
Returns a `np.ndarray` of shape `(n,)` containing float scores in the range `[0.0, 1.0]`. A value of `-1` indicates that the comparison is out of the supported gamut (e.g., invalid quality or bass note).

### Valid Call Patterns
```python
comparisons = mir_eval.chord.majmin_inv(ref_labels, est_labels)
```

### LLM Instruction Prompt
- When using `mir_eval.chord.majmin_inv`, ensure that the input labels are synchronized with the intervals being evaluated.
- Always use `mir_eval.util.merge_labeled_intervals` to create the aligned label lists if the reference and estimated intervals differ.
- Use the returned `comparison_scores` with `mir_eval.chord.weighted_accuracy` to compute the final performance metric.

### Prompt Snippet
```text
# Ensure labels are aligned to the same intervals first
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.majmin_inv(ref_labels, est_labels)
```

### Common Failure Modes
- **Mismatched Lengths:** Passing lists of different lengths will cause an error; ensure `merge_labeled_intervals` is used to align them.
- **Invalid Labels:** Providing labels that do not conform to standard syntax may raise an `InvalidChordException`.
- **Out of Gamut:** If the chord quality is not Major/minor/no-chord or the bass note is not in the triad, the function returns `-1`, which must be handled when calculating aggregate accuracy.

### Fix Code Hint
```python
# If you receive -1 in your comparison array, filter them out or handle them 
# as non-comparable before passing to weighted_accuracy.
comparisons = mir_eval.chord.majmin_inv(ref_labels, est_labels)
valid_mask = comparisons != -1
score = mir_eval.chord.weighted_accuracy(comparisons[valid_mask], durations[valid_mask])
```

## API Test: `python:mir_eval.chord.merge_chord_intervals`

### Signature
```python
def merge_chord_intervals(intervals, labels)
```
_Source: source/mir_eval/chord.py:1489_

_Source doc:_ Merge consecutive chord intervals if they represent the same chord.

Parameters
----------
intervals : np.ndarray, shape=(n, 2), dtype=float
    Chord intervals to be merged, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
labels : list, shape=(n,)
    Chord labels to be merged, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.

Returns
-------
merged_ivs : np.ndarray, shape=(k, 2), dtype=float
    Merged chord intervals, k <= n

### Goal
This function simplifies chord annotation sequences by collapsing adjacent intervals that share identical chord labels into a single continuous interval.

### Parameters
- `intervals`: A NumPy array of shape `(n, 2)` containing `[start, end]` time pairs in seconds.
- `labels`: A list of `n` strings representing the chord labels corresponding to each interval.

### Input
The caller must provide `intervals` and `labels` in the format returned by `mir_eval.io.load_labeled_intervals`. Preconditions include that the input arrays must be sorted by time and represent valid, non-overlapping (or logically sequential) chord segments.

### Output
Returns a NumPy array of shape `(k, 2)` where `k <= n`, representing the consolidated intervals after merging consecutive identical labels.

### Valid Call Patterns
```python
import mir_eval
# Assuming ref_intervals and ref_labels are loaded via mir_eval.io.load_labeled_intervals
merged_intervals = mir_eval.chord.merge_chord_intervals(ref_intervals, ref_labels)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.merge_chord_intervals`, ensure the `intervals` array and `labels` list are of equal length `n`.
- The function is intended for post-processing chord annotations; ensure inputs are cleaned or validated using `mir_eval.chord.validate` if the source data is untrusted.

### Prompt Snippet
```text
# Example usage of merge_chord_intervals
import mir_eval.chord
# intervals: np.ndarray (n, 2), labels: list (n,)
merged_ivs = mir_eval.chord.merge_chord_intervals(intervals, labels)
```

### Common Failure Modes
- **Shape Mismatch:** Providing `intervals` and `labels` with different lengths will result in an error.
- **Unsorted Input:** If the input intervals are not chronologically ordered, the merging logic may fail to identify consecutive identical labels.
- **Invalid Labels:** While this function merges intervals, it does not validate the chord syntax itself; ensure labels are valid according to `mir_eval.chord` standards to avoid downstream errors in evaluation.

### Fix Code Hint
```python
# Ensure inputs are sorted by start time before merging
idx = np.argsort(intervals[:, 0])
intervals = intervals[idx]
labels = [labels[i] for i in idx]
merged_ivs = mir_eval.chord.merge_chord_intervals(intervals, labels)
```

## API Test: `python:mir_eval.chord.mirex`

### Signature
```python
def mirex(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:1043_

_Source doc:_ Compare chords along MIREX rules.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.mirex(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
comparison_scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0]

### Goal
Computes a frame-wise comparison of chord labels against ground truth using the standard MIREX evaluation criteria.

### Parameters
- `reference_labels`: A list of ground-truth chord labels (strings) corresponding to the intervals being evaluated.
- `estimated_labels`: A list of estimated chord labels (strings) corresponding to the intervals being evaluated.

### Input
- **Data Format:** Requires two lists of chord labels of equal length `n`.
- **Preconditions:** Inputs must be aligned to the same set of time intervals. Use `mir_eval.util.merge_labeled_intervals` to ensure that reference and estimated labels are synchronized across a common set of time segments before calling this function.
- **Label Syntax:** Chord labels must follow standard syntax (e.g., `C:maj`). Invalid labels will raise an `InvalidChordException`.

### Output
Returns a `np.ndarray` of shape `(n,)` containing float scores in the range `[0.0, 1.0]`, where each value represents the correctness of the estimated chord label relative to the reference for that specific interval.

### Valid Call Patterns
```python
comparisons = mir_eval.chord.mirex(ref_labels, est_labels)
```

### LLM Instruction Prompt
- Always ensure that `reference_labels` and `estimated_labels` have been synchronized using `mir_eval.util.merge_labeled_intervals` before passing them to `mirex`.
- The output of `mirex` is a per-interval score; use `mir_eval.chord.weighted_accuracy` to aggregate these into a final scalar score based on interval durations.

### Prompt Snippet
```text
# Ensure intervals are merged and aligned before calling mirex
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.mirex(ref_labels, est_labels)
```

### Common Failure Modes
- **Length Mismatch:** Passing lists of different lengths will result in an error; ensure `merge_labeled_intervals` is used to align them.
- **Invalid Labels:** Providing non-standard chord strings (e.g., missing root or quality) will trigger an `InvalidChordException`.
- **Unadjusted Intervals:** Failing to use `mir_eval.util.adjust_intervals` to match the start/end times of the reference and estimation can lead to misaligned labels and incorrect evaluation.

### Fix Code Hint
```python
# If labels are misaligned, use merge_labeled_intervals:
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
# Then compute scores:
comparisons = mir_eval.chord.mirex(ref_labels, est_labels)
```

## API Test: `python:mir_eval.chord.overseg`

### Signature
```python
def overseg(reference_intervals, estimated_intervals)
```
_Source: source/mir_eval/chord.py:1408_

_Source doc:_ Compute the MIREX 'OverSeg' score.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> score = mir_eval.chord.overseg(ref_intervals, est_intervals)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2), dtype=float
    Reference chord intervals to score against.
estimated_intervals : np.ndarray, shape=(m, 2), dtype=float
    Estimated chord intervals to score against.

Returns
-------
oversegmentation score : float
    Comparison score, in [0.0, 1.0], where 1.0 means no oversegmentation.

### Goal
Computes the MIREX 'OverSeg' score to quantify the degree of oversegmentation in estimated chord intervals relative to ground-truth reference intervals.

### Parameters
- `reference_intervals`: A NumPy array of shape `(n, 2)` containing the start and end times (in seconds) of the reference chord segments.
- `estimated_intervals`: A NumPy array of shape `(m, 2)` containing the start and end times (in seconds) of the estimated chord segments.

### Input
- **Data Format:** Both inputs must be `np.ndarray` of type `float` with shape `(N, 2)`.
- **Preconditions:** Intervals must be sorted by start time. It is recommended to use `mir_eval.util.adjust_intervals` to ensure estimated intervals span the same total duration as reference intervals before evaluation.

### Output
Returns a `float` representing the oversegmentation score, bounded in the range `[0.0, 1.0]`, where a value of `1.0` indicates no oversegmentation.

### Valid Call Patterns
```python
import mir_eval
# Assuming ref_intervals and est_intervals are loaded as (N, 2) numpy arrays
score = mir_eval.chord.overseg(ref_intervals, est_intervals)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.overseg`, ensure both `reference_intervals` and `estimated_intervals` are provided as `np.ndarray` objects of shape `(n, 2)` and `(m, 2)` respectively.
- Always verify that the input arrays are sorted by time.
- Use this function specifically for evaluating chord segmentation quality; do not use it for label-based chord accuracy metrics.

### Prompt Snippet
```text
# Example usage for chord oversegmentation evaluation:
score = mir_eval.chord.overseg(ref_intervals, est_intervals)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays that are not `(N, 2)` will cause internal NumPy errors or incorrect calculations.
- **Unsorted Intervals:** Providing unsorted intervals may lead to undefined behavior or inaccurate scores.
- **Duration Mismatch:** If the total duration of the estimated intervals differs significantly from the reference, the score may be misleading; ensure intervals are adjusted to the same total duration using `mir_eval.util.adjust_intervals` if necessary.

### Fix Code Hint
```python
import mir_eval
import numpy as np

# Ensure intervals are sorted and adjusted to the same duration
ref_intervals = np.sort(ref_intervals, axis=0)
est_intervals = np.sort(est_intervals, axis=0)
# Optional: adjust_intervals(ref_intervals, est_intervals)
score = mir_eval.chord.overseg(ref_intervals, est_intervals)
```

## API Test: `python:mir_eval.chord.pitch_class_to_semitone`

### Signature
```python
def pitch_class_to_semitone(pitch_class)
```
_Source: source/mir_eval/chord.py:142_

_Source doc:_ Convert a pitch class to semitone.

Parameters
----------
pitch_class : str
    Spelling of a given pitch class, e.g. 'C#', 'Gbb'

Returns
-------
semitone : int
    Semitone value of the pitch class.

### Goal
Converts a string-based musical pitch class representation into its corresponding integer semitone value (0-11) for use in chord analysis and encoding.

### Parameters
- `pitch_class`: A string representing the spelling of a pitch class (e.g., 'C', 'C#', 'Db', 'Gbb').

### Input
The input must be a string representing a valid pitch class. The function expects standard musical notation for accidentals (e.g., '#' for sharp, 'b' for flat).

### Output
Returns an `int` representing the semitone value of the pitch class, where C is typically mapped to 0, C#/Db to 1, and so on, up to B (11).

### Valid Call Patterns
```python
import mir_eval
# Example usage inferred from signature
semitone = mir_eval.chord.pitch_class_to_semitone('C#')
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.pitch_class_to_semitone`, ensure the input is a string representing a valid musical pitch class.
- Do not pass numeric types or lists; the function expects a single string argument.
- Use this function when parsing chord labels or performing pitch-class-based arithmetic within the `mir_eval.chord` module.

### Prompt Snippet
```text
# Convert a pitch class string to its integer semitone representation
semitone_val = mir_eval.chord.pitch_class_to_semitone(pitch_class_string)
```

### Common Failure Modes
- **Invalid Input Type:** Passing an integer or float instead of a string will result in a `TypeError`.
- **Invalid Pitch Spelling:** Passing a string that does not conform to recognized pitch class notation may raise a `ValueError` or `KeyError` depending on the internal implementation of the lookup table.
- **Case Sensitivity:** Ensure the pitch class string follows the expected case (e.g., 'C#' rather than 'c#') if the implementation is case-sensitive.

### Fix Code Hint
```python
# Ensure input is a string and handle potential errors
try:
    semitone = mir_eval.chord.pitch_class_to_semitone(str(pitch_class_input))
except (ValueError, KeyError):
    print(f"Invalid pitch class: {pitch_class_input}")
```

## API Test: `python:mir_eval.chord.quality_to_bitmap`

### Signature
```python
def quality_to_bitmap(quality)
```
_Source: source/mir_eval/chord.py:275_

_Source doc:_ Return the bitmap for a given quality.

Parameters
----------
quality : str
    Chord quality name.

Returns
-------
bitmap : np.ndarray
    Bitmap representation of this quality (12-dim).

### Goal
Converts a string-based chord quality name into a 12-dimensional binary NumPy array (bitmap) representing the pitch classes present in that quality.

### Parameters
- `quality`: A string representing the chord quality (e.g., 'maj', 'min').

### Input
- **Data:** A string representing a valid chord quality.
- **Preconditions:** The input string must correspond to a quality recognized by the `mir_eval.chord` module's internal mapping.

### Output
Returns `np.ndarray` — A 12-dimensional array where each element is 1 if the corresponding pitch class is present in the chord quality, and 0 otherwise.

### Valid Call Patterns
```python
# Example inferred from signature
import mir_eval
bitmap = mir_eval.chord.quality_to_bitmap('maj')
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.quality_to_bitmap`, ensure the `quality` argument is a string.
- The returned value is a 12-element NumPy array; do not assume it contains frequency data, as it represents pitch-class presence (bitmap).

### Prompt Snippet
```text
# Convert chord quality to 12-dim bitmap
bitmap = mir_eval.chord.quality_to_bitmap(quality_string)
```

### Common Failure Modes
- **Invalid Quality:** Passing a string that does not correspond to a defined chord quality will likely raise an error or exception within the `mir_eval.chord` module.
- **Type Mismatch:** Passing a non-string type (e.g., integer or list) as the `quality` argument will cause a failure.

### Fix Code Hint
```python
# Ensure the input is a valid string quality
try:
    bitmap = mir_eval.chord.quality_to_bitmap('maj')
except Exception as e:
    print(f"Invalid chord quality: {e}")
```

## API Test: `python:mir_eval.chord.reduce_extended_quality`

### Signature
```python
def reduce_extended_quality(quality)
```
_Source: source/mir_eval/chord.py:318_

_Source doc:_ Map an extended chord quality to a simpler one, moving upper voices to
a set of scale degree extensions.

Parameters
----------
quality : str
    Extended chord quality to reduce.

Returns
-------
base_quality : str
    New chord quality.
extensions : set
    Scale degrees extensions for the quality.

### Goal
Simplifies complex chord quality labels by decomposing them into a base triad or dyad quality and a set of additional scale degree extensions.

### Parameters
- `quality`: A string representing the extended chord quality (e.g., 'maj7', 'min9', '13').

### Input
- **Data:** A string representing a chord quality.
- **Preconditions:** The input string must be a valid chord quality recognized by the `mir_eval.chord` module's internal mapping logic.

### Output
Returns a tuple containing:
- `base_quality` (str): The simplified base quality of the chord.
- `extensions` (set): A set of strings representing the scale degree extensions (e.g., {'7', '9'}).

### Valid Call Patterns
```python
# Example inferred from signature
base_quality, extensions = mir_eval.chord.reduce_extended_quality('maj7')
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.reduce_extended_quality`, ensure the input `quality` is a string representing a chord quality.
- Always unpack the returned tuple into two variables: `base_quality` (str) and `extensions` (set).
- Do not attempt to pass raw chord labels (e.g., 'C:maj7') directly if the function expects only the quality component; ensure the input is stripped of the root note if necessary.

### Prompt Snippet
```text
# Example usage:
base, exts = mir_eval.chord.reduce_extended_quality('min9')
# base will be 'min', exts will be {'7', '9'}
```

### Common Failure Modes
- **Invalid Input:** Passing a string that does not correspond to a known chord quality may result in unexpected behavior or errors if the internal mapping does not support the specific extension.
- **Type Mismatch:** Passing a non-string object will raise a `TypeError`.
- **Root Note Inclusion:** Passing a full chord label (e.g., 'C:maj7') instead of just the quality ('maj7') will likely fail to match any internal definitions.

### Fix Code Hint
```python
# Ensure you are passing only the quality part of the chord label
import mir_eval
quality_part = 'maj7' # Extracted from 'C:maj7'
base, exts = mir_eval.chord.reduce_extended_quality(quality_part)
```

## API Test: `python:mir_eval.chord.root`

### Signature
```python
def root(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:999_

_Source doc:_ Compare chords according to roots.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.root(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
comparison_scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0], or -1 if the comparison is out of
    gamut.

### Goal
Computes a frame-wise comparison of chord labels based solely on their root notes to evaluate the accuracy of chord estimation systems.

### Parameters
- `reference_labels`: A list of ground-truth chord labels (strings) corresponding to the intervals being evaluated.
- `estimated_labels`: A list of estimated chord labels (strings) corresponding to the intervals being evaluated.

### Input
- **Data Format:** Labels must follow standard chord syntax (e.g., `C:maj`).
- **Preconditions:** Inputs must be aligned in time. It is standard practice to use `mir_eval.util.merge_labeled_intervals` to create synchronized lists of labels before calling this function.
- **Validation:** Invalid chord labels will raise an `InvalidChordException`.

### Output
Returns a `np.ndarray` of shape `(n,)` containing float scores. A value of `1.0` indicates the roots match, `0.0` indicates they do not, and `-1.0` indicates the comparison is out of gamut (e.g., involving `NO_CHORD` labels).

### Valid Call Patterns
```python
comparisons = mir_eval.chord.root(ref_labels, est_labels)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.root`, ensure that `reference_labels` and `estimated_labels` are of equal length.
- Always perform interval alignment using `mir_eval.util.merge_labeled_intervals` prior to calling this function to ensure the labels correspond to the same time segments.
- Use the returned `comparison_scores` with `mir_eval.chord.weighted_accuracy` to compute a duration-weighted score.

### Prompt Snippet
```text
# Ensure labels are aligned before comparison
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.root(ref_labels, est_labels)
```

### Common Failure Modes
- **Length Mismatch:** Passing lists of different lengths will result in an error; ensure `merge_labeled_intervals` is used to synchronize inputs.
- **Invalid Syntax:** Providing non-standard chord strings will trigger an `InvalidChordException`.
- **Unweighted Scoring:** Using the raw output of `root` without weighting by interval duration can lead to misleading accuracy metrics if chord durations vary significantly.

### Fix Code Hint
```python
# If labels are not aligned, use merge_labeled_intervals first
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
# Then compute root-based comparisons
comparisons = mir_eval.chord.root(ref_labels, est_labels)
```

## API Test: `python:mir_eval.chord.rotate_bitmap_to_root`

### Signature
```python
def rotate_bitmap_to_root(bitmap, chord_root)
```
_Source: source/mir_eval/chord.py:558_

_Source doc:_ Circularly shift a relative bitmap to its absolute pitch classes.

For clarity, the best explanation is an example. Given 'G:Maj', the root
and quality map are as follows::

    root=5
    quality=[1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]  # Relative chord shape

After rotating to the root, the resulting bitmap becomes::

    abs_quality = [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1]  # G, B, and D

Parameters
----------
bitmap : np.ndarray, shape=(12,)
    Bitmap of active notes, relative to the given root.
chord_root : int
    Absolute pitch class number.

Returns
-------
bitmap : np.ndarray, shape=(12,)
    Absolute bitmap of active pitch classes.

### Goal
This function transforms a relative chord representation into an absolute pitch-class bitmap by applying a circular shift based on the specified root note.

### Parameters
- `bitmap`: A 1D NumPy array of length 12 representing the presence (1) or absence (0) of pitch classes relative to a chord root.
- `chord_root`: An integer representing the absolute pitch class (0-11, where 0 is C, 1 is C#, etc.) to which the relative bitmap should be rotated.

### Input
- `bitmap`: Must be a 1D `np.ndarray` of shape `(12,)`.
- `chord_root`: Must be an `int` in the range `[0, 11]`.
- Preconditions: The input `bitmap` is assumed to be defined relative to a root of 0 (C).

### Output
Returns a 1D `np.ndarray` of shape `(12,)` containing the absolute pitch class bitmap, where indices correspond to absolute pitch classes (0=C, 1=C#, ..., 11=B).

### Valid Call Patterns
```python
import numpy as np
from mir_eval.chord import rotate_bitmap_to_root

# Example: G:Maj (Root=5, relative shape [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0])
bitmap = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0])
chord_root = 5
abs_bitmap = rotate_bitmap_to_root(bitmap, chord_root)
```

### LLM Instruction Prompt
- When calling `rotate_bitmap_to_root`, ensure the `bitmap` is a 12-element NumPy array and `chord_root` is an integer between 0 and 11. The function performs a circular shift; ensure the input `bitmap` is correctly formatted as a relative chord shape before rotation.

### Prompt Snippet
```text
# Rotate a relative chord bitmap to an absolute pitch class bitmap
abs_bitmap = mir_eval.chord.rotate_bitmap_to_root(relative_bitmap, root_index)
```

### Common Failure Modes
- Passing a `bitmap` that does not have exactly 12 elements will result in an index error or incorrect circular shift behavior.
- Providing a `chord_root` outside the range `[0, 11]` may lead to unexpected rotation results or index errors depending on the underlying NumPy implementation.
- Providing non-integer values for `chord_root` will cause a `TypeError`.

### Fix Code Hint
```python
# Ensure root is within valid range [0, 11]
chord_root = chord_root % 12
abs_bitmap = mir_eval.chord.rotate_bitmap_to_root(bitmap, chord_root)
```

## API Test: `python:mir_eval.chord.rotate_bitmaps_to_roots`

### Signature
```python
def rotate_bitmaps_to_roots(bitmaps, roots)
```
_Source: source/mir_eval/chord.py:593_

_Source doc:_ Circularly shift a relative bitmaps to absolute pitch classes.

See :func:`rotate_bitmap_to_root` for more information.

Parameters
----------
bitmaps : np.ndarray, shape=(N, 12)
    Bitmap of active notes, relative to the given root.
roots : np.ndarray, shape=(N,)
    Absolute pitch class number.

Returns
-------
bitmap : np.ndarray, shape=(N, 12)
    Absolute bitmaps of active pitch classes.

### Goal
Converts a set of chord bitmaps defined relative to their roots into absolute pitch-class bitmaps by applying a circular shift based on the provided root indices.

### Parameters
- `bitmaps`: A NumPy array of shape `(N, 12)` representing the presence of pitch classes (0-11) relative to a root note.
- `roots`: A NumPy array of shape `(N,)` containing the absolute pitch class numbers (0-11) corresponding to each bitmap.

### Input
- **Data Format:** Requires two NumPy arrays. `bitmaps` must be a 2D array of shape `(N, 12)` and `roots` must be a 1D array of shape `(N,)`.
- **Preconditions:** The number of rows `N` must match between `bitmaps` and `roots`. `roots` values should be integers in the range `[0, 11]`.

### Output
Returns a `np.ndarray` of shape `(N, 12)` containing the absolute pitch class bitmaps, where each row has been circularly shifted to align with its corresponding absolute root.

### Valid Call Patterns
```python
import numpy as np
import mir_eval

# Example: Rotating a major triad (1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0) 
# relative to root 0 (C) to absolute pitch classes.
bitmaps = np.array([[1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]])
roots = np.array([0])
absolute_bitmaps = mir_eval.chord.rotate_bitmaps_to_roots(bitmaps, roots)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.rotate_bitmaps_to_roots`, ensure that `bitmaps` and `roots` are NumPy arrays with matching first dimensions `N`.
- The `roots` array must contain integer values representing pitch classes (0-11).
- Use this function when transforming chord representations from a relative "root-centric" view to an absolute "chromagram-style" view.

### Prompt Snippet
```text
mir_eval.chord.rotate_bitmaps_to_roots(bitmaps, roots)
```

### Common Failure Modes
- **Shape Mismatch:** Providing `bitmaps` and `roots` with different lengths `N` will raise a `ValueError` or index error during internal broadcasting.
- **Invalid Root Values:** Providing `roots` outside the range `[0, 11]` may result in unexpected circular shifts or index errors.
- **Input Type:** Passing lists instead of NumPy arrays may cause failures; ensure inputs are cast to `np.ndarray` before calling.

### Fix Code Hint
```python
# Ensure inputs are numpy arrays and shapes are aligned
bitmaps = np.asarray(bitmaps)
roots = np.asarray(roots)
if bitmaps.shape[0] != roots.shape[0]:
    raise ValueError("bitmaps and roots must have the same number of elements.")
result = mir_eval.chord.rotate_bitmaps_to_roots(bitmaps, roots)
```

## API Test: `python:mir_eval.chord.scale_degree_to_bitmap`

### Signature
```python
def scale_degree_to_bitmap(scale_degree, modulo=False, length=BITMAP_LENGTH)
```
_Source: source/mir_eval/chord.py:211_

_Source doc:_ Create a bitmap representation of a scale degree.

Note that values in the bitmap may be negative, indicating that the
semitone is to be removed.

Parameters
----------
scale_degree : str
    Spelling of a relative scale degree, e.g. 'b3', '7', '#5'
modulo : bool, default=True
    If a scale degree exceeds the length of the bit-vector, modulo the
    scale degree back into the bit-vector; otherwise it is discarded.
length : int, default=12
    Length of the bit-vector to produce

Returns
-------
bitmap : np.ndarray, in [-1, 0, 1], len=`length`
    Bitmap representation of this scale degree.

### Goal
Converts a string-based relative scale degree spelling into a numerical bitmap representation suitable for chord analysis and comparison.

### Parameters
- `scale_degree`: A string representing the relative scale degree (e.g., 'b3', '7', '#5').
- `modulo`, default `False`: A boolean flag; if `True`, scale degrees exceeding the bit-vector length are wrapped using modulo arithmetic; if `False`, they are discarded.
- `length`, default `BITMAP_LENGTH`: An integer defining the length of the resulting bit-vector (default is 12).

### Input
The caller must provide a valid string representing a scale degree. No specific file format is required as this is a utility function for processing chord label components.

### Output
Returns a `np.ndarray` of length `length`, containing values in the set `[-1, 0, 1]`. A value of `1` indicates the presence of a semitone, `-1` indicates the removal of a semitone, and `0` indicates no change.

### Valid Call Patterns
```python
# Inferred from signature
import mir_eval
bitmap = mir_eval.chord.scale_degree_to_bitmap('b3', modulo=True, length=12)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.scale_degree_to_bitmap`, ensure the `scale_degree` is a valid string representation.
- Use the `modulo` parameter to control how out-of-bounds degrees are handled.
- The returned array is a NumPy array of integers; ensure downstream operations are compatible with `[-1, 0, 1]` values.

### Prompt Snippet
```text
# Example usage:
bitmap = mir_eval.chord.scale_degree_to_bitmap('b3', modulo=True)
```

### Common Failure Modes
- Passing an invalid string format for `scale_degree` that does not conform to standard relative scale degree notation.
- Assuming the output is a binary `[0, 1]` vector; the function can return `-1` to indicate the removal of a semitone.
- Mismatching the `length` parameter with the expected bit-vector size of the specific chord evaluation task.

### Fix Code Hint
```python
# Ensure the scale degree is a string and handle potential index errors if modulo=False
try:
    bitmap = mir_eval.chord.scale_degree_to_bitmap(degree_str, modulo=True)
except Exception as e:
    print(f"Invalid scale degree: {e}")
```

## API Test: `python:mir_eval.chord.scale_degree_to_semitone`

### Signature
```python
def scale_degree_to_semitone(scale_degree)
```
_Source: source/mir_eval/chord.py:175_

_Source doc:_ Convert a scale degree to semitone.

Parameters
----------
scale_degree : str
    Spelling of a relative scale degree, e.g. 'b3', '7', '#5'

Returns
-------
semitone : int
    Relative semitone of the scale degree, wrapped to a single octave

Raises
------
InvalidChordException if `scale_degree` is invalid.

### Goal
Converts a string-based musical scale degree representation into its corresponding integer semitone value relative to a root, normalized to a single octave.

### Parameters
- `scale_degree`: A string representing the relative scale degree (e.g., '1', 'b3', '#5', '7').

### Input
The input must be a valid string representation of a scale degree. There are no specific file format requirements as this is a utility function for processing chord label components.

### Output
Returns an `int` representing the relative semitone value of the provided scale degree, wrapped to a single octave (0-11).

### Valid Call Patterns
```python
import mir_eval
# Example of converting a flattened third to a semitone
semitone = mir_eval.chord.scale_degree_to_semitone('b3')
```

### LLM Instruction Prompt
- When using `mir_eval.chord.scale_degree_to_semitone`, ensure the input `scale_degree` is a string.
- The function expects standard chord notation syntax for degrees (e.g., using 'b' for flat and '#' for sharp).
- Be prepared to handle `InvalidChordException` if the input string does not conform to recognized scale degree formats.

### Prompt Snippet
```text
# Example usage:
import mir_eval.chord
semitone = mir_eval.chord.scale_degree_to_semitone('b3')
```

### Common Failure Modes
- **InvalidChordException**: Raised if the `scale_degree` string is not recognized by the parser (e.g., passing an empty string, an invalid character, or a non-degree label).
- **Type Errors**: Passing a non-string type (e.g., an integer or list) will result in a `TypeError` as the function expects a string input.

### Fix Code Hint
```python
try:
    semitone = mir_eval.chord.scale_degree_to_semitone(my_degree_str)
except mir_eval.chord.InvalidChordException:
    # Handle cases where the degree string is malformed
    semitone = None
```

## API Test: `python:mir_eval.chord.seg`

### Signature
```python
def seg(reference_intervals, estimated_intervals)
```
_Source: source/mir_eval/chord.py:1460_

_Source doc:_ Compute the MIREX 'MeanSeg' score.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> score = mir_eval.chord.seg(ref_intervals, est_intervals)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2), dtype=float
    Reference chord intervals to score against.
estimated_intervals : np.ndarray, shape=(m, 2), dtype=float
    Estimated chord intervals to score against.

Returns
-------
segmentation score : float
    Comparison score, in [0.0, 1.0], where 1.0 means perfect segmentation.

### Goal
Computes the MIREX 'MeanSeg' score to evaluate the temporal alignment and segmentation accuracy of estimated chord intervals against ground-truth reference intervals.

### Parameters
- `reference_intervals`: A NumPy array of shape `(n, 2)` containing the ground-truth start and end times (in seconds) for chord segments.
- `estimated_intervals`: A NumPy array of shape `(m, 2)` containing the estimated start and end times (in seconds) for chord segments.

### Input
- **Data Format:** Intervals must be provided as `(n, 2)` NumPy arrays of floats, where each row represents `[start_time, end_time]`.
- **Preconditions:** Intervals should be sorted by time. It is recommended to use `mir_eval.util.adjust_intervals` to ensure estimated intervals span the same total duration as reference intervals before evaluation to avoid boundary mismatches.

### Output
Returns a `float` representing the segmentation score in the range `[0.0, 1.0]`, where `1.0` indicates a perfect match between the reference and estimated segment boundaries.

### Valid Call Patterns
```python
score = mir_eval.chord.seg(ref_intervals, est_intervals)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.seg`, ensure both `reference_intervals` and `estimated_intervals` are `np.ndarray` objects of shape `(n, 2)` and `(m, 2)` respectively.
- Always verify that time values are in seconds.
- If the intervals do not cover the same total duration, use `mir_eval.util.adjust_intervals` prior to calling this function to ensure valid comparison.

### Prompt Snippet
```text
# Ensure intervals are loaded and adjusted before calling seg
ref_intervals, _ = mir_eval.io.load_labeled_intervals('ref.lab')
est_intervals, _ = mir_eval.io.load_labeled_intervals('est.lab')
score = mir_eval.chord.seg(ref_intervals, est_intervals)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays that are not `(n, 2)` will cause internal NumPy errors or invalid metric calculations.
- **Unsorted Intervals:** Providing unsorted intervals can lead to incorrect segmentation logic; ensure inputs are ordered by start time.
- **Duration Mismatch:** Failing to align the total duration of estimated intervals with reference intervals can result in misleadingly low scores.

### Fix Code Hint
```python
import mir_eval
# Ensure intervals are sorted and adjusted to match total duration
ref_intervals, _ = mir_eval.io.load_labeled_intervals('ref.lab')
est_intervals, _ = mir_eval.io.load_labeled_intervals('est.lab')
est_intervals = mir_eval.util.adjust_intervals(est_intervals, ref_intervals)
score = mir_eval.chord.seg(ref_intervals, est_intervals)
```

## API Test: `python:mir_eval.chord.sevenths`

### Signature
```python
def sevenths(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:1235_

_Source doc:_ Compare chords along MIREX 'sevenths' rules. Chords with qualities
outside [maj, maj7, 7, min, min7, N] are ignored.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.sevenths(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
comparison_scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0], or -1 if the comparison is out of
    gamut.

### Goal
Computes a comparison score for chord labels based on MIREX 'sevenths' rules, which evaluate chord quality equivalence within the subset of [maj, maj7, 7, min, min7, N].

### Parameters
- `reference_labels`: A list of ground-truth chord labels (strings) corresponding to the intervals being evaluated.
- `estimated_labels`: A list of estimated chord labels (strings) corresponding to the intervals being evaluated.

### Input
- **Format:** Labels must follow standard chord syntax (e.g., `C:maj`).
- **Preconditions:** Inputs must be aligned in time. Typically, users must first use `mir_eval.util.merge_labeled_intervals` to ensure the reference and estimated labels correspond to the same time intervals before calling this function.
- **Validation:** Invalid chord labels will raise an `InvalidChordException`.

### Output
Returns a `np.ndarray` of shape `(n,)` containing float scores. A score of `1.0` indicates a match, `0.0` indicates a mismatch, and `-1.0` indicates that one or both labels fall outside the 'sevenths' gamut (maj, maj7, 7, min, min7, N).

### Valid Call Patterns
```python
comparisons = mir_eval.chord.sevenths(ref_labels, est_labels)
```

### LLM Instruction Prompt
- Always ensure `reference_labels` and `estimated_labels` are of equal length `n` before calling.
- Use this function only when evaluating chord quality specifically under the MIREX 'sevenths' subset.
- Always pair the output with `mir_eval.chord.weighted_accuracy` and the corresponding interval durations to obtain a final scalar performance metric.

### Prompt Snippet
```text
# Ensure labels are aligned via merge_labeled_intervals first
comparisons = mir_eval.chord.sevenths(ref_labels, est_labels)
score = mir_eval.chord.weighted_accuracy(comparisons, durations)
```

### Common Failure Modes
- **Mismatched Lengths:** Passing lists of different lengths will result in an error.
- **Out-of-Gamut Labels:** Labels not in the [maj, maj7, 7, min, min7, N] set will return `-1`, which must be handled by the downstream aggregation function (e.g., `weighted_accuracy`).
- **Unmerged Intervals:** Calling this on raw, unmerged intervals will lead to incorrect comparisons; always use `mir_eval.util.merge_labeled_intervals` first.

### Fix Code Hint
```python
# If labels are not aligned, use merge_labeled_intervals:
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.sevenths(ref_labels, est_labels)
```

## API Test: `python:mir_eval.chord.sevenths_inv`

### Signature
```python
def sevenths_inv(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:1294_

_Source doc:_ Compare chords along MIREX 'sevenths' rules. Chords with qualities
outside [maj, maj7, 7, min, min7, N] are ignored.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.sevenths_inv(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
comparison_scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0], or -1 if the comparison is out of
    gamut.

### Goal
Computes chord comparison scores based on MIREX 'sevenths' rules, evaluating the accuracy of estimated chord labels against reference labels for a restricted set of chord qualities.

### Parameters
- `reference_labels`: A list of ground-truth chord labels (strings) corresponding to the intervals being evaluated.
- `estimated_labels`: A list of estimated chord labels (strings) corresponding to the intervals being evaluated.

### Input
- **Data Format:** Both `reference_labels` and `estimated_labels` must be lists of equal length `n`.
- **Preconditions:** Labels must follow standard chord syntax (e.g., `C:maj`). Before calling this function, inputs should be synchronized using `mir_eval.util.merge_labeled_intervals` to ensure that the reference and estimated labels correspond to the same time intervals.
- **Gamut:** Only chords with qualities [maj, maj7, 7, min, min7, N] are considered; others are ignored.

### Output
Returns a `np.ndarray` of shape `(n,)` containing float scores in the range `[0.0, 1.0]`. A value of `-1` indicates that the comparison is out of the defined gamut.

### Valid Call Patterns
```python
comparisons = mir_eval.chord.sevenths_inv(ref_labels, est_labels)
```

### LLM Instruction Prompt
- When using `mir_eval.chord.sevenths_inv`, ensure that the input labels have been aligned with their respective time intervals using `mir_eval.util.merge_labeled_intervals` first.
- Always pass the reference labels as the first argument and estimated labels as the second.
- Use the returned array with `mir_eval.chord.weighted_accuracy` to compute a final score based on interval durations.

### Prompt Snippet
```text
# Ensure labels are aligned to intervals before calling
comparisons = mir_eval.chord.sevenths_inv(ref_labels, est_labels)
```

### Common Failure Modes
- **Length Mismatch:** Providing `reference_labels` and `estimated_labels` of different lengths will cause an error.
- **Invalid Labels:** Providing chord labels that do not conform to the expected syntax will raise an `InvalidChordException`.
- **Unsynchronized Intervals:** Passing raw labels without first merging intervals (using `mir_eval.util.merge_labeled_intervals`) will result in semantically incorrect comparisons.

### Fix Code Hint
```python
# Ensure intervals are merged and aligned before scoring
(intervals, ref_labels, est_labels) = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.sevenths_inv(ref_labels, est_labels)
```

## API Test: `python:mir_eval.chord.split`

### Signature
```python
def split(chord_label, reduce_extended_chords=False)
```
_Source: source/mir_eval/chord.py:360_

_Source doc:_ Parse a chord label into its four constituent parts:
    - root
    - quality shorthand
    - scale degrees
    - bass

Note: Chords lacking quality AND interval information are major.
  - If a quality is specified, it is returned.
  - If an interval is specified WITHOUT a quality, the quality field is
    empty.

Some examples::

    'C' -> ['C', 'maj', {}, '1']
    'G#:min(*b3,*5)/5' -> ['G#', 'min', {'*b3', '*5'}, '5']
    'A:(3)/6' -> ['A', '', {'3'}, '6']

Parameters
----------
chord_label : str
    A chord label.
reduce_extended_chords : bool
    Whether to map the upper voicings of extended chords (9's, 11's, 13's)
    to semitone extensions. (Default value = False)

Returns
-------
chord_parts : list
    Split version of the chord label.

### Goal
Parses a standardized chord label string into its fundamental components (root, quality, scale degrees, and bass) to facilitate symbolic chord analysis and comparison.

### Parameters
- `chord_label`: A string representing a chord label (e.g., 'C:maj', 'G#:min(*b3,*5)/5').
- `reduce_extended_chords`, default `False`: A boolean flag; if `True`, maps upper voicings (9ths, 11ths, 13ths) to their corresponding semitone extensions.

### Input
The input must be a valid chord label string. Precondition: The label must conform to the standard syntax expected by `mir_eval.chord`. If the label is invalid, the function may raise an `InvalidChordException`.

### Output
Returns a `list` containing four elements:
1. `root` (str): The root note of the chord.
2. `quality` (str): The quality shorthand (e.g., 'maj', 'min'). If no quality is specified but intervals are present, this field is empty.
3. `scale_degrees` (set): A set of strings representing the chord's scale degrees.
4. `bass` (str): The bass note or interval of the chord.

### Valid Call Patterns
```python
import mir_eval
# Basic parsing
parts = mir_eval.chord.split('G#:min(*b3,*5)/5')

# Parsing with extended chord reduction
parts_reduced = mir_eval.chord.split('C:maj9', reduce_extended_chords=True)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.split`, ensure the `chord_label` is a string formatted according to standard MIR chord annotation conventions.
- Use the `reduce_extended_chords` parameter only when the specific research context requires mapping complex extensions to simpler semitone representations.
- Always handle the returned list as a 4-element structure: `[root, quality, scale_degrees, bass]`.

### Prompt Snippet
```text
# Example usage of mir_eval.chord.split
root, quality, degrees, bass = mir_eval.chord.split('A:(3)/6')
```

### Common Failure Modes
- **InvalidChordException**: Raised if the `chord_label` string does not match the expected syntax (e.g., malformed root or bass notation).
- **Type Errors**: Passing a non-string object as `chord_label` will cause a failure.
- **Assumption Mismatch**: Assuming the `quality` field will always contain a value; if only intervals are provided in the label, the `quality` field will be an empty string.

### Fix Code Hint
```python
# Ensure labels are stripped of whitespace before splitting
clean_label = label.strip()
try:
    root, quality, degrees, bass = mir_eval.chord.split(clean_label)
except mir_eval.chord.InvalidChordException:
    # Handle or log invalid labels
    pass
```

## API Test: `python:mir_eval.chord.tetrads`

### Signature
```python
def tetrads(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:904_

_Source doc:_ Compare chords along tetrad (root & full quality) relationships.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.tetrads(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
comparison_scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0]

### Goal
Computes a comparison score for chord labels based on their root and full quality (tetrad) relationships to evaluate the accuracy of chord estimation systems.

### Parameters
- `reference_labels`: A list of ground-truth chord labels (strings) corresponding to the intervals being evaluated.
- `estimated_labels`: A list of estimated chord labels (strings) corresponding to the intervals being evaluated.

### Input
- **Data Format:** Both inputs must be lists of equal length `n` containing standard chord syntax (e.g., `C:maj7`).
- **Preconditions:** Before calling this function, inputs should be aligned using `mir_eval.util.merge_labeled_intervals` to ensure that the reference and estimated labels correspond to the same time intervals.
- **Validation:** Chord labels must be valid; invalid labels will raise an `InvalidChordException`.

### Output
Returns a `np.ndarray` of shape `(n,)` containing float values in the range `[0.0, 1.0]`, where 1.0 indicates a perfect match of root and tetrad quality for that interval.

### Valid Call Patterns
```python
comparisons = mir_eval.chord.tetrads(ref_labels, est_labels)
```

### LLM Instruction Prompt
- When using `mir_eval.chord.tetrads`, ensure that the input labels are first synchronized with their corresponding intervals using `mir_eval.util.merge_labeled_intervals`.
- The function returns a per-interval comparison array; use `mir_eval.chord.weighted_accuracy` with the interval durations to compute a final aggregate score.

### Prompt Snippet
```text
# Ensure labels are aligned to the same intervals before comparison
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.tetrads(ref_labels, est_labels)
```

### Common Failure Modes
- **Length Mismatch:** Passing lists of different lengths will result in an error; ensure `merge_labeled_intervals` is used to synchronize them.
- **Invalid Labels:** Providing non-standard chord strings (e.g., "Cmaj") instead of the expected syntax (e.g., "C:maj") will trigger an `InvalidChordException`.
- **Unadjusted Intervals:** Comparing raw labels without adjusting intervals to a common time range will lead to incorrect evaluation scores.

### Fix Code Hint
```python
# Use adjust_intervals to ensure temporal alignment before merging
est_intervals, est_labels = mir_eval.util.adjust_intervals(
    est_intervals, est_labels, ref_intervals.min(), ref_intervals.max(),
    mir_eval.chord.NO_CHORD, mir_eval.chord.NO_CHORD)
```

## API Test: `python:mir_eval.chord.tetrads_inv`

### Signature
```python
def tetrads_inv(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:951_

_Source doc:_ Compare chords along tetrad (root, full quality, & bass) relationships.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.tetrads_inv(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
comparison_scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0]

### Goal
Computes a comparison score for chord labels by evaluating the equivalence of the root, full quality, and bass note (tetrad) between reference and estimated chord annotations.

### Parameters
- `reference_labels`: A list of strings representing the ground-truth chord labels (e.g., "C:maj").
- `estimated_labels`: A list of strings representing the system-estimated chord labels to be evaluated.

### Input
- **Data Format:** Both inputs must be lists of equal length `n` containing valid chord label strings.
- **Preconditions:** Before calling this function, inputs should be aligned using `mir_eval.util.merge_labeled_intervals` to ensure that the reference and estimated labels correspond to the same time intervals.
- **Label Syntax:** Labels must follow standard `mir_eval` chord syntax (e.g., `C:maj`, `D:min7`). Invalid labels will raise an `InvalidChordException`.

### Output
Returns a `np.ndarray` of shape `(n,)` containing float values in the range `[0.0, 1.0]`, where 1.0 indicates a perfect match of the tetrad components and 0.0 indicates no match.

### Valid Call Patterns
```python
comparisons = mir_eval.chord.tetrads_inv(ref_labels, est_labels)
```

### LLM Instruction Prompt
- When using `mir_eval.chord.tetrads_inv`, ensure that the input lists are of identical length.
- Always perform interval alignment using `mir_eval.util.merge_labeled_intervals` prior to calling this function to ensure the labels are temporally synchronized.
- Use the resulting `comparison_scores` with `mir_eval.chord.weighted_accuracy` to compute a duration-weighted score.

### Prompt Snippet
```text
# Ensure labels are aligned by interval before comparison
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.tetrads_inv(ref_labels, est_labels)
```

### Common Failure Modes
- **Length Mismatch:** Passing lists of different lengths will result in an error; ensure `merge_labeled_intervals` is used to synchronize the inputs.
- **Invalid Labels:** Providing strings that do not conform to the expected chord syntax will raise an `InvalidChordException`.
- **Unweighted Scores:** Using the raw output of `tetrads_inv` without weighting by duration (using `weighted_accuracy`) may lead to misleading evaluation results if chord durations vary significantly.

### Fix Code Hint
```python
# If labels are not aligned, use merge_labeled_intervals first
from mir_eval.util import merge_labeled_intervals
intervals, ref_labels, est_labels = merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
# Now safe to compare
scores = mir_eval.chord.tetrads_inv(ref_labels, est_labels)
```

## API Test: `python:mir_eval.chord.thirds`

### Signature
```python
def thirds(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:714_

_Source doc:_ Compare chords along root & third relationships.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.thirds(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
comparison_scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0]

### Goal
Computes a similarity score between reference and estimated chord labels based specifically on the correctness of the chord root and the quality of the third (major/minor).

### Parameters
- `reference_labels`: A list of ground-truth chord labels (strings) corresponding to the intervals being evaluated.
- `estimated_labels`: A list of estimated chord labels (strings) corresponding to the intervals being evaluated.

### Input
- **Data Format:** Both inputs must be lists of equal length `n`.
- **Preconditions:** Labels must follow standard chord syntax (e.g., `C:maj`). Before calling this function, ensure that reference and estimated intervals are aligned and merged using `mir_eval.util.merge_labeled_intervals` to ensure the labels correspond to the same time segments.
- **Validation:** Invalid chord labels will raise an `InvalidChordException`.

### Output
Returns a `np.ndarray` of shape `(n,)` containing float values in the range `[0.0, 1.0]`, where each value represents the degree of match between the reference and estimated chord for that segment based on root and third relationships.

### Valid Call Patterns
```python
comparisons = mir_eval.chord.thirds(ref_labels, est_labels)
```

### LLM Instruction Prompt
- When using `mir_eval.chord.thirds`, ensure that the input labels are derived from synchronized intervals.
- Always use `mir_eval.util.merge_labeled_intervals` to prepare the label lists if the reference and estimated intervals do not perfectly align.
- The output of this function is intended to be passed to `mir_eval.chord.weighted_accuracy` along with the corresponding interval durations.

### Prompt Snippet
```text
# Ensure labels are aligned before comparison
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.thirds(ref_labels, est_labels)
```

### Common Failure Modes
- **Length Mismatch:** Passing lists of different lengths will cause an error; ensure `len(reference_labels) == len(estimated_labels)`.
- **Unsorted Intervals:** If the input labels were not derived from sorted intervals, the resulting comparison scores will not correspond correctly to the timeline.
- **Invalid Syntax:** Providing non-standard chord strings (e.g., "Cmaj" instead of "C:maj") will trigger an `InvalidChordException`.

### Fix Code Hint
```python
# If lengths mismatch, re-merge intervals to ensure alignment
(intervals, ref_labels, est_labels) = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.thirds(ref_labels, est_labels)
```

## API Test: `python:mir_eval.chord.thirds_inv`

### Signature
```python
def thirds_inv(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:761_

_Source doc:_ Score chords along root, third, & bass relationships.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.thirds_inv(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0]

### Goal
Computes a chord comparison score by evaluating the root, third, and bass relationships between reference and estimated chord labels.

### Parameters
- `reference_labels`: A list of ground-truth chord labels (strings) corresponding to the intervals being evaluated.
- `estimated_labels`: A list of estimated chord labels (strings) corresponding to the intervals being evaluated.

### Input
- **Data Format:** Requires two lists of equal length `n` containing chord labels (e.g., `C:maj`).
- **Preconditions:** Inputs must be aligned such that `reference_labels[i]` corresponds to `estimated_labels[i]`. Typically, this is achieved by using `mir_eval.util.merge_labeled_intervals` to ensure both lists share the same temporal segmentation.
- **Label Syntax:** Chord labels must follow standard syntax (e.g., `C:maj`); invalid labels will raise an `InvalidChordException`.

### Output
Returns a `np.ndarray` of shape `(n,)` containing float scores in the range `[0.0, 1.0]`, where each value represents the similarity of the chord relationship at that index.

### Valid Call Patterns
```python
comparisons = mir_eval.chord.thirds_inv(ref_labels, est_labels)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.thirds_inv`, ensure that `reference_labels` and `estimated_labels` are of equal length.
- Always perform interval merging using `mir_eval.util.merge_labeled_intervals` before passing labels to this function to ensure temporal alignment.
- Use the resulting `comparisons` array with `mir_eval.chord.weighted_accuracy` to compute a final aggregate score based on interval durations.

### Prompt Snippet
```text
# Ensure labels are aligned via merged intervals before scoring
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.thirds_inv(ref_labels, est_labels)
```

### Common Failure Modes
- **Length Mismatch:** Passing lists of different lengths will result in an error; ensure `merge_labeled_intervals` is used to synchronize the inputs.
- **Invalid Labels:** Providing strings that do not conform to the expected chord syntax will trigger an `InvalidChordException`.
- **Unsynchronized Intervals:** Passing raw labels without first aligning them to the same time intervals will lead to semantically meaningless comparison scores.

### Fix Code Hint
```python
# If labels are not aligned, use merge_labeled_intervals first:
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
# Then compute scores:
scores = mir_eval.chord.thirds_inv(ref_labels, est_labels)
```

## API Test: `python:mir_eval.chord.triads`

### Signature
```python
def triads(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:809_

_Source doc:_ Compare chords along triad (root & quality to #5) relationships.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.triads(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
comparison_scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0]

### Goal
Computes a binary comparison score for chord labels based on triad equivalence, evaluating whether the root and chord quality (up to the fifth) match between reference and estimated labels.

### Parameters
- `reference_labels`: A list of ground-truth chord labels (strings) corresponding to the intervals being evaluated.
- `estimated_labels`: A list of estimated chord labels (strings) corresponding to the intervals being evaluated.

### Input
- **Data Format:** Labels must follow standard chord syntax (e.g., `C:maj`).
- **Preconditions:** Inputs must be of equal length `n`. Before calling this function, labels should be aligned with reference intervals using `mir_eval.util.merge_labeled_intervals` and `mir_eval.util.adjust_intervals` to ensure temporal correspondence.

### Output
Returns a `np.ndarray` of shape `(n,)` containing float values (0.0 or 1.0) indicating whether the triad components of the reference and estimated labels match.

### Valid Call Patterns
```python
comparisons = mir_eval.chord.triads(ref_labels, est_labels)
```

### LLM Instruction Prompt
- Always ensure `reference_labels` and `estimated_labels` are aligned by time intervals before passing them to this function.
- Use `mir_eval.util.merge_labeled_intervals` to generate the aligned label lists required for this function.
- The output is a per-label comparison; use `mir_eval.chord.weighted_accuracy` with the corresponding interval durations to compute a final aggregate score.

### Prompt Snippet
```text
# Align labels first
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
# Compute triad comparisons
comparisons = mir_eval.chord.triads(ref_labels, est_labels)
```

### Common Failure Modes
- **Label Syntax Errors:** Providing labels that do not conform to standard syntax will raise an `InvalidChordException`.
- **Mismatched Lengths:** Passing lists of different lengths will result in a `ValueError`.
- **Temporal Misalignment:** Failing to use `merge_labeled_intervals` will result in comparing labels that do not correspond to the same time segments, leading to incorrect evaluation scores.

### Fix Code Hint
```python
# Ensure labels are aligned to the same intervals before comparison
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.triads(ref_labels, est_labels)
```

## API Test: `python:mir_eval.chord.triads_inv`

### Signature
```python
def triads_inv(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:856_

_Source doc:_ Score chords along triad (root, quality to #5, & bass) relationships.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> comparisons = mir_eval.chord.triads_inv(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

Returns
-------
scores : np.ndarray, shape=(n,), dtype=float
    Comparison scores, in [0.0, 1.0]

### Goal
Computes a comparison score for chord labels based on triad relationships, specifically evaluating the root, quality (up to the 5th), and bass note.

### Parameters
- `reference_labels`: A list of ground-truth chord labels (strings) corresponding to the intervals being evaluated.
- `estimated_labels`: A list of estimated chord labels (strings) corresponding to the intervals being evaluated.

### Input
- **Data Format:** Labels must follow standard chord syntax (e.g., `C:maj`).
- **Preconditions:** The input lists must be of equal length `n`. Before calling this function, use `mir_eval.util.merge_labeled_intervals` to ensure that the reference and estimated labels are aligned over the same time intervals.

### Output
Returns a `np.ndarray` of shape `(n,)` containing float scores in the range `[0.0, 1.0]`, where 1.0 indicates a perfect match for the triad and bass components.

### Valid Call Patterns
```python
comparisons = mir_eval.chord.triads_inv(ref_labels, est_labels)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.triads_inv`, ensure that `reference_labels` and `estimated_labels` have been synchronized using `mir_eval.util.merge_labeled_intervals` to ensure the lists correspond to the same time segments.
- The function returns a per-interval score; use `mir_eval.chord.weighted_accuracy` with the corresponding interval durations to compute a final aggregate score.

### Prompt Snippet
```text
# Ensure labels are aligned before calling triads_inv
(intervals, ref_labels, est_labels) = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
comparisons = mir_eval.chord.triads_inv(ref_labels, est_labels)
```

### Common Failure Modes
- **Length Mismatch:** Passing lists of different lengths will result in an error; ensure `merge_labeled_intervals` is used to align them first.
- **Invalid Labels:** Providing strings that do not conform to standard chord syntax will raise an `InvalidChordException`.
- **Unadjusted Intervals:** Failing to use `mir_eval.util.adjust_intervals` to normalize the time span of estimated labels to the reference labels will lead to incorrect evaluation results.

### Fix Code Hint
```python
# If labels are not aligned, use merge_labeled_intervals first:
intervals, ref_labels, est_labels = mir_eval.util.merge_labeled_intervals(
    ref_intervals, ref_labels, est_intervals, est_labels)
scores = mir_eval.chord.triads_inv(ref_labels, est_labels)
```

## API Test: `python:mir_eval.chord.underseg`

### Signature
```python
def underseg(reference_intervals, estimated_intervals)
```
_Source: source/mir_eval/chord.py:1434_

_Source doc:_ Compute the MIREX 'UnderSeg' score.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> score = mir_eval.chord.underseg(ref_intervals, est_intervals)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2), dtype=float
    Reference chord intervals to score against.
estimated_intervals : np.ndarray, shape=(m, 2), dtype=float
    Estimated chord intervals to score against.

Returns
-------
undersegmentation score : float
    Comparison score, in [0.0, 1.0], where 1.0 means no undersegmentation.

### Goal
Computes the MIREX 'UnderSeg' score to quantify the degree of undersegmentation in estimated chord intervals relative to ground-truth reference intervals.

### Parameters
- `reference_intervals`: A NumPy array of shape `(n, 2)` containing the start and end times (in seconds) of the reference chord segments.
- `estimated_intervals`: A NumPy array of shape `(m, 2)` containing the start and end times (in seconds) of the estimated chord segments.

### Input
- **Data Format:** Both inputs must be `np.ndarray` objects with `dtype=float`.
- **Preconditions:** Intervals must be sorted by time. It is recommended to use `mir_eval.util.adjust_intervals` to ensure estimated intervals span the same total duration as reference intervals before evaluation.

### Output
Returns a `float` representing the undersegmentation score in the range `[0.0, 1.0]`, where `1.0` indicates no undersegmentation.

### Valid Call Patterns
```python
score = mir_eval.chord.underseg(ref_intervals, est_intervals)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.underseg`, ensure that both `reference_intervals` and `estimated_intervals` are provided as `np.ndarray` objects of shape `(N, 2)` containing time in seconds.
- Always verify that the intervals are sorted by start time before passing them to the function.

### Prompt Snippet
```text
# Example usage of mir_eval.chord.underseg
import mir_eval
# Assuming ref_intervals and est_intervals are pre-loaded np.ndarrays
score = mir_eval.chord.underseg(ref_intervals, est_intervals)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays that do not conform to the `(N, 2)` shape requirement will result in errors.
- **Unsorted Intervals:** Providing unsorted intervals can lead to incorrect metric calculations; ensure data is pre-processed.
- **Time Units:** Providing time in samples instead of seconds will cause the metric to be computed incorrectly.

### Fix Code Hint
```python
# Ensure intervals are sorted and adjusted to match duration
import mir_eval.util
ref_intervals, est_intervals = mir_eval.util.adjust_intervals(ref_intervals, est_intervals)
score = mir_eval.chord.underseg(ref_intervals, est_intervals)
```

## API Test: `python:mir_eval.chord.validate`

### Signature
```python
def validate(reference_labels, estimated_labels)
```
_Source: source/mir_eval/chord.py:618_

_Source doc:_ Check that the input annotations to a comparison function look like
valid chord labels.

Parameters
----------
reference_labels : list, len=n
    Reference chord labels to score against.
estimated_labels : list, len=n
    Estimated chord labels to score against.

### Goal
Validates that the provided reference and estimated chord label lists conform to the expected syntax and structure required for chord evaluation metrics.

### Parameters
- `reference_labels`: A list of strings representing the ground-truth chord annotations.
- `estimated_labels`: A list of strings representing the system-predicted chord annotations.

### Input
- **Data Format:** Both arguments must be lists of strings of equal length ($n$).
- **Preconditions:** Chord labels must follow standard syntax (e.g., `C:maj`, `N` for no chord).
- **Compatibility:** This function is typically called internally by `mir_eval.chord.evaluate` to ensure data integrity before metric computation.

### Output
Returns `None` if validation succeeds. If validation fails, it raises an `InvalidChordException`.

### Valid Call Patterns
```python
import mir_eval
# Example inferred from signature and project usage
mir_eval.chord.validate(['C:maj', 'G:maj'], ['C:maj', 'G:min'])
```

### LLM Instruction Prompt
- Use `mir_eval.chord.validate` to verify chord label lists before passing them to `mir_eval.chord.evaluate`.
- Ensure both `reference_labels` and `estimated_labels` are lists of strings and have the same length.
- Handle `InvalidChordException` if the input labels do not conform to the expected chord syntax.

### Prompt Snippet
```text
# Validate chord labels before evaluation
mir_eval.chord.validate(ref_labels, est_labels)
```

### Common Failure Modes
- **Length Mismatch:** Passing lists of different lengths will result in a validation error.
- **Invalid Syntax:** Providing strings that do not conform to standard chord notation (e.g., malformed root or quality) will raise an `InvalidChordException`.
- **Type Errors:** Passing non-list types or non-string elements within the lists will cause the validation to fail.

### Fix Code Hint
```python
try:
    mir_eval.chord.validate(ref_labels, est_labels)
except mir_eval.chord.InvalidChordException as e:
    print(f"Invalid chord labels detected: {e}")
```

## API Test: `python:mir_eval.chord.validate_chord_label`

### Signature
```python
def validate_chord_label(chord_label)
```
_Source: source/mir_eval/chord.py:347_

_Source doc:_ Test for well-formedness of a chord label.

Parameters
----------
chord_label : str
    Chord label to validate.

### Goal
Validates that a given string conforms to the standard chord label syntax expected by the `mir_eval.chord` module.

### Parameters
- `chord_label`: A string representing a chord (e.g., "C:maj", "D#:min7").

### Input
- **Data:** A single string.
- **Preconditions:** The label must follow standard chord syntax. The function is typically used to verify labels before they are processed by other `mir_eval.chord` functions.

### Output
Returns `None` if the label is valid. If the label is malformed, it raises an `InvalidChordException`.

### Valid Call Patterns
```python
import mir_eval
# Example of validating a standard chord label
mir_eval.chord.validate_chord_label("C:maj")
```

### LLM Instruction Prompt
- Use `mir_eval.chord.validate_chord_label` to verify chord strings before passing them to evaluation functions.
- Always wrap calls in a `try-except` block to handle `InvalidChordException` if the input source is untrusted.

### Prompt Snippet
```text
# Validate a chord label before processing
try:
    mir_eval.chord.validate_chord_label(label)
except mir_eval.chord.InvalidChordException:
    print(f"Invalid chord label encountered: {label}")
```

### Common Failure Modes
- **Invalid Syntax:** Passing a string that does not conform to the expected chord format (e.g., "Cmaj" instead of "C:maj") will raise an `InvalidChordException`.
- **Type Errors:** Passing a non-string type (e.g., `None`, `int`, or `list`) will result in a `TypeError`.

### Fix Code Hint
```python
# Ensure the input is a string and follows the expected format
if isinstance(label, str):
    try:
        mir_eval.chord.validate_chord_label(label)
    except mir_eval.chord.InvalidChordException:
        # Handle or log the invalid label
        pass
```

## API Test: `python:mir_eval.chord.weighted_accuracy`

### Signature
```python
def weighted_accuracy(comparisons, weights)
```
_Source: source/mir_eval/chord.py:646_

_Source doc:_ Compute the weighted accuracy of a list of chord comparisons.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> est_intervals, est_labels = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, ref_intervals.min(),
...     ref_intervals.max(), mir_eval.chord.NO_CHORD,
...     mir_eval.chord.NO_CHORD)
>>> (intervals,
...  ref_labels,
...  est_labels) = mir_eval.util.merge_labeled_intervals(
...      ref_intervals, ref_labels, est_intervals, est_labels)
>>> durations = mir_eval.util.intervals_to_durations(intervals)
>>> # Here, we're using the "thirds" function to compare labels
>>> # but any of the comparison functions would work.
>>> comparisons = mir_eval.chord.thirds(ref_labels, est_labels)
>>> score = mir_eval.chord.weighted_accuracy(comparisons, durations)

Parameters
----------
comparisons : np.ndarray
    List of chord comparison scores, in [0, 1] or -1
weights : np.ndarray
    Weights (not necessarily normalized) for each comparison.
    This can be a list of interval durations

Returns
-------
score : float
    Weighted accuracy

### Goal
Computes the weighted average accuracy of chord recognition performance by aggregating comparison scores across time intervals.

### Parameters
- `comparisons`: A 1D NumPy array containing scores for each chord segment, where each value is in the range [0, 1] (representing accuracy) or -1 (representing an invalid comparison).
- `weights`: A 1D NumPy array of the same length as `comparisons`, representing the weight (e.g., duration in seconds) to assign to each corresponding comparison score.

### Input
The caller must provide two NumPy arrays of equal length. Before calling, ensure that reference and estimated intervals have been synchronized using `mir_eval.util.adjust_intervals` and merged using `mir_eval.util.merge_labeled_intervals` to ensure the `comparisons` and `weights` arrays align correctly with the temporal structure of the audio.

### Output
Returns a `float` representing the weighted accuracy score, calculated as the sum of (comparison * weight) divided by the sum of weights.

### Valid Call Patterns
```python
score = mir_eval.chord.weighted_accuracy(comparisons, durations)
```

### LLM Instruction Prompt
- When calling `mir_eval.chord.weighted_accuracy`, ensure that `comparisons` and `weights` are 1D NumPy arrays of identical length.
- Always verify that the `comparisons` array contains values in the range [0, 1] or -1, as generated by `mir_eval.chord` comparison functions (e.g., `thirds`, `majmin`).
- Ensure that `weights` corresponds to the duration of the intervals used to generate the `comparisons`.

### Prompt Snippet
```text
# Ensure arrays are aligned and of equal length
comparisons = mir_eval.chord.majmin(ref_labels, est_labels)
durations = mir_eval.util.intervals_to_durations(intervals)
score = mir_eval.chord.weighted_accuracy(comparisons, durations)
```

### Common Failure Modes
- **Shape Mismatch:** Passing `comparisons` and `weights` arrays of different lengths will raise a `ValueError` during computation.
- **Unsynchronized Intervals:** Failing to use `mir_eval.util.adjust_intervals` or `merge_labeled_intervals` before generating comparisons will lead to misaligned data and incorrect accuracy scores.
- **Invalid Values:** Including values outside the [0, 1] or -1 range in `comparisons` may lead to misleading or mathematically invalid accuracy results.

### Fix Code Hint
```python
# Ensure inputs are aligned before computing accuracy
import numpy as np
# Check lengths
if comparisons.shape != weights.shape:
    raise ValueError("Comparisons and weights must have the same length.")
# Compute weighted accuracy
score = mir_eval.chord.weighted_accuracy(comparisons, weights)
```

## API Test: `python:mir_eval.display.IntervalFormatter`

### Signature
```python
class IntervalFormatter(Formatter)
```
_Source: source/mir_eval/display.py:364_

_Source doc:_ Ticker formatter for labeled interval plots.

Parameters
----------
base : array-like of int
    The base positions of each label

ticks : array-like of string
    The labels for the ticks

### Goal
Provides a custom Matplotlib tick formatter to map specific axis positions to corresponding interval labels for visualization of MIR annotations.

### Parameters
- `base`: An array-like collection of integers representing the specific coordinate positions on an axis where labels should be placed.
- `ticks`: An array-like collection of strings corresponding to the labels to be displayed at each position defined in `base`.

### Input
- The caller must provide `base` and `ticks` as sequences of equal length.
- These are typically used in conjunction with Matplotlib axes objects when plotting labeled intervals (e.g., segment boundaries or chord labels).

### Output
Returns `mir_eval.display.IntervalFormatter` — An instance of the formatter class that can be assigned to a Matplotlib axis formatter (e.g., `ax.xaxis.set_major_formatter`).

### Valid Call Patterns
```python
import mir_eval.display
import matplotlib.pyplot as plt

# Example usage with Matplotlib
formatter = mir_eval.display.IntervalFormatter(base=[0, 5, 10], ticks=['A', 'B', 'C'])
fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(formatter)
```

### LLM Instruction Prompt
- When using `mir_eval.display.IntervalFormatter`, ensure the `base` array contains the numerical positions where ticks should appear and the `ticks` array contains the string labels for those positions.
- The lengths of `base` and `ticks` must be identical.
- This class is intended for use with Matplotlib's `set_major_formatter` or `set_minor_formatter` methods.

### Prompt Snippet
```text
# Assigning the formatter to a Matplotlib axis
ax.xaxis.set_major_formatter(mir_eval.display.IntervalFormatter(base_positions, label_strings))
```

### Common Failure Modes
- **Length Mismatch:** Providing `base` and `ticks` arrays of different lengths will result in errors during the rendering phase when Matplotlib attempts to map positions to labels.
- **Non-numeric Base:** Passing non-integer or non-float values in the `base` array will cause issues with axis coordinate mapping.
- **Missing Matplotlib Context:** Attempting to use the formatter outside of a Matplotlib plotting workflow will not produce the intended visualization.

### Fix Code Hint
```python
# Ensure arrays are of equal length before instantiation
if len(base) != len(ticks):
    raise ValueError("base and ticks must have the same length.")
formatter = mir_eval.display.IntervalFormatter(base, ticks)
```

## API Test: `python:mir_eval.display.IntervalFormatter.__call__`

### Signature
```python
def __call__(self, x, pos=None)
```
_Source: source/mir_eval/display.py:379_

_Source doc:_ Map the input position to its corresponding interval label

### Goal
Maps a numerical coordinate (typically a timestamp) to its corresponding interval label for use in Matplotlib axis formatting.

### Parameters
- `x`: The numerical coordinate (e.g., time in seconds) to be formatted.
- `pos`, default `None`: A Matplotlib-specific position argument; typically ignored by the formatter logic.

### Input
- The `IntervalFormatter` instance must be initialized with the relevant interval data.
- `x` should be a numeric value representing a point within the range of the intervals managed by the formatter.
- Precondition: The formatter must be configured with valid labeled intervals (start, end, label) to perform the mapping.

### Output
Returns `str` — The label associated with the interval containing the input coordinate `x`, or an empty string if no interval corresponds to the position.

### Valid Call Patterns
```python
# Inferred from signature:
formatter = mir_eval.display.IntervalFormatter(intervals, labels)
label = formatter(x)
```

### LLM Instruction Prompt
- Use `mir_eval.display.IntervalFormatter` as a callable object to format Matplotlib axis ticks.
- Ensure the input `x` is a scalar numeric value representing time in seconds.
- Do not rely on the `pos` argument, as it is reserved for Matplotlib internal tick-positioning logic.

### Prompt Snippet
```text
# Example of using IntervalFormatter for custom axis labels
import matplotlib.pyplot as plt
from mir_eval.display import IntervalFormatter

formatter = IntervalFormatter(intervals, labels)
ax = plt.gca()
ax.xaxis.set_major_formatter(formatter)
```

### Common Failure Modes
- Passing `x` values outside the range of the intervals provided during initialization, which may result in empty string returns.
- Attempting to use the formatter before the underlying interval/label data has been correctly structured as an $N \times 2$ array and corresponding label list.
- Misinterpreting the `pos` argument; it should be left as `None` in manual calls.

### Fix Code Hint
```python
# Ensure intervals are sorted and labels match the count
import numpy as np
# intervals: np.ndarray of shape (N, 2)
# labels: list of N strings
formatter = mir_eval.display.IntervalFormatter(intervals, labels)
```

## API Test: `python:mir_eval.display.events`

### Signature
```python
def events(times, labels=None, base=None, height=None, ax=None, text_kw=None, prop_cycle=None, **kwargs)
```
_Source: source/mir_eval/display.py:429_

_Source doc:_ Plot event times as a set of vertical lines

Parameters
----------
times : np.ndarray, shape=(n,)
    event times, in the format returned by
    :func:`mir_eval.io.load_events` or
    :func:`mir_eval.io.load_labeled_events`.
labels : list, shape=(n,), optional
    event labels, in the format returned by
    :func:`mir_eval.io.load_labeled_events`.
base : number
    The vertical position of the base of the line.
    By default, this will be the bottom of the plot.
height : number
    The height of the lines.
    By default, this will be the top of the plot (minus `base`).
    .. note:: If either `base` or `height` are provided, both must be provided.
ax : matplotlib.pyplot.axes
    An axis handle on which to draw the segmentation.
    If none is provided, a new set of axes is created.
text_kw : dict
    If `labels` is provided, the properties of the text
    objects can be specified here.
    See `matplotlib.pyplot.Text` for valid parameters
prop_cycle : cycle.Cycler
    An optional property cycle object to specify style properties.
    If not provided, the default property cycler will be retrieved from matplotlib.
**kwargs
    Additional keyword arguments to pass to
    `matplotlib.pyplot.vlines`.

Returns
-------
ax : matplotlib.pyplot.axes._subplots.AxesSubplot
    A handle to the (possibly constructed) plot axes

### Goal
Visualizes discrete event timestamps as vertical lines on a Matplotlib axis, supporting optional labeling and custom styling for qualitative analysis of MIR annotations.

### Parameters
- `times`: A 1D NumPy array of event timestamps in seconds.
- `labels`, default `None`: A list of strings corresponding to each timestamp for annotation.
- `base`, default `None`: The y-coordinate for the bottom of the vertical lines.
- `height`, default `None`: The vertical length of the lines.
- `ax`, default `None`: A Matplotlib axes object; if omitted, a new figure/axes is generated.
- `text_kw`, default `None`: A dictionary of keyword arguments passed to `matplotlib.pyplot.Text` for label styling.
- `prop_cycle`, default `None`: A `cycler.Cycler` object for controlling line aesthetics.
- `kwargs`: Arbitrary keyword arguments passed directly to `matplotlib.pyplot.vlines`.

### Input
- **Data Format:** `times` must be a 1D `np.ndarray` of floats (seconds). `labels` must be a list of length `n`.
- **Preconditions:** Input arrays should be sorted by time. If `base` or `height` are provided, both must be specified.

### Output
Returns a `matplotlib.pyplot.axes._subplots.AxesSubplot` object containing the rendered event visualization.

### Valid Call Patterns
```python
# Example inferred from signature
import matplotlib.pyplot as plt
import mir_eval
import numpy as np

times = np.array([1.0, 2.5, 3.0])
ax = mir_eval.display.events(times)
plt.show()
```

### LLM Instruction Prompt
- Always ensure `times` is a 1D NumPy array.
- If providing `base` or `height`, you must provide both; otherwise, the function will fail to define the vertical extent correctly.
- Use `text_kw` to pass styling dictionaries (e.g., `{'fontsize': 10}`) when `labels` are provided.

### Prompt Snippet
```text
mir_eval.display.events(times=my_times, labels=my_labels, base=0, height=1)
```

### Common Failure Modes
- **Incomplete Geometry:** Providing `base` without `height` (or vice versa) will result in an error.
- **Dimension Mismatch:** Passing `labels` with a length different from `times` will cause an indexing error.
- **Unsorted Input:** While not strictly enforced by the display function, unsorted `times` may lead to confusing visual overlaps or incorrect label placement.

### Fix Code Hint
```python
# Ensure base and height are paired
if (base is not None) != (height is not None):
    raise ValueError("Both 'base' and 'height' must be provided together.")
```

## API Test: `python:mir_eval.display.hierarchy`

### Signature
```python
def hierarchy(intervals_hier, labels_hier, levels=None, ax=None, **kwargs)
```
_Source: source/mir_eval/display.py:384_

_Source doc:_ Plot a hierarchical segmentation

Parameters
----------
intervals_hier : list of np.ndarray
    A list of segmentation intervals.  Each element should be
    an n-by-2 array of segment intervals, in the format returned by
    :func:`mir_eval.io.load_intervals` or
    :func:`mir_eval.io.load_labeled_intervals`.
    Segmentations should be ordered by increasing specificity.
labels_hier : list of list-like
    A list of segmentation labels.  Each element should
    be a list of labels for the corresponding element in
    `intervals_hier`.
levels : list of string
    Each element ``levels[i]`` is a label for the ```i`` th segmentation.
    This is used in the legend to denote the levels in a segment hierarchy.
ax : matplotlib.pyplot.axes
    An axis handle on which to draw the intervals.
    If none is provided, a new set of axes is created.
**kwargs
    Additional keyword arguments to `labeled_intervals`.

Returns
-------
ax : matplotlib.pyplot.axes._subplots.AxesSubplot
    A handle to the (possibly constructed) plot axes

### Goal
Visualizes hierarchical music segmentation data by plotting multiple levels of labeled intervals on a shared timeline.

### Parameters
- `intervals_hier`: A list of $N \times 2$ NumPy arrays representing segment start and end times in seconds, ordered from least to most specific.
- `labels_hier`: A list of lists containing string labels corresponding to each interval in `intervals_hier`.
- `levels`, default `None`: An optional list of strings used to label each segmentation level in the plot legend.
- `ax`, default `None`: A Matplotlib axes object; if not provided, a new figure and axes are generated.
- `kwargs`: Arbitrary keyword arguments passed directly to the underlying `labeled_intervals` plotting function.

### Input
- **Data Format:** Requires lists of NumPy arrays (intervals) and lists of labels.
- **Preconditions:** Intervals must be sorted by time. The input lists must be ordered by increasing specificity (e.g., from coarse section-level segments to fine-grained phrase-level segments).
- **Units:** All time-based values must be in seconds.

### Output
Returns a `matplotlib.pyplot.axes._subplots.AxesSubplot` object containing the rendered hierarchical visualization.

### Valid Call Patterns
```python
# Inferred from signature:
import matplotlib.pyplot as plt
import mir_eval

# Assuming intervals_list and labels_list are prepared
ax = mir_eval.display.hierarchy(intervals_list, labels_list, levels=['Level 1', 'Level 2'])
plt.show()
```

### LLM Instruction Prompt
- When calling `mir_eval.display.hierarchy`, ensure `intervals_hier` and `labels_hier` are lists of equal length.
- Ensure the order of elements in the lists represents increasing specificity (coarse to fine).
- If providing `levels`, ensure the length matches the number of segmentation levels provided in `intervals_hier`.

### Prompt Snippet
```text
mir_eval.display.hierarchy(intervals_hier=my_intervals, labels_hier=my_labels, levels=['Coarse', 'Fine'])
```

### Common Failure Modes
- **Mismatched Lengths:** Providing a different number of interval arrays and label lists will cause an index error or visual misalignment.
- **Unsorted Intervals:** Passing intervals that are not sorted by time will result in overlapping or incorrectly rendered segments.
- **Missing Dependencies:** Attempting to plot without `matplotlib` installed will raise an `ImportError`.

### Fix Code Hint
```python
# Ensure intervals are sorted before passing to hierarchy
import numpy as np
sorted_intervals = intervals[np.argsort(intervals[:, 0])]
```

## API Test: `python:mir_eval.display.labeled_intervals`

### Signature
```python
def labeled_intervals(intervals, labels, label_set=None, base=None, height=None, extend_labels=True, ax=None, tick=True, prop_cycle=None, **kwargs)
```
_Source: source/mir_eval/display.py:198_

_Source doc:_ Plot labeled intervals with each label on its own row.

Parameters
----------
intervals : np.ndarray, shape=(n, 2)
    segment intervals, in the format returned by
    :func:`mir_eval.io.load_intervals` or
    :func:`mir_eval.io.load_labeled_intervals`.

labels : list, shape=(n,)
    reference segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.

label_set : list
    An (ordered) list of labels to determine the plotting order.
    If not provided, the labels will be inferred from
    ``ax.get_yticklabels()``.
    If no ``yticklabels`` exist, then the sorted set of unique values
    in ``labels`` is taken as the label set.

base : np.ndarray, shape=(n,), optional
    Vertical positions of each label.
    By default, labels are positioned at integers
    ``np.arange(len(labels))``.

height : scalar or np.ndarray, shape=(n,), optional
    Height for each label.
    If scalar, the same value is applied to all labels.
    By default, each label has ``height=1``.

extend_labels : bool
    If ``False``, only values of ``labels`` that also exist in
    ``label_set`` will be shown.

    If ``True``, all labels are shown, with those in `labels` but
    not in ``label_set`` appended to the top of the plot.
    A horizontal line is drawn to indicate the separation between
    values in or out of ``label_set``.

ax : matplotlib.pyplot.axes
    An axis handle on which to draw the intervals.
    If none is provided, a new set of axes is created.

tick : bool
    If ``True``, sets tick positions and labels on the y-axis.

prop_cycle : cycle.Cycler
    An optional property cycle object to specify style properties.
    If not provided, the default property cycler will be retrieved from matplotlib.

**kwargs
    Additional keyword arguments to pass to
    `matplotlib.collection.PolyCollection`.

Returns
-------
ax : matplotlib.pyplot.axes._subplots.AxesSubplot
    A handle to the (possibly constructed) plot axes

### Goal
Visualizes segment-based annotations (such as structural segmentation or chord sequences) by plotting labeled intervals on a Matplotlib axis, with each unique label assigned to a specific vertical row.

### Parameters
- `intervals`: An $N \times 2$ NumPy array of start and end times (in seconds) for each segment.
- `labels`: A list of $N$ strings or identifiers corresponding to each interval.
- `label_set`, default `None`: An optional ordered list defining the vertical order of labels on the y-axis.
- `base`, default `None`: Optional array defining specific vertical offsets for each label.
- `height`, default `None`: Optional scalar or array defining the vertical thickness of the plotted intervals.
- `extend_labels`, default `True`: If `True`, labels not in `label_set` are appended to the top of the plot with a separator line.
- `ax`, default `None`: The Matplotlib axis object to draw on; creates a new one if `None`.
- `tick`, default `True`: Whether to automatically configure y-axis ticks and labels.
- `prop_cycle`, default `None`: A Matplotlib `Cycler` object for custom styling of the intervals.
- `kwargs`: Arbitrary keyword arguments passed directly to `matplotlib.collection.PolyCollection`.

### Input
- **Data:** Requires `intervals` as an $N \times 2$ NumPy array and `labels` as a list of length $N$.
- **Preconditions:** Inputs should be in the format produced by `mir_eval.io.load_labeled_intervals`. Time values must be in seconds.

### Output
Returns a `matplotlib.pyplot.axes._subplots.AxesSubplot` object containing the rendered visualization.

### Valid Call Patterns
```python
# Inferred from signature:
import matplotlib.pyplot as plt
import mir_eval
ax = mir_eval.display.labeled_intervals(intervals, labels)
plt.show()
```

### LLM Instruction Prompt
- When calling `mir_eval.display.labeled_intervals`, ensure `intervals` is a 2D NumPy array of shape `(n, 2)` and `labels` is a list of length `n`.
- Always provide the `ax` parameter if you intend to overlay this plot on an existing figure.
- Use `extend_labels=False` if you want to strictly filter the visualization to only include labels defined in `label_set`.

### Prompt Snippet
```text
mir_eval.display.labeled_intervals(intervals=my_intervals, labels=my_labels, ax=my_ax)
```

### Common Failure Modes
- **Shape Mismatch:** Passing `intervals` and `labels` with different lengths $N$ will cause an error.
- **Empty Input:** Passing empty arrays may result in an empty plot or errors depending on the Matplotlib version.
- **Non-numeric Intervals:** Providing intervals that are not in seconds or are not numeric will cause plotting failures.

### Fix Code Hint
```python
# Ensure intervals are sorted by start time before plotting
idx = np.argsort(intervals[:, 0])
intervals = intervals[idx]
labels = [labels[i] for i in idx]
mir_eval.display.labeled_intervals(intervals, labels)
```

## API Test: `python:mir_eval.display.multipitch`

### Signature
```python
def multipitch(times, frequencies, midi=False, unvoiced=False, ax=None, prop_cycle=None, **kwargs)
```
_Source: source/mir_eval/display.py:648_

_Source doc:_ Visualize multiple f0 measurements

Parameters
----------
times : np.ndarray, shape=(n,)
    Sample times of frequencies

frequencies : list of np.ndarray
    frequencies (in Hz) of the pitch measurements.
    Voicing is indicated by sign (positive for voiced,
    non-positive for non-voiced).

    `times` and `frequencies` should be in the format produced by
    :func:`mir_eval.io.load_ragged_time_series`

midi : bool
    If `True`, plot on a MIDI-numbered vertical axis.
    Otherwise, plot on a linear frequency axis.

unvoiced : bool
    If `True`, unvoiced pitches are plotted and indicated
    by transparency.

    Otherwise, unvoiced pitches are omitted from the display.

ax : matplotlib.pyplot.axes
    An axis handle on which to draw the pitch contours.
    If none is provided, a new set of axes is created.

prop_cycle : cycle.Cycler
    An optional property cycle object to specify style properties.
    If not provided, the default property cycler will be retrieved from matplotlib.

**kwargs
    Additional keyword arguments to `plt.scatter`.

Returns
-------
ax : matplotlib.pyplot.axes._subplots.AxesSubplot
    A handle to the (possibly constructed) plot axes

### Goal
Visualizes multiple fundamental frequency (f0) measurements over time, supporting both linear frequency and MIDI-scaled axes for multi-pitch or multi-source audio analysis.

### Parameters
- `times`: A 1D NumPy array of shape `(n,)` containing the sample timestamps in seconds.
- `frequencies`: A list of NumPy arrays containing f0 values in Hz; positive values indicate voiced segments, while non-positive values indicate unvoiced segments.
- `midi`, default `False`: If `True`, the vertical axis is scaled to MIDI note numbers; otherwise, it uses a linear frequency scale.
- `unvoiced`, default `False`: If `True`, unvoiced pitch measurements are rendered with transparency; if `False`, they are excluded from the plot.
- `ax`, default `None`: A Matplotlib axes object to draw on; if `None`, a new figure and axes are initialized.
- `prop_cycle`, default `None`: A `matplotlib.cycler.Cycler` object to define the visual style of the plotted contours.
- `kwargs`: Arbitrary keyword arguments passed directly to `matplotlib.pyplot.scatter` for styling the markers.

### Input
The function expects data in the format produced by `mir_eval.io.load_ragged_time_series`. Inputs must be pre-processed such that `times` and `frequencies` are aligned. Frequencies must be in Hz, with voicing encoded by the sign of the value.

### Output
Returns a `matplotlib.pyplot.axes._subplots.AxesSubplot` object containing the rendered visualization.

### Valid Call Patterns
```python
# Example inferred from signature (not verified by test suite)
import matplotlib.pyplot as plt
import mir_eval
times, frequencies = mir_eval.io.load_ragged_time_series('path/to/data.txt')
ax = mir_eval.display.multipitch(times, frequencies, midi=True, unvoiced=True)
plt.show()
```

### LLM Instruction Prompt
- Always ensure `times` and `frequencies` are loaded via `mir_eval.io.load_ragged_time_series` to guarantee the expected ragged structure.
- If plotting multiple sources, ensure the `frequencies` list corresponds correctly to the `times` array.
- Use `midi=True` when comparing against ground truth annotations that are typically represented in MIDI note numbers.

### Prompt Snippet
```text
mir_eval.display.multipitch(times, frequencies, midi=True, unvoiced=True)
```

### Common Failure Modes
- Passing non-ragged arrays or mismatched dimensions between `times` and `frequencies` will result in `ValueError` or plotting errors.
- Providing frequencies in units other than Hz (e.g., cents) will lead to incorrect visual scaling unless `midi=True` is used to interpret the values appropriately.
- Attempting to plot without a valid Matplotlib backend in a headless environment may cause display errors.

### Fix Code Hint
```python
# Ensure data is loaded correctly before visualization
times, frequencies = mir_eval.io.load_ragged_time_series(file_path)
# Use the returned ax for further customization
ax = mir_eval.display.multipitch(times, frequencies, midi=True)
ax.set_title("Multi-pitch Contour")
```

## API Test: `python:mir_eval.display.piano_roll`

### Signature
```python
def piano_roll(intervals, pitches=None, midi=None, ax=None, **kwargs)
```
_Source: source/mir_eval/display.py:759_

_Source doc:_ Plot a quantized piano roll as intervals

Parameters
----------
intervals : np.ndarray, shape=(n, 2)
    timing intervals for notes

pitches : np.ndarray, shape=(n,), optional
    pitches of notes (in Hz).

midi : np.ndarray, shape=(n,), optional
    pitches of notes (in MIDI numbers).

    At least one of ``pitches`` or ``midi`` must be provided.

ax : matplotlib.pyplot.axes
    An axis handle on which to draw the intervals.
    If none is provided, a new set of axes is created.

**kwargs
    Additional keyword arguments to :func:`labeled_intervals`.

Returns
-------
ax : matplotlib.pyplot.axes._subplots.AxesSubplot
    A handle to the (possibly constructed) plot axes

### Goal
Visualizes note-level information as a quantized piano roll plot, mapping time intervals and pitch values to a 2D coordinate system.

### Parameters
- `intervals`: A NumPy array of shape `(n, 2)` containing `[start, end]` timestamps in seconds for each note.
- `pitches`, default `None`: A NumPy array of shape `(n,)` containing fundamental frequencies in Hz.
- `midi`, default `None`: A NumPy array of shape `(n,)` containing MIDI note numbers.
- `ax`, default `None`: A Matplotlib axes object. If `None`, a new figure and axes are initialized.
- `kwargs`: Arbitrary keyword arguments passed directly to `labeled_intervals` for styling or configuration.

### Input
- **Data Format:** Requires `intervals` as an `(n, 2)` NumPy array.
- **Pitch Requirement:** At least one of `pitches` (Hz) or `midi` (MIDI numbers) must be provided.
- **Preconditions:** Input arrays must be of consistent length `n`. Time values must be in seconds.

### Output
Returns a `matplotlib.pyplot.axes._subplots.AxesSubplot` object containing the rendered piano roll visualization.

### Valid Call Patterns
```python
# Example inferred from signature (not verified)
import mir_eval
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
mir_eval.display.piano_roll(intervals, midi=midi_values, ax=ax)
```

### LLM Instruction Prompt
- When calling `mir_eval.display.piano_roll`, ensure that `intervals` is a 2D NumPy array of shape `(n, 2)`.
- You must provide either `pitches` or `midi` as a 1D NumPy array of length `n`.
- If no `ax` is provided, the function will generate a new Matplotlib figure; ensure the environment supports headless plotting if necessary.

### Prompt Snippet
```text
mir_eval.display.piano_roll(intervals=my_intervals, midi=my_midi_array)
```

### Common Failure Modes
- **Missing Pitch Data:** Providing neither `pitches` nor `midi` will result in an error as the function cannot map the vertical axis.
- **Shape Mismatch:** Providing `intervals` and `pitches`/`midi` arrays with different lengths `n` will cause a runtime exception.
- **Invalid Time Units:** Passing time values in samples rather than seconds will result in an incorrectly scaled horizontal axis.

### Fix Code Hint
```python
# Ensure arrays are aligned and in correct units
import numpy as np
intervals = np.array([[0.0, 1.0], [1.0, 2.0]])
midi = np.array([60, 62])
mir_eval.display.piano_roll(intervals, midi=midi)
```

## API Test: `python:mir_eval.display.pitch`

### Signature
```python
def pitch(times, frequencies, midi=False, unvoiced=False, ax=None, prop_cycle=None, **kwargs)
```
_Source: source/mir_eval/display.py:545_

_Source doc:_ Visualize pitch contours

Parameters
----------
times : np.ndarray, shape=(n,)
    Sample times of frequencies

frequencies : np.ndarray, shape=(n,)
    frequencies (in Hz) of the pitch contours.
    Voicing is indicated by sign (positive for voiced,
    non-positive for non-voiced).

midi : bool
    If `True`, plot on a MIDI-numbered vertical axis.
    Otherwise, plot on a linear frequency axis.

unvoiced : bool
    If `True`, unvoiced pitch contours are plotted and indicated
    by transparency.

    Otherwise, unvoiced pitch contours are omitted from the display.

ax : matplotlib.pyplot.axes
    An axis handle on which to draw the pitch contours.
    If none is provided, a new set of axes is created.

prop_cycle : cycle.Cycler
    An optional property cycle object to specify style properties.
    If not provided, the default property cycler will be retrieved from matplotlib.

**kwargs
    Additional keyword arguments to `matplotlib.pyplot.plot`.

Returns
-------
ax : matplotlib.pyplot.axes._subplots.AxesSubplot
    A handle to the (possibly constructed) plot axes

### Goal
Visualize pitch contours by plotting frequency over time, supporting both linear frequency and MIDI-note vertical axes.

### Parameters
- `times`: A 1D NumPy array of shape `(n,)` containing the timestamps in seconds corresponding to each frequency measurement.
- `frequencies`: A 1D NumPy array of shape `(n,)` containing fundamental frequencies in Hz. Voiced segments must be positive; non-voiced segments must be non-positive.
- `midi`, default `False`: If `True`, the vertical axis is scaled to MIDI note numbers; otherwise, it uses a linear frequency scale.
- `unvoiced`, default `False`: If `True`, non-voiced segments are rendered with transparency; if `False`, they are excluded from the plot.
- `ax`, default `None`: A Matplotlib axes object to draw on. If `None`, a new figure and axes are created.
- `prop_cycle`, default `None`: A `matplotlib.cycler.Cycler` object to define line styles.
- `kwargs`: Arbitrary keyword arguments passed directly to `matplotlib.pyplot.plot` for styling (e.g., `color`, `linewidth`).

### Input
- **Data:** Requires two 1D NumPy arrays of equal length `n`.
- **Preconditions:** `times` must be sorted in ascending order. `frequencies` must use the sign-based voicing convention (positive = voiced, non-positive = unvoiced).

### Output
Returns a `matplotlib.pyplot.axes._subplots.AxesSubplot` object containing the rendered pitch contour visualization.

### Valid Call Patterns
```python
import matplotlib.pyplot as plt
import mir_eval.display
import numpy as np

# Inferred from signature:
times = np.linspace(0, 10, 100)
freqs = 440 + 10 * np.sin(times)
ax = mir_eval.display.pitch(times, freqs, midi=True, unvoiced=True)
plt.show()
```

### LLM Instruction Prompt
- When calling `mir_eval.display.pitch`, ensure `times` and `frequencies` are 1D NumPy arrays of the same length.
- Always verify that the voicing convention (positive for voiced, non-positive for unvoiced) is applied to the `frequencies` array before plotting.
- Use `midi=True` if the visualization is intended for musical note analysis.

### Prompt Snippet
```text
mir_eval.display.pitch(times, frequencies, midi=True, unvoiced=True)
```

### Common Failure Modes
- **Shape Mismatch:** Passing `times` and `frequencies` arrays of different lengths will raise a `ValueError` during plotting.
- **Unsorted Times:** If `times` are not monotonically increasing, the resulting plot will contain visual artifacts (lines connecting non-sequential points).
- **Voicing Errors:** Providing positive values for non-voiced segments will cause them to be plotted as valid pitch contours, leading to incorrect visual representations.

### Fix Code Hint
```python
# Ensure arrays are sorted by time
idx = np.argsort(times)
times = times[idx]
frequencies = frequencies[idx]

# Ensure voicing convention is correct
# Example: set non-voiced (e.g., 0 Hz) to -1
frequencies[frequencies <= 0] = -1
```

## API Test: `python:mir_eval.display.segments`

### Signature
```python
def segments(intervals, labels, base=None, height=None, text=False, text_kw=None, ax=None, prop_cycle=None, **kwargs)
```
_Source: source/mir_eval/display.py:66_

_Source doc:_ Plot a segmentation as a set of disjoint rectangles.

Parameters
----------
intervals : np.ndarray, shape=(n, 2)
    segment intervals, in the format returned by
    :func:`mir_eval.io.load_intervals` or
    :func:`mir_eval.io.load_labeled_intervals`.
labels : list, shape=(n,)
    reference segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
base : number
    The vertical position of the base of the rectangles.
    By default, this will be the bottom of the plot.
height : number
    The height of the rectangles.
    By default, this will be the top of the plot (minus ``base``).
    .. note:: If either `base` or `height` are provided, both must be provided.
text : bool
    If true, each segment's label is displayed in its
    upper-left corner
text_kw : dict
    If ``text == True``, the properties of the text
    object can be specified here.
    See ``matplotlib.pyplot.Text`` for valid parameters
ax : matplotlib.pyplot.axes
    An axis handle on which to draw the segmentation.
    If none is provided, a new set of axes is created.
prop_cycle : cycle.Cycler
    An optional property cycle object to specify style properties.
    If not provided, the default property cycler will be retrieved from matplotlib.
**kwargs
    Additional keyword arguments to pass to
    ``matplotlib.patches.Rectangle``.

Returns
-------
ax : matplotlib.pyplot.axes._subplots.AxesSubplot
    A handle to the (possibly constructed) plot axes

### Goal
Visualizes music segmentation data as a sequence of disjoint rectangles on a Matplotlib axis, facilitating qualitative analysis of structural boundaries and labels.

### Parameters
- `intervals`: An $N \times 2$ NumPy array of start and end times (in seconds) for each segment.
- `labels`: A list of $N$ strings or identifiers corresponding to each segment interval.
- `base`, default `None`: The vertical coordinate for the bottom edge of the rectangles; requires `height` to be set if provided.
- `height`, default `None`: The vertical span of the rectangles; requires `base` to be set if provided.
- `text`, default `False`: If `True`, renders the segment label text inside the top-left corner of each rectangle.
- `text_kw`, default `None`: A dictionary of keyword arguments passed to the Matplotlib `Text` object when `text=True`.
- `ax`, default `None`: A pre-existing Matplotlib `Axes` object to draw on; if `None`, a new figure and axes are created.
- `prop_cycle`, default `None`: A `matplotlib.cycler.Cycler` object to control the color or style cycle of the segments.
- `kwargs`: Arbitrary keyword arguments passed directly to `matplotlib.patches.Rectangle` (e.g., `alpha`, `edgecolor`).

### Input
- **Data Format:** Requires `intervals` as an $N \times 2$ NumPy array and `labels` as a list of length $N$.
- **Preconditions:** Time values must be in seconds. Intervals should be disjoint. It is recommended to use `mir_eval.io.load_labeled_intervals` to ensure compatibility with the expected input structure.

### Output
Returns a `matplotlib.axes.Axes` object containing the rendered segmentation plot.

### Valid Call Patterns
```python
import matplotlib.pyplot as plt
import mir_eval

# Inferred from signature:
fig, ax = plt.subplots()
mir_eval.display.segments(intervals, labels, ax=ax, text=True)
```

### LLM Instruction Prompt
- Always ensure `intervals` is a 2D NumPy array of shape `(n, 2)` and `labels` is a list of length `n`.
- If providing `base`, you must also provide `height`.
- When `text=True`, ensure `text_kw` is a dictionary if specific font or alignment properties are required.
- Always return the `ax` object to the user for further plot customization.

### Prompt Snippet
```text
mir_eval.display.segments(intervals, labels, text=True, ax=ax)
```

### Common Failure Modes
- **Mismatched Dimensions:** Providing `intervals` and `labels` with different lengths will cause an error during iteration.
- **Partial Vertical Specification:** Providing `base` without `height` (or vice versa) will raise a `ValueError` or result in unexpected plot behavior.
- **Invalid Types:** Passing non-NumPy arrays for `intervals` or non-list types for `labels` may cause failures in internal indexing.

### Fix Code Hint
```python
# Ensure intervals are sorted and labels match length
import numpy as np
intervals = np.array(intervals)
assert len(intervals) == len(labels), "Intervals and labels must have the same length."
```

## API Test: `python:mir_eval.display.separation`

### Signature
```python
def separation(sources, fs=22050, labels=None, alpha=0.75, ax=None, rasterized=True, edgecolors='None', shading='gouraud', prop_cycle=None, **kwargs)
```
_Source: source/mir_eval/display.py:809_

_Source doc:_ Source-separation visualization

Parameters
----------
sources : np.ndarray, shape=(nsrc, nsampl)
    A list of waveform buffers corresponding to each source
fs : number > 0
    The sampling rate
labels : list of strings
    An optional list of descriptors corresponding to each source
alpha : float in [0, 1]
    Maximum alpha (opacity) of spectrogram values.
ax : matplotlib.pyplot.axes
    An axis handle on which to draw the spectrograms.
    If none is provided, a new set of axes is created.
rasterized : bool
    If `True`, the spectrogram is rasterized.
edgecolors : str or None
    The color of the edges of the spectrogram patches.
    Set to "None" (default) to disable edge coloring.
shading : str
    The shading method to use for the spectrogram.
    See `matplotlib.pyplot.pcolormesh` for valid options.
prop_cycle : cycle.Cycler
    An optional property cycle object to specify colors for each signal.
    If not provided, the default property cycler will be retrieved from matplotlib.
**kwargs
    Additional keyword arguments to ``scipy.signal.spectrogram``

Returns
-------
ax
    The axis handle for this plot

### Goal
Visualizes the results of a source separation task by plotting the spectrograms of multiple audio source buffers on a shared or provided Matplotlib axis.

### Parameters
- `sources`: A 2D NumPy array of shape `(nsrc, nsampl)` containing the waveform buffers for each separated source.
- `fs`, default `22050`: The sampling rate of the input audio signals in Hz.
- `labels`, default `None`: An optional list of strings to label each source in the visualization.
- `alpha`, default `0.75`: The maximum opacity (0 to 1) applied to the spectrogram visualization.
- `ax`, default `None`: A Matplotlib `Axes` object. If `None`, a new figure and axes are generated.
- `rasterized`, default `True`: Boolean flag to enable rasterization of the spectrogram for efficient rendering.
- `edgecolors`, default `'None'`: The color of the edges of the spectrogram patches; defaults to "None" to disable.
- `shading`, default `'gouraud'`: The shading method used for the spectrogram, passed to `matplotlib.pyplot.pcolormesh`.
- `prop_cycle`, default `None`: A `matplotlib.cycler.Cycler` object to define the color scheme for the signals.
- `kwargs`: Arbitrary keyword arguments passed directly to `scipy.signal.spectrogram` to control spectrogram computation.

### Input
- **Data:** A 2D NumPy array representing the separated audio sources.
- **Preconditions:** The input `sources` must be a valid NumPy array. The `fs` must be a positive number.
- **Note:** This function is deprecated in favor of `sigsep-museval`.

### Output
Returns a `matplotlib.axes.Axes` object containing the rendered spectrogram visualization.

### Valid Call Patterns
```python
# Inferred from signature:
import mir_eval
import numpy as np
import matplotlib.pyplot as plt

sources = np.random.randn(2, 44100) # 2 sources, 1 second at 44.1kHz
ax = mir_eval.display.separation(sources, fs=44100)
plt.show()
```

### LLM Instruction Prompt
- When calling `mir_eval.display.separation`, ensure the `sources` array is correctly shaped as `(n_sources, n_samples)`.
- Always provide the `fs` parameter if the sampling rate differs from the default 22050 Hz.
- Note that this function is deprecated; if the user is performing formal evaluation, suggest `sigsep-museval` instead.

### Prompt Snippet
```text
mir_eval.display.separation(sources=my_sources, fs=44100, labels=['vocals', 'drums'])
```

### Common Failure Modes
- **Shape Mismatch:** Passing a 1D array or an incorrectly transposed array for `sources` will cause a failure in `scipy.signal.spectrogram`.
- **Deprecation:** Users may encounter warnings or lack of support for newer separation evaluation workflows as this function is deprecated.
- **Matplotlib Errors:** Providing an invalid `ax` object or incompatible `shading` string will raise standard Matplotlib exceptions.

### Fix Code Hint
```python
# Ensure sources are (n_sources, n_samples)
if sources.ndim == 1:
    sources = sources[np.newaxis, :]
ax = mir_eval.display.separation(sources, fs=fs)
```

## API Test: `python:mir_eval.display.ticker_notes`

### Signature
```python
def ticker_notes(ax=None)
```
_Source: source/mir_eval/display.py:963_

_Source doc:_ Set the y-axis of the given axes to MIDI notes

Parameters
----------
ax : matplotlib.pyplot.axes
    The axes handle to apply the ticker.
    By default, uses the current axes handle.

### Goal
Configures the y-axis of a Matplotlib plot to display MIDI note numbers, facilitating the visualization of pitch-based annotations such as piano rolls or transcription outputs.

### Parameters
- `ax`, default `None`: A `matplotlib.pyplot.axes` object. If `None`, the function automatically targets the current active axes handle.

### Input
- **Preconditions:** The caller must have an existing Matplotlib axes object where the y-axis data represents MIDI note values (e.g., 0–127). The function assumes the axes are already initialized and populated with data relevant to MIDI pitch.

### Output
Returns `None`. The function modifies the provided `ax` object in-place by updating the y-axis ticker to reflect MIDI note formatting.

### Valid Call Patterns
```python
import matplotlib.pyplot as plt
import mir_eval.display

# Using the current axes
mir_eval.display.ticker_notes()

# Using a specific axes handle
fig, ax = plt.subplots()
mir_eval.display.ticker_notes(ax=ax)
```

### LLM Instruction Prompt
- When calling `mir_eval.display.ticker_notes`, ensure that the target axes are already configured for pitch-related data. If no axes are provided, the function will implicitly modify the current Matplotlib state; ensure `plt.gca()` is valid before calling.

### Prompt Snippet
```text
# Example of applying MIDI note ticker to a plot
import mir_eval.display
import matplotlib.pyplot as plt

# ... (plotting logic)
mir_eval.display.ticker_notes(ax=plt.gca())
```

### Common Failure Modes
- **Missing Matplotlib:** The function requires `matplotlib` to be installed and imported; failure to provide a valid axes object when one does not exist in the current state will raise a `matplotlib` error.
- **Incorrect Data Mapping:** If the y-axis data is not in MIDI note units (e.g., if it is in Hz), the ticker will display misleading labels. Ensure data is converted to MIDI note numbers (e.g., using `mir_eval.util.hz_to_midi`) before plotting.

### Fix Code Hint
```python
# Ensure data is in MIDI format before applying the ticker
import mir_eval.util
import mir_eval.display

# Convert Hz to MIDI if necessary
midi_pitches = mir_eval.util.hz_to_midi(freq_data)
plt.plot(time_data, midi_pitches)
mir_eval.display.ticker_notes()
```

## API Test: `python:mir_eval.display.ticker_pitch`

### Signature
```python
def ticker_pitch(ax=None)
```
_Source: source/mir_eval/display.py:981_

_Source doc:_ Set the y-axis of the given axes to MIDI frequencies

Parameters
----------
ax : matplotlib.pyplot.axes
    The axes handle to apply the ticker.
    By default, uses the current axes handle.

### Goal
Configures the y-axis of a Matplotlib plot to display tick marks corresponding to MIDI note numbers, facilitating the visualization of pitch-based MIR data.

### Parameters
- `ax`, default `None`: A `matplotlib.pyplot.axes` object. If `None`, the function automatically targets the current active axes handle.

### Input
- **Preconditions:** The caller must have an existing Matplotlib figure and axes object. The data plotted on the y-axis should be in units of MIDI note numbers (where 69 corresponds to A4 = 440 Hz).
- **Data Format:** The function expects the axes to be populated with pitch data represented as MIDI note numbers.

### Output
Returns `None`. The function modifies the provided `ax` object in-place by updating the y-axis tick locations and labels.

### Valid Call Patterns
```python
import matplotlib.pyplot as plt
import mir_eval.display

# Using the current axes
mir_eval.display.ticker_pitch()

# Using a specific axes handle
fig, ax = plt.subplots()
mir_eval.display.ticker_pitch(ax=ax)
```

### LLM Instruction Prompt
- When generating code for `mir_eval.display.ticker_pitch`, ensure that the Matplotlib environment is initialized.
- If the user provides an axes object, pass it explicitly to the `ax` parameter.
- Always assume the y-axis data is already scaled to MIDI note numbers before calling this function.

### Prompt Snippet
```text
# Example of setting up a pitch plot
import matplotlib.pyplot as plt
import mir_eval.display

fig, ax = plt.subplots()
# ... plot your pitch data here ...
mir_eval.display.ticker_pitch(ax=ax)
plt.show()
```

### Common Failure Modes
- **Incorrect Units:** Passing frequency data in Hz instead of MIDI note numbers will result in incorrect tick labels. Use `mir_eval.util.hz_to_midi` to convert frequency data before plotting.
- **Missing Matplotlib:** Calling the function without an active figure or axes when `ax=None` will raise a `matplotlib` error.
- **Axes Overwrite:** If multiple tickers are applied to the same axis, the last one called will determine the final formatting.

### Fix Code Hint
```python
# Convert Hz to MIDI before plotting if necessary
import mir_eval.util
midi_data = mir_eval.util.hz_to_midi(frequency_data)
plt.plot(time_data, midi_data)
mir_eval.display.ticker_pitch()
```

## API Test: `python:mir_eval.hierarchy.evaluate`

### Signature
```python
def evaluate(ref_intervals_hier, ref_labels_hier, est_intervals_hier, est_labels_hier, **kwargs)
```
_Source: source/mir_eval/hierarchy.py:619_

_Source doc:_ Compute all hierarchical structure metrics for the given reference and
estimated annotations.

### Goal
Computes a comprehensive suite of hierarchical structure evaluation metrics (T-measures) by comparing multi-level reference and estimated segmentations.

### Parameters
- `ref_intervals_hier`: A list of list-like objects, where each element represents the intervals for a specific level of the reference hierarchy.
- `ref_labels_hier`: A list of lists of strings, where each inner list contains the labels corresponding to the intervals at that level of the reference hierarchy.
- `est_intervals_hier`: A list of list-like objects, where each element represents the intervals for a specific level of the estimated hierarchy.
- `est_labels_hier`: A list of lists of strings, where each inner list contains the labels corresponding to the intervals at that level of the estimated hierarchy.
- `kwargs`: Additional keyword arguments passed to the underlying evaluation metrics (e.g., `transitive` flags).

### Input
- **Data Format:** Hierarchical annotations must be provided as ordered lists of segmentations. Each segmentation level consists of intervals (typically $N \times 2$ arrays) and corresponding labels.
- **Preconditions:** All time-based inputs must be in seconds. Annotations should be validated for consistency (e.g., interval boundaries must be sorted and non-overlapping within a level).

### Output
Returns `OrderedDict` — A dictionary mapping metric names (e.g., 'T-Measure full', 'T-Precision reduced') to their corresponding float scores.

### Valid Call Patterns
```python
import mir_eval
# Toy example
ref_i = [[[0, 30], [30, 60]], [[0, 15], [15, 30], [30, 45], [45, 60]]]
est_i = [[[0, 45], [45, 60]], [[0, 15], [15, 30], [30, 45], [45, 60]]]
ref_l = [ ['A', 'B'], ['a', 'b', 'a', 'c'] ]
est_l = [ ['A', 'B'], ['a', 'a', 'b', 'b'] ]
scores = mir_eval.hierarchy.evaluate(ref_i, ref_l, est_i, est_l)
```

### LLM Instruction Prompt
- When calling `mir_eval.hierarchy.evaluate`, ensure that `ref_intervals_hier` and `est_intervals_hier` are structured as lists of segmentations, where each segmentation is a list of `[start, end]` pairs.
- Ensure that the number of labels in `ref_labels_hier` matches the number of intervals in the corresponding level of `ref_intervals_hier`.
- The function returns an `OrderedDict`; access specific metrics by their string keys (e.g., 'T-Measure full').

### Prompt Snippet
```text
Use mir_eval.hierarchy.evaluate(ref_intervals_hier, ref_labels_hier, est_intervals_hier, est_labels_hier) to compute hierarchical structure metrics.
```

### Common Failure Modes
- **ValueError:** Raised if the input annotations are invalid, such as mismatched interval/label counts or malformed interval structures.
- **Sorting Errors:** Metrics may produce incorrect results if intervals are not sorted by time.
- **Hierarchy Mismatch:** Providing a different number of levels between reference and estimation may lead to unexpected behavior or errors depending on the specific metric implementation.

### Fix Code Hint
```python
# Ensure intervals are sorted and labels match length
import numpy as np
# Example of ensuring interval validity
ref_intervals = [np.array(level) for level in ref_intervals_hier]
# Use mir_eval.util.validate_intervals if necessary before passing to evaluate
```

## API Test: `python:mir_eval.hierarchy.lmeasure`

### Signature
```python
def lmeasure(reference_intervals_hier, reference_labels_hier, estimated_intervals_hier, estimated_labels_hier, frame_size=0.1, beta=1.0)
```
_Source: source/mir_eval/hierarchy.py:548_

_Source doc:_ Compute the tree measures for hierarchical segment annotations.

Parameters
----------
reference_intervals_hier : list of ndarray
    ``reference_intervals_hier[i]`` contains the segment intervals
    (in seconds) for the ``i`` th layer of the annotations.  Layers are
    ordered from top to bottom, so that the last list of intervals should
    be the most specific.
reference_labels_hier : list of list of str
    ``reference_labels_hier[i]`` contains the segment labels for the
    ``i`` th layer of the annotations
estimated_intervals_hier : list of ndarray
estimated_labels_hier : list of ndarray
    Like ``reference_intervals_hier`` and ``reference_labels_hier``
    but for the estimated annotation
frame_size : float > 0
    length (in seconds) of frames.  The frame size cannot be longer than
    the window.
beta : float > 0
    beta parameter for the F-measure.

Returns
-------
l_precision : number [0, 1]
    L-measure Precision
l_recall : number [0, 1]
    L-measure Recall
l_measure : number [0, 1]
    F-beta measure for ``(l_precision, l_recall)``

Raises
------
ValueError
    If either of the input hierarchies are inconsistent

    If the input hierarchies have different time durations

    If ``frame_size > window`` or ``frame_size <= 0``

### Goal
Computes the L-measure, a hierarchical evaluation metric that assesses the accuracy of multi-layer segment annotations by comparing tree-structured segmentations against ground truth.

### Parameters
- `reference_intervals_hier`: A list of `np.ndarray` objects, where each array contains `[start, end]` intervals in seconds for a specific hierarchical layer.
- `reference_labels_hier`: A list of lists of strings, where each inner list contains the labels corresponding to the intervals in the respective layer of `reference_intervals_hier`.
- `estimated_intervals_hier`: A list of `np.ndarray` objects representing the estimated segment intervals for each hierarchical layer.
- `estimated_labels_hier`: A list of lists of strings representing the estimated labels for each hierarchical layer.
- `frame_size`, default `0.1`: The length of frames in seconds used for discretization; must be greater than 0 and less than or equal to the window size.
- `beta`, default `1.0`: The weighting factor for the F-measure; a higher beta weights recall more heavily than precision.

### Input
The function expects hierarchical data structures where each layer is represented as a list of intervals and labels. All time-based inputs must be in seconds. Preconditions include that the hierarchies must be consistent (e.g., matching time durations across layers) and that intervals within each layer are sorted by time.

### Output
Returns a tuple of three floats: `(l_precision, l_recall, l_measure)`, representing the L-measure Precision, Recall, and the F-beta measure respectively.

### Valid Call Patterns
```python
# Example inferred from signature
l_precision, l_recall, l_measure = mir_eval.hierarchy.lmeasure(
    ref_intervals, ref_labels, est_intervals, est_labels, frame_size=0.1, beta=1.0
)
```

### LLM Instruction Prompt
- When calling `mir_eval.hierarchy.lmeasure`, ensure that `reference_intervals_hier` and `estimated_intervals_hier` are lists of `np.ndarray` objects.
- Ensure that the number of layers in the reference and estimated hierarchies match.
- Always verify that the total duration of the reference and estimated hierarchies are identical to avoid `ValueError`.

### Prompt Snippet
```text
# Ensure hierarchical inputs are lists of arrays and labels
# Example:
# ref_intervals = [np.array([[0, 10]]), np.array([[0, 5], [5, 10]])]
# ref_labels = [['A'], ['A1', 'A2']]
```

### Common Failure Modes
- `ValueError`: Raised if the input hierarchies have different total time durations or if the `frame_size` is invalid (e.g., `<= 0` or larger than the window).
- `IndexError`: Occurs if the number of labels in a layer does not match the number of intervals in that same layer.
- Inconsistent hierarchy depth: Providing a different number of layers for the reference versus the estimated annotation will cause evaluation errors.

### Fix Code Hint
```python
# Ensure intervals are sorted and durations match before calling
import numpy as np
from mir_eval.util import adjust_intervals

# Example of ensuring interval consistency
ref_intervals = [adjust_intervals(layer) for layer in ref_intervals]
```

## API Test: `python:mir_eval.hierarchy.tmeasure`

### Signature
```python
def tmeasure(reference_intervals_hier, estimated_intervals_hier, transitive=False, window=15.0, frame_size=0.1, beta=1.0)
```
_Source: source/mir_eval/hierarchy.py:466_

_Source doc:_ Compute the tree measures for hierarchical segment annotations.

Parameters
----------
reference_intervals_hier : list of ndarray
    ``reference_intervals_hier[i]`` contains the segment intervals
    (in seconds) for the ``i`` th layer of the annotations.  Layers are
    ordered from top to bottom, so that the last list of intervals should
    be the most specific.
estimated_intervals_hier : list of ndarray
    Like ``reference_intervals_hier`` but for the estimated annotation
transitive : bool
    whether to compute the t-measures using transitivity or not.
window : float > 0
    size of the window (in seconds).  For each query frame q,
    result frames are only counted within q +- window.
frame_size : float > 0
    length (in seconds) of frames.  The frame size cannot be longer than
    the window.
beta : float > 0
    beta parameter for the F-measure.

Returns
-------
t_precision : number [0, 1]
    T-measure Precision
t_recall : number [0, 1]
    T-measure Recall
t_measure : number [0, 1]
    F-beta measure for ``(t_precision, t_recall)``

Raises
------
ValueError
    If either of the input hierarchies are inconsistent

    If the input hierarchies have different time durations

    If ``frame_size > window`` or ``frame_size <= 0``

### Goal
Computes hierarchical tree measures (T-measures) to evaluate the accuracy of multi-layer segment annotations by comparing reference and estimated interval hierarchies.

### Parameters
- `reference_intervals_hier`: A list of `np.ndarray` objects, where each array contains `(N, 2)` interval pairs `[start, end]` in seconds for a specific hierarchical layer.
- `estimated_intervals_hier`: A list of `np.ndarray` objects representing the estimated hierarchical layers, matching the structure of the reference.
- `transitive`, default `False`: A boolean flag determining whether to compute T-measures using transitivity across hierarchical levels.
- `window`, default `15.0`: The temporal tolerance window (in seconds) for matching frames; frames are compared within `q ± window`.
- `frame_size`, default `0.1`: The length of each frame in seconds; must be less than or equal to the `window`.
- `beta`, default `1.0`: The weighting factor for the F-measure calculation.

### Input
- **Data Format:** Hierarchies must be provided as lists of `(N, 2)` NumPy arrays.
- **Preconditions:** All time values must be in seconds. The hierarchies must have consistent total durations. Input arrays should be sorted by time.

### Output
Returns a tuple of three floats: `(t_precision, t_recall, t_measure)`, representing the precision, recall, and F-beta score of the hierarchical segmentation.

### Valid Call Patterns
```python
# Example inferred from signature
t_precision, t_recall, t_measure = mir_eval.hierarchy.tmeasure(
    ref_hier, est_hier, transitive=True, window=10.0, frame_size=0.05, beta=1.0
)
```

### LLM Instruction Prompt
- When calling `mir_eval.hierarchy.tmeasure`, ensure that `reference_intervals_hier` and `estimated_intervals_hier` are lists of `np.ndarray` where each array is `(N, 2)`.
- Always verify that `frame_size <= window` and both are positive floats to avoid `ValueError`.
- Ensure all time-based inputs are converted to seconds before passing to the function.

### Prompt Snippet
```text
from mir_eval.hierarchy import tmeasure
# Ensure ref_hier and est_hier are lists of (N, 2) numpy arrays
t_prec, t_rec, t_f = tmeasure(ref_hier, est_hier, transitive=True)
```

### Common Failure Modes
- **Inconsistent Durations:** Passing hierarchies that do not span the same total time duration will raise a `ValueError`.
- **Invalid Parameters:** Setting `frame_size > window` or providing non-positive values for `window` or `frame_size` will trigger a `ValueError`.
- **Inconsistent Hierarchies:** If the structure of the input lists (e.g., number of layers or interval alignment) is logically inconsistent, the function may raise a `ValueError`.

### Fix Code Hint
```python
# Ensure intervals are sorted and durations match before evaluation
import numpy as np
ref_hier = [np.sort(layer, axis=0) for layer in ref_hier]
# Use mir_eval.util.adjust_intervals if durations differ
```

## API Test: `python:mir_eval.hierarchy.validate_hier_intervals`

### Signature
```python
def validate_hier_intervals(intervals_hier)
```
_Source: source/mir_eval/hierarchy.py:431_

_Source doc:_ Validate a hierarchical segment annotation.

Parameters
----------
intervals_hier : ordered list of segmentations

Raises
------
ValueError
    If any segmentation does not span the full duration of the top-level
    segmentation.

    If any segmentation does not start at 0.

### Goal
Validates that a hierarchical segment annotation structure is consistent, ensuring all levels of the hierarchy are temporally aligned and span the same total duration.

### Parameters
- `intervals_hier`: An ordered list of segmentations, where each element is typically an $N \times 2$ NumPy array representing `[start, end]` intervals.

### Input
- **Data Format:** A list of $N \times 2$ NumPy arrays.
- **Preconditions:** 
    - The input must be an ordered list of segmentations.
    - All time-based inputs must be in seconds.
    - Each segmentation array must be sorted by time.
    - All segmentations must start at 0.0 seconds.
    - All segmentations must span the same total duration as the top-level segmentation.

### Output
Returns `None` if the validation succeeds. If the validation fails, it raises a `ValueError`.

### Valid Call Patterns
```python
# Example inferred from signature
import mir_eval
# Assuming levels is a list of N x 2 numpy arrays
mir_eval.hierarchy.validate_hier_intervals(levels)
```

### LLM Instruction Prompt
- When calling `mir_eval.hierarchy.validate_hier_intervals`, ensure the input is a list of segmentations where each segmentation is an $N \times 2$ NumPy array.
- Verify that all arrays in the list are sorted by time and start at 0.0.
- Ensure that the end time of the final interval in every array matches the end time of the top-level segmentation.

### Prompt Snippet
```text
# Validate hierarchical structure before evaluation
mir_eval.hierarchy.validate_hier_intervals(hierarchical_intervals)
```

### Common Failure Modes
- **ValueError (Start Time):** Occurs if any segmentation in the list does not begin at 0.0 seconds.
- **ValueError (Duration Mismatch):** Occurs if the total duration (the end time of the last interval) of any segmentation does not match the duration of the top-level segmentation.
- **Input Type Error:** Passing a single $N \times 2$ array instead of a list of arrays will cause a failure during iteration.

### Fix Code Hint
```python
# Ensure all segmentations start at 0 and span the same duration
# If validation fails, check your interval generation logic:
import numpy as np
# Example: Ensure the last interval end matches the total duration
for i, level in enumerate(intervals_hier):
    if level[0, 0] != 0:
        raise ValueError(f"Segmentation at index {i} does not start at 0.")
```

## API Test: `python:mir_eval.io.load_delimited`

### Signature
```python
def load_delimited(filename, converters, delimiter='\\s+', comment='#')
```
_Source: source/mir_eval/io.py:32_

_Source doc:_ Load data from an annotation file where columns are delimited.
The number of columns is inferred from the length of the provided converters list.

Examples
--------
>>> # Load in a one-column list of event times (floats)
>>> load_delimited('events.txt', [float])
>>> # Load in a list of labeled events, separated by commas
>>> load_delimited('labeled_events.csv', [float, str], ',')

Parameters
----------
filename : str or `os.Pathlike`
    Path to the annotation file

converters : list of functions
    Each entry in column ``n`` of the file will be cast by the function
    ``converters[n]``.

delimiter : str
    Separator regular expression.
    By default, lines will be split by any amount of whitespace.

comment : str or None
    Comment regular expression.
    Any lines beginning with this string or pattern will be ignored.

    Setting to `None` disables comments.

Returns
-------
columns : tuple of lists
    Each list in this tuple corresponds to values in one of the columns
    in the file.

### Goal
Provides a flexible, low-level utility to parse structured annotation files into Python lists for subsequent conversion into NumPy arrays for MIR evaluation.

### Parameters
- `filename`: The file path to the annotation data (string or `os.Pathlike`).
- `converters`: A list of callable functions (e.g., `float`, `str`) used to cast each column's data; the length of this list determines the expected number of columns.
- `delimiter`, default `'\\s+'`: A regular expression string defining the column separator; defaults to any amount of whitespace.
- `comment`, default `'#'`: A string or regex pattern identifying lines to be ignored as comments; set to `None` to disable comment filtering.

### Input
The function expects a text-based annotation file. Preconditions include ensuring the file structure matches the number of provided `converters`. If the file contains headers or metadata, ensure the `comment` parameter is configured to ignore those lines.

### Output
Returns a `tuple` of `list` objects, where each list contains the parsed and converted values for a specific column in the input file.

### Valid Call Patterns
```python
# Load a simple list of timestamps
mir_eval.io.load_delimited('events.txt', [float])

# Load labeled events with a custom comma delimiter
mir_eval.io.load_delimited('labeled_events.csv', [float, str], delimiter=',')
```

### LLM Instruction Prompt
- When using `mir_eval.io.load_delimited`, always provide a list of converters that matches the number of columns in the target file.
- Use the `delimiter` parameter to specify non-whitespace separators (e.g., `','` for CSV).
- If the file contains header lines, ensure the `comment` parameter is set to match the header prefix (e.g., `'%'` or `'#'`).

### Prompt Snippet
```text
# Example of loading a 3-column file (time, time, label)
intervals, labels = mir_eval.io.load_delimited('data.lab', [float, float, str])
```

### Common Failure Modes
- **Converter Mismatch:** Providing a `converters` list shorter or longer than the actual number of columns in the file will cause parsing errors or index exceptions.
- **Type Casting Errors:** If a converter (e.g., `float`) is applied to a column containing non-numeric data, a `ValueError` will be raised.
- **Delimiter Mismatch:** Using the default whitespace delimiter on a comma-separated file will result in a single column being parsed incorrectly.

### Fix Code Hint
```python
# Ensure the number of converters matches the file structure
# If parsing fails, verify the delimiter and check for unexpected header lines
data = mir_eval.io.load_delimited('file.txt', [float, float], delimiter='\t', comment=None)
```

## API Test: `python:mir_eval.io.load_events`

### Signature
```python
def load_events(filename, delimiter='\\s+', comment='#')
```
_Source: source/mir_eval/io.py:123_

_Source doc:_ Import time-stamp events from an annotation file.  The file should
consist of a single column of numeric values corresponding to the event
times. This is primarily useful for processing events which lack duration,
such as beats or onsets.

Parameters
----------
filename : str or `os.Pathlike`
    Path to the annotation file

delimiter : str
    Separator regular expression.
    By default, lines will be split by any amount of whitespace.

comment : str or None
    Comment regular expression.
    Any lines beginning with this string or pattern will be ignored.

    Setting to `None` disables comments.

Returns
-------
event_times : np.ndarray
    array of event times (float)

### Goal
Loads a single-column text file of numeric timestamps into a 1D NumPy array for use in event-based MIR evaluation tasks like beat or onset detection.

### Parameters
- `filename`: The path to the text file containing the event timestamps.
- `delimiter`, default `'\\s+'`: A regular expression string used to split lines; defaults to any whitespace.
- `comment`, default `'#'`: A regular expression string; lines starting with this pattern are ignored. Set to `None` to disable comment filtering.

### Input
The input must be a text file containing a single column of numeric values representing time in seconds. Precondition: The resulting array should be sorted by time before being passed to evaluation metrics, as most `mir_eval` task modules require chronologically ordered inputs.

### Output
Returns a 1D `np.ndarray` of floats representing the event timestamps in seconds.

### Valid Call Patterns
```python
import mir_eval
# Standard usage for loading beat or onset annotations
event_times = mir_eval.io.load_events('annotations.txt')

# Usage with custom delimiter and comment character
event_times = mir_eval.io.load_events('data.csv', delimiter=',', comment='%')
```

### LLM Instruction Prompt
- Use `mir_eval.io.load_events` when the task requires loading simple timestamp data (e.g., beats, onsets) that lacks duration.
- Ensure the input file contains only one column of numeric values.
- Always verify that the returned array is sorted by time before passing it to `mir_eval` evaluation functions, as many metrics assume sorted input.

### Prompt Snippet
```text
# Load event timestamps from a file
events = mir_eval.io.load_events(filename)
```

### Common Failure Modes
- **Unsorted Data:** Passing unsorted arrays to evaluation functions (e.g., `mir_eval.beat.evaluate`) may lead to incorrect metric calculations; ensure the array is sorted if the source file is not.
- **Multi-column Files:** If the file contains more than one column (e.g., start and end times), this function will fail or produce unexpected results; use `mir_eval.io.load_intervals` instead.
- **Invalid Numeric Formats:** If the file contains non-numeric characters that are not filtered by the `comment` parameter, the function will raise a `ValueError` during array conversion.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# If data is unsorted, ensure it is sorted before evaluation
events = mir_eval.io.load_events('events.txt')
events = np.sort(events)
```

## API Test: `python:mir_eval.io.load_intervals`

### Signature
```python
def load_intervals(filename, delimiter='\\s+', comment='#')
```
_Source: source/mir_eval/io.py:206_

_Source doc:_ Import intervals from an annotation file.  The file should consist of two
columns of numeric values corresponding to start and end time of each
interval.  This is primarily useful for processing events which span a
duration, such as segmentation, chords, or instrument activation.

Parameters
----------
filename : str or `os.Pathlike`
    Path to the annotation file

delimiter : str
    Separator regular expression.
    By default, lines will be split by any amount of whitespace.

comment : str or None
    Comment regular expression.
    Any lines beginning with this string or pattern will be ignored.

    Setting to `None` disables comments.

Returns
-------
intervals : np.ndarray, shape=(n_events, 2)
    array of event start and end times

### Goal
Loads time-interval annotations (start and end times) from a delimited text file into a NumPy array for use in MIR evaluation tasks like segmentation or chord analysis.

### Parameters
- `filename`: The path to the annotation file containing numeric data.
- `delimiter`, default `'\\s+'`: A regular expression string used to split columns in the file; defaults to any whitespace.
- `comment`, default `'#'`: A regular expression string defining lines to be ignored; set to `None` to disable comment filtering.

### Input
The input must be a text file where each row contains two numeric values representing the start and end time of an event in seconds. Preconditions: The file must be formatted such that the two columns are consistently separated by the provided `delimiter`.

### Output
Returns a `np.ndarray` of shape `(n_events, 2)`, where each row contains the `[start, end]` time of an event in seconds.

### Valid Call Patterns
```python
# Loading intervals from a standard space-delimited file
intervals = mir_eval.io.load_intervals('segments.txt')

# Loading intervals with a custom delimiter and no comments
intervals = mir_eval.io.load_intervals('data.csv', delimiter=',', comment=None)
```

### LLM Instruction Prompt
- When calling `mir_eval.io.load_intervals`, ensure the input file contains exactly two columns of numeric data.
- Always treat the returned array as a collection of `[start, end]` pairs in seconds.
- If the file uses a non-standard separator (e.g., tabs or commas), explicitly provide the `delimiter` argument.

### Prompt Snippet
```text
# Example of loading intervals for segmentation evaluation
import mir_eval
intervals = mir_eval.io.load_intervals('path/to/annotation.txt')
```

### Common Failure Modes
- **Malformed Files:** Providing a file with more or fewer than two columns per line will cause parsing errors.
- **Non-numeric Data:** Including headers or non-numeric text without setting the `comment` parameter correctly will raise a `ValueError`.
- **Unsorted Intervals:** While this function loads the data, many downstream `mir_eval` metrics require the returned intervals to be sorted by start time; ensure the input file is ordered or sort the array post-load.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# If the file has a header, use the comment parameter to skip it
intervals = mir_eval.io.load_intervals('data.txt', comment='start_time')

# Ensure intervals are sorted by start time for downstream evaluation
intervals = intervals[np.argsort(intervals[:, 0])]
```

## API Test: `python:mir_eval.io.load_key`

### Signature
```python
def load_key(filename, delimiter='\\s+', comment='#')
```
_Source: source/mir_eval/io.py:497_

_Source doc:_ Load key labels from an annotation file. The file should
consist of two string columns: One denoting the key scale degree
(semitone), and the other denoting the mode (major or minor).  The file
should contain only one row.

Parameters
----------
filename : str or `os.Pathlike`
    Path to the annotation file

delimiter : str
    Separator regular expression.
    By default, lines will be split by any amount of whitespace.

comment : str or None
    Comment regular expression.
    Any lines beginning with this string or pattern will be ignored.

    Setting to `None` disables comments.

Returns
-------
key : str
    Key label, in the form ``'(key) (mode)'``

### Goal
Loads a single key annotation from a text file into a standardized string format for use in music information retrieval evaluation.

### Parameters
- `filename`: The path to the annotation file containing the key information.
- `delimiter`, default `'\\s+'`: A regular expression string used to separate the two columns (scale degree and mode) in the file.
- `comment`, default `'#'`: A regular expression string defining lines to be ignored; set to `None` to disable comment filtering.

### Input
The input must be a text file containing exactly one row with two string columns: the first representing the key scale degree (semitone) and the second representing the mode (major or minor).

### Output
Returns a single `str` representing the key label in the format `'(key) (mode)'`.

### Valid Call Patterns
```python
# Example inferred from signature
key_label = mir_eval.io.load_key('path/to/key_annotation.txt')

# Example with custom delimiter
key_label = mir_eval.io.load_key('path/to/key_annotation.csv', delimiter=',')
```

### LLM Instruction Prompt
- When calling `mir_eval.io.load_key`, ensure the target file contains exactly one row of data.
- The function returns a string; do not expect a NumPy array or list.
- Use the `delimiter` parameter if the annotation file uses a format other than whitespace (e.g., commas or tabs).

### Prompt Snippet
```text
# Load a key annotation file
key = mir_eval.io.load_key(filename='annotation.txt')
```

### Common Failure Modes
- **File Format Errors:** Providing a file with multiple rows will cause the function to process only the first valid row, potentially leading to silent data loss if the file structure is unexpected.
- **Delimiter Mismatch:** If the file uses a specific delimiter (like a comma) and the default `delimiter='\\s+'` is used, the function may fail to parse the columns correctly, resulting in an error or an incorrectly formatted string.
- **Missing File:** Passing a non-existent path will raise an `IOError` or `FileNotFoundError`.

### Fix Code Hint
```python
# Ensure the file exists and is formatted correctly before loading
import os
if os.path.exists(filename):
    key = mir_eval.io.load_key(filename)
else:
    print(f"File {filename} not found.")
```

## API Test: `python:mir_eval.io.load_labeled_events`

### Signature
```python
def load_labeled_events(filename, delimiter='\\s+', comment='#')
```
_Source: source/mir_eval/io.py:162_

_Source doc:_ Import labeled time-stamp events from an annotation file.  The file should
consist of two columns; the first having numeric values corresponding to
the event times and the second having string labels for each event.  This
is primarily useful for processing labeled events which lack duration, such
as beats with metric beat number or onsets with an instrument label.

Parameters
----------
filename : str or `os.Pathlike`
    Path to the annotation file

delimiter : str
    Separator regular expression.
    By default, lines will be split by any amount of whitespace.

comment : str or None
    Comment regular expression.
    Any lines beginning with this string or pattern will be ignored.

    Setting to `None` disables comments.

Returns
-------
event_times : np.ndarray
    array of event times (float)
labels : list of str
    list of labels

### Goal
Loads time-stamped events with associated string labels from a delimited text file into a NumPy array of timestamps and a list of labels.

### Parameters
- `filename`: The path to the annotation file containing the event data.
- `delimiter`, default `'\\s+'`: A regular expression string used to separate columns in the file.
- `comment`, default `'#'`: A regular expression string defining lines to be ignored; set to `None` to disable comment filtering.

### Input
The input file must be a delimited text file with two columns:
1. Column 1: Numeric values representing event times (in seconds).
2. Column 2: String labels for each event.
Precondition: The file must be formatted such that the delimiter correctly separates these two columns.

### Output
Returns a tuple containing:
- `event_times`: A 1D `np.ndarray` of floats representing the event timestamps.
- `labels`: A `list` of strings corresponding to the labels for each event.

### Valid Call Patterns
```python
import mir_eval
# Example inferred from signature
event_times, labels = mir_eval.io.load_labeled_events('annotations.txt')
```

### LLM Instruction Prompt
When using `mir_eval.io.load_labeled_events`, ensure the input file is a two-column text file where the first column is numeric (time in seconds) and the second is a string (label). If the file uses a non-standard separator (e.g., commas), explicitly provide the `delimiter` argument.

### Prompt Snippet
```text
# Load labeled events from a file
event_times, labels = mir_eval.io.load_labeled_events(filename, delimiter='\t', comment=None)
```

### Common Failure Modes
- **File Format Mismatch:** Providing a file that does not have exactly two columns or contains non-numeric data in the first column will raise an error.
- **Delimiter Issues:** If the file uses a specific character (like a comma) but the default whitespace delimiter is used, the parser will fail to split the columns correctly.
- **Sorting:** While this function loads the data, many downstream `mir_eval` metrics require the returned `event_times` to be sorted in ascending order; ensure the input file is sorted or sort the array after loading.

### Fix Code Hint
```python
import numpy as np
# Ensure events are sorted by time if required by downstream metrics
event_times, labels = mir_eval.io.load_labeled_events('data.lab')
sort_idx = np.argsort(event_times)
event_times = event_times[sort_idx]
labels = [labels[i] for i in sort_idx]
```

## API Test: `python:mir_eval.io.load_labeled_intervals`

### Signature
```python
def load_labeled_intervals(filename, delimiter='\\s+', comment='#')
```
_Source: source/mir_eval/io.py:248_

_Source doc:_ Import labeled intervals from an annotation file.  The file should consist
of three columns: Two consisting of numeric values corresponding to start
and end time of each interval and a third corresponding to the label of
each interval.  This is primarily useful for processing events which span a
duration, such as segmentation, chords, or instrument activation.

Parameters
----------
filename : str or `os.Pathlike`
    Path to the annotation file

delimiter : str
    Separator regular expression.
    By default, lines will be split by any amount of whitespace.

comment : str or None
    Comment regular expression.
    Any lines beginning with this string or pattern will be ignored.

    Setting to `None` disables comments.

Returns
-------
intervals : np.ndarray, shape=(n_events, 2)
    array of event start and end time
labels : list of str
    list of labels

### Goal
Loads ground-truth or estimated interval-based annotations (such as chords or segments) from a delimited text file into structured NumPy arrays and label lists for evaluation.

### Parameters
- `filename`: The path to the annotation file containing three columns: start time, end time, and label.
- `delimiter`, default `'\\s+'`: A regular expression string used to split columns; defaults to any whitespace.
- `comment`, default `'#'`: A regular expression string; lines starting with this pattern are ignored. Set to `None` to disable.

### Input
The input file must be a text file with three columns: `[start_time (float), end_time (float), label (str)]`. Time values must be in seconds. Precondition: For most evaluation metrics, the resulting `intervals` array should be sorted by start time.

### Output
Returns a tuple containing:
- `intervals`: A `np.ndarray` of shape `(n_events, 2)` containing the start and end times.
- `labels`: A `list` of strings corresponding to the label for each interval.

### Valid Call Patterns
```python
(intervals, labels) = mir_eval.io.load_labeled_intervals('ref.lab')
```

### LLM Instruction Prompt
When using `mir_eval.io.load_labeled_intervals`, ensure the input file is formatted with three columns (start, end, label). Always assign the output to a tuple `(intervals, labels)`. If the file uses a non-standard separator (e.g., commas), explicitly provide the `delimiter` argument.

### Prompt Snippet
```text
# Load labeled intervals for chord or segment evaluation
intervals, labels = mir_eval.io.load_labeled_intervals(path_to_file)
```

### Common Failure Modes
- **Malformed Files:** Files missing the third column or containing non-numeric values in the first two columns will raise parsing errors.
- **Unsorted Data:** Many downstream `mir_eval` evaluation functions require intervals to be sorted by start time; if the file is unsorted, you must sort the arrays manually after loading.
- **Delimiter Mismatch:** Using the default whitespace delimiter on CSV files will cause the loader to fail to identify columns correctly.

### Fix Code Hint
```python
# If intervals are unsorted, ensure they are ordered before evaluation
intervals, labels = mir_eval.io.load_labeled_intervals('data.lab')
sort_idx = intervals[:, 0].argsort()
intervals = intervals[sort_idx]
labels = [labels[i] for i in sort_idx]
```

## API Test: `python:mir_eval.io.load_patterns`

### Signature
```python
def load_patterns(filename)
```
_Source: source/mir_eval/io.py:331_

_Source doc:_ Load the patterns contained in the filename and puts them into a list
of patterns, each pattern being a list of occurrence, and each
occurrence being a list of (onset, midi) pairs.

The input file must be formatted as described in MIREX 2013:
http://www.music-ir.org/mirex/wiki/2013:Discovery_of_Repeated_Themes_%26_Sections

Parameters
----------
filename : str or `os.Pathlike`
    The input file path containing the patterns of a given piece using the
    MIREX 2013 format.

Returns
-------
pattern_list : list
    The list of patterns, containing all their occurrences,
    using the following format::

        onset_midi = (onset_time, midi_number)
        occurrence = [onset_midi1, ..., onset_midiO]
        pattern = [occurrence1, ..., occurrenceM]
        pattern_list = [pattern1, ..., patternN]

    where ``N`` is the number of patterns, ``M[i]`` is the number of
    occurrences of the ``i`` th pattern, and ``O[j]`` is the number of
    onsets in the ``j``'th occurrence.  E.g.::

        occ1 = [(0.5, 67.0), (1.0, 67.0), (1.5, 67.0), (2.0, 64.0)]
        occ2 = [(4.5, 65.0), (5.0, 65.0), (5.5, 65.0), (6.0, 62.0)]
        pattern1 = [occ1, occ2]

        occ1 = [(10.5, 67.0), (11.0, 67.0), (11.5, 67.0), (12.0, 64.0),
                (12.5, 69.0), (13.0, 69.0), (13.5, 69.0), (14.0, 67.0),
                (14.5, 76.0), (15.0, 76.0), (15.5, 76.0), (16.0, 72.0)]
        occ2 = [(18.5, 67.0), (19.0, 67.0), (19.5, 67.0), (20.0, 62.0),
                (20.5, 69.0), (21.0, 69.0), (21.5, 69.0), (22.0, 67.0),
                (22.5, 77.0), (23.0, 77.0), (23.5, 77.0), (24.0, 74.0)]
        pattern2 = [occ1, occ2]

        pattern_list = [pattern1, pattern2]

### Goal
`mir_eval.io.load_patterns` parses a text file containing repeated musical themes or sections into a structured Python list of occurrences for pattern discovery evaluation.

### Parameters
- `filename`: A string or `os.Pathlike` object representing the path to a text file formatted according to the MIREX 2013 "Discovery of Repeated Themes & Sections" specification.

### Input
The input must be a text file adhering to the MIREX 2013 format. The function expects the file to contain data representing patterns, where each pattern consists of multiple occurrences, and each occurrence is a sequence of (onset time, MIDI note number) pairs.

### Output
Returns a `list` of patterns (`pattern_list`). Each element in the list is a `pattern` (a list of occurrences), where each `occurrence` is a list of `(onset_time, midi_number)` tuples.

### Valid Call Patterns
```python
import mir_eval
patterns = mir_eval.io.load_patterns('path/to/patterns.txt')
```

### LLM Instruction Prompt
- Use `mir_eval.io.load_patterns` only when processing files specifically formatted for the MIREX 2013 "Discovery of Repeated Themes & Sections" task.
- Ensure the input path points to a valid file on the local filesystem.
- The returned object is a nested list structure; do not expect a NumPy array.

### Prompt Snippet
```text
# Load patterns from a MIREX 2013 formatted file
patterns = mir_eval.io.load_patterns(filename)
```

### Common Failure Modes
- **Format Mismatch:** Providing a file that does not strictly follow the MIREX 2013 specification will result in parsing errors or incorrectly structured lists.
- **File Not Found:** Passing a path that does not exist or is inaccessible will raise an `IOError` or `FileNotFoundError`.
- **Data Type Assumptions:** Attempting to perform NumPy operations directly on the returned list without conversion, as the output is a nested list of tuples, not a flat array.

### Fix Code Hint
```python
# Ensure the file exists before loading
import os
if os.path.exists(filename):
    patterns = mir_eval.io.load_patterns(filename)
else:
    print(f"File {filename} not found.")
```

## API Test: `python:mir_eval.io.load_ragged_time_series`

### Signature
```python
def load_ragged_time_series(filename, dtype=float, delimiter='\\s+', header=False, comment='#')
```
_Source: source/mir_eval/io.py:594_

_Source doc:_ Load data from a delimited time series annotation file with
a variable number of columns.

This function assumes that column 0 contains time stamps and
columns 1 through n contain values.
n may be variable from time stamp to time stamp.

Examples
--------
>>> # Load a ragged list of tab-delimited multi-f0 midi notes
>>> times, vals = load_ragged_time_series('multif0.txt', dtype=int,
                                          delimiter='\t')
>>> # Load a raggled list of space delimited multi-f0 values with a header
>>> times, vals = load_ragged_time_series('labeled_events.csv',
                                          header=True)

Parameters
----------
filename : str or `os.Pathlike`
    Path to the annotation file

dtype : function
    Data type to apply to values columns.

delimiter : str
    Separator regular expression.
    By default, lines will be split by any amount of whitespace.

header : bool
    Indicates whether a header row is present or not.
    By default, assumes no header is present.

comment : str or None
    Comment regular expression.
    Any lines beginning with this string or pattern will be ignored.

    Setting to `None` disables comments.

Returns
-------
times : np.ndarray
    array of timestamps (float)
values : list of np.ndarray
    list of arrays of corresponding values

### Goal
Loads time-series data from a delimited text file where each row contains a timestamp followed by a variable number of associated values, commonly used for multi-pitch or multi-source annotations.

### Parameters
- `filename`: Path to the annotation file (string or `os.Pathlike`).
- `dtype`, default `float`: The data type (e.g., `int`, `float`) to cast the values columns into.
- `delimiter`, default `'\\s+'`: A regular expression string used to split columns; defaults to any whitespace.
- `header`, default `False`: Boolean flag; set to `True` if the file contains a header row that should be skipped.
- `comment`, default `'#'`: A string or pattern defining lines to be ignored as comments; set to `None` to disable.

### Input
The input must be a delimited text file. The first column of each row is interpreted as a timestamp (float). Subsequent columns in the row are interpreted as values. Because the number of values can vary per row, the function returns a list of arrays rather than a single 2D matrix.

### Output
Returns a tuple containing:
- `times`: A 1D `np.ndarray` of timestamps (floats).
- `values`: A `list` of `np.ndarray` objects, where each array contains the values associated with the corresponding timestamp.

### Valid Call Patterns
```python
# Load tab-delimited multi-f0 data
times, vals = mir_eval.io.load_ragged_time_series('multif0.txt', dtype=int, delimiter='\t')

# Load space-delimited data with a header
times, vals = mir_eval.io.load_ragged_time_series('labeled_events.csv', header=True)
```

### LLM Instruction Prompt
When calling `mir_eval.io.load_ragged_time_series`, ensure the `delimiter` matches the file format (e.g., `\t` for TSV, `\s+` for space-delimited). If the file contains metadata or headers, set `header=True` or adjust the `comment` parameter to prevent parsing errors.

### Prompt Snippet
```text
import mir_eval
times, values = mir_eval.io.load_ragged_time_series(filename, dtype=float, delimiter='\s+', header=False, comment='#')
```

### Common Failure Modes
- **Delimiter Mismatch:** Providing a space-based delimiter for a tab-separated file will result in incorrect column parsing.
- **Header Inclusion:** Failing to set `header=True` when a header exists will cause the first row of text to be parsed as data, likely raising a `ValueError` during `dtype` conversion.
- **Empty Lines:** Files with trailing empty lines or malformed rows may cause parsing errors depending on the `delimiter` regex.

### Fix Code Hint
```python
# If parsing fails due to unexpected characters, verify the delimiter and comment settings
times, vals = mir_eval.io.load_ragged_time_series('data.txt', delimiter=',', comment=None)
```

## API Test: `python:mir_eval.io.load_tempo`

### Signature
```python
def load_tempo(filename, delimiter='\\s+', comment='#')
```
_Source: source/mir_eval/io.py:542_

_Source doc:_ Load tempo estimates from an annotation file in MIREX format.
The file should consist of three numeric columns: the first two
correspond to tempo estimates (in beats-per-minute), and the third
denotes the relative confidence of the first value compared to the
second (in the range [0, 1]). The file should contain only one row.

Parameters
----------
filename : str or `os.Pathlike`
    Path to the annotation file

delimiter : str
    Separator regular expression.
    By default, lines will be split by any amount of whitespace.

comment : str or None
    Comment regular expression.
    Any lines beginning with this string or pattern will be ignored.

    Setting to `None` disables comments.

Returns
-------
tempi : np.ndarray, non-negative
    The two tempo estimates
weight : float [0, 1]
    The relative importance of ``tempi[0]`` compared to ``tempi[1]``

### Goal
Loads tempo estimates and their associated confidence weight from a single-row MIREX-formatted annotation file for use in tempo evaluation workflows.

### Parameters
- `filename`: The path to the text file containing the tempo data.
- `delimiter`, default `'\\s+'`: A regular expression string used to split columns in the file.
- `comment`, default `'#'`: A regular expression string defining lines to be ignored; set to `None` to disable comment filtering.

### Input
The input must be a text file containing exactly one row with three numeric columns:
1. Two tempo estimates in beats-per-minute (BPM).
2. A confidence value in the range [0, 1] representing the relative importance of the first tempo estimate compared to the second.
Precondition: The file must be formatted such that the columns are parsable by the provided `delimiter`.

### Output
Returns a tuple containing:
- `tempi`: A `np.ndarray` of length 2 containing the two tempo estimates.
- `weight`: A `float` in the range [0, 1] representing the relative importance of the first tempo estimate.

### Valid Call Patterns
```python
import mir_eval
tempi, weight = mir_eval.io.load_tempo('tempo_annotation.txt')
```

### LLM Instruction Prompt
- When calling `mir_eval.io.load_tempo`, ensure the target file contains exactly one row of data.
- The returned `tempi` array is a `numpy.ndarray` and `weight` is a `float`.
- Use this function specifically for loading MIREX-formatted tempo files; do not use it for general time-series data.

### Prompt Snippet
```text
tempi, weight = mir_eval.io.load_tempo(filename)
```

### Common Failure Modes
- **File Format Errors:** Providing a file with multiple rows or incorrect column counts will cause parsing errors.
- **Missing File:** Passing a `filename` that does not exist or is inaccessible will raise an `IOError` or `FileNotFoundError`.
- **Invalid Delimiters:** If the file uses a non-standard separator (e.g., commas) and the default `delimiter` is not overridden, the function will fail to parse the columns correctly.

### Fix Code Hint
```python
# Ensure the file is formatted correctly for MIREX tempo (3 columns, 1 row)
# Example: 120.0 60.0 0.8
import mir_eval
try:
    tempi, weight = mir_eval.io.load_tempo('path/to/tempo.txt')
except Exception as e:
    print(f"Failed to load tempo: {e}")
```

## API Test: `python:mir_eval.io.load_time_series`

### Signature
```python
def load_time_series(filename, delimiter='\\s+', comment='#')
```
_Source: source/mir_eval/io.py:293_

_Source doc:_ Import a time series from an annotation file.  The file should consist of
two columns of numeric values corresponding to the time and value of each
sample of the time series.

Parameters
----------
filename : str or `os.Pathlike`
    Path to the annotation file

delimiter : str
    Separator regular expression.
    By default, lines will be split by any amount of whitespace.

comment : str or None
    Comment regular expression.
    Any lines beginning with this string or pattern will be ignored.

    Setting to `None` disables comments.

Returns
-------
times : np.ndarray
    array of timestamps (float)
values : np.ndarray
    array of corresponding numeric values (float)

### Goal
Loads a two-column time series (time and value) from a delimited text file into NumPy arrays for use in MIR evaluation tasks such as melody or pitch contour analysis.

### Parameters
- `filename`: The path to the annotation file containing the time series data.
- `delimiter`, default `'\\s+'`: A regular expression string used to separate columns in the file; defaults to any whitespace.
- `comment`, default `'#'`: A regular expression string defining lines to be ignored; lines starting with this pattern are skipped. Set to `None` to disable comment filtering.

### Input
The input must be a text file where each row contains two numeric values: a timestamp (in seconds) and a corresponding value (e.g., frequency in Hz). Precondition: The file should be formatted such that columns are consistently separated by the provided `delimiter`.

### Output
Returns a tuple of two `np.ndarray` objects:
- `times`: A 1D array of floats representing the timestamps.
- `values`: A 1D array of floats representing the corresponding numeric values.

### Valid Call Patterns
```python
# Standard usage for melody evaluation
ref_time, ref_freq = mir_eval.io.load_time_series('ref.txt')
est_time, est_freq = mir_eval.io.load_time_series('est.txt')
```

### LLM Instruction Prompt
When calling `mir_eval.io.load_time_series`, ensure the input file contains exactly two columns of numeric data. If the file uses a non-standard separator (e.g., commas), explicitly provide the `delimiter` argument. Always verify that the returned `times` array is sorted chronologically before passing it to evaluation modules like `mir_eval.melody`.

### Prompt Snippet
```text
# Load reference and estimated time series for melody evaluation
ref_time, ref_freq = mir_eval.io.load_time_series(ref_path)
est_time, est_freq = mir_eval.io.load_time_series(est_path)
```

### Common Failure Modes
- **File Format Mismatch:** Providing a file with more or fewer than two columns will cause parsing errors.
- **Unsorted Data:** Many `mir_eval` evaluation functions require time-series data to be sorted by time; if the input file is not sorted, the evaluation results may be incorrect.
- **Delimiter Issues:** Using a default whitespace delimiter on CSV files will fail to parse columns correctly; ensure the `delimiter` parameter matches the file format (e.g., `delimiter=','`).

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure data is sorted by time if the file is not guaranteed to be
times, values = mir_eval.io.load_time_series('data.txt')
sort_idx = np.argsort(times)
times, values = times[sort_idx], values[sort_idx]
```

## API Test: `python:mir_eval.io.load_valued_intervals`

### Signature
```python
def load_valued_intervals(filename, delimiter='\\s+', comment='#')
```
_Source: source/mir_eval/io.py:448_

_Source doc:_ Import valued intervals from an annotation file. The file should
consist of three columns: Two consisting of numeric values corresponding to
start and end time of each interval and a third, also of numeric values,
corresponding to the value of each interval. This is primarily useful for
processing events which span a duration and have a numeric value, such as
piano-roll notes which have an onset, offset, and a pitch value.

Parameters
----------
filename : str or `os.Pathlike`
    Path to the annotation file

delimiter : str
    Separator regular expression.
    By default, lines will be split by any amount of whitespace.

comment : str or None
    Comment regular expression.
    Any lines beginning with this string or pattern will be ignored.

    Setting to `None` disables comments.

Returns
-------
intervals : np.ndarray, shape=(n_events, 2)
    Array of event start and end times
values : np.ndarray, shape=(n_events,)
    Array of values

### Goal
Loads annotation data from a three-column text file into NumPy arrays, representing events that span a duration and possess an associated numeric value, such as piano-roll notes.

### Parameters
- `filename`: The path to the text file containing the annotation data.
- `delimiter`, default `'\\s+'`: A regular expression string used to split columns; defaults to any whitespace.
- `comment`, default `'#'`: A regular expression string defining lines to ignore; lines starting with this pattern are skipped. Set to `None` to disable.

### Input
The input file must be a delimited text file containing exactly three columns of numeric values:
1. Start time (seconds).
2. End time (seconds).
3. Event value (e.g., pitch in Hz or MIDI note number).
Precondition: The file must be formatted such that each row represents a single event.

### Output
Returns a tuple containing:
- `intervals`: A `np.ndarray` of shape `(n_events, 2)` containing the start and end times.
- `values`: A `np.ndarray` of shape `(n_events,)` containing the associated numeric values for each interval.

### Valid Call Patterns
```python
ref_intervals, ref_pitches = mir_eval.io.load_valued_intervals('reference.txt')
```

### LLM Instruction Prompt
When using `mir_eval.io.load_valued_intervals`, ensure the input file contains exactly three columns of numeric data. The function returns two distinct NumPy arrays; ensure your downstream logic (such as `mir_eval.transcription.evaluate`) receives these as separate arguments.

### Prompt Snippet
```text
# Load reference and estimated valued intervals for transcription evaluation
ref_intervals, ref_pitches = mir_eval.io.load_valued_intervals('ref.txt')
est_intervals, est_pitches = mir_eval.io.load_valued_intervals('est.txt')
```

### Common Failure Modes
- **File Format Mismatch:** Providing a file that does not contain exactly three columns will result in an error during array construction.
- **Non-numeric Data:** If the file contains headers or non-numeric labels in the data columns, the loader will fail to parse the file into NumPy arrays.
- **Unsorted Data:** While the loader reads the file as-is, many downstream `mir_eval` metrics require the returned `intervals` array to be sorted by start time; ensure data is pre-sorted or sorted after loading.

### Fix Code Hint
```python
# Ensure intervals are sorted by start time after loading
intervals, values = mir_eval.io.load_valued_intervals('data.txt')
sort_idx = intervals[:, 0].argsort()
intervals = intervals[sort_idx]
values = values[sort_idx]
```

## API Test: `python:mir_eval.io.load_wav`

### Signature
```python
def load_wav(path, mono=True)
```
_Source: source/mir_eval/io.py:409_

_Source doc:_ Load a .wav file as a numpy array using ``scipy.io.wavfile``.

.. warning:: This function is deprecatred in mir_eval 0.8.1
    and will be removed in 0.9.0.
    We recommend using a dedicated audio IO library such as
    `soundfile` instead.

Parameters
----------
path : str or `os.Pathlike`
    Path to a .wav file
mono : bool
    If the provided .wav has more than one channel, it will be
    converted to mono if ``mono=True``. (Default value = True)

Returns
-------
audio_data : np.ndarray
    Array of audio samples, normalized to the range [-1., 1.]
fs : int
    Sampling rate of the audio data

### Goal
Loads a .wav audio file into a normalized NumPy array and returns the sampling rate for use in MIR evaluation workflows.

### Parameters
- `path`: A string or `os.Pathlike` object representing the file system path to the target .wav file.
- `mono`, default `True`: A boolean flag; if `True`, multi-channel audio is downmixed to a single channel.

### Input
The function expects a valid .wav file on disk. No specific pre-processing is required, though the function relies on `scipy.io.wavfile` for the underlying I/O operations.

### Output
Returns a tuple containing:
- `audio_data`: A `np.ndarray` of audio samples, normalized to the range `[-1., 1.]`.
- `fs`: An `int` representing the sampling rate of the audio data in Hz.

### Valid Call Patterns
```python
import mir_eval
audio, fs = mir_eval.io.load_wav('path/to/audio.wav', mono=True)
```

### LLM Instruction Prompt
- Always prefer using `soundfile` or other modern audio I/O libraries instead of this function, as `mir_eval.io.load_wav` is deprecated and scheduled for removal in version 0.9.0.
- When calling, ensure the `path` points to a valid .wav file.
- The function returns two values: the audio array and the sampling rate; ensure both are captured.

### Prompt Snippet
```text
# Deprecated: use soundfile instead
audio, fs = mir_eval.io.load_wav(path, mono=True)
```

### Common Failure Modes
- **Deprecation Warning:** Users may encounter warnings in newer versions of `mir_eval` (0.8.1+), indicating the function will be removed.
- **File Format Errors:** Since it uses `scipy.io.wavfile`, it may fail on non-standard or compressed .wav formats that `scipy` does not support.
- **Path Errors:** Providing a non-existent path or a file that is not a valid .wav will raise an `IOError` or `ValueError`.

### Fix Code Hint
```python
# Recommended replacement using soundfile
import soundfile as sf
audio, fs = sf.read(path, always_2d=True)
if mono and audio.shape[1] > 1:
    audio = audio.mean(axis=1)
```

## API Test: `python:mir_eval.key.evaluate`

### Signature
```python
def evaluate(reference_key, estimated_key, **kwargs)
```
_Source: source/mir_eval/key.py:184_

_Source doc:_ Compute all metrics for the given reference and estimated annotations.

Examples
--------
>>> ref_key = mir_eval.io.load_key('reference.txt')
>>> est_key = mir_eval.io.load_key('estimated.txt')
>>> scores = mir_eval.key.evaluate(ref_key, est_key)

Parameters
----------
reference_key : str
    Reference key string.
estimated_key : str
    Estimated key string.
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of key estimation accuracy metrics by comparing a reference key annotation against an estimated key annotation.

### Parameters
- `reference_key`: A string representing the ground-truth key (e.g., "C:maj").
- `estimated_key`: A string representing the system-predicted key.
- `kwargs`: Optional keyword arguments passed to underlying metric or preprocessing functions.

### Input
- **Data Format:** The function expects key strings, typically loaded via `mir_eval.io.load_key`.
- **Preconditions:** Inputs must be valid key strings. The function assumes the caller has already performed any necessary file I/O or data extraction.

### Output
Returns `dict` — A dictionary where keys are metric names (strings) and values are the corresponding floating-point scores.

### Valid Call Patterns
```python
import mir_eval
ref_key = mir_eval.io.load_key('reference.txt')
est_key = mir_eval.io.load_key('estimated.txt')
scores = mir_eval.key.evaluate(ref_key, est_key)
```

### LLM Instruction Prompt
- Use `mir_eval.key.evaluate` to compute key estimation performance.
- Ensure inputs are strings representing musical keys, typically obtained via `mir_eval.io.load_key`.
- The function returns a dictionary of metrics; access specific scores by their string keys.

### Prompt Snippet
```text
# Example of key evaluation
scores = mir_eval.key.evaluate(ref_key, est_key)
# Accessing a specific metric
accuracy = scores['key_accuracy']
```

### Common Failure Modes
- **Invalid Input:** Passing non-string types or malformed key strings that do not conform to expected key annotation formats.
- **Missing I/O:** Attempting to pass file paths directly instead of the loaded key strings returned by `mir_eval.io.load_key`.

### Fix Code Hint
```python
# Ensure keys are loaded correctly before evaluation
import mir_eval
try:
    ref = mir_eval.io.load_key('ref.txt')
    est = mir_eval.io.load_key('est.txt')
    scores = mir_eval.key.evaluate(ref, est)
except Exception as e:
    print(f"Evaluation failed: {e}")
```

## API Test: `python:mir_eval.key.split_key_string`

### Signature
```python
def split_key_string(key)
```
_Source: source/mir_eval/key.py:92_

_Source doc:_ Split a key string (of the form, e.g. ``'C# major'``), into a tuple of
``(key, mode)`` where ``key`` is is an integer representing the semitone
distance from C.

Parameters
----------
key : str
    String representing a key.

Returns
-------
key : int
    Number of semitones above C.
mode : str
    String representing the mode.

### Goal
Parses a standard musical key string into a numeric semitone representation and a mode string to facilitate programmatic key comparison and evaluation.

### Parameters
- `key`: A string representing a musical key (e.g., `'C# major'`, `'Ab minor'`).

### Input
- **Data Format:** A single string containing the tonic note (optionally with accidentals like `#` or `b`) followed by the mode (e.g., `'major'` or `'minor'`).
- **Preconditions:** The input string must follow standard musical nomenclature recognized by the library's key parsing logic.

### Output
Returns a tuple `(key, mode)`:
- `key` (int): The semitone distance from C (e.g., C=0, C#=1, D=2).
- `mode` (str): The identified mode string (e.g., `'major'`, `'minor'`).

### Valid Call Patterns
```python
import mir_eval
# Example of splitting a key string
key_int, mode_str = mir_eval.key.split_key_string('C# major')
```

### LLM Instruction Prompt
- When calling `mir_eval.key.split_key_string`, ensure the input is a single string representing a key. The function returns a tuple; always unpack this into two variables (an integer for the semitone index and a string for the mode) to avoid type errors in downstream processing.

### Prompt Snippet
```text
# Example usage:
key_val, mode_val = mir_eval.key.split_key_string('Eb minor')
# key_val will be 3, mode_val will be 'minor'
```

### Common Failure Modes
- **Invalid String Format:** Passing a string that does not conform to the expected `[Tonic] [Mode]` format may result in parsing errors or incorrect integer mapping.
- **Case Sensitivity:** While the library handles standard notation, ensure the input string casing matches expected conventions (e.g., `'major'` vs `'Major'`).
- **Unexpected Types:** Passing a non-string type (e.g., `None` or an integer) will raise a `TypeError`.

### Fix Code Hint
```python
# Ensure input is a string and handle potential parsing errors
try:
    key_int, mode_str = mir_eval.key.split_key_string(input_key)
except (ValueError, TypeError):
    # Handle cases where the key string is malformed
    key_int, mode_str = None, None
```

## API Test: `python:mir_eval.key.validate`

### Signature
```python
def validate(reference_key, estimated_key)
```
_Source: source/mir_eval/key.py:77_

_Source doc:_ Check that the input annotations to a metric are valid key strings and
throws helpful errors if not.

Parameters
----------
reference_key : str
    Reference key string.
estimated_key : str
    Estimated key string.

### Goal
Validates that provided reference and estimated key strings conform to the expected format required for key evaluation metrics.

### Parameters
- `reference_key`: A string representing the ground-truth musical key (e.g., "C:maj").
- `estimated_key`: A string representing the system-estimated musical key (e.g., "C:maj").

### Input
- **Data Format:** Both inputs must be strings.
- **Preconditions:** The strings must follow the standard `mir_eval` key syntax (e.g., root note followed by a colon and the quality, such as "C:maj" or "Ab:min").

### Output
Returns `None` if the inputs are valid. If the inputs are invalid, the function raises an exception with a descriptive error message.

### Valid Call Patterns
```python
import mir_eval
# Example inferred from signature
mir_eval.key.validate("C:maj", "C:maj")
```

### LLM Instruction Prompt
- Use `mir_eval.key.validate` before passing key strings to evaluation functions to ensure data integrity.
- Ensure both `reference_key` and `estimated_key` are provided as strings.
- Do not attempt to pass lists or arrays of keys; this function validates individual key pairs.

### Prompt Snippet
```text
# Validate key strings before evaluation
mir_eval.key.validate(ref_key, est_key)
```

### Common Failure Modes
- **Invalid Format:** Passing a string that does not match the expected key syntax (e.g., "Cmaj" instead of "C:maj") will trigger a validation error.
- **Type Mismatch:** Passing non-string types (e.g., `None`, `int`, or `list`) will result in a `TypeError`.
- **Missing Arguments:** Calling the function with fewer than two arguments will raise a `TypeError`.

### Fix Code Hint
```python
# Ensure keys are formatted correctly before validation
try:
    mir_eval.key.validate(ref_key, est_key)
except Exception as e:
    print(f"Invalid key format: {e}")
```

## API Test: `python:mir_eval.key.validate_key`

### Signature
```python
def validate_key(key)
```
_Source: source/mir_eval/key.py:46_

_Source doc:_ Check that a key is well-formatted, e.g. in the form ``'C# major'``.
The Key can be 'X' if it is not possible to categorize the Key and mode
can be 'other' if it can't be categorized as major or minor.

Parameters
----------
key : str
    Key to verify

### Goal
Validates that a given key string conforms to the expected format for MIR key evaluation tasks.

### Parameters
- `key`: A string representing the musical key (e.g., `'C# major'`, `'A minor'`, `'X'`, or `'C other'`).

### Input
- **Data:** A single string.
- **Preconditions:** The string must follow the standard `mir_eval` key syntax. The key can be `'X'` if the key is uncategorizable, and the mode can be `'other'` if it cannot be categorized as major or minor.

### Output
Returns `None` if the key is valid. If the key is improperly formatted, it will raise an exception (typically an `InvalidKeyException` or similar validation error depending on the implementation context).

### Valid Call Patterns
```python
import mir_eval
# Validating a standard key
mir_eval.key.validate_key('C# major')

# Validating an uncategorized key
mir_eval.key.validate_key('X')
```

### LLM Instruction Prompt
- When calling `mir_eval.key.validate_key`, ensure the input is a string.
- Use this function to sanitize or verify key labels before passing them to evaluation functions in the `mir_eval.key` module.
- Do not assume the function returns a boolean; it is designed to validate and raise errors on failure.

### Prompt Snippet
```text
# Example of validating a key label
try:
    mir_eval.key.validate_key(estimated_key)
except Exception as e:
    print(f"Invalid key format: {e}")
```

### Common Failure Modes
- **Type Error:** Passing a non-string object (e.g., `None`, `int`, or `list`) will cause the validation to fail.
- **Format Mismatch:** Providing a string that does not follow the expected `[Root] [Mode]` syntax (e.g., `'Major C#'` instead of `'C# major'`) will trigger a validation error.
- **Case Sensitivity:** Ensure the string matches the expected casing conventions used in the library.

### Fix Code Hint
```python
# Ensure the key is a string and follows the expected format
if not isinstance(key, str):
    key = str(key)
mir_eval.key.validate_key(key)
```

## API Test: `python:mir_eval.key.weighted_score`

### Signature
```python
def weighted_score(reference_key, estimated_key)
```
_Source: source/mir_eval/key.py:116_

_Source doc:_ Compute a heuristic score which is weighted according to the
relationship of the reference and estimated key, as follows:

+------------------------------------------------------+-------+
| Relationship                                         | Score |
+------------------------------------------------------+-------+
| Same key and mode                                    | 1.0   |
+------------------------------------------------------+-------+
| Estimated key is a perfect fifth above reference key | 0.5   |
+------------------------------------------------------+-------+
| Relative major/minor (same key signature)            | 0.3   |
+------------------------------------------------------+-------+
| Parallel major/minor (same key)                      | 0.2   |
+------------------------------------------------------+-------+
| Other                                                | 0.0   |
+------------------------------------------------------+-------+

Examples
--------
>>> ref_key = mir_eval.io.load_key('ref.txt')
>>> est_key = mir_eval.io.load_key('est.txt')
>>> score = mir_eval.key.weighted_score(ref_key, est_key)

Parameters
----------
reference_key : str
    Reference key string.
estimated_key : str
    Estimated key string.

Returns
-------
score : float
    Score representing how closely related the keys are.

### Goal
Computes a heuristic accuracy score for key estimation by assigning weights based on the musical relationship between the reference and estimated keys.

### Parameters
- `reference_key`: A string representing the ground-truth key (e.g., "C:maj").
- `estimated_key`: A string representing the system-estimated key (e.g., "G:maj").

### Input
- **Data Format:** Both inputs must be strings representing keys.
- **Preconditions:** The strings should follow standard key labeling conventions (e.g., "Root:mode"). The function assumes the inputs are valid key strings as typically loaded via `mir_eval.io.load_key`.

### Output
Returns a `float` representing the weighted accuracy score (ranging from 0.0 to 1.0) based on the musical proximity of the estimated key to the reference key.

### Valid Call Patterns
```python
import mir_eval
# Assuming ref.txt and est.txt contain valid key strings
ref_key = mir_eval.io.load_key('ref.txt')
est_key = mir_eval.io.load_key('est.txt')
score = mir_eval.key.weighted_score(ref_key, est_key)
```

### LLM Instruction Prompt
- When calling `mir_eval.key.weighted_score`, ensure both `reference_key` and `estimated_key` are strings.
- Do not attempt to pass raw audio or frequency arrays; this function operates strictly on symbolic key labels.
- Use this function to evaluate key estimation systems where partial credit for musically related keys (e.g., perfect fifths or relative minors) is desired.

### Prompt Snippet
```text
# Example of calculating weighted key accuracy
score = mir_eval.key.weighted_score(reference_key_str, estimated_key_str)
```

### Common Failure Modes
- **Invalid String Format:** Passing strings that do not conform to the expected key labeling syntax may result in unexpected behavior or errors during the internal relationship lookup.
- **Type Mismatch:** Passing non-string types (e.g., lists or integers) will cause the function to fail as it expects string-based key representations.
- **Case Sensitivity:** Ensure key strings are formatted consistently (e.g., "C:maj" vs "c:maj") as per the project's expected input conventions.

### Fix Code Hint
```python
# Ensure keys are loaded correctly before scoring
try:
    score = mir_eval.key.weighted_score(ref_key, est_key)
except Exception as e:
    print(f"Error computing weighted score: {e}")
```

## API Test: `python:mir_eval.melody.constant_hop_timebase`

### Signature
```python
def constant_hop_timebase(hop, end_time)
```
_Source: source/mir_eval/melody.py:195_

_Source doc:_ Generate a time series from 0 to ``end_time`` with times spaced ``hop`` apart

Parameters
----------
hop : float
    Spacing of samples in the time series
end_time : float
    Time series will span ``[0, end_time]``

Returns
-------
times : np.ndarray
    Generated timebase

### Goal
Generates a deterministic, linearly spaced array of timestamps in seconds, commonly used to establish a uniform timebase for melody pitch contour evaluation.

### Parameters
- `hop`: A float representing the temporal resolution (in seconds) between consecutive samples.
- `end_time`: A float representing the total duration (in seconds) of the time series, defining the upper bound of the generated range.

### Input
- The caller must provide two positive floats.
- Preconditions: `hop` must be greater than 0 to ensure a valid step size. `end_time` should be non-negative.

### Output
Returns `np.ndarray` — A 1D NumPy array containing timestamps starting at 0.0 and incrementing by `hop` up to (and potentially including) `end_time`.

### Valid Call Patterns
```python
import mir_eval
# Generate a timebase with 10ms resolution for a 5-second audio clip
times = mir_eval.melody.constant_hop_timebase(0.01, 5.0)
```

### LLM Instruction Prompt
- When calling `mir_eval.melody.constant_hop_timebase`, ensure both `hop` and `end_time` are provided as floats.
- Use this function to create a consistent time axis when your estimated melody frequency data lacks an explicit time array or needs to be resampled to a specific resolution.

### Prompt Snippet
```text
# Example usage for melody evaluation timebase
timebase = mir_eval.melody.constant_hop_timebase(hop=0.01, end_time=duration)
```

### Common Failure Modes
- **Zero or Negative Hop:** Providing a `hop` value of 0 or less will result in an empty array or an error during subsequent processing, as the step size is invalid.
- **Type Mismatch:** Passing strings or non-numeric types for `hop` or `end_time` will raise a `TypeError`.
- **Incompatibility:** Using this timebase with frequency arrays of a different length will cause index errors in downstream evaluation functions like `mir_eval.melody.evaluate`.

### Fix Code Hint
```python
# Ensure inputs are numeric and positive
hop = float(hop_value)
end_time = float(end_time_value)
if hop <= 0:
    raise ValueError("Hop size must be greater than zero.")
times = mir_eval.melody.constant_hop_timebase(hop, end_time)
```

## API Test: `python:mir_eval.melody.evaluate`

### Signature
```python
def evaluate(ref_time, ref_freq, est_time, est_freq, est_voicing=None, ref_reward=None, **kwargs)
```
_Source: source/mir_eval/melody.py:770_

_Source doc:_ Evaluate two melody (predominant f0) transcriptions, where the first is
treated as the reference (ground truth) and the second as the estimate to
be evaluated (prediction).

Examples
--------
>>> ref_time, ref_freq = mir_eval.io.load_time_series('ref.txt')
>>> est_time, est_freq = mir_eval.io.load_time_series('est.txt')
>>> scores = mir_eval.melody.evaluate(ref_time, ref_freq,
...                                   est_time, est_freq)

Parameters
----------
ref_time : np.ndarray
    Time of each reference frequency value

ref_freq : np.ndarray
    Array of reference frequency values

est_time : np.ndarray
    Time of each estimated frequency value

est_freq : np.ndarray
    Array of estimated frequency values

est_voicing : np.ndarray
    Estimate voicing confidence.
    Default None, which means the voicing is inferred from est_freq:

      - frames with frequency <= 0.0 are considered "unvoiced"
      - frames with frequency > 0.0 are considered "voiced"

ref_reward : np.ndarray
    Reference pitch estimation reward.
    Default None, which means all frames are weighted equally.

**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

References
----------
.. [#] J. Salamon, E. Gomez, D. P. W. Ellis and G. Richard, "Melody
    Extraction from Polyphonic Music Signals: Approaches, Applications
    and Challenges", IEEE Signal Processing Magazine, 31(2):118-134,
    Mar. 2014.

.. [#] G. E. Poliner, D. P. W. Ellis, A. F. Ehmann, E. Gomez, S.
    Streich, and B. Ong. "Melody transcription from music audio:
    Approaches and evaluation", IEEE Transactions on Audio, Speech, and
    Language Processing, 15(4):1247-1256, 2007.

.. [#] R. Bittner and J. Bosch, "Generalized Metrics for Single-F0
    Estimation Evaluation", International Society for Music Information
    Retrieval Conference (ISMIR), 2019.

### Goal
Computes a comprehensive suite of melody extraction performance metrics by comparing a ground-truth predominant F0 contour against an estimated F0 contour.

### Parameters
- `ref_time`: 1D NumPy array of timestamps (in seconds) corresponding to the reference frequency values.
- `ref_freq`: 1D NumPy array of reference fundamental frequency values (in Hz).
- `est_time`: 1D NumPy array of timestamps (in seconds) corresponding to the estimated frequency values.
- `est_freq`: 1D NumPy array of estimated fundamental frequency values (in Hz).
- `est_voicing`, default `None`: Optional 1D NumPy array representing voicing confidence; if `None`, voicing is inferred from `est_freq` (<= 0.0 is unvoiced, > 0.0 is voiced).
- `ref_reward`, default `None`: Optional 1D NumPy array of weights for reference frames; if `None`, all frames are weighted equally.
- `kwargs`: Additional keyword arguments passed to underlying metric or preprocessing functions.

### Input
Inputs must be NumPy arrays. Time values must be in seconds. Frequency values are typically in Hz. Precondition: Reference and estimated arrays should be sorted by time. Use `mir_eval.io.load_time_series` to load data from standard text files.

### Output
Returns a `dict` where keys are metric names (strings) and values are the corresponding scalar scores (floats).

### Valid Call Patterns
```python
ref_time, ref_freq = mir_eval.io.load_time_series('ref.txt')
est_time, est_freq = mir_eval.io.load_time_series('est.txt')
scores = mir_eval.melody.evaluate(ref_time, ref_freq, est_time, est_freq)
```

### LLM Instruction Prompt
- Always ensure `ref_time` and `est_time` are provided as 1D NumPy arrays in seconds.
- If voicing information is not explicitly provided, rely on the default inference logic (frequency <= 0.0 is unvoiced).
- Ensure the reference and estimate arrays are sorted by time before passing them to the function.

### Prompt Snippet
```text
# Example of melody evaluation
scores = mir_eval.melody.evaluate(ref_time, ref_freq, est_time, est_freq)
```

### Common Failure Modes
- Mismatched array lengths between time and frequency inputs.
- Providing time values in samples instead of seconds.
- Unsorted input arrays, which may lead to incorrect metric computation.
- Providing frequency values in MIDI or cents when the function expects Hz.

### Fix Code Hint
```python
# Ensure arrays are sorted by time
idx = np.argsort(ref_time)
ref_time, ref_freq = ref_time[idx], ref_freq[idx]
```

## API Test: `python:mir_eval.melody.freq_to_voicing`

### Signature
```python
def freq_to_voicing(frequencies, voicing=None)
```
_Source: source/mir_eval/melody.py:157_

_Source doc:_ Convert from an array of frequency values to frequency array +
voice/unvoiced array

Parameters
----------
frequencies : np.ndarray
    Array of frequencies.  A frequency <= 0 indicates "unvoiced".

voicing : np.ndarray
    Array of voicing values.
    (Default value = None)
    Default None, which means the voicing is inferred from `frequencies`:

       - frames with frequency <= 0.0 are considered "unvoiced"
       - frames with frequency > 0.0 are considered "voiced"

    If specified, `voicing` is used as the voicing array, but
    frequencies with value 0 are forced to have 0 voicing.

       - Voicing inferred by negative frequency values is ignored.

Returns
-------
frequencies : np.ndarray
    Array of frequencies, all >= 0.
voiced : np.ndarray
    Array of voicings between 0 and 1, same length as frequencies,
    which indicates voiced or unvoiced

### Goal
Converts a raw frequency array into a standardized format consisting of a non-negative frequency array and a corresponding binary voicing mask for melody evaluation.

### Parameters
- `frequencies`: A 1D `np.ndarray` of fundamental frequency values in Hertz. Values <= 0 are treated as unvoiced.
- `voicing`, default `None`: An optional 1D `np.ndarray` of voicing values. If provided, it must match the length of `frequencies`.

### Input
- **Data:** `np.ndarray` of floats.
- **Preconditions:** The input `frequencies` array should represent time-series data. If `voicing` is provided, it is used to determine the voiced/unvoiced state, but any index where `frequencies` is 0 will be forced to 0 in the output voicing array.

### Output
Returns a tuple of two `np.ndarray` objects:
1. `frequencies`: The input frequencies, with all negative values converted to 0.0.
2. `voiced`: A binary array (0 or 1) of the same length as the input, indicating the voicing state for each frame.

### Valid Call Patterns
```python
# Example inferred from signature
import numpy as np
import mir_eval

frequencies = np.array([440.0, 0.0, 220.0, -1.0])
freqs, voiced = mir_eval.melody.freq_to_voicing(frequencies)
```

### LLM Instruction Prompt
- When calling `mir_eval.melody.freq_to_voicing`, ensure the input `frequencies` is a 1D NumPy array.
- If you have a separate voicing array, pass it as the second argument; otherwise, leave it as `None` to allow the function to infer voicing from the frequency values.
- Always expect a tuple return value containing the cleaned frequency array and the binary voicing array.

### Prompt Snippet
```text
# Convert raw frequency data to standard melody evaluation format
freqs, voiced = mir_eval.melody.freq_to_voicing(raw_frequencies, voicing=optional_voicing_mask)
```

### Common Failure Modes
- **Shape Mismatch:** Providing a `voicing` array that does not have the same length as the `frequencies` array will raise a `ValueError`.
- **Invalid Input Type:** Passing lists instead of `np.ndarray` may cause errors in downstream processing; ensure inputs are cast to NumPy arrays first.
- **Implicit Voicing Confusion:** Users may forget that providing a `voicing` array overrides the inference from `frequencies`, except for the hard-coded constraint that `frequencies == 0` forces `voicing == 0`.

### Fix Code Hint
```python
# Ensure inputs are numpy arrays and handle potential shape mismatches
import numpy as np
frequencies = np.asarray(frequencies)
if voicing is not None:
    voicing = np.asarray(voicing)
    assert frequencies.shape == voicing.shape, "Frequencies and voicing must have the same shape."
freqs, voiced = mir_eval.melody.freq_to_voicing(frequencies, voicing)
```

## API Test: `python:mir_eval.melody.hz2cents`

### Signature
```python
def hz2cents(freq_hz, base_frequency=10.0)
```
_Source: source/mir_eval/melody.py:138_

_Source doc:_ Convert an array of frequency values in Hz to cents.
0 values are left in place.

Parameters
----------
freq_hz : np.ndarray
    Array of frequencies in Hz.
base_frequency : float
    Base frequency for conversion.
    (Default value = 10.0)

### Goal
Converts an array of fundamental frequency (F0) values from Hertz to a cent-based scale relative to a specified base frequency for melody evaluation tasks.

### Parameters
- `freq_hz`: A `np.ndarray` containing frequency values in Hz.
- `base_frequency`, default `10.0`: A float representing the reference frequency used as the zero-point for the cent conversion.

### Input
- **Data:** A `np.ndarray` of frequency values.
- **Preconditions:** The input array must be a NumPy array. Values of `0` (typically representing unvoiced segments in melody transcription) are preserved as `0` in the output.

### Output
Returns an `np.ndarray` of the same shape as `freq_hz`, containing the converted values in cents.

### Valid Call Patterns
```python
import numpy as np
import mir_eval

# Example: Converting a frequency array to cents
freqs = np.array([0.0, 440.0, 880.0])
cents = mir_eval.melody.hz2cents(freqs, base_frequency=10.0)
```

### LLM Instruction Prompt
- When calling `mir_eval.melody.hz2cents`, ensure the input `freq_hz` is a `numpy.ndarray`.
- Do not attempt to convert scalar values; the function expects an array-like structure.
- Remember that `0` values are treated as special markers for unvoiced audio and will remain `0` in the output.

### Prompt Snippet
```text
# Convert frequency array to cents using mir_eval
cents_array = mir_eval.melody.hz2cents(freq_hz_array, base_frequency=10.0)
```

### Common Failure Modes
- **Type Error:** Passing a Python list instead of a `np.ndarray` may cause issues if the underlying implementation expects NumPy-specific array operations.
- **Unvoiced Handling:** Users may mistakenly assume `0` Hz will be converted to a logarithmic value; the function explicitly leaves `0` values in place to maintain the distinction between voiced and unvoiced frames.

### Fix Code Hint
```python
import numpy as np
# Ensure input is a numpy array before conversion
freq_array = np.array(my_frequency_list)
cents = mir_eval.melody.hz2cents(freq_array)
```

## API Test: `python:mir_eval.melody.overall_accuracy`

### Signature
```python
def overall_accuracy(ref_voicing, ref_cent, est_voicing, est_cent, cent_tolerance=50)
```
_Source: source/mir_eval/melody.py:691_

_Source doc:_ Compute the overall accuracy given two pitch (frequency) sequences
in cents and matching voicing indicator sequences. The first pitch and
voicing arrays are treated as the reference (truth), and the second two
as the estimate (prediction).  All 4 sequences must be of the same length.

Examples
--------
>>> ref_time, ref_freq = mir_eval.io.load_time_series('ref.txt')
>>> est_time, est_freq = mir_eval.io.load_time_series('est.txt')
>>> (ref_v, ref_c,
...  est_v, est_c) = mir_eval.melody.to_cent_voicing(ref_time,
...                                                  ref_freq,
...                                                  est_time,
...                                                  est_freq)
>>> overall_accuracy = mir_eval.melody.overall_accuracy(ref_v, ref_c,
...                                                     est_v, est_c)

Parameters
----------
ref_voicing : np.ndarray
    Reference voicing array. When this array is non-binary, it is treated
    as a 'reference reward', as in (Bittner & Bosch, 2019)
ref_cent : np.ndarray
    Reference pitch sequence in cents
est_voicing : np.ndarray
    Estimated voicing array
est_cent : np.ndarray
    Estimate pitch sequence in cents
cent_tolerance : float
    Maximum absolute deviation in cents for a frequency value to be
    considered correct
    (Default value = 50)

Returns
-------
overall_accuracy : float
    Overall accuracy, the total fraction of correctly estimates frames,
    where provides a correct frequency values (within cent_tolerance).

### Goal
Computes the overall accuracy of a melody estimation by calculating the fraction of frames where the estimated pitch and voicing state correctly match the reference ground truth within a specified cent tolerance.

### Parameters
- `ref_voicing`: `np.ndarray` representing the ground truth voicing state; non-binary values are interpreted as 'reference rewards'.
- `ref_cent`: `np.ndarray` containing the ground truth pitch sequence expressed in cents.
- `est_voicing`: `np.ndarray` representing the estimated voicing state.
- `est_cent`: `np.ndarray` containing the estimated pitch sequence expressed in cents.
- `cent_tolerance`, default `50`: `float` defining the maximum absolute deviation in cents allowed for a pitch estimate to be considered correct.

### Input
- **Data:** Four 1D `np.ndarray` objects of identical length.
- **Preconditions:** Inputs must be pre-processed into cent and voicing arrays (typically using `mir_eval.melody.to_cent_voicing`). All arrays must be aligned frame-by-frame.

### Output
- `overall_accuracy`: A `float` representing the proportion of frames correctly estimated, ranging from 0.0 to 1.0.

### Valid Call Patterns
```python
# Standard usage after conversion
overall_accuracy = mir_eval.melody.overall_accuracy(ref_v, ref_c, est_v, est_c)

# Usage with custom tolerance
overall_accuracy = mir_eval.melody.overall_accuracy(ref_v, ref_c, est_v, est_c, cent_tolerance=25.0)
```

### LLM Instruction Prompt
- Always ensure the four input arrays (`ref_voicing`, `ref_cent`, `est_voicing`, `est_cent`) are of the same length before calling this function.
- Use `mir_eval.melody.to_cent_voicing` to prepare raw time-series data into the required cent/voicing format before evaluation.

### Prompt Snippet
```text
# Ensure inputs are aligned and converted to cent/voicing format
ref_v, ref_c, est_v, est_c = mir_eval.melody.to_cent_voicing(ref_time, ref_freq, est_time, est_freq)
accuracy = mir_eval.melody.overall_accuracy(ref_v, ref_c, est_v, est_c)
```

### Common Failure Modes
- **Length Mismatch:** Passing arrays of different lengths will raise a `ValueError`.
- **Unconverted Data:** Passing raw frequency (Hz) instead of cents will result in mathematically incorrect accuracy scores.
- **Non-aligned Data:** If the reference and estimate time series are not aligned to the same time grid, the accuracy score will be invalid.

### Fix Code Hint
```python
# If lengths differ, ensure they are resampled or aligned to the same time grid
# before calling to_cent_voicing.
if len(ref_v) != len(est_v):
    raise ValueError("Reference and estimate arrays must have the same length.")
```

## API Test: `python:mir_eval.melody.raw_chroma_accuracy`

### Signature
```python
def raw_chroma_accuracy(ref_voicing, ref_cent, est_voicing, est_cent, cent_tolerance=50)
```
_Source: source/mir_eval/melody.py:622_

_Source doc:_ Compute the raw chroma accuracy given two pitch (frequency) sequences
in cents and matching voicing indicator sequences. The first pitch and
voicing arrays are treated as the reference (truth), and the second two as
the estimate (prediction).  All 4 sequences must be of the same length.

Examples
--------
>>> ref_time, ref_freq = mir_eval.io.load_time_series('ref.txt')
>>> est_time, est_freq = mir_eval.io.load_time_series('est.txt')
>>> (ref_v, ref_c,
...  est_v, est_c) = mir_eval.melody.to_cent_voicing(ref_time,
...                                                  ref_freq,
...                                                  est_time,
...                                                  est_freq)
>>> raw_chroma = mir_eval.melody.raw_chroma_accuracy(ref_v, ref_c,
...                                                  est_v, est_c)

Parameters
----------
ref_voicing : np.ndarray
    Reference voicing array. When this array is non-binary, it is treated
    as a 'reference reward', as in (Bittner & Bosch, 2019)
ref_cent : np.ndarray
    Reference pitch sequence in cents
est_voicing : np.ndarray
    Estimated voicing array
est_cent : np.ndarray
    Estimate pitch sequence in cents
cent_tolerance : float
    Maximum absolute deviation in cents for a frequency value to be
    considered correct
    (Default value = 50)

Returns
-------
raw_chroma : float
    Raw chroma accuracy, the fraction of voiced frames in ref_cent for
    which est_cent provides a correct frequency values (within
    cent_tolerance cents), ignoring octave errors

### Goal
Computes the raw chroma accuracy for melody estimation by evaluating the fraction of voiced reference frames where the estimated pitch matches the reference pitch within a specified tolerance, while ignoring octave errors.

### Parameters
- `ref_voicing`: `np.ndarray` representing the reference voicing state; non-binary values are treated as 'reference rewards'.
- `ref_cent`: `np.ndarray` containing the reference pitch sequence in cents.
- `est_voicing`: `np.ndarray` containing the estimated voicing state.
- `est_cent`: `np.ndarray` containing the estimated pitch sequence in cents.
- `cent_tolerance`, default `50`: `float` defining the maximum absolute deviation in cents allowed for a frequency match.

### Input
- All four input arrays must be of the same length.
- Inputs should be prepared using `mir_eval.melody.to_cent_voicing` to ensure time-alignment and conversion to the required cent/voicing format.
- Precondition: The sequences must represent time-aligned pitch and voicing data.

### Output
Returns a `float` representing the raw chroma accuracy score (the proportion of correctly estimated voiced frames).

### Valid Call Patterns
```python
raw_chroma = mir_eval.melody.raw_chroma_accuracy(ref_v, ref_c, est_v, est_c)
raw_chroma = mir_eval.melody.raw_chroma_accuracy(ref_v, ref_c, est_v, est_c, cent_tolerance=25.0)
```

### LLM Instruction Prompt
- Always ensure that `ref_voicing`, `ref_cent`, `est_voicing`, and `est_cent` are passed as `np.ndarray` objects of identical length.
- Use `mir_eval.melody.to_cent_voicing` to preprocess raw time-series data before calling this function.
- Remember that this metric specifically ignores octave errors, focusing only on chroma accuracy.

### Prompt Snippet
```text
# Preprocess data first
ref_v, ref_c, est_v, est_c = mir_eval.melody.to_cent_voicing(ref_time, ref_freq, est_time, est_freq)
# Compute accuracy
score = mir_eval.melody.raw_chroma_accuracy(ref_v, ref_c, est_v, est_c)
```

### Common Failure Modes
- Passing arrays of unequal length, which will cause an error.
- Providing frequency data in Hz instead of cents (must use `to_cent_voicing` or manual conversion).
- Misinterpreting the output as a standard pitch accuracy score; this metric specifically ignores octave errors.

### Fix Code Hint
```python
# Ensure inputs are aligned and converted to cents
import numpy as np
import mir_eval
# If arrays are not the same length, they must be resampled or truncated to match
assert len(ref_v) == len(est_v) == len(ref_c) == len(est_c)
score = mir_eval.melody.raw_chroma_accuracy(ref_v, ref_c, est_v, est_c)
```

## API Test: `python:mir_eval.melody.raw_pitch_accuracy`

### Signature
```python
def raw_pitch_accuracy(ref_voicing, ref_cent, est_voicing, est_cent, cent_tolerance=50)
```
_Source: source/mir_eval/melody.py:554_

_Source doc:_ Compute the raw pitch accuracy given two pitch (frequency) sequences in
cents and matching voicing indicator sequences. The first pitch and voicing
arrays are treated as the reference (truth), and the second two as the
estimate (prediction).  All 4 sequences must be of the same length.

Examples
--------
>>> ref_time, ref_freq = mir_eval.io.load_time_series('ref.txt')
>>> est_time, est_freq = mir_eval.io.load_time_series('est.txt')
>>> (ref_v, ref_c,
...  est_v, est_c) = mir_eval.melody.to_cent_voicing(ref_time,
...                                                  ref_freq,
...                                                  est_time,
...                                                  est_freq)
>>> raw_pitch = mir_eval.melody.raw_pitch_accuracy(ref_v, ref_c,
...                                                est_v, est_c)

Parameters
----------
ref_voicing : np.ndarray
    Reference voicing array. When this array is non-binary, it is treated
    as a 'reference reward', as in (Bittner & Bosch, 2019)
ref_cent : np.ndarray
    Reference pitch sequence in cents
est_voicing : np.ndarray
    Estimated voicing array
est_cent : np.ndarray
    Estimate pitch sequence in cents
cent_tolerance : float
    Maximum absolute deviation in cents for a frequency value to be
    considered correct
    (Default value = 50)

Returns
-------
raw_pitch : float
    Raw pitch accuracy, the fraction of voiced frames in ref_cent for
    which est_cent provides a correct frequency values
    (within cent_tolerance cents).

### Goal
Computes the raw pitch accuracy metric for melody estimation by calculating the proportion of voiced reference frames where the estimated pitch is within a specified cent tolerance.

### Parameters
- `ref_voicing`: `np.ndarray` representing the ground-truth voicing state; non-binary values are interpreted as 'reference rewards'.
- `ref_cent`: `np.ndarray` containing the ground-truth pitch sequence expressed in cents.
- `est_voicing`: `np.ndarray` representing the estimated voicing state.
- `est_cent`: `np.ndarray` containing the estimated pitch sequence expressed in cents.
- `cent_tolerance`, default `50`: `float` defining the maximum absolute deviation in cents allowed for a pitch estimate to be considered correct.

### Input
- All four input arrays must be of the same length.
- Inputs should be prepared using `mir_eval.melody.to_cent_voicing` to ensure time-series alignment and proper unit conversion (Hz to cents) before evaluation.

### Output
Returns `float` representing the raw pitch accuracy, defined as the fraction of voiced frames in the reference sequence for which the estimate provides a correct frequency value within the defined `cent_tolerance`.

### Valid Call Patterns
```python
raw_pitch = mir_eval.melody.raw_pitch_accuracy(ref_v, ref_c, est_v, est_c)
raw_pitch = mir_eval.melody.raw_pitch_accuracy(ref_v, ref_c, est_v, est_c, cent_tolerance=25.0)
```

### LLM Instruction Prompt
- Always ensure that the four input arrays (`ref_voicing`, `ref_cent`, `est_voicing`, `est_cent`) are of identical length before calling this function.
- Use `mir_eval.melody.to_cent_voicing` to convert raw time-series data into the required cent/voicing format prior to calling this metric.

### Prompt Snippet
```text
# Ensure inputs are aligned and converted to cent/voicing format
ref_v, ref_c, est_v, est_c = mir_eval.melody.to_cent_voicing(ref_time, ref_freq, est_time, est_freq)
# Compute raw pitch accuracy
accuracy = mir_eval.melody.raw_pitch_accuracy(ref_v, ref_c, est_v, est_c, cent_tolerance=50)
```

### Common Failure Modes
- **Length Mismatch:** Passing arrays of different lengths will result in a runtime error.
- **Unit Mismatch:** Passing frequencies in Hz instead of cents will lead to incorrect accuracy scores; ensure `to_cent_voicing` is used.
- **Unsorted Data:** If the input time series are not sorted by time, the resulting alignment from `to_cent_voicing` may be invalid.

### Fix Code Hint
```python
# If arrays are not the same length, verify the source time series alignment
assert len(ref_voicing) == len(est_voicing) == len(ref_cent) == len(est_cent)
```

## API Test: `python:mir_eval.melody.resample_melody_series`

### Signature
```python
def resample_melody_series(times, frequencies, voicing, times_new, kind='linear')
```
_Source: source/mir_eval/melody.py:220_

_Source doc:_ Resamples frequency and voicing time series to a new timescale. Maintains
any zero ("unvoiced") values in frequencies.

If ``times`` and ``times_new`` are equivalent, no resampling will be
performed.

Parameters
----------
times : np.ndarray
    Times of each frequency value
frequencies : np.ndarray
    Array of frequency values, >= 0
voicing : np.ndarray
    Array which indicates voiced or unvoiced. This array may be binary
    or have continuous values between 0 and 1.
times_new : np.ndarray
    Times to resample frequency and voicing sequences to
kind : str
    kind parameter to pass to scipy.interpolate.interp1d.
    (Default value = 'linear')

Returns
-------
frequencies_resampled : np.ndarray
    Frequency array resampled to new timebase
voicing_resampled : np.ndarray
    Voicing array resampled to new timebase

### Goal
Resamples melody frequency and voicing time series to a target timebase to ensure consistency across different annotation sources or evaluation requirements.

### Parameters
- `times`: A 1D `np.ndarray` containing the timestamps (in seconds) corresponding to the frequency and voicing observations.
- `frequencies`: A 1D `np.ndarray` of fundamental frequency values (in Hz or cents), where values $\ge 0$.
- `voicing`: A 1D `np.ndarray` indicating the voicing state; values should be in the range $[0, 1]$ (binary or continuous).
- `times_new`: A 1D `np.ndarray` representing the target timestamps to which the series should be resampled.
- `kind`, default `'linear'`: A string specifying the interpolation method passed to `scipy.interpolate.interp1d`.

### Input
- **Data:** Requires three 1D `np.ndarray` inputs of equal length for the original series and a 1D `np.ndarray` for the target timebase.
- **Preconditions:** All time-based inputs must be in seconds. Frequency values must be non-negative. The input arrays should be sorted by time.

### Output
Returns a tuple of two `np.ndarray` objects:
1. `frequencies_resampled`: The frequency values interpolated to the `times_new` timebase.
2. `voicing_resampled`: The voicing values interpolated to the `times_new` timebase.

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example usage (inferred from signature)
freq_resampled, voice_resampled = mir_eval.melody.resample_melody_series(
    times, frequencies, voicing, times_new, kind='linear'
)
```

### LLM Instruction Prompt
- When calling `mir_eval.melody.resample_melody_series`, ensure that `times` and `times_new` are provided as 1D NumPy arrays in seconds.
- Always verify that `frequencies` contains non-negative values and `voicing` contains values between 0 and 1.
- If the interpolation method is not specified, the default `'linear'` is used.

### Prompt Snippet
```text
mir_eval.melody.resample_melody_series(times, frequencies, voicing, times_new, kind='linear')
```

### Common Failure Modes
- **Shape Mismatch:** Providing `times`, `frequencies`, and `voicing` arrays that do not have the same length will cause an error.
- **Negative Frequencies:** Passing negative values in the `frequencies` array violates the input constraints.
- **Unsorted Input:** If the input `times` array is not monotonically increasing, interpolation results may be invalid or raise errors.

### Fix Code Hint
```python
# Ensure inputs are sorted by time before resampling
idx = np.argsort(times)
times_sorted = times[idx]
frequencies_sorted = frequencies[idx]
voicing_sorted = voicing[idx]

freq_resampled, voice_resampled = mir_eval.melody.resample_melody_series(
    times_sorted, frequencies_sorted, voicing_sorted, times_new
)
```

## API Test: `python:mir_eval.melody.to_cent_voicing`

### Signature
```python
def to_cent_voicing(ref_time, ref_freq, est_time, est_freq, est_voicing=None, ref_reward=None, base_frequency=10.0, hop=None, kind='linear')
```
_Source: source/mir_eval/melody.py:316_

_Source doc:_ Convert reference and estimated time/frequency (Hz) annotations to sampled
frequency (cent)/voicing arrays.

A zero frequency indicates "unvoiced".

If est_voicing is not provided, a negative frequency indicates:
    "Predicted as unvoiced, but if it's voiced,
    this is the frequency estimate".

If it is provided, negative frequency values are ignored, and the voicing
from est_voicing is directly used.

Parameters
----------
ref_time : np.ndarray
    Time of each reference frequency value

ref_freq : np.ndarray
    Array of reference frequency values

est_time : np.ndarray
    Time of each estimated frequency value

est_freq : np.ndarray
    Array of estimated frequency values

est_voicing : np.ndarray
    Estimate voicing confidence.
    Default None, which means the voicing is inferred from est_freq:

      - frames with frequency <= 0.0 are considered "unvoiced"
      - frames with frequency > 0.0 are considered "voiced"

ref_reward : np.ndarray
    Reference voicing reward.
    Default None, which means all frames are weighted equally.

base_frequency : float
    Base frequency in Hz for conversion to cents
    (Default value = 10.)

hop : float
    Hop size, in seconds, to resample,
    default None which means use ref_time

kind : str
    kind parameter to pass to scipy.interpolate.interp1d.
    (Default value = 'linear')

Returns
-------
ref_voicing : np.ndarray
    Resampled reference voicing array
ref_cent : np.ndarray
    Resampled reference frequency (cent) array
est_voicing : np.ndarray
    Resampled estimated voicing array
est_cent : np.ndarray
    Resampled estimated frequency (cent) array

### Goal
Standardizes melody evaluation inputs by resampling reference and estimated frequency contours into a common time grid and converting frequency values from Hz to cents.

### Parameters
- `ref_time`: 1D `np.ndarray` of timestamps (seconds) corresponding to `ref_freq`.
- `ref_freq`: 1D `np.ndarray` of fundamental frequencies (Hz) for the reference.
- `est_time`: 1D `np.ndarray` of timestamps (seconds) corresponding to `est_freq`.
- `est_freq`: 1D `np.ndarray` of fundamental frequencies (Hz) for the estimate.
- `est_voicing`, default `None`: Optional 1D `np.ndarray` of voicing confidence. If `None`, voicing is inferred from `est_freq` (<= 0 is unvoiced, > 0 is voiced).
- `ref_reward`, default `None`: Optional 1D `np.ndarray` of weights for reference frames.
- `base_frequency`, default `10.0`: The reference frequency (Hz) used as the zero-point for cent conversion.
- `hop`, default `None`: The target sampling interval in seconds. If `None`, the `ref_time` grid is used.
- `kind`, default `'linear'`: Interpolation method passed to `scipy.interpolate.interp1d`.

### Input
- **Data:** Requires 1D NumPy arrays for time and frequency.
- **Preconditions:** Time arrays must be sorted in ascending order. Frequency values should be in Hz; negative values in `est_freq` are treated as unvoiced if `est_voicing` is `None`.

### Output
Returns a tuple of four `np.ndarray` objects: `(ref_voicing, ref_cent, est_voicing, est_cent)`, representing the resampled and converted data ready for metric computation.

### Valid Call Patterns
```python
# Example inferred from signature
ref_voicing, ref_cent, est_voicing, est_cent = mir_eval.melody.to_cent_voicing(
    ref_time, ref_freq, est_time, est_freq
)
```

### LLM Instruction Prompt
- Always ensure `ref_time` and `est_time` are sorted before passing to this function.
- Use `base_frequency` only if the specific evaluation protocol requires a non-standard reference (default 10Hz is standard for `mir_eval`).
- If `est_voicing` is provided, ensure it matches the length of `est_time`.

### Prompt Snippet
```text
mir_eval.melody.to_cent_voicing(ref_time, ref_freq, est_time, est_freq, ...)
```

### Common Failure Modes
- **Shape Mismatch:** Providing `ref_time` and `ref_freq` arrays of different lengths.
- **Unsorted Input:** Passing unsorted time arrays, which causes interpolation errors.
- **Frequency Units:** Passing MIDI note numbers instead of Hz, leading to incorrect cent conversion.

### Fix Code Hint
```python
# Ensure inputs are sorted by time
idx = np.argsort(ref_time)
ref_time, ref_freq = ref_time[idx], ref_freq[idx]
# Then call the function
```

## API Test: `python:mir_eval.melody.validate`

### Signature
```python
def validate(ref_voicing, ref_cent, est_voicing, est_cent)
```
_Source: source/mir_eval/melody.py:107_

_Source doc:_ Check that voicing and frequency arrays are well-formed.  To be used in
conjunction with :func:`mir_eval.melody.validate_voicing`

Parameters
----------
ref_voicing : np.ndarray
    Reference voicing array
ref_cent : np.ndarray
    Reference pitch sequence in cents
est_voicing : np.ndarray
    Estimated voicing array
est_cent : np.ndarray
    Estimate pitch sequence in cents

### Goal
Validates that the provided reference and estimated melody voicing and pitch sequences are well-formed and conform to the expected array structures for melody evaluation.

### Parameters
- `ref_voicing`: A 1D NumPy array representing the ground-truth voicing (typically binary: 1 for voiced, 0 for unvoiced).
- `ref_cent`: A 1D NumPy array representing the ground-truth pitch sequence in cents.
- `est_voicing`: A 1D NumPy array representing the estimated voicing.
- `est_cent`: A 1D NumPy array representing the estimated pitch sequence in cents.

### Input
The caller must provide four NumPy arrays. Preconditions include that the reference and estimated arrays must be of consistent length and represent time-aligned sequences. This function is intended to be used in conjunction with `mir_eval.melody.validate_voicing` to ensure complete data integrity before metric computation.

### Output
Returns `None` if the inputs are valid. Raises an exception (e.g., `ValueError` or `DimensionError`) if the arrays are malformed, have mismatched lengths, or contain invalid data types.

### Valid Call Patterns
```python
# Example inferred from signature
mir_eval.melody.validate(ref_voicing, ref_cent, est_voicing, est_cent)
```

### LLM Instruction Prompt
- Always call `mir_eval.melody.validate` before passing melody data to `mir_eval.melody.evaluate`.
- Ensure all four arguments are provided as 1D NumPy arrays.
- Use this function to verify that `ref_voicing` and `est_voicing` match the lengths of `ref_cent` and `est_cent` respectively.

### Prompt Snippet
```text
# Validate melody inputs before evaluation
mir_eval.melody.validate(ref_voicing, ref_cent, est_voicing, est_cent)
scores = mir_eval.melody.evaluate(ref_voicing, ref_cent, est_voicing, est_cent)
```

### Common Failure Modes
- **Dimension Mismatch:** Passing arrays of different lengths for voicing and pitch sequences will trigger a validation error.
- **Missing Voicing Validation:** Failing to call `mir_eval.melody.validate_voicing` alongside this function may allow logically inconsistent voicing data (e.g., non-binary values) to pass through.
- **Non-NumPy Inputs:** Passing lists instead of NumPy arrays may cause the validation logic to fail or raise unexpected errors.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure inputs are numpy arrays and validated
ref_voicing = np.array(ref_voicing)
ref_cent = np.array(ref_cent)
est_voicing = np.array(est_voicing)
est_cent = np.array(est_cent)

mir_eval.melody.validate(ref_voicing, ref_cent, est_voicing, est_cent)
```

## API Test: `python:mir_eval.melody.validate_voicing`

### Signature
```python
def validate_voicing(ref_voicing, est_voicing)
```
_Source: source/mir_eval/melody.py:77_

_Source doc:_ Check that voicing inputs to a metric are in the correct format.

Parameters
----------
ref_voicing : np.ndarray
    Reference voicing array
est_voicing : np.ndarray
    Estimated voicing array

### Goal
Validates that the reference and estimated voicing arrays conform to the expected format required for melody evaluation metrics.

### Parameters
- `ref_voicing`: A 1D NumPy array representing the ground-truth voicing state (typically binary: 1 for voiced, 0 for unvoiced).
- `est_voicing`: A 1D NumPy array representing the estimated voicing state to be compared against the reference.

### Input
- **Data Format:** Both inputs must be `np.ndarray` objects.
- **Preconditions:** The arrays should represent the voicing status corresponding to the time series used in melody evaluation. While the function checks format, it is generally expected that these arrays are of the same length as the frequency arrays being evaluated.

### Output
Returns `None` if the inputs are valid. If the inputs do not conform to the expected format, the function will raise an exception (typically a `ValueError` or `TypeError` depending on the specific validation failure).

### Valid Call Patterns
```python
# Example inferred from signature
import numpy as np
import mir_eval

ref_voicing = np.array([1, 1, 0, 0])
est_voicing = np.array([1, 0, 0, 1])
mir_eval.melody.validate_voicing(ref_voicing, est_voicing)
```

### LLM Instruction Prompt
- When calling `mir_eval.melody.validate_voicing`, ensure both `ref_voicing` and `est_voicing` are provided as 1D NumPy arrays.
- This function is intended for internal validation; ensure it is called before passing voicing data to melody evaluation metrics to prevent downstream errors.

### Prompt Snippet
```text
# Validate voicing arrays before melody evaluation
mir_eval.melody.validate_voicing(ref_voicing, est_voicing)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays of different lengths or incompatible dimensions will cause validation to fail.
- **Invalid Types:** Passing lists or other non-NumPy array types instead of `np.ndarray` will result in a `TypeError`.
- **Non-Binary Values:** While the function checks format, ensure the arrays contain appropriate voicing indicators (e.g., 0 and 1) as expected by subsequent melody evaluation logic.

### Fix Code Hint
```python
import numpy as np
# Ensure inputs are numpy arrays before validation
ref_voicing = np.asarray(ref_voicing)
est_voicing = np.asarray(est_voicing)
mir_eval.melody.validate_voicing(ref_voicing, est_voicing)
```

## API Test: `python:mir_eval.melody.voicing_false_alarm`

### Signature
```python
def voicing_false_alarm(ref_voicing, est_voicing)
```
_Source: source/mir_eval/melody.py:478_

_Source doc:_ Compute the voicing false alarm rates given two voicing
indicator sequences, one as reference (truth) and the other as the estimate
(prediction).  The sequences must be of the same length.

Examples
--------
>>> ref_time, ref_freq = mir_eval.io.load_time_series('ref.txt')
>>> est_time, est_freq = mir_eval.io.load_time_series('est.txt')
>>> (ref_v, ref_c,
...  est_v, est_c) = mir_eval.melody.to_cent_voicing(ref_time,
...                                                  ref_freq,
...                                                  est_time,
...                                                  est_freq)
>>> false_alarm = mir_eval.melody.voicing_false_alarm(ref_v, est_v)

Parameters
----------
ref_voicing : np.ndarray
    Reference boolean voicing array
est_voicing : np.ndarray
    Estimated boolean voicing array

Returns
-------
vx_false_alarm : float
    Voicing false alarm rate, the fraction of unvoiced frames in ref
    indicated as voiced in est

### Goal
Computes the voicing false alarm rate for melody estimation, quantifying the proportion of unvoiced reference frames that were incorrectly identified as voiced by the system.

### Parameters
- `ref_voicing`: A 1D `np.ndarray` of boolean values representing the ground-truth voicing state (True for voiced, False for unvoiced).
- `est_voicing`: A 1D `np.ndarray` of boolean values representing the estimated voicing state (True for voiced, False for unvoiced).

### Input
- **Data Format:** Both inputs must be 1D NumPy arrays of the same length.
- **Preconditions:** The arrays should be derived from time-aligned melody sequences. It is standard practice to use `mir_eval.melody.to_cent_voicing` to convert raw time-series frequency data into the required boolean voicing arrays before calling this function.

### Output
Returns `float`: The voicing false alarm rate, calculated as the fraction of frames where `ref_voicing` is `False` (unvoiced) but `est_voicing` is `True` (voiced).

### Valid Call Patterns
```python
# Standard usage following conversion from time-series data
false_alarm = mir_eval.melody.voicing_false_alarm(ref_v, est_v)
```

### LLM Instruction Prompt
- When calling `mir_eval.melody.voicing_false_alarm`, ensure that both `ref_voicing` and `est_voicing` are boolean NumPy arrays of identical length.
- Always perform the conversion from raw frequency time-series to voicing arrays using `mir_eval.melody.to_cent_voicing` prior to calling this metric to ensure temporal alignment.

### Prompt Snippet
```text
# Ensure voicing arrays are prepared via to_cent_voicing
ref_v, ref_c, est_v, est_c = mir_eval.melody.to_cent_voicing(ref_time, ref_freq, est_time, est_freq)
false_alarm = mir_eval.melody.voicing_false_alarm(ref_v, est_v)
```

### Common Failure Modes
- **Length Mismatch:** Passing arrays of different lengths will result in a `ValueError` during computation.
- **Non-Boolean Inputs:** Passing raw frequency arrays instead of boolean voicing arrays will lead to incorrect metric calculations; ensure inputs are boolean.
- **Unsynchronized Data:** If the reference and estimated time series are not aligned to the same time grid, the resulting voicing arrays will not be comparable.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure inputs are boolean and same length
ref_v = np.array([False, True, True, False])
est_v = np.array([False, False, True, True])

# Compute false alarm rate
rate = mir_eval.melody.voicing_false_alarm(ref_v, est_v)
```

## API Test: `python:mir_eval.melody.voicing_measures`

### Signature
```python
def voicing_measures(ref_voicing, est_voicing)
```
_Source: source/mir_eval/melody.py:515_

_Source doc:_ Compute the voicing recall and false alarm rates given two voicing
indicator sequences, one as reference (truth) and the other as the estimate
(prediction).  The sequences must be of the same length.

Examples
--------
>>> ref_time, ref_freq = mir_eval.io.load_time_series('ref.txt')
>>> est_time, est_freq = mir_eval.io.load_time_series('est.txt')
>>> (ref_v, ref_c,
...  est_v, est_c) = mir_eval.melody.to_cent_voicing(ref_time,
...                                                  ref_freq,
...                                                  est_time,
...                                                  est_freq)
>>> recall, false_alarm = mir_eval.melody.voicing_measures(ref_v,
...                                                        est_v)

Parameters
----------
ref_voicing : np.ndarray
    Reference boolean voicing array
est_voicing : np.ndarray
    Estimated boolean voicing array

Returns
-------
vx_recall : float
    Voicing recall rate, the fraction of voiced frames in ref
    indicated as voiced in est
vx_false_alarm : float
    Voicing false alarm rate, the fraction of unvoiced frames in ref
    indicated as voiced in est

### Goal
Computes the voicing recall and false alarm rates to evaluate the accuracy of a melody extraction system's voicing detection.

### Parameters
- `ref_voicing`: A 1D `np.ndarray` of boolean values representing the ground-truth voicing state (True for voiced, False for unvoiced).
- `est_voicing`: A 1D `np.ndarray` of boolean values representing the estimated voicing state (True for voiced, False for unvoiced).

### Input
- **Data Format:** Both inputs must be 1D `np.ndarray` objects of the same length.
- **Preconditions:** The arrays must represent aligned frames. Typically, these are generated by first processing raw time-series data through `mir_eval.melody.to_cent_voicing` to ensure the reference and estimate are synchronized and sampled at the same time intervals.

### Output
Returns a tuple of two floats:
- `vx_recall`: The fraction of voiced frames in the reference that were correctly identified as voiced in the estimate.
- `vx_false_alarm`: The fraction of unvoiced frames in the reference that were incorrectly identified as voiced in the estimate.

### Valid Call Patterns
```python
recall, false_alarm = mir_eval.melody.voicing_measures(ref_v, est_v)
```

### LLM Instruction Prompt
- When calling `mir_eval.melody.voicing_measures`, ensure that `ref_voicing` and `est_voicing` are boolean arrays of identical length. Always use the output of `mir_eval.melody.to_cent_voicing` to prepare these inputs from raw time-series data to guarantee temporal alignment.

### Prompt Snippet
```text
# Ensure inputs are boolean arrays of the same length
recall, false_alarm = mir_eval.melody.voicing_measures(ref_voicing, est_voicing)
```

### Common Failure Modes
- **Length Mismatch:** Passing arrays of different lengths will raise a `ValueError` (or similar indexing error) because the function performs element-wise comparison.
- **Non-Boolean Inputs:** Passing non-boolean arrays may lead to incorrect logical evaluation; ensure inputs are cast to boolean types if they contain numeric indicators (e.g., 0 and 1).
- **Temporal Misalignment:** Using raw time-series data without first aligning them via `to_cent_voicing` will result in semantically meaningless metrics.

### Fix Code Hint
```python
# Ensure alignment before computing measures
ref_v, ref_c, est_v, est_c = mir_eval.melody.to_cent_voicing(ref_time, ref_freq, est_time, est_freq)
recall, false_alarm = mir_eval.melody.voicing_measures(ref_v.astype(bool), est_v.astype(bool))
```

## API Test: `python:mir_eval.melody.voicing_recall`

### Signature
```python
def voicing_recall(ref_voicing, est_voicing)
```
_Source: source/mir_eval/melody.py:441_

_Source doc:_ Compute the voicing recall given two voicing
indicator sequences, one as reference (truth) and the other as the estimate
(prediction).  The sequences must be of the same length.

Examples
--------
>>> ref_time, ref_freq = mir_eval.io.load_time_series('ref.txt')
>>> est_time, est_freq = mir_eval.io.load_time_series('est.txt')
>>> (ref_v, ref_c,
...  est_v, est_c) = mir_eval.melody.to_cent_voicing(ref_time,
...                                                  ref_freq,
...                                                  est_time,
...                                                  est_freq)
>>> recall = mir_eval.melody.voicing_recall(ref_v, est_v)

Parameters
----------
ref_voicing : np.ndarray
    Reference boolean voicing array
est_voicing : np.ndarray
    Estimated boolean voicing array

Returns
-------
vx_recall : float
    Voicing recall rate, the fraction of voiced frames in ref
    indicated as voiced in est

### Goal
Computes the voicing recall metric for melody evaluation, measuring the proportion of reference voiced frames that are correctly identified as voiced by an estimation system.

### Parameters
- `ref_voicing`: A 1D `np.ndarray` of boolean values representing the ground-truth voicing state (True for voiced, False for unvoiced).
- `est_voicing`: A 1D `np.ndarray` of boolean values representing the estimated voicing state (True for voiced, False for unvoiced).

### Input
- **Data Format:** Both inputs must be 1D `np.ndarray` objects of the same length.
- **Preconditions:** The arrays must represent aligned frames. Typically, these are derived from raw time-series data using `mir_eval.melody.to_cent_voicing` to ensure the reference and estimate are sampled at the same time intervals.

### Output
Returns `float` — The voicing recall rate, calculated as the fraction of frames where `ref_voicing` is True that are also True in `est_voicing`.

### Valid Call Patterns
```python
# Standard usage after converting time-series to aligned voicing arrays
recall = mir_eval.melody.voicing_recall(ref_v, est_v)
```

### LLM Instruction Prompt
- When calling `mir_eval.melody.voicing_recall`, ensure that `ref_voicing` and `est_voicing` are boolean `np.ndarray` objects of identical length.
- Always perform the conversion from raw time-series data to voicing arrays using `mir_eval.melody.to_cent_voicing` before calling this function to ensure temporal alignment.

### Prompt Snippet
```text
import mir_eval
# Assuming ref_v and est_v are boolean numpy arrays of equal length
recall = mir_eval.melody.voicing_recall(ref_v, est_v)
```

### Common Failure Modes
- **Length Mismatch:** Passing arrays of different lengths will raise a `ValueError` (or similar indexing error) because the function requires frame-by-frame comparison.
- **Non-Boolean Inputs:** Passing non-boolean arrays may lead to incorrect logical evaluation; ensure inputs are cast to boolean types.
- **Unsynchronized Data:** Failing to use `mir_eval.melody.to_cent_voicing` first can result in comparing non-corresponding frames, leading to meaningless evaluation scores.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure inputs are boolean and same length
ref_v = ref_v.astype(bool)
est_v = est_v.astype(bool)

if len(ref_v) != len(est_v):
    raise ValueError("ref_voicing and est_voicing must have the same length.")

recall = mir_eval.melody.voicing_recall(ref_v, est_v)
```

## API Test: `python:mir_eval.multipitch.compute_accuracy`

### Signature
```python
def compute_accuracy(true_positives, n_ref, n_est)
```
_Source: source/mir_eval/multipitch.py:249_

_Source doc:_ Compute accuracy metrics.

Parameters
----------
true_positives : np.ndarray
    Array containing the number of true positives at each time point.
n_ref : np.ndarray
    Array containing the number of reference frequencies at each time
    point.
n_est : np.ndarray
    Array containing the number of estimate frequencies at each time point.

Returns
-------
precision : float
    ``sum(true_positives)/sum(n_est)``
recall : float
    ``sum(true_positives)/sum(n_ref)``
acc : float
    ``sum(true_positives)/sum(n_est + n_ref - true_positives)``

### Goal
Computes standard multi-pitch evaluation metrics (precision, recall, and accuracy) by aggregating true positive counts against reference and estimated frequency counts across time.

### Parameters
- `true_positives`: A 1D `np.ndarray` where each element represents the count of correctly identified pitches at a specific time point.
- `n_ref`: A 1D `np.ndarray` where each element represents the total count of ground-truth pitches present at a specific time point.
- `n_est`: A 1D `np.ndarray` where each element represents the total count of estimated pitches provided by the system at a specific time point.

### Input
- **Data Format:** All inputs must be 1D `np.ndarray` objects of equal length, representing the time-series counts of pitches.
- **Preconditions:** The arrays must be aligned such that index `i` in each array corresponds to the same time point. These arrays are typically derived from comparing reference and estimated frequency sets at each frame.

### Output
Returns a tuple of three floats: `(precision, recall, acc)`.
- `precision`: The ratio of total true positives to total estimated pitches.
- `recall`: The ratio of total true positives to total reference pitches.
- `acc`: The accuracy score, calculated as the ratio of true positives to the union of reference and estimated pitch sets (true positives + false positives + false negatives).

### Valid Call Patterns
```python
# Example inferred from signature
precision, recall, acc = mir_eval.multipitch.compute_accuracy(true_positives, n_ref, n_est)
```

### LLM Instruction Prompt
- When calling `mir_eval.multipitch.compute_accuracy`, ensure all three input arrays are of identical length.
- The function returns a tuple of three floats; ensure the calling code unpacks these correctly.
- Do not perform manual summation before passing the arrays; the function performs the necessary summation internally.

### Prompt Snippet
```text
# Calculate multi-pitch accuracy metrics
precision, recall, acc = mir_eval.multipitch.compute_accuracy(tp_array, ref_count_array, est_count_array)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays of different lengths will result in a `ValueError` or incorrect summation behavior during the internal `sum()` operations.
- **Division by Zero:** If `sum(n_est)` or `sum(n_ref)` is zero (e.g., empty reference or estimate arrays), the function may raise a `ZeroDivisionError` or return `NaN` depending on the NumPy configuration.
- **Input Type:** Passing lists instead of `np.ndarray` may cause issues if the internal logic expects NumPy-specific summation behavior.

### Fix Code Hint
```python
import numpy as np
# Ensure inputs are numpy arrays of the same length
tp = np.array(true_positives)
ref = np.array(n_ref)
est = np.array(n_est)
precision, recall, acc = mir_eval.multipitch.compute_accuracy(tp, ref, est)
```

## API Test: `python:mir_eval.multipitch.compute_err_score`

### Signature
```python
def compute_err_score(true_positives, n_ref, n_est)
```
_Source: source/mir_eval/multipitch.py:297_

_Source doc:_ Compute error score metrics.

Parameters
----------
true_positives : np.ndarray
    Array containing the number of true positives at each time point.
n_ref : np.ndarray
    Array containing the number of reference frequencies at each time
    point.
n_est : np.ndarray
    Array containing the number of estimate frequencies at each time point.

Returns
-------
e_sub : float
    Substitution error
e_miss : float
    Miss error
e_fa : float
    False alarm error
e_tot : float
    Total error

### Goal
Computes the fundamental multipitch error metrics (substitution, miss, false alarm, and total error) by comparing the number of true positives against the reference and estimated frequency counts at each time point.

### Parameters
- `true_positives`: A 1D `np.ndarray` representing the count of correctly identified pitches at each time step.
- `n_ref`: A 1D `np.ndarray` representing the total count of ground-truth pitches at each time step.
- `n_est`: A 1D `np.ndarray` representing the total count of estimated pitches at each time step.

### Input
- **Data Format:** All inputs must be 1D `np.ndarray` objects of equal length, where each index corresponds to a specific time point in the evaluation window.
- **Preconditions:** The arrays must be pre-calculated from the multipitch estimation results. Ensure that `true_positives` does not exceed `n_ref` or `n_est` at any index.

### Output
Returns a tuple of four floats: `(e_sub, e_miss, e_fa, e_tot)`, representing the substitution error, miss error, false alarm error, and total error respectively.

### Valid Call Patterns
```python
# Example inferred from signature
e_sub, e_miss, e_fa, e_tot = mir_eval.multipitch.compute_err_score(
    true_positives, n_ref, n_est
)
```

### LLM Instruction Prompt
- When calling `mir_eval.multipitch.compute_err_score`, ensure all three input arrays are of identical length.
- The function returns four distinct float values; ensure the caller unpacks these into the correct variables: `e_sub`, `e_miss`, `e_fa`, and `e_tot`.

### Prompt Snippet
```text
# Calculate multipitch error metrics
e_sub, e_miss, e_fa, e_tot = mir_eval.multipitch.compute_err_score(tp_array, ref_count_array, est_count_array)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays of different lengths will result in a `ValueError` during internal NumPy operations.
- **Invalid Counts:** If `true_positives` contains values greater than `n_ref` or `n_est`, the resulting error metrics may be mathematically invalid or negative.
- **Empty Arrays:** Passing empty arrays will result in an error or return `NaN` values depending on the underlying implementation.

### Fix Code Hint
```python
# Ensure arrays are aligned and valid before computation
import numpy as np
assert len(true_positives) == len(n_ref) == len(n_est)
# Ensure true_positives is bounded by reference and estimate counts
true_positives = np.minimum(true_positives, np.minimum(n_ref, n_est))
```

## API Test: `python:mir_eval.multipitch.compute_num_freqs`

### Signature
```python
def compute_num_freqs(frequencies)
```
_Source: source/mir_eval/multipitch.py:191_

_Source doc:_ Compute the number of frequencies for each time point.

Parameters
----------
frequencies : list of np.ndarray
    Frequency values

Returns
-------
num_freqs : np.ndarray
    Number of frequencies at each time point.

### Goal
Calculates the count of detected frequency components present at each discrete time point within a multi-pitch estimation or ground-truth dataset.

### Parameters
- `frequencies`: A list of `np.ndarray` objects, where each array contains the frequency values (in Hz) detected at a specific time point.

### Input
- **Data Format:** The input must be a list of NumPy arrays. Each element in the list corresponds to a time point, and the array within that element contains the fundamental frequencies (F0) identified at that time.
- **Preconditions:** The input should represent a ragged time series structure where the number of detected pitches can vary per time step.

### Output
Returns `np.ndarray` — A 1D NumPy array where each element represents the integer count of frequencies found at the corresponding time index of the input list.

### Valid Call Patterns
```python
# Example inferred from signature
import numpy as np
import mir_eval

# frequencies is a list of arrays, e.g., [np.array([440.0]), np.array([440.0, 880.0])]
num_freqs = mir_eval.multipitch.compute_num_freqs(frequencies)
```

### LLM Instruction Prompt
- When calling `mir_eval.multipitch.compute_num_freqs`, ensure the input `frequencies` is a list of `np.ndarray` objects. 
- Do not pass a single 2D array; the function expects a list structure to accommodate varying numbers of frequencies per time point.

### Prompt Snippet
```text
# Ensure frequencies is a list of np.ndarray
num_freqs = mir_eval.multipitch.compute_num_freqs(frequencies)
```

### Common Failure Modes
- **TypeError:** Passing a single `np.ndarray` instead of a `list` of `np.ndarray` objects will cause the function to fail when iterating or calculating lengths.
- **Empty Input:** Passing an empty list will result in an empty `np.ndarray` return value.
- **Invalid Data Types:** Passing non-numeric types within the arrays will lead to errors during processing.

### Fix Code Hint
```python
# Ensure input is a list of arrays
if not isinstance(frequencies, list):
    frequencies = [frequencies]
num_freqs = mir_eval.multipitch.compute_num_freqs(frequencies)
```

## API Test: `python:mir_eval.multipitch.compute_num_true_positives`

### Signature
```python
def compute_num_true_positives(ref_freqs, est_freqs, window=0.5, chroma=False)
```
_Source: source/mir_eval/multipitch.py:207_

_Source doc:_ Compute the number of true positives in an estimate given a reference.
A frequency is correct if it is within a quartertone of the
correct frequency.

Parameters
----------
ref_freqs : list of np.ndarray
    reference frequencies (MIDI)
est_freqs : list of np.ndarray
    estimated frequencies (MIDI)
window : float
    Window size, in semitones
chroma : bool
    If True, computes distances modulo n.
    If True, ``ref_freqs`` and ``est_freqs`` should be wrapped modulo n.

Returns
-------
true_positives : np.ndarray
    Array the same length as ref_freqs containing the number of true
    positives.

### Goal
Computes the count of correctly identified pitches by comparing estimated frequencies against a reference set within a specified semitone tolerance.

### Parameters
- `ref_freqs`: A list of NumPy arrays containing the ground-truth fundamental frequencies expressed in MIDI note numbers.
- `est_freqs`: A list of NumPy arrays containing the estimated fundamental frequencies expressed in MIDI note numbers.
- `window`, default `0.5`: The tolerance threshold in semitones used to determine if a frequency match is considered a true positive.
- `chroma`, default `False`: A boolean flag; if set to `True`, the function computes distances modulo $n$ (octave-agnostic), requiring inputs to be pre-wrapped.

### Input
- **Data Format:** Both `ref_freqs` and `est_freqs` must be provided as lists of NumPy arrays.
- **Preconditions:** Inputs must be in MIDI note numbers. If `chroma=True`, the caller must ensure that both reference and estimated frequencies are wrapped modulo $n$ before passing them to the function.

### Output
Returns `np.ndarray` — An array of the same length as `ref_freqs`, where each element represents the count of correctly matched frequencies for that specific time index.

### Valid Call Patterns
```python
# Example inferred from signature
import numpy as np
from mir_eval.multipitch import compute_num_true_positives

# ref_freqs and est_freqs are lists of np.ndarray
tp = compute_num_true_positives(ref_freqs, est_freqs, window=0.5, chroma=False)
```

### LLM Instruction Prompt
- When calling `compute_num_true_positives`, ensure that `ref_freqs` and `est_freqs` are lists of NumPy arrays containing MIDI note numbers.
- If performing chroma-based evaluation, explicitly set `chroma=True` and verify that input arrays are wrapped to the appropriate modulo range.
- The `window` parameter should be a float representing semitones; the default is 0.5.

### Prompt Snippet
```text
# Calculate true positives for multi-pitch estimation
tp_counts = mir_eval.multipitch.compute_num_true_positives(ref_data, est_data, window=0.5)
```

### Common Failure Modes
- **Mismatched Units:** Passing frequencies in Hz instead of MIDI note numbers will result in incorrect evaluation. Use `mir_eval.util.hz_to_midi` to convert if necessary.
- **Chroma Mismatch:** Setting `chroma=True` without pre-wrapping the input arrays will lead to invalid distance calculations.
- **Input Shape:** Providing a single NumPy array instead of a list of arrays will cause indexing errors within the function.

### Fix Code Hint
```python
# Ensure inputs are in MIDI and correctly formatted
import mir_eval.util
ref_midi = [mir_eval.util.hz_to_midi(f) for f in ref_freqs]
est_midi = [mir_eval.util.hz_to_midi(f) for f in est_freqs]
tp = mir_eval.multipitch.compute_num_true_positives(ref_midi, est_midi)
```

## API Test: `python:mir_eval.multipitch.evaluate`

### Signature
```python
def evaluate(ref_time, ref_freqs, est_time, est_freqs, **kwargs)
```
_Source: source/mir_eval/multipitch.py:479_

_Source doc:_ Evaluate two multipitch (multi-f0) transcriptions, where the first is
treated as the reference (ground truth) and the second as the estimate to
be evaluated (prediction).

Examples
--------
>>> ref_time, ref_freq = mir_eval.io.load_ragged_time_series('ref.txt')
>>> est_time, est_freq = mir_eval.io.load_ragged_time_series('est.txt')
>>> scores = mir_eval.multipitch.evaluate(ref_time, ref_freq,
...                                       est_time, est_freq)

Parameters
----------
ref_time : np.ndarray
    Time of each reference frequency value
ref_freqs : list of np.ndarray
    List of np.ndarrays of reference frequency values
est_time : np.ndarray
    Time of each estimated frequency value
est_freqs : list of np.ndarray
    List of np.ndarrays of estimate frequency values
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of multi-f0 transcription accuracy metrics by comparing a reference transcription against an estimated transcription.

### Parameters
- `ref_time`: A 1D NumPy array containing the timestamps (in seconds) for the reference transcription.
- `ref_freqs`: A list of NumPy arrays, where each array contains the fundamental frequencies (in Hz) present at the corresponding timestamp in `ref_time`.
- `est_time`: A 1D NumPy array containing the timestamps (in seconds) for the estimated transcription.
- `est_freqs`: A list of NumPy arrays, where each array contains the fundamental frequencies (in Hz) present at the corresponding timestamp in `est_time`.
- `kwargs`: Optional keyword arguments passed to underlying metric or preprocessing functions.

### Input
The function expects "ragged time series" data. Inputs must be prepared such that `ref_time` and `est_time` are sorted by time. Frequencies are expected in Hertz. Use `mir_eval.io.load_ragged_time_series` to load data from standard text files.

### Output
Returns a `dict` where keys are strings representing metric names (e.g., precision, recall, F-measure) and values are `float` scores.

### Valid Call Patterns
```python
import mir_eval
ref_time, ref_freq = mir_eval.io.load_ragged_time_series('ref.txt')
est_time, est_freq = mir_eval.io.load_ragged_time_series('est.txt')
scores = mir_eval.multipitch.evaluate(ref_time, ref_freq, est_time, est_freq)
```

### LLM Instruction Prompt
When calling `mir_eval.multipitch.evaluate`, ensure that the input arrays are sorted by time and that frequencies are provided in Hz. The function requires four positional arguments corresponding to the reference and estimated time-frequency pairs.

### Prompt Snippet
```text
scores = mir_eval.multipitch.evaluate(ref_time, ref_freqs, est_time, est_freqs)
```

### Common Failure Modes
- **Unsorted Input:** Providing `ref_time` or `est_time` arrays that are not sorted by time will lead to incorrect metric calculations.
- **Mismatched Lengths:** The length of `ref_time` must match the length of the `ref_freqs` list; similarly for the estimate.
- **Frequency Units:** Providing frequencies in MIDI or cents instead of Hz will result in invalid evaluation scores.

### Fix Code Hint
```python
# Ensure inputs are sorted by time before evaluation
idx = np.argsort(ref_time)
ref_time = ref_time[idx]
ref_freqs = [ref_freqs[i] for i in idx]
```

## API Test: `python:mir_eval.multipitch.frequencies_to_midi`

### Signature
```python
def frequencies_to_midi(frequencies, ref_frequency=440.0)
```
_Source: source/mir_eval/multipitch.py:156_

_Source doc:_ Convert frequencies to continuous MIDI values.

Parameters
----------
frequencies : list of np.ndarray
    Original frequency values
ref_frequency : float
    reference frequency in Hz.

Returns
-------
frequencies_midi : list of np.ndarray
    Continuous MIDI frequency values.

### Goal
Converts fundamental frequency values (in Hz) into continuous MIDI note numbers to facilitate pitch-based evaluation and comparison in multi-pitch estimation tasks.

### Parameters
- `frequencies`: A list of `np.ndarray` objects containing the original frequency values in Hertz.
- `ref_frequency`, default `440.0`: The reference frequency in Hz used to define the MIDI tuning standard (default is A4 = 440 Hz).

### Input
- **Data Format:** Expects a list of NumPy arrays.
- **Preconditions:** Frequencies should be positive values. The function assumes the input is structured as a list of arrays, consistent with the ragged time series format used in multi-pitch evaluation.

### Output
Returns a `list of np.ndarray` containing the corresponding continuous MIDI values, where each value represents the pitch height relative to the provided `ref_frequency`.

### Valid Call Patterns
```python
# Inferred from signature:
import mir_eval
import numpy as np

# Example with a single array of frequencies
freqs = [np.array([440.0, 880.0])]
midi_values = mir_eval.multipitch.frequencies_to_midi(freqs, ref_frequency=440.0)
```

### LLM Instruction Prompt
- When calling `mir_eval.multipitch.frequencies_to_midi`, ensure the input `frequencies` is provided as a list of `np.ndarray` objects.
- Always specify `ref_frequency` if the tuning standard deviates from the default 440.0 Hz.
- The output will maintain the same list-of-arrays structure as the input.

### Prompt Snippet
```text
# Convert frequency arrays to MIDI for evaluation
midi_data = mir_eval.multipitch.frequencies_to_midi(freq_list, ref_frequency=440.0)
```

### Common Failure Modes
- **Type Mismatch:** Passing a single `np.ndarray` instead of a `list` of `np.ndarray` objects will cause indexing errors during processing.
- **Non-positive Frequencies:** Providing zero or negative frequency values may result in mathematically undefined MIDI values (logarithm of non-positive numbers).
- **Tuning Mismatch:** Using the default `ref_frequency` when the source audio was recorded at a different tuning standard (e.g., 442 Hz) will introduce systematic bias in the resulting MIDI values.

### Fix Code Hint
```python
# Ensure input is a list of arrays and handle potential non-positive values
import numpy as np
frequencies = [np.maximum(f, 1e-6) for f in frequencies]
midi_values = mir_eval.multipitch.frequencies_to_midi(frequencies, ref_frequency=440.0)
```

## API Test: `python:mir_eval.multipitch.metrics`

### Signature
```python
def metrics(ref_time, ref_freqs, est_time, est_freqs, **kwargs)
```
_Source: source/mir_eval/multipitch.py:349_

_Source doc:_ Compute multipitch metrics. All metrics are computed at the 'macro' level
such that the frame true positive/false positive/false negative rates are
summed across time and the metrics are computed on the combined values.

Examples
--------
>>> ref_time, ref_freqs = mir_eval.io.load_ragged_time_series(
...     'reference.txt')
>>> est_time, est_freqs = mir_eval.io.load_ragged_time_series(
...     'estimated.txt')
>>> metris_tuple = mir_eval.multipitch.metrics(
...     ref_time, ref_freqs, est_time, est_freqs)

Parameters
----------
ref_time : np.ndarray
    Time of each reference frequency value
ref_freqs : list of np.ndarray
    List of np.ndarrays of reference frequency values
est_time : np.ndarray
    Time of each estimated frequency value
est_freqs : list of np.ndarray
    List of np.ndarrays of estimate frequency values
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
precision : float
    Precision (TP/(TP + FP))
recall : float
    Recall (TP/(TP + FN))
accuracy : float
    Accuracy (TP/(TP + FP + FN))
e_sub : float
    Substitution error
e_miss : float
    Miss error
e_fa : float
    False alarm error
e_tot : float
    Total error
precision_chroma : float
    Chroma precision
recall_chroma : float
    Chroma recall
accuracy_chroma : float
    Chroma accuracy
e_sub_chroma : float
    Chroma substitution error
e_miss_chroma : float
    Chroma miss error
e_fa_chroma : float
    Chroma false alarm error
e_tot_chroma : float
    Chroma total error

### Goal
Computes macro-averaged multipitch evaluation metrics by comparing reference and estimated frequency time series at the frame level.

### Parameters
- `ref_time`: A 1D NumPy array containing the timestamps (in seconds) for the reference frequency data.
- `ref_freqs`: A list of NumPy arrays, where each array contains the fundamental frequencies (in Hz) present at the corresponding timestamp in `ref_time`.
- `est_time`: A 1D NumPy array containing the timestamps (in seconds) for the estimated frequency data.
- `est_freqs`: A list of NumPy arrays, where each array contains the fundamental frequencies (in Hz) present at the corresponding timestamp in `est_time`.
- `kwargs`: Optional keyword arguments passed to internal metric or preprocessing functions.

### Input
The function expects "ragged time series" data, typically loaded via `mir_eval.io.load_ragged_time_series`. Preconditions include that time arrays must be sorted by time and represent valid timestamps in seconds. Frequencies must be provided in Hz.

### Output
Returns a tuple of 14 floats representing standard multipitch metrics (Precision, Recall, Accuracy, and various error rates) and their corresponding chroma-based variants.

### Valid Call Patterns
```python
ref_time, ref_freqs = mir_eval.io.load_ragged_time_series('reference.txt')
est_time, est_freqs = mir_eval.io.load_ragged_time_series('estimated.txt')
metrics = mir_eval.multipitch.metrics(ref_time, ref_freqs, est_time, est_freqs)
```

### LLM Instruction Prompt
When calling `mir_eval.multipitch.metrics`, ensure that the input data is loaded as a ragged time series. The function returns a flat tuple of 14 metrics; ensure the calling code unpacks these correctly or accesses them by index if necessary.

### Prompt Snippet
```text
# Ensure inputs are loaded as ragged time series
ref_time, ref_freqs = mir_eval.io.load_ragged_time_series(ref_path)
est_time, est_freqs = mir_eval.io.load_ragged_time_series(est_path)
# Compute metrics
results = mir_eval.multipitch.metrics(ref_time, ref_freqs, est_time, est_freqs)
```

### Common Failure Modes
- Providing non-sorted time arrays, which violates the expected input structure for time-series evaluation.
- Mismatched lengths between `ref_time` and `ref_freqs` (or `est_time` and `est_freqs`).
- Providing frequencies in units other than Hz (e.g., MIDI or cents), which will lead to incorrect metric calculations.

### Fix Code Hint
```python
# Ensure data is sorted by time if not already
idx = np.argsort(ref_time)
ref_time = ref_time[idx]
ref_freqs = [ref_freqs[i] for i in idx]
```

## API Test: `python:mir_eval.multipitch.midi_to_chroma`

### Signature
```python
def midi_to_chroma(frequencies_midi)
```
_Source: source/mir_eval/multipitch.py:174_

_Source doc:_ Wrap MIDI frequencies to a single octave (chroma).

Parameters
----------
frequencies_midi : list of np.ndarray
    Continuous MIDI note frequency values.

Returns
-------
frequencies_chroma : list of np.ndarray
    Midi values wrapped to one octave.

### Goal
Wraps continuous MIDI note frequency values into a single octave (chroma) representation to facilitate pitch-class-based analysis in multipitch evaluation.

### Parameters
- `frequencies_midi`: A list of `np.ndarray` objects containing continuous MIDI note frequency values to be mapped into the [0, 12) chroma space.

### Input
- **Data Format:** The input must be a list of `np.ndarray` objects.
- **Preconditions:** The values should represent MIDI note numbers (where 69 corresponds to A440). The function assumes the input is in a format compatible with standard MIDI frequency scaling.

### Output
Returns `list of np.ndarray` — A list of `np.ndarray` objects where each MIDI value has been wrapped modulo 12, representing the pitch class (chroma) of the input frequencies.

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example inferred from signature
midi_data = [np.array([60.0, 61.5, 72.0])]
chroma_data = mir_eval.multipitch.midi_to_chroma(midi_data)
```

### LLM Instruction Prompt
- When calling `mir_eval.multipitch.midi_to_chroma`, ensure the input is a list of `np.ndarray` objects.
- Do not attempt to pass raw frequency values in Hertz; ensure they are converted to MIDI note numbers first (e.g., using `mir_eval.util.hz_to_midi`).
- The output will maintain the same list structure as the input.

### Prompt Snippet
```text
# Convert Hz to MIDI then wrap to chroma
midi_vals = [mir_eval.util.hz_to_midi(freq_array)]
chroma = mir_eval.multipitch.midi_to_chroma(midi_vals)
```

### Common Failure Modes
- **Type Mismatch:** Passing a single `np.ndarray` instead of a `list` of `np.ndarray` objects will cause an iteration error.
- **Unit Error:** Passing frequencies in Hertz instead of MIDI note numbers will result in mathematically incorrect chroma values.
- **Empty Input:** Passing an empty list or empty arrays may result in unexpected behavior depending on the downstream processing; ensure inputs are validated using `mir_eval.multipitch.validate` if applicable.

### Fix Code Hint
```python
# Ensure input is a list of arrays
if not isinstance(frequencies_midi, list):
    frequencies_midi = [frequencies_midi]
chroma = mir_eval.multipitch.midi_to_chroma(frequencies_midi)
```

## API Test: `python:mir_eval.multipitch.resample_multipitch`

### Signature
```python
def resample_multipitch(times, frequencies, target_times)
```
_Source: source/mir_eval/multipitch.py:102_

_Source doc:_ Resamples multipitch time series to a new timescale using nearest
neighbor interpolation. Values in ``target_times`` outside the range
of ``times`` return no pitch estimate.

Parameters
----------
times : np.ndarray
    Array of time stamps
frequencies : list of np.ndarray
    List of np.ndarrays of frequency values
target_times : np.ndarray
    Array of target time stamps

Returns
-------
frequencies_resampled : list of numpy arrays
    Frequency list of lists resampled to new timebase

### Goal
Resamples a multi-pitch time series to a new temporal grid using nearest-neighbor interpolation to align pitch estimates across different timebases.

### Parameters
- `times`: A 1D `np.ndarray` of time stamps (in seconds) corresponding to the original frequency estimates.
- `frequencies`: A list of `np.ndarray` objects, where each array contains the frequency values (in Hz) detected at the corresponding time stamp in `times`.
- `target_times`: A 1D `np.ndarray` of new time stamps (in seconds) to which the frequency data should be resampled.

### Input
- **Data Format:** `times` and `target_times` must be 1D NumPy arrays. `frequencies` must be a list of arrays (ragged time series).
- **Preconditions:** Time stamps must be provided in seconds. The input `times` array should be sorted chronologically.
- **Compatibility:** Values in `target_times` that fall outside the range defined by `times` will result in an empty pitch estimate for those specific time points.

### Output
Returns `frequencies_resampled` (list of `np.ndarray`): A list of frequency arrays corresponding to the time points provided in `target_times`.

### Valid Call Patterns
```python
# Example inferred from signature
resampled_freqs = mir_eval.multipitch.resample_multipitch(times, frequencies, target_times)
```

### LLM Instruction Prompt
- Use `mir_eval.multipitch.resample_multipitch` when you need to synchronize multi-pitch estimation data to a common time grid.
- Ensure all time inputs are in seconds.
- Note that this function uses nearest-neighbor interpolation; it does not perform linear or spline interpolation.

### Prompt Snippet
```text
# Resample multi-pitch data to a new timebase
resampled_data = mir_eval.multipitch.resample_multipitch(times, frequencies, target_times)
```

### Common Failure Modes
- **Out-of-bounds:** Providing `target_times` that are entirely outside the range of `times` will result in a list of empty arrays.
- **Input Shape Mismatch:** Passing `frequencies` as a single 2D array instead of a list of 1D arrays will cause indexing errors.
- **Unsorted Times:** If `times` is not sorted, the nearest-neighbor interpolation may produce non-deterministic or incorrect results.

### Fix Code Hint
```python
# Ensure inputs are sorted by time before resampling
sort_idx = np.argsort(times)
times_sorted = times[sort_idx]
frequencies_sorted = [frequencies[i] for i in sort_idx]
resampled = mir_eval.multipitch.resample_multipitch(times_sorted, frequencies_sorted, target_times)
```

## API Test: `python:mir_eval.multipitch.validate`

### Signature
```python
def validate(ref_time, ref_freqs, est_time, est_freqs)
```
_Source: source/mir_eval/multipitch.py:57_

_Source doc:_ Check that the time and frequency inputs are well-formed.

Parameters
----------
ref_time : np.ndarray
    reference time stamps in seconds
ref_freqs : list of np.ndarray
    reference frequencies in Hz
est_time : np.ndarray
    estimate time stamps in seconds
est_freqs : list of np.ndarray
    estimated frequencies in Hz

### Goal
Validates that reference and estimated multi-pitch data structures conform to the expected format and constraints required for multi-pitch evaluation.

### Parameters
- `ref_time`: A 1D NumPy array of reference time stamps in seconds.
- `ref_freqs`: A list of NumPy arrays, where each array contains the reference frequencies (in Hz) corresponding to the respective time stamp in `ref_time`.
- `est_time`: A 1D NumPy array of estimated time stamps in seconds.
- `est_freqs`: A list of NumPy arrays, where each array contains the estimated frequencies (in Hz) corresponding to the respective time stamp in `est_time`.

### Input
- **Data Format:** Time stamps must be provided as 1D `np.ndarray` objects. Frequencies must be provided as a `list` of `np.ndarray` objects (ragged time series).
- **Preconditions:** Time stamps must be sorted in ascending order. The length of the time array must match the length of the corresponding frequency list.
- **Units:** Time must be in seconds; frequencies must be in Hz.

### Output
Returns `None` if the inputs are valid. Raises an exception (e.g., `ValueError` or `TypeError`) if the inputs are malformed or violate structural constraints.

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example of validating multi-pitch data
ref_time = np.array([0.1, 0.2, 0.3])
ref_freqs = [np.array([440.0]), np.array([440.0, 880.0]), np.array([440.0])]
est_time = np.array([0.1, 0.2, 0.3])
est_freqs = [np.array([442.0]), np.array([440.0, 882.0]), np.array([440.0])]

mir_eval.multipitch.validate(ref_time, ref_freqs, est_time, est_freqs)
```

### LLM Instruction Prompt
- When calling `mir_eval.multipitch.validate`, ensure that `ref_time` and `est_time` are 1D NumPy arrays and that `ref_freqs` and `est_freqs` are lists of NumPy arrays.
- Always verify that the length of the time array matches the length of the frequency list before calling this function.
- Ensure all time values are in seconds and frequency values are in Hz.

### Prompt Snippet
```text
mir_eval.multipitch.validate(ref_time, ref_freqs, est_time, est_freqs)
```

### Common Failure Modes
- **Shape Mismatch:** Providing a frequency list that does not have the same length as the corresponding time array.
- **Unsorted Input:** Providing time arrays that are not sorted in ascending order.
- **Incorrect Types:** Passing raw lists instead of `np.ndarray` for time stamps, or failing to wrap frequency arrays in a list.
- **Empty Inputs:** Passing empty arrays or lists, which may trigger validation errors depending on the specific implementation requirements for the evaluation task.

### Fix Code Hint
```python
# Ensure inputs are sorted and correctly typed
ref_time = np.sort(ref_time)
# Ensure frequency list matches time array length
if len(ref_time) != len(ref_freqs):
    raise ValueError("Time and frequency arrays must have the same length.")
mir_eval.multipitch.validate(ref_time, ref_freqs, est_time, est_freqs)
```

## API Test: `python:mir_eval.onset.evaluate`

### Signature
```python
def evaluate(reference_onsets, estimated_onsets, **kwargs)
```
_Source: source/mir_eval/onset.py:101_

_Source doc:_ Compute all metrics for the given reference and estimated annotations.

Examples
--------
>>> reference_onsets = mir_eval.io.load_events('reference.txt')
>>> estimated_onsets = mir_eval.io.load_events('estimated.txt')
>>> scores = mir_eval.onset.evaluate(reference_onsets,
...                                  estimated_onsets)

Parameters
----------
reference_onsets : np.ndarray
    reference onset locations, in seconds
estimated_onsets : np.ndarray
    estimated onset locations, in seconds
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of onset detection performance metrics by comparing estimated onset timestamps against ground-truth reference annotations.

### Parameters
- `reference_onsets`: A 1D `np.ndarray` containing the ground-truth onset timestamps in seconds.
- `estimated_onsets`: A 1D `np.ndarray` containing the estimated onset timestamps in seconds.
- `kwargs`: Optional keyword arguments passed to underlying metric or preprocessing functions (e.g., window tolerances).

### Input
- **Data Format:** Both `reference_onsets` and `estimated_onsets` must be 1D NumPy arrays of floats representing time in seconds.
- **Preconditions:** Arrays should be sorted by time. It is recommended to use `mir_eval.io.load_events` to ensure data is loaded into the correct format.

### Output
Returns `dict` — A dictionary mapping metric names (strings) to their corresponding scalar scores (floats), providing a complete evaluation summary.

### Valid Call Patterns
```python
import mir_eval
reference_onsets = mir_eval.io.load_events('reference.txt')
estimated_onsets = mir_eval.io.load_events('estimated.txt')
scores = mir_eval.onset.evaluate(reference_onsets, estimated_onsets)
```

### LLM Instruction Prompt
- When calling `mir_eval.onset.evaluate`, ensure both input arrays are 1D NumPy arrays containing timestamps in seconds.
- Always use `mir_eval.io.load_events` to prepare inputs from text files to ensure compatibility.
- Do not attempt to pass raw audio or non-timestamp data; the function expects pre-extracted event times.

### Prompt Snippet
```text
# Example of evaluating onset detection
import mir_eval
ref = mir_eval.io.load_events('ref.txt')
est = mir_eval.io.load_events('est.txt')
results = mir_eval.onset.evaluate(ref, est)
```

### Common Failure Modes
- **Unsorted Inputs:** Providing unsorted arrays can lead to incorrect matching logic; ensure arrays are sorted by time.
- **Incorrect Units:** Passing timestamps in samples instead of seconds will result in invalid metric calculations.
- **Empty Arrays:** Passing empty arrays may cause errors in metric computation; validate inputs using `mir_eval.onset.validate` if necessary.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure inputs are sorted
ref = np.sort(reference_onsets)
est = np.sort(estimated_onsets)
scores = mir_eval.onset.evaluate(ref, est)
```

## API Test: `python:mir_eval.onset.f_measure`

### Signature
```python
def f_measure(reference_onsets, estimated_onsets, window=0.05)
```
_Source: source/mir_eval/onset.py:56_

_Source doc:_ Compute the F-measure of correct vs incorrectly predicted onsets.
"Correctness" is determined over a small window.

Examples
--------
>>> reference_onsets = mir_eval.io.load_events('reference.txt')
>>> estimated_onsets = mir_eval.io.load_events('estimated.txt')
>>> F, P, R = mir_eval.onset.f_measure(reference_onsets,
...                                    estimated_onsets)

Parameters
----------
reference_onsets : np.ndarray
    reference onset locations, in seconds
estimated_onsets : np.ndarray
    estimated onset locations, in seconds
window : float
    Window size, in seconds
    (Default value = .05)

Returns
-------
f_measure : float
    2*precision*recall/(precision + recall)
precision : float
    (# true positives)/(# true positives + # false positives)
recall : float
    (# true positives)/(# true positives + # false negatives)

### Goal
Computes the F-measure, precision, and recall for onset detection systems by evaluating the correspondence between reference and estimated onset timestamps within a specified temporal window.

### Parameters
- `reference_onsets`: A 1D `np.ndarray` containing the ground-truth onset timestamps in seconds.
- `estimated_onsets`: A 1D `np.ndarray` containing the estimated onset timestamps in seconds.
- `window`, default `0.05`: The tolerance window in seconds; an estimated onset is considered a true positive if it falls within this distance of a reference onset.

### Input
- **Data Format:** Both `reference_onsets` and `estimated_onsets` must be 1D NumPy arrays of floats representing time in seconds.
- **Preconditions:** Inputs should be sorted by time. Use `mir_eval.io.load_events` to load data from standard text files.

### Output
Returns a tuple of three floats: `(f_measure, precision, recall)`.
- `f_measure`: The harmonic mean of precision and recall.
- `precision`: The ratio of correctly identified onsets to the total number of estimated onsets.
- `recall`: The ratio of correctly identified onsets to the total number of reference onsets.

### Valid Call Patterns
```python
import mir_eval
# Standard usage with default window
f, p, r = mir_eval.onset.f_measure(reference_onsets, estimated_onsets)

# Usage with custom window
f, p, r = mir_eval.onset.f_measure(reference_onsets, estimated_onsets, window=0.025)
```

### LLM Instruction Prompt
- When calling `mir_eval.onset.f_measure`, ensure both input arrays are 1D NumPy arrays containing timestamps in seconds.
- Always return the tuple `(f_measure, precision, recall)` as defined in the signature.
- If the input arrays are not sorted, sort them before passing to the function to ensure correct matching.

### Prompt Snippet
```text
# Example of calling mir_eval.onset.f_measure
f_measure, precision, recall = mir_eval.onset.f_measure(ref_onsets, est_onsets, window=0.05)
```

### Common Failure Modes
- **Unsorted Inputs:** Providing unsorted arrays may lead to incorrect matching logic.
- **Unit Mismatch:** Providing timestamps in milliseconds instead of seconds will result in incorrect evaluation.
- **Empty Arrays:** Passing empty arrays may result in division by zero or undefined behavior; ensure inputs are validated using `mir_eval.onset.validate()` if available.

### Fix Code Hint
```python
import numpy as np
# Ensure inputs are sorted
ref_onsets = np.sort(ref_onsets)
est_onsets = np.sort(est_onsets)
f, p, r = mir_eval.onset.f_measure(ref_onsets, est_onsets, window=0.05)
```

## API Test: `python:mir_eval.onset.validate`

### Signature
```python
def validate(reference_onsets, estimated_onsets)
```
_Source: source/mir_eval/onset.py:35_

_Source doc:_ Check that the input annotations to a metric look like valid onset time
arrays, and throws helpful errors if not.

Parameters
----------
reference_onsets : np.ndarray
    reference onset locations, in seconds
estimated_onsets : np.ndarray
    estimated onset locations, in seconds

### Goal
Validates that the provided reference and estimated onset time arrays conform to the expected format and constraints required for onset evaluation metrics.

### Parameters
- `reference_onsets`: A 1D NumPy array containing the ground-truth onset timestamps in seconds.
- `estimated_onsets`: A 1D NumPy array containing the estimated onset timestamps in seconds.

### Input
- **Data Format:** Both inputs must be 1D `np.ndarray` objects.
- **Preconditions:** Timestamps must be represented in seconds. For most `mir_eval` metrics, these arrays should be sorted by time.
- **Validation:** The function checks that the inputs are valid onset time arrays and raises descriptive errors if the data structures are malformed or incompatible.

### Output
Returns `None` if the validation passes; otherwise, it raises an exception with a descriptive error message.

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example inferred from signature
ref = np.array([0.5, 1.2, 2.0])
est = np.array([0.52, 1.18, 2.05])
mir_eval.onset.validate(ref, est)
```

### LLM Instruction Prompt
- Use `mir_eval.onset.validate` as a pre-computation check before passing arrays to `mir_eval.onset.evaluate`.
- Ensure both `reference_onsets` and `estimated_onsets` are 1D NumPy arrays containing floats representing time in seconds.
- Do not attempt to catch the validation error if the input data is expected to be correct; allow the library to raise its standard exceptions for debugging.

### Prompt Snippet
```text
# Validate onset arrays before evaluation
mir_eval.onset.validate(reference_onsets, estimated_onsets)
scores = mir_eval.onset.evaluate(reference_onsets, estimated_onsets)
```

### Common Failure Modes
- **Dimension Mismatch:** Passing multi-dimensional arrays instead of 1D arrays.
- **Type Errors:** Passing lists or other non-NumPy array types.
- **Unsorted Data:** While `validate` checks structure, many downstream evaluation functions will fail if the arrays are not sorted by time.
- **Missing Units:** Providing timestamps in samples rather than seconds.

### Fix Code Hint
```python
import numpy as np
# Ensure arrays are 1D and sorted
reference_onsets = np.sort(np.array(reference_onsets).flatten())
estimated_onsets = np.sort(np.array(estimated_onsets).flatten())
mir_eval.onset.validate(reference_onsets, estimated_onsets)
```

## API Test: `python:mir_eval.pattern.establishment_FPR`

### Signature
```python
def establishment_FPR(reference_patterns, estimated_patterns, similarity_metric='cardinality_score')
```
_Source: source/mir_eval/pattern.py:238_

_Source doc:_ Compute the establishment F1 Score, Precision and Recall.

Examples
--------
>>> ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
>>> est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
>>> F, P, R = mir_eval.pattern.establishment_FPR(ref_patterns,
...                                              est_patterns)

Parameters
----------
reference_patterns : list
    The reference patterns in the format returned by
    :func:`mir_eval.io.load_patterns()`

estimated_patterns : list
    The estimated patterns in the same format

similarity_metric : str
    A string representing the metric to be used when computing the
    similarity matrix. Accepted values:

        - "cardinality_score": Count of the intersection
          between occurrences.

    (Default value = "cardinality_score")

Returns
-------
f_measure : float
    The establishment F1 Score
precision : float
    The establishment Precision
recall : float
    The establishment Recall

### Goal
Computes the establishment F1-measure, precision, and recall for pattern discovery evaluation by comparing reference and estimated pattern sets.

### Parameters
- `reference_patterns`: A list of patterns representing the ground truth, structured as returned by `mir_eval.io.load_patterns`.
- `estimated_patterns`: A list of patterns representing the system output, structured as returned by `mir_eval.io.load_patterns`.
- `similarity_metric`, default `'cardinality_score'`: The method used to compute the similarity matrix between patterns; currently supports `"cardinality_score"` (intersection count).

### Input
- **Format:** Requires data in the MIREX 2013 pattern format (a list of lists of tuples).
- **Preconditions:** Both `reference_patterns` and `estimated_patterns` must be loaded using `mir_eval.io.load_patterns` to ensure they conform to the expected internal structure.

### Output
Returns a tuple of three floats: `(f_measure, precision, recall)`, representing the establishment performance metrics.

### Valid Call Patterns
```python
import mir_eval
ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
f_measure, precision, recall = mir_eval.pattern.establishment_FPR(ref_patterns, est_patterns)
```

### LLM Instruction Prompt
- When calling `mir_eval.pattern.establishment_FPR`, ensure that both pattern inputs are loaded via `mir_eval.io.load_patterns` first.
- The function returns three distinct float values; ensure the caller unpacks them into `f_measure`, `precision`, and `recall` variables.

### Prompt Snippet
```text
# Example of calling establishment_FPR
f, p, r = mir_eval.pattern.establishment_FPR(ref_data, est_data)
```

### Common Failure Modes
- **Format Mismatch:** Passing raw lists or incorrectly structured data that does not match the MIREX 2013 format expected by `load_patterns`.
- **Empty Inputs:** Passing empty lists for either `reference_patterns` or `estimated_patterns` may lead to undefined behavior or division by zero in metric calculation.

### Fix Code Hint
```python
# Ensure data is loaded correctly before evaluation
import mir_eval
ref = mir_eval.io.load_patterns("ground_truth.txt")
est = mir_eval.io.load_patterns("system_output.txt")
f, p, r = mir_eval.pattern.establishment_FPR(ref, est)
```

## API Test: `python:mir_eval.pattern.evaluate`

### Signature
```python
def evaluate(ref_patterns, est_patterns, **kwargs)
```
_Source: source/mir_eval/pattern.py:597_

_Source doc:_ Load data and perform the evaluation.

Examples
--------
>>> ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
>>> est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
>>> scores = mir_eval.pattern.evaluate(ref_patterns, est_patterns)

Parameters
----------
ref_patterns : list
    The reference patterns in the format returned by
    :func:`mir_eval.io.load_patterns()`
est_patterns : list
    The estimated patterns in the same format
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of pattern discovery evaluation metrics by comparing reference patterns against estimated patterns.

### Parameters
- `ref_patterns`: A list of patterns representing the ground truth, structured as a list of lists of tuples (MIREX 2013 format).
- `est_patterns`: A list of patterns representing the system output, following the same structure as `ref_patterns`.
- `kwargs`: Optional keyword arguments passed directly to underlying metric or preprocessing functions.

### Input
- **Data Format:** Patterns must be loaded using `mir_eval.io.load_patterns`, which expects the MIREX 2013 format (list of lists of tuples).
- **Preconditions:** Inputs must be validated to ensure they conform to the expected list-of-lists-of-tuples structure before evaluation.

### Output
Returns `dict` — A dictionary where keys are metric names (strings) and values are the corresponding floating-point scores.

### Valid Call Patterns
```python
ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
scores = mir_eval.pattern.evaluate(ref_patterns, est_patterns)
```

### LLM Instruction Prompt
- Always use `mir_eval.io.load_patterns` to prepare inputs before calling `evaluate`.
- Ensure that both `ref_patterns` and `est_patterns` are passed as lists of lists of tuples.
- Do not attempt to pass raw file paths directly to `evaluate`; it expects the loaded data structures.

### Prompt Snippet
```text
# Load patterns and evaluate
ref = mir_eval.io.load_patterns(ref_path)
est = mir_eval.io.load_patterns(est_path)
scores = mir_eval.pattern.evaluate(ref, est)
```

### Common Failure Modes
- **Format Mismatch:** Passing data that is not in the MIREX 2013 list-of-lists-of-tuples format will cause the evaluation to fail or produce incorrect results.
- **Missing IO:** Attempting to pass file paths directly instead of the output of `mir_eval.io.load_patterns`.
- **Empty Inputs:** Providing empty lists may result in undefined behavior or empty score dictionaries depending on the specific metric implementation.

### Fix Code Hint
```python
# Ensure data is loaded correctly before evaluation
import mir_eval
ref_patterns = mir_eval.io.load_patterns("ground_truth.txt")
est_patterns = mir_eval.io.load_patterns("system_output.txt")
scores = mir_eval.pattern.evaluate(ref_patterns, est_patterns)
```

## API Test: `python:mir_eval.pattern.first_n_target_proportion_R`

### Signature
```python
def first_n_target_proportion_R(reference_patterns, estimated_patterns, n=5)
```
_Source: source/mir_eval/pattern.py:554_

_Source doc:_ First n target proportion establishment recall metric.

This metric is similar is similar to the establishment FPR score, but it
only takes into account the first n estimated patterns and it only
outputs the Recall value of it.

Examples
--------
>>> ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
>>> est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
>>> R = mir_eval.pattern.first_n_target_proportion_R(
...                                 ref_patterns, est_patterns, n=5)

Parameters
----------
reference_patterns : list
    The reference patterns in the format returned by
    :func:`mir_eval.io.load_patterns()`
estimated_patterns : list
    The estimated patterns in the same format
n : int
    Number of patterns to consider from the estimated results, in
    the order they appear in the matrix.
    (Default value = 5)

Returns
-------
recall : float
    The first n target proportion Recall.

### Goal
Computes the recall of the "first n target proportion" metric for pattern discovery, evaluating how well the top-n estimated patterns cover the reference patterns.

### Parameters
- `reference_patterns`: A list of patterns representing the ground truth, formatted as returned by `mir_eval.io.load_patterns`.
- `estimated_patterns`: A list of patterns representing the system output, formatted as returned by `mir_eval.io.load_patterns`.
- `n`, default `5`: The number of patterns to consider from the `estimated_patterns` list, ordered by their appearance in the input matrix.

### Input
- **Format:** Both `reference_patterns` and `estimated_patterns` must be in the MIREX 2013 pattern format (a list of lists of tuples).
- **Preconditions:** Inputs should be loaded using `mir_eval.io.load_patterns`. The metric assumes the patterns are ordered as they appear in the source data.

### Output
Returns `recall` (float): The calculated recall value representing the proportion of reference patterns established by the first `n` estimated patterns.

### Valid Call Patterns
```python
import mir_eval
ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
R = mir_eval.pattern.first_n_target_proportion_R(ref_patterns, est_patterns, n=5)
```

### LLM Instruction Prompt
- When calling `mir_eval.pattern.first_n_target_proportion_R`, ensure that both pattern arguments are lists derived from `mir_eval.io.load_patterns`.
- The `n` parameter is an integer; if not provided, it defaults to 5.
- Ensure the environment has `numpy` and `scipy` installed, as these are required for `mir_eval` operations.

### Prompt Snippet
```text
# Example usage of first_n_target_proportion_R
recall = mir_eval.pattern.first_n_target_proportion_R(ref_data, est_data, n=10)
```

### Common Failure Modes
- **Format Mismatch:** Passing raw lists or incorrectly structured data that does not match the MIREX 2013 pattern format expected by `load_patterns`.
- **Empty Inputs:** Passing empty lists for `reference_patterns` or `estimated_patterns` may lead to undefined behavior or division by zero errors during recall calculation.
- **Index Out of Bounds:** Providing an `n` larger than the number of available estimated patterns may cause unexpected behavior depending on the internal implementation of the pattern list slicing.

### Fix Code Hint
```python
# Ensure patterns are loaded correctly before evaluation
import mir_eval
try:
    ref = mir_eval.io.load_patterns("ref.txt")
    est = mir_eval.io.load_patterns("est.txt")
    score = mir_eval.pattern.first_n_target_proportion_R(ref, est, n=5)
except Exception as e:
    print(f"Evaluation failed: {e}")
```

## API Test: `python:mir_eval.pattern.first_n_three_layer_P`

### Signature
```python
def first_n_three_layer_P(reference_patterns, estimated_patterns, n=5)
```
_Source: source/mir_eval/pattern.py:509_

_Source doc:_ First n three-layer precision.

This metric is basically the same as the three-layer FPR but it is only
applied to the first n estimated patterns, and it only returns the
precision. In MIREX and typically, n = 5.

Examples
--------
>>> ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
>>> est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
>>> P = mir_eval.pattern.first_n_three_layer_P(ref_patterns,
...                                            est_patterns, n=5)

Parameters
----------
reference_patterns : list
    The reference patterns in the format returned by
    :func:`mir_eval.io.load_patterns()`
estimated_patterns : list
    The estimated patterns in the same format
n : int
    Number of patterns to consider from the estimated results, in
    the order they appear in the matrix
    (Default value = 5)

Returns
-------
precision : float
    The first n three-layer Precision

### Goal
Computes the precision of the first `n` estimated patterns by comparing them against reference patterns using a three-layer evaluation approach.

### Parameters
- `reference_patterns`: A list of patterns representing the ground truth, formatted as returned by `mir_eval.io.load_patterns()`.
- `estimated_patterns`: A list of patterns representing the system output, formatted as returned by `mir_eval.io.load_patterns()`.
- `n`, default `5`: The number of patterns to evaluate from the beginning of the `estimated_patterns` list.

### Input
- **Format:** Both `reference_patterns` and `estimated_patterns` must be in the MIREX 2013 pattern format (a list of lists of tuples).
- **Preconditions:** The patterns should be loaded using `mir_eval.io.load_patterns()`. The metric considers the order of patterns as they appear in the input lists.

### Output
- Returns a `float` representing the precision score calculated over the first `n` estimated patterns.

### Valid Call Patterns
```python
import mir_eval
ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
P = mir_eval.pattern.first_n_three_layer_P(ref_patterns, est_patterns, n=5)
```

### LLM Instruction Prompt
- When calling `mir_eval.pattern.first_n_three_layer_P`, ensure that both `reference_patterns` and `estimated_patterns` are loaded via `mir_eval.io.load_patterns()` to guarantee the correct list-of-lists-of-tuples structure.
- The `n` parameter is an integer; if not provided, it defaults to 5.

### Prompt Snippet
```text
# Example usage of first_n_three_layer_P
precision = mir_eval.pattern.first_n_three_layer_P(ref_data, est_data, n=5)
```

### Common Failure Modes
- **Format Mismatch:** Passing raw arrays or incorrectly formatted lists that do not match the MIREX 2013 pattern structure expected by `load_patterns()`.
- **Index Errors:** Providing an `n` larger than the number of patterns available in `estimated_patterns` may lead to unexpected behavior or errors depending on the internal implementation of the pattern slicing.
- **Empty Inputs:** Passing empty lists for either reference or estimated patterns may result in undefined precision values.

### Fix Code Hint
```python
# Ensure patterns are loaded correctly before evaluation
import mir_eval
try:
    ref = mir_eval.io.load_patterns("ref.txt")
    est = mir_eval.io.load_patterns("est.txt")
    score = mir_eval.pattern.first_n_three_layer_P(ref, est, n=5)
except Exception as e:
    print(f"Evaluation failed: {e}")
```

## API Test: `python:mir_eval.pattern.occurrence_FPR`

### Signature
```python
def occurrence_FPR(reference_patterns, estimated_patterns, thres=0.75, similarity_metric='cardinality_score')
```
_Source: source/mir_eval/pattern.py:299_

_Source doc:_ Compute the occurrence F1 Score, Precision and Recall.

Examples
--------
>>> ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
>>> est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
>>> F, P, R = mir_eval.pattern.occurrence_FPR(ref_patterns,
...                                           est_patterns)

Parameters
----------
reference_patterns : list
    The reference patterns in the format returned by
    :func:`mir_eval.io.load_patterns()`

estimated_patterns : list
    The estimated patterns in the same format

thres : float
    How similar two occurrences must be in order to be considered
    equal
    (Default value = .75)

similarity_metric : str
    A string representing the metric to be used
    when computing the similarity matrix. Accepted values:

        - "cardinality_score": Count of the intersection
          between occurrences.

    (Default value = "cardinality_score")

Returns
-------
f_measure : float
    The occurrence F1 Score
precision : float
    The occurrence Precision
recall : float
    The occurrence Recall

### Goal
Computes the occurrence-based F1 score, precision, and recall for pattern discovery evaluation by comparing estimated patterns against ground-truth reference patterns.

### Parameters
- `reference_patterns`: A list of patterns (typically in MIREX 2013 format) representing the ground truth.
- `estimated_patterns`: A list of patterns in the same format as the reference, representing the system output.
- `thres`, default `0.75`: A float defining the similarity threshold required for two occurrences to be considered a match.
- `similarity_metric`, default `'cardinality_score'`: The method used to compute the similarity matrix; currently supports `"cardinality_score"` (intersection count).

### Input
The function expects `reference_patterns` and `estimated_patterns` to be provided as lists of lists of tuples, consistent with the format returned by `mir_eval.io.load_patterns()`.

### Output
Returns a tuple of three floats: `(f_measure, precision, recall)`, representing the occurrence-based evaluation metrics.

### Valid Call Patterns
```python
ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
F, P, R = mir_eval.pattern.occurrence_FPR(ref_patterns, est_patterns)
```

### LLM Instruction Prompt
When calling `mir_eval.pattern.occurrence_FPR`, ensure that both `reference_patterns` and `estimated_patterns` have been loaded using `mir_eval.io.load_patterns()` to guarantee the correct list-of-lists-of-tuples structure. The `thres` parameter should be a float between 0 and 1.

### Prompt Snippet
```text
# Example usage of occurrence_FPR
f_score, precision, recall = mir_eval.pattern.occurrence_FPR(ref_data, est_data, thres=0.8)
```

### Common Failure Modes
- **Format Mismatch:** Passing raw arrays or incorrectly structured lists that do not match the MIREX 2013 pattern format expected by `load_patterns`.
- **Threshold Sensitivity:** Setting `thres` too high or too low may result in zero matches, leading to undefined or zero-valued precision/recall scores.
- **Empty Inputs:** Providing empty lists for either reference or estimated patterns may cause errors or return zeroed metrics.

### Fix Code Hint
```python
# Ensure patterns are loaded correctly before evaluation
import mir_eval
ref = mir_eval.io.load_patterns("ref.txt")
est = mir_eval.io.load_patterns("est.txt")
f, p, r = mir_eval.pattern.occurrence_FPR(ref, est, thres=0.75)
```

## API Test: `python:mir_eval.pattern.standard_FPR`

### Signature
```python
def standard_FPR(reference_patterns, estimated_patterns, tol=1e-05)
```
_Source: source/mir_eval/pattern.py:171_

_Source doc:_ Compute the standard F1 Score, Precision and Recall.

This metric checks if the prototype patterns of the reference match
possible translated patterns in the prototype patterns of the estimations.
Since the sizes of these prototypes must be equal, this metric is quite
restrictive and it tends to be 0 in most of 2013 MIREX results.

Examples
--------
>>> ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
>>> est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
>>> F, P, R = mir_eval.pattern.standard_FPR(ref_patterns, est_patterns)

Parameters
----------
reference_patterns : list
    The reference patterns using the format returned by
    :func:`mir_eval.io.load_patterns()`
estimated_patterns : list
    The estimated patterns in the same format
tol : float
    Tolerance level when comparing reference against estimation.
    Default parameter is the one found in the original matlab code by
    Tom Collins used for MIREX 2013.
    (Default value = 1e-5)

Returns
-------
f_measure : float
    The standard F1 Score
precision : float
    The standard Precision
recall : float
    The standard Recall

### Goal
Computes the standard F1-measure, precision, and recall for pattern discovery by comparing prototype patterns in reference and estimated datasets.

### Parameters
- `reference_patterns`: A list of patterns (typically loaded via `mir_eval.io.load_patterns`) representing the ground truth.
- `estimated_patterns`: A list of patterns (typically loaded via `mir_eval.io.load_patterns`) representing the system output.
- `tol`, default `1e-05`: A float representing the tolerance level used for comparing reference patterns against estimated patterns.

### Input
- **Format:** Requires data in the MIREX 2013 pattern format (a list of lists of tuples).
- **Preconditions:** The prototype patterns in the reference and estimated sets must have equal sizes for the comparison to be valid.

### Output
Returns a tuple of three floats: `(f_measure, precision, recall)`.

### Valid Call Patterns
```python
ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
F, P, R = mir_eval.pattern.standard_FPR(ref_patterns, est_patterns)
```

### LLM Instruction Prompt
- When calling `mir_eval.pattern.standard_FPR`, ensure that both `reference_patterns` and `estimated_patterns` are loaded using `mir_eval.io.load_patterns` to ensure the correct list-of-lists-of-tuples structure.
- Note that this metric is highly restrictive; if the prototype sizes do not match, the function may return zero or fail to produce meaningful results.

### Prompt Snippet
```text
# Example usage of standard_FPR
import mir_eval
ref = mir_eval.io.load_patterns('ref.txt')
est = mir_eval.io.load_patterns('est.txt')
f, p, r = mir_eval.pattern.standard_FPR(ref, est)
```

### Common Failure Modes
- **Size Mismatch:** The metric is highly restrictive; if the number of prototype patterns or their internal sizes differ between reference and estimation, the score will likely be 0.
- **Format Errors:** Passing raw arrays or incorrectly formatted lists instead of the output of `mir_eval.io.load_patterns` will cause runtime errors.

### Fix Code Hint
```python
# Ensure patterns are loaded correctly before evaluation
try:
    ref = mir_eval.io.load_patterns(ref_path)
    est = mir_eval.io.load_patterns(est_path)
    f, p, r = mir_eval.pattern.standard_FPR(ref, est)
except Exception as e:
    print(f"Evaluation failed: {e}")
```

## API Test: `python:mir_eval.pattern.three_layer_FPR`

### Signature
```python
def three_layer_FPR(reference_patterns, estimated_patterns)
```
_Source: source/mir_eval/pattern.py:382_

_Source doc:_ Three Layer F1 Score, Precision and Recall. As described by Meridith.

Examples
--------
>>> ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
>>> est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
>>> F, P, R = mir_eval.pattern.three_layer_FPR(ref_patterns,
...                                            est_patterns)

Parameters
----------
reference_patterns : list
    The reference patterns in the format returned by
    :func:`mir_eval.io.load_patterns()`
estimated_patterns : list
    The estimated patterns in the same format

Returns
-------
f_measure : float
    The three-layer F1 Score
precision : float
    The three-layer Precision
recall : float
    The three-layer Recall

### Goal
Computes the three-layer F1 score, precision, and recall for pattern discovery evaluation as described by Meridith.

### Parameters
- `reference_patterns`: A list of patterns representing the ground truth, formatted as returned by `mir_eval.io.load_patterns()`.
- `estimated_patterns`: A list of patterns representing the system output, formatted as returned by `mir_eval.io.load_patterns()`.

### Input
- **Format:** Both inputs must be lists of patterns in the MIREX 2013 format (list of lists of tuples).
- **Preconditions:** Ensure that the patterns are loaded correctly using `mir_eval.io.load_patterns()` before passing them to this function.

### Output
Returns a tuple of three floats: `(f_measure, precision, recall)`, representing the three-layer evaluation metrics.

### Valid Call Patterns
```python
ref_patterns = mir_eval.io.load_patterns("ref_pattern.txt")
est_patterns = mir_eval.io.load_patterns("est_pattern.txt")
F, P, R = mir_eval.pattern.three_layer_FPR(ref_patterns, est_patterns)
```

### LLM Instruction Prompt
- When evaluating pattern discovery, always use `mir_eval.io.load_patterns()` to prepare the input lists.
- Ensure the reference and estimated patterns are provided as the first and second arguments respectively.
- The function returns three distinct float values; ensure your implementation unpacks these into `f_measure`, `precision`, and `recall`.

### Prompt Snippet
```text
# Example usage of three_layer_FPR
ref_patterns = mir_eval.io.load_patterns("ref.txt")
est_patterns = mir_eval.io.load_patterns("est.txt")
f_measure, precision, recall = mir_eval.pattern.three_layer_FPR(ref_patterns, est_patterns)
```

### Common Failure Modes
- **Format Mismatch:** Passing data that does not conform to the MIREX 2013 pattern format (list of lists of tuples) will cause errors.
- **Empty Inputs:** Providing empty lists may result in undefined or zero-value metrics depending on the internal implementation of the three-layer logic.

### Fix Code Hint
```python
# Ensure patterns are loaded via the correct I/O utility
import mir_eval
ref = mir_eval.io.load_patterns("ground_truth.txt")
est = mir_eval.io.load_patterns("system_output.txt")
f, p, r = mir_eval.pattern.three_layer_FPR(ref, est)
```

## API Test: `python:mir_eval.pattern.validate`

### Signature
```python
def validate(reference_patterns, estimated_patterns)
```
_Source: source/mir_eval/pattern.py:81_

_Source doc:_ Check that the input annotations to a metric look like valid pattern
lists, and throws helpful errors if not.

Parameters
----------
reference_patterns : list
    The reference patterns using the format returned by
    :func:`mir_eval.io.load_patterns()`
estimated_patterns : list
    The estimated patterns in the same format

### Goal
Validates that the provided reference and estimated pattern lists conform to the expected structure required for pattern evaluation metrics.

### Parameters
- `reference_patterns`: A list of patterns representing the ground truth, formatted as returned by `mir_eval.io.load_patterns()`.
- `estimated_patterns`: A list of patterns representing the system output, expected to be in the same format as the reference patterns.

### Input
- **Format:** The input must follow the MIREX 2013 pattern format, which is a list of lists of tuples.
- **Preconditions:** The data should be loaded using `mir_eval.io.load_patterns()` to ensure compatibility with the expected internal structure.

### Output
Returns `None` if the validation passes. If the inputs do not conform to the expected structure, the function raises an exception with a descriptive error message.

### Valid Call Patterns
```python
import mir_eval

# Example inferred from signature and documentation
ref_patterns = mir_eval.io.load_patterns('reference.txt')
est_patterns = mir_eval.io.load_patterns('estimated.txt')
mir_eval.pattern.validate(ref_patterns, est_patterns)
```

### LLM Instruction Prompt
- Always call `mir_eval.pattern.validate` before passing pattern data to evaluation functions to ensure data integrity.
- Ensure that both `reference_patterns` and `estimated_patterns` are loaded using `mir_eval.io.load_patterns()` prior to validation.

### Prompt Snippet
```text
# Validate patterns before evaluation
mir_eval.pattern.validate(reference_patterns, estimated_patterns)
```

### Common Failure Modes
- **Format Mismatch:** Passing data that is not a list of lists of tuples (e.g., raw arrays or incorrectly parsed text) will trigger a validation error.
- **Empty Inputs:** Providing empty lists or `None` types may cause the validator to raise an error if the underlying structure is not satisfied.

### Fix Code Hint
```python
# Ensure data is loaded correctly before validation
try:
    mir_eval.pattern.validate(ref, est)
except Exception as e:
    print(f"Validation failed: {e}")
```

## API Test: `python:mir_eval.segment.ari`

### Signature
```python
def ari(reference_intervals, reference_labels, estimated_intervals, estimated_labels, frame_size=0.1)
```
_Source: source/mir_eval/segment.py:589_

_Source doc:_ Compute the Adjusted Rand Index (ARI) for frame clustering segmentation evaluation.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> # Trim or pad the estimate to match reference timing
>>> (ref_intervals,
...  ref_labels) = mir_eval.util.adjust_intervals(ref_intervals,
...                                               ref_labels,
...                                               t_min=0)
>>> (est_intervals,
...  est_labels) = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
>>> ari_score = mir_eval.structure.ari(ref_intervals, ref_labels,
...                                    est_intervals, est_labels)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2)
    reference segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
reference_labels : list, shape=(n,)
    reference segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_intervals : np.ndarray, shape=(m, 2)
    estimated segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_labels : list, shape=(m,)
    estimated segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
frame_size : float > 0
    length (in seconds) of frames for clustering
    (Default value = 0.1)

Returns
-------
ari_score : float > 0
    Adjusted Rand index between segmentations.

### Goal
Computes the Adjusted Rand Index (ARI) to evaluate the similarity between a reference segmentation and an estimated segmentation by clustering the audio into frames.

### Parameters
- `reference_intervals`: An $N \times 2$ NumPy array of start and end times (in seconds) for the ground-truth segments.
- `reference_labels`: A list of $N$ labels corresponding to the ground-truth segments.
- `estimated_intervals`: An $M \times 2$ NumPy array of start and end times (in seconds) for the estimated segments.
- `estimated_labels`: A list of $M$ labels corresponding to the estimated segments.
- `frame_size`, default `0.1`: The duration in seconds used to discretize the timeline into frames for clustering comparison.

### Input
- **Data Format:** Intervals must be provided as $N \times 2$ NumPy arrays and labels as lists of length $N$.
- **Preconditions:** Inputs must be sorted by time. Before calling, use `mir_eval.util.adjust_intervals` to ensure the estimated intervals span the same total duration as the reference intervals.

### Output
Returns a `float` representing the Adjusted Rand Index, which quantifies the agreement between the two segmentations, adjusted for chance.

### Valid Call Patterns
```python
ari_score = mir_eval.segment.ari(ref_intervals, ref_labels, est_intervals, est_labels, frame_size=0.1)
```

### LLM Instruction Prompt
- Always ensure `estimated_intervals` and `reference_intervals` are aligned using `mir_eval.util.adjust_intervals` before passing them to this function.
- Ensure `frame_size` is a positive float.
- The function expects the reference and estimated data to be in the format produced by `mir_eval.io.load_labeled_intervals`.

### Prompt Snippet
```text
# Ensure intervals are adjusted to match reference duration
est_intervals, est_labels = mir_eval.util.adjust_intervals(est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
ari_score = mir_eval.segment.ari(ref_intervals, ref_labels, est_intervals, est_labels)
```

### Common Failure Modes
- **Mismatched Durations:** Failing to adjust the estimated intervals to match the reference duration will lead to errors or invalid clustering results.
- **Unsorted Intervals:** Providing intervals that are not sorted by start time will cause incorrect segmentation evaluation.
- **Invalid Frame Size:** Providing a non-positive `frame_size` will raise a value error.

### Fix Code Hint
```python
# Use adjust_intervals to fix duration mismatches
est_intervals, est_labels = mir_eval.util.adjust_intervals(est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
```

## API Test: `python:mir_eval.segment.detection`

### Signature
```python
def detection(reference_intervals, estimated_intervals, window=0.5, beta=1.0, trim=False)
```
_Source: source/mir_eval/segment.py:168_

_Source doc:_ Boundary detection hit-rate.

A hit is counted whenever an reference boundary is within ``window`` of a
estimated boundary.  Note that each boundary is matched at most once: this
is achieved by computing the size of a maximal matching between reference
and estimated boundary points, subject to the window constraint.

Examples
--------
>>> ref_intervals, _ = mir_eval.io.load_labeled_intervals('ref.lab')
>>> est_intervals, _ = mir_eval.io.load_labeled_intervals('est.lab')
>>> # With 0.5s windowing
>>> P05, R05, F05 = mir_eval.segment.detection(ref_intervals,
...                                            est_intervals,
...                                            window=0.5)
>>> # With 3s windowing
>>> P3, R3, F3 = mir_eval.segment.detection(ref_intervals,
...                                         est_intervals,
...                                         window=3)
>>> # Ignoring hits for the beginning and end of track
>>> P, R, F = mir_eval.segment.detection(ref_intervals,
...                                      est_intervals,
...                                      window=0.5,
...                                      trim=True)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2)
    reference segment intervals, in the format returned by
    :func:`mir_eval.io.load_intervals` or
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_intervals : np.ndarray, shape=(m, 2)
    estimated segment intervals, in the format returned by
    :func:`mir_eval.io.load_intervals` or
    :func:`mir_eval.io.load_labeled_intervals`.
window : float > 0
    size of the window of 'correctness' around ground-truth beats
    (in seconds)
    (Default value = 0.5)
beta : float > 0
    weighting constant for F-measure.
    (Default value = 1.0)
trim : boolean
    if ``True``, the first and last boundary times are ignored.
    Typically, these denote start (0) and end-markers.
    (Default value = False)

Returns
-------
precision : float
    precision of estimated predictions
recall : float
    recall of reference reference boundaries
f_measure : float
    F-measure (weighted harmonic mean of ``precision`` and ``recall``)

### Goal
Computes the boundary detection hit-rate for music segmentation by calculating the precision, recall, and F-measure of estimated segment boundaries relative to ground-truth intervals.

### Parameters
- `reference_intervals`: An $N \times 2$ NumPy array of ground-truth segment start and end times in seconds.
- `estimated_intervals`: An $M \times 2$ NumPy array of estimated segment start and end times in seconds.
- `window`, default `0.5`: The tolerance threshold in seconds; a boundary is considered a hit if it falls within this distance of a reference boundary.
- `beta`, default `1.0`: The weighting constant for the F-measure calculation.
- `trim`, default `False`: If `True`, ignores the first and last boundaries, which typically represent the start and end of the audio track.

### Input
- **Data Format:** Requires NumPy arrays of shape `(n, 2)` representing intervals.
- **Preconditions:** Intervals must be sorted by time. Use `mir_eval.io` loaders to ensure compatibility.
- **Units:** All time values must be in seconds.

### Output
Returns a tuple of three floats: `(precision, recall, f_measure)`.

### Valid Call Patterns
```python
# Standard usage with default parameters
precision, recall, f_measure = mir_eval.segment.detection(ref_intervals, est_intervals)

# Usage with custom window and trim enabled
precision, recall, f_measure = mir_eval.segment.detection(ref_intervals, est_intervals, window=0.5, trim=True)
```

### LLM Instruction Prompt
- Always ensure `reference_intervals` and `estimated_intervals` are NumPy arrays of shape `(n, 2)`.
- Ensure time values are in seconds.
- If the task involves evaluating segment boundaries, use `trim=True` if the start and end markers of the track should be excluded from the hit-rate calculation.

### Prompt Snippet
```text
# Example of segment detection evaluation
precision, recall, f_measure = mir_eval.segment.detection(ref_intervals, est_intervals, window=0.5, trim=True)
```

### Common Failure Modes
- **Shape Mismatch:** Passing 1D arrays instead of $N \times 2$ interval arrays.
- **Unsorted Intervals:** Providing intervals that are not sorted by start time, which may lead to incorrect matching.
- **Units:** Providing time in samples instead of seconds.

### Fix Code Hint
```python
# Ensure intervals are sorted by start time before evaluation
ref_intervals = ref_intervals[ref_intervals[:, 0].argsort()]
est_intervals = est_intervals[est_intervals[:, 0].argsort()]
precision, recall, f_measure = mir_eval.segment.detection(ref_intervals, est_intervals)
```

## API Test: `python:mir_eval.segment.deviation`

### Signature
```python
def deviation(reference_intervals, estimated_intervals, trim=False)
```
_Source: source/mir_eval/segment.py:252_

_Source doc:_ Compute the median deviations between reference
and estimated boundary times.

Examples
--------
>>> ref_intervals, _ = mir_eval.io.load_labeled_intervals('ref.lab')
>>> est_intervals, _ = mir_eval.io.load_labeled_intervals('est.lab')
>>> r_to_e, e_to_r = mir_eval.boundary.deviation(ref_intervals,
...                                              est_intervals)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2)
    reference segment intervals, in the format returned by
    :func:`mir_eval.io.load_intervals` or
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_intervals : np.ndarray, shape=(m, 2)
    estimated segment intervals, in the format returned by
    :func:`mir_eval.io.load_intervals` or
    :func:`mir_eval.io.load_labeled_intervals`.
trim : boolean
    if ``True``, the first and last intervals are ignored.
    Typically, these denote start (0.0) and end-of-track markers.
    (Default value = False)

Returns
-------
reference_to_estimated : float
    median time from each reference boundary to the
    closest estimated boundary
estimated_to_reference : float
    median time from each estimated boundary to the
    closest reference boundary

### Goal
Computes the median temporal deviation between reference and estimated segment boundaries to quantify the precision of boundary detection in music segmentation tasks.

### Parameters
- `reference_intervals`: A NumPy array of shape `(n, 2)` containing ground-truth segment start and end times in seconds.
- `estimated_intervals`: A NumPy array of shape `(m, 2)` containing estimated segment start and end times in seconds.
- `trim`, default `False`: If `True`, ignores the first and last intervals, which are typically used to represent track start (0.0) and end markers.

### Input
- **Data Format:** Must be `np.ndarray` of shape `(N, 2)` representing `[start, end]` intervals.
- **Preconditions:** Intervals must be sorted by time. It is recommended to use `mir_eval.util.adjust_intervals` to ensure estimated intervals span the same duration as reference intervals before evaluation.

### Output
Returns a tuple of two floats: `(reference_to_estimated, estimated_to_reference)`, representing the median time (in seconds) from each reference boundary to the closest estimated boundary, and vice versa.

### Valid Call Patterns
```python
# Standard usage with loaded intervals
r_to_e, e_to_r = mir_eval.segment.deviation(ref_intervals, est_intervals)

# Usage with trim enabled to ignore start/end markers
r_to_e, e_to_r = mir_eval.segment.deviation(ref_intervals, est_intervals, trim=True)
```

### LLM Instruction Prompt
- Always ensure `reference_intervals` and `estimated_intervals` are `np.ndarray` objects of shape `(N, 2)`.
- Time values must be in seconds.
- If the input data contains track-start/end markers, set `trim=True` to avoid skewing the median deviation calculation.

### Prompt Snippet
```text
# Example of computing segment deviation
ref_intervals, _ = mir_eval.io.load_labeled_intervals('ref.lab')
est_intervals, _ = mir_eval.io.load_labeled_intervals('est.lab')
r_to_e, e_to_r = mir_eval.segment.deviation(ref_intervals, est_intervals, trim=True)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays that are not `(N, 2)` will cause errors in the underlying interval processing.
- **Unsorted Intervals:** If intervals are not sorted by time, the deviation calculation may produce incorrect results.
- **Empty Arrays:** Passing empty arrays may result in `NaN` or errors during median calculation.

### Fix Code Hint
```python
# Ensure intervals are sorted and valid before calling
import numpy as np
ref_intervals = ref_intervals[ref_intervals[:, 0].argsort()]
est_intervals = est_intervals[est_intervals[:, 0].argsort()]
r_to_e, e_to_r = mir_eval.segment.deviation(ref_intervals, est_intervals)
```

## API Test: `python:mir_eval.segment.evaluate`

### Signature
```python
def evaluate(ref_intervals, ref_labels, est_intervals, est_labels, **kwargs)
```
_Source: source/mir_eval/segment.py:1181_

_Source doc:_ Compute all metrics for the given reference and estimated annotations.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> scores = mir_eval.segment.evaluate(ref_intervals, ref_labels,
...                                    est_intervals, est_labels)

Parameters
----------
ref_intervals : np.ndarray, shape=(n, 2)
    reference segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
ref_labels : list, shape=(n,)
    reference segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
est_intervals : np.ndarray, shape=(m, 2)
    estimated segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
est_labels : list, shape=(m,)
    estimated segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of evaluation metrics for music segmentation tasks by comparing estimated segment boundaries and labels against ground-truth reference annotations.

### Parameters
- `ref_intervals`: A NumPy array of shape `(n, 2)` containing the start and end times (in seconds) of reference segments.
- `ref_labels`: A list of length `n` containing the string labels corresponding to each reference interval.
- `est_intervals`: A NumPy array of shape `(m, 2)` containing the start and end times (in seconds) of estimated segments.
- `est_labels`: A list of length `m` containing the string labels corresponding to each estimated interval.
- `kwargs`: Optional keyword arguments passed to underlying metric functions (e.g., tolerance thresholds for boundary matching).

### Input
- **Data Format:** Intervals must be provided as `(n, 2)` NumPy arrays where each row is `[start, end]`. Labels must be provided as lists of strings.
- **Preconditions:** Reference and estimated intervals should be sorted by start time. It is recommended to use `mir_eval.util.adjust_intervals` to ensure estimated intervals span the same total duration as reference intervals before evaluation.
- **Time Units:** All time-based inputs must be in seconds.

### Output
Returns a `dict` where keys are metric names (e.g., 'Precision', 'Recall', 'F-measure') and values are `float` scores representing the performance of the segmentation system.

### Valid Call Patterns
```python
(ref_intervals, ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
(est_intervals, est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
scores = mir_eval.segment.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
```

### LLM Instruction Prompt
- Always ensure that `ref_intervals` and `est_intervals` are loaded using `mir_eval.io.load_labeled_intervals` or equivalent structures before passing them to this function.
- Ensure that the number of intervals matches the number of labels for both reference and estimation sets.
- Use this function as the primary entry point for batch metric calculation in segmentation tasks.

### Prompt Snippet
```text
# Example of segment evaluation
scores = mir_eval.segment.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
```

### Common Failure Modes
- **Mismatched Lengths:** Providing an interval array and label list of different lengths will raise an error.
- **Unsorted Intervals:** If intervals are not sorted by start time, metrics may produce incorrect results; ensure data is pre-processed if necessary.
- **Duration Mismatch:** If the total duration of estimated intervals differs significantly from the reference, consider using `mir_eval.util.adjust_intervals` to normalize the input.

### Fix Code Hint
```python
# Ensure intervals are sorted and adjusted before evaluation
import mir_eval
ref_intervals, ref_labels = mir_eval.util.adjust_intervals(ref_intervals, ref_labels, est_intervals, est_labels)
scores = mir_eval.segment.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
```

## API Test: `python:mir_eval.segment.mutual_information`

### Signature
```python
def mutual_information(reference_intervals, reference_labels, estimated_intervals, estimated_labels, frame_size=0.1)
```
_Source: source/mir_eval/segment.py:869_

_Source doc:_ Frame-clustering segmentation: mutual information metrics.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> # Trim or pad the estimate to match reference timing
>>> (ref_intervals,
...  ref_labels) = mir_eval.util.adjust_intervals(ref_intervals,
...                                               ref_labels,
...                                               t_min=0)
>>> (est_intervals,
...  est_labels) = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
>>> mi, ami, nmi = mir_eval.structure.mutual_information(ref_intervals,
...                                                      ref_labels,
...                                                      est_intervals,
...                                                      est_labels)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2)
    reference segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
reference_labels : list, shape=(n,)
    reference segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_intervals : np.ndarray, shape=(m, 2)
    estimated segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_labels : list, shape=(m,)
    estimated segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
frame_size : float > 0
    length (in seconds) of frames for clustering
    (Default value = 0.1)

Returns
-------
MI : float > 0
    Mutual information between segmentations
AMI : float
    Adjusted mutual information between segmentations.
NMI : float > 0
    Normalize mutual information between segmentations

### Goal
Computes information-theoretic metrics (MI, AMI, NMI) to evaluate the correspondence between reference and estimated music segmentations by clustering them into frames.

### Parameters
- `reference_intervals`: An $N \times 2$ NumPy array of ground-truth segment start and end times (seconds).
- `reference_labels`: A list of $N$ labels corresponding to the reference intervals.
- `estimated_intervals`: An $M \times 2$ NumPy array of estimated segment start and end times (seconds).
- `estimated_labels`: A list of $M$ labels corresponding to the estimated intervals.
- `frame_size`, default `0.1`: The duration in seconds used to discretize the timeline for clustering.

### Input
Requires labeled intervals loaded via `mir_eval.io.load_labeled_intervals`. Precondition: Intervals must be sorted by time. It is highly recommended to use `mir_eval.util.adjust_intervals` to ensure the estimated timeline matches the reference timeline (e.g., trimming or padding to `t_max=ref_intervals.max()`) before evaluation.

### Output
Returns a tuple of three floats: `(MI, AMI, NMI)`, representing the Mutual Information, Adjusted Mutual Information, and Normalized Mutual Information between the two segmentations.

### Valid Call Patterns
```python
mi, ami, nmi = mir_eval.segment.mutual_information(
    ref_intervals, ref_labels, est_intervals, est_labels, frame_size=0.1
)
```

### LLM Instruction Prompt
When calling `mir_eval.segment.mutual_information`, ensure that `reference_intervals` and `estimated_intervals` are pre-processed using `mir_eval.util.adjust_intervals` to align the temporal boundaries. Always pass intervals as NumPy arrays and labels as lists.

### Prompt Snippet
```text
# Ensure temporal alignment before calling
ref_intervals, ref_labels = mir_eval.util.adjust_intervals(ref_intervals, ref_labels, t_min=0)
est_intervals, est_labels = mir_eval.util.adjust_intervals(est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
mi, ami, nmi = mir_eval.segment.mutual_information(ref_intervals, ref_labels, est_intervals, est_labels)
```

### Common Failure Modes
- **Temporal Mismatch:** Failing to align the total duration of estimated intervals with reference intervals, which can lead to inaccurate clustering.
- **Unsorted Intervals:** Passing intervals that are not sorted by start time, which violates the expected input format for `mir_eval` interval-based functions.
- **Invalid Frame Size:** Providing a non-positive `frame_size`, which will cause the function to fail.

### Fix Code Hint
```python
# Use adjust_intervals to fix temporal mismatches
est_intervals, est_labels = mir_eval.util.adjust_intervals(
    est_intervals, est_labels, t_min=0, t_max=ref_intervals.max()
)
```

## API Test: `python:mir_eval.segment.nce`

### Signature
```python
def nce(reference_intervals, reference_labels, estimated_intervals, estimated_labels, frame_size=0.1, beta=1.0, marginal=False)
```
_Source: source/mir_eval/segment.py:960_

_Source doc:_ Frame-clustering segmentation: normalized conditional entropy

Computes cross-entropy of cluster assignment, normalized by the
max-entropy.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> # Trim or pad the estimate to match reference timing
>>> (ref_intervals,
...  ref_labels) = mir_eval.util.adjust_intervals(ref_intervals,
...                                               ref_labels,
...                                               t_min=0)
>>> (est_intervals,
...  est_labels) = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
>>> S_over, S_under, S_F = mir_eval.structure.nce(ref_intervals,
...                                               ref_labels,
...                                               est_intervals,
...                                               est_labels)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2)
    reference segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
reference_labels : list, shape=(n,)
    reference segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_intervals : np.ndarray, shape=(m, 2)
    estimated segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_labels : list, shape=(m,)
    estimated segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
frame_size : float > 0
    length (in seconds) of frames for clustering
    (Default value = 0.1)
beta : float > 0
    beta for F-measure
    (Default value = 1.0)
marginal : bool
    If `False`, normalize conditional entropy by uniform entropy.
    If `True`, normalize conditional entropy by the marginal entropy.
    (Default value = False)

Returns
-------
S_over
    Over-clustering score:

    - For `marginal=False`, ``1 - H(y_est | y_ref) / log(|y_est|)``

    - For `marginal=True`, ``1 - H(y_est | y_ref) / H(y_est)``

    If `|y_est|==1`, then `S_over` will be 0.
S_under
    Under-clustering score:

    - For `marginal=False`, ``1 - H(y_ref | y_est) / log(|y_ref|)``

    - For `marginal=True`, ``1 - H(y_ref | y_est) / H(y_ref)``

    If `|y_ref|==1`, then `S_under` will be 0.
S_F
    F-measure for (S_over, S_under)

### Goal
Computes the normalized conditional entropy (NCE) between reference and estimated segmentations to evaluate how well estimated clusters align with ground-truth segments.

### Parameters
- `reference_intervals`: An $N \times 2$ NumPy array of start and end times (in seconds) for ground-truth segments.
- `reference_labels`: A list of $N$ labels corresponding to the reference intervals.
- `estimated_intervals`: An $M \times 2$ NumPy array of start and end times (in seconds) for estimated segments.
- `estimated_labels`: A list of $M$ labels corresponding to the estimated intervals.
- `frame_size`, default `0.1`: The duration in seconds of the frames used to discretize the timeline for entropy calculation.
- `beta`, default `1.0`: The weighting factor for the F-measure calculation.
- `marginal`, default `False`: Determines the normalization method; `False` uses uniform entropy, `True` uses marginal entropy.

### Input
Inputs must be provided as labeled intervals (start/end times in seconds and associated labels). Precondition: Intervals should be sorted by time. It is highly recommended to use `mir_eval.util.adjust_intervals` to ensure the estimated intervals span the same total duration as the reference intervals before calling this function.

### Output
Returns a tuple `(S_over, S_under, S_F)` containing the over-clustering score, under-clustering score, and the resulting F-measure.

### Valid Call Patterns
```python
S_over, S_under, S_F = mir_eval.segment.nce(ref_intervals, ref_labels, est_intervals, est_labels)
```

### LLM Instruction Prompt
- Always ensure `reference_intervals` and `estimated_intervals` are passed as NumPy arrays of shape `(n, 2)`.
- Ensure labels are provided as lists of length `n` and `m` respectively.
- Always perform interval adjustment using `mir_eval.util.adjust_intervals` before passing data to this function to avoid timing mismatches.

### Prompt Snippet
```text
# Example of calling nce
S_over, S_under, S_F = mir_eval.segment.nce(ref_intervals, ref_labels, est_intervals, est_labels, frame_size=0.1, beta=1.0, marginal=False)
```

### Common Failure Modes
- Passing unsorted intervals, which violates the expected input structure.
- Mismatched durations between reference and estimated intervals, leading to inaccurate entropy calculations; always use `adjust_intervals` first.
- Providing `frame_size` $\le 0$, which is invalid.

### Fix Code Hint
```python
# Ensure intervals are adjusted to match reference duration
est_intervals, est_labels = mir_eval.util.adjust_intervals(est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
# Compute NCE
S_over, S_under, S_F = mir_eval.segment.nce(ref_intervals, ref_labels, est_intervals, est_labels)
```

## API Test: `python:mir_eval.segment.pairwise`

### Signature
```python
def pairwise(reference_intervals, reference_labels, estimated_intervals, estimated_labels, frame_size=0.1, beta=1.0)
```
_Source: source/mir_eval/segment.py:310_

_Source doc:_ Frame-clustering segmentation evaluation by pair-wise agreement.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> # Trim or pad the estimate to match reference timing
>>> (ref_intervals,
...  ref_labels) = mir_eval.util.adjust_intervals(ref_intervals,
...                                               ref_labels,
...                                               t_min=0)
>>> (est_intervals,
...  est_labels) = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
>>> precision, recall, f = mir_eval.structure.pairwise(ref_intervals,
...                                                    ref_labels,
...                                                    est_intervals,
...                                                    est_labels)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2)
    reference segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
reference_labels : list, shape=(n,)
    reference segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_intervals : np.ndarray, shape=(m, 2)
    estimated segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_labels : list, shape=(m,)
    estimated segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
frame_size : float > 0
    length (in seconds) of frames for clustering
    (Default value = 0.1)
beta : float > 0
    beta value for F-measure
    (Default value = 1.0)

Returns
-------
precision : float > 0
    Precision of detecting whether frames belong in the same cluster
recall : float > 0
    Recall of detecting whether frames belong in the same cluster
f : float > 0
    F-measure of detecting whether frames belong in the same cluster

### Goal
Evaluates music segmentation performance by calculating the pairwise agreement between reference and estimated segmentations using frame-based clustering.

### Parameters
- `reference_intervals`: An $N \times 2$ NumPy array of ground-truth segment start and end times in seconds.
- `reference_labels`: A list of $N$ labels corresponding to the reference intervals.
- `estimated_intervals`: An $M \times 2$ NumPy array of estimated segment start and end times in seconds.
- `estimated_labels`: A list of $M$ labels corresponding to the estimated intervals.
- `frame_size`, default `0.1`: The temporal resolution in seconds used to discretize the timeline for pairwise comparison.
- `beta`, default `1.0`: The weighting factor for the F-measure calculation.

### Input
Requires labeled intervals loaded via `mir_eval.io.load_labeled_intervals`. Precondition: Reference and estimated intervals must be adjusted to span the same temporal range using `mir_eval.util.adjust_intervals` to ensure valid comparison.

### Output
Returns a tuple of three floats: `(precision, recall, f)`, representing the pairwise agreement metrics between the reference and estimated segmentations.

### Valid Call Patterns
```python
precision, recall, f = mir_eval.segment.pairwise(
    ref_intervals, ref_labels, est_intervals, est_labels, frame_size=0.1, beta=1.0
)
```

### LLM Instruction Prompt
When calling `mir_eval.segment.pairwise`, ensure that `reference_intervals` and `estimated_intervals` are pre-processed using `mir_eval.util.adjust_intervals` to align the temporal boundaries. The function expects intervals in seconds and labels as lists.

### Prompt Snippet
```text
# Ensure temporal alignment before calling pairwise
ref_intervals, ref_labels = mir_eval.util.adjust_intervals(ref_intervals, ref_labels, t_min=0)
est_intervals, est_labels = mir_eval.util.adjust_intervals(est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
precision, recall, f = mir_eval.segment.pairwise(ref_intervals, ref_labels, est_intervals, est_labels)
```

### Common Failure Modes
- Mismatched temporal ranges between reference and estimated intervals (must be aligned via `adjust_intervals`).
- Providing intervals that are not sorted by time.
- Using a `frame_size` that is too large relative to the segment durations, leading to poor resolution.

### Fix Code Hint
```python
# Use adjust_intervals to prevent shape or range mismatch errors
est_intervals, est_labels = mir_eval.util.adjust_intervals(
    est_intervals, est_labels, t_min=0, t_max=ref_intervals.max()
)
```

## API Test: `python:mir_eval.segment.rand_index`

### Signature
```python
def rand_index(reference_intervals, reference_labels, estimated_intervals, estimated_labels, frame_size=0.1, beta=1.0)
```
_Source: source/mir_eval/segment.py:413_

_Source doc:_ (Non-adjusted) Rand index.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> # Trim or pad the estimate to match reference timing
>>> (ref_intervals,
...  ref_labels) = mir_eval.util.adjust_intervals(ref_intervals,
...                                               ref_labels,
...                                               t_min=0)
>>> (est_intervals,
...  est_labels) = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
>>> rand_index = mir_eval.structure.rand_index(ref_intervals,
...                                            ref_labels,
...                                            est_intervals,
...                                            est_labels)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2)
    reference segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
reference_labels : list, shape=(n,)
    reference segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_intervals : np.ndarray, shape=(m, 2)
    estimated segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_labels : list, shape=(m,)
    estimated segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
frame_size : float > 0
    length (in seconds) of frames for clustering
    (Default value = 0.1)
beta : float > 0
    beta value for F-measure
    (Default value = 1.0)

Returns
-------
rand_index : float > 0
    Rand index

### Goal
Computes the non-adjusted Rand index to evaluate the similarity between reference and estimated music segmentations by clustering time frames.

### Parameters
- `reference_intervals`: An $N \times 2$ NumPy array of start and end times (in seconds) for the ground-truth segments.
- `reference_labels`: A list of $N$ labels corresponding to the reference intervals.
- `estimated_intervals`: An $M \times 2$ NumPy array of start and end times (in seconds) for the estimated segments.
- `estimated_labels`: A list of $M$ labels corresponding to the estimated intervals.
- `frame_size`, default `0.1`: The duration in seconds used to discretize the timeline into frames for clustering.
- `beta`, default `1.0`: The weighting factor used for the F-measure calculation.

### Input
The function requires labeled intervals as input, typically loaded via `mir_eval.io.load_labeled_intervals`. Precondition: The reference and estimated intervals must be adjusted to cover the same total duration using `mir_eval.util.adjust_intervals` to ensure valid comparison. All time values must be in seconds.

### Output
Returns a `float` representing the Rand index, which quantifies the agreement between the reference and estimated segmentations.

### Valid Call Patterns
```python
# Standard usage with pre-loaded and adjusted intervals
rand_index = mir_eval.segment.rand_index(
    ref_intervals, ref_labels, est_intervals, est_labels, frame_size=0.1, beta=1.0
)
```

### LLM Instruction Prompt
When calling `mir_eval.segment.rand_index`, ensure that `reference_intervals` and `estimated_intervals` are first processed through `mir_eval.util.adjust_intervals` to align their temporal boundaries. Always provide intervals as $N \times 2$ NumPy arrays and labels as lists of the same length.

### Prompt Snippet
```text
# Ensure intervals are adjusted before calling rand_index
ref_intervals, ref_labels = mir_eval.util.adjust_intervals(ref_intervals, ref_labels, t_min=0)
est_intervals, est_labels = mir_eval.util.adjust_intervals(est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
score = mir_eval.segment.rand_index(ref_intervals, ref_labels, est_intervals, est_labels)
```

### Common Failure Modes
- Mismatched temporal ranges: Failing to use `mir_eval.util.adjust_intervals` to align the reference and estimated timelines will lead to incorrect metric computation.
- Invalid input shapes: Passing arrays that do not conform to the $(N, 2)$ interval format or lists that do not match the number of intervals.
- Non-positive parameters: Providing `frame_size` or `beta` values $\le 0$ will violate the function's constraints.

### Fix Code Hint
```python
# Use adjust_intervals to prevent shape or range mismatches
ref_intervals, ref_labels = mir_eval.util.adjust_intervals(ref_intervals, ref_labels, t_min=0)
est_intervals, est_labels = mir_eval.util.adjust_intervals(est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
```

## API Test: `python:mir_eval.segment.validate_boundary`

### Signature
```python
def validate_boundary(reference_intervals, estimated_intervals, trim)
```
_Source: source/mir_eval/segment.py:86_

_Source doc:_ Check that the input annotations to a segment boundary estimation
metric (i.e. one that only takes in segment intervals) look like valid
segment times, and throws helpful errors if not.

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2)
    reference segment intervals, in the format returned by
    :func:`mir_eval.io.load_intervals` or
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_intervals : np.ndarray, shape=(m, 2)
    estimated segment intervals, in the format returned by
    :func:`mir_eval.io.load_intervals` or
    :func:`mir_eval.io.load_labeled_intervals`.
trim : bool
    will the start and end events be trimmed?

### Goal
Validates that segment boundary annotations are correctly formatted as interval arrays before they are passed to segment boundary estimation metrics.

### Parameters
- `reference_intervals`: A NumPy array of shape `(n, 2)` containing ground-truth segment start and end times in seconds.
- `estimated_intervals`: A NumPy array of shape `(m, 2)` containing estimated segment start and end times in seconds.
- `trim`: A boolean flag indicating whether the start and end events of the segments will be trimmed during the evaluation process.

### Input
- **Data Format:** Must be `np.ndarray` of shape `(N, 2)` where each row represents `[start, end]` in seconds.
- **Preconditions:** Inputs should be loaded via `mir_eval.io.load_intervals` or `mir_eval.io.load_labeled_intervals`. Arrays must be sorted by time.

### Output
Returns `None` if validation succeeds; otherwise, raises an exception with a descriptive error message if the input arrays do not conform to the expected structure.

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example inferred from signature
ref = np.array([[0.0, 10.0], [10.0, 20.0]])
est = np.array([[0.1, 10.2], [10.2, 19.8]])
mir_eval.segment.validate_boundary(ref, est, trim=True)
```

### LLM Instruction Prompt
- Always validate segment intervals using `mir_eval.segment.validate_boundary` before passing them to segment evaluation metrics.
- Ensure `reference_intervals` and `estimated_intervals` are `np.ndarray` objects of shape `(N, 2)`.
- Set `trim` to `True` if the evaluation logic intends to trim start/end events, or `False` otherwise.

### Prompt Snippet
```text
# Validate segment boundaries before evaluation
mir_eval.segment.validate_boundary(reference_intervals, estimated_intervals, trim=True)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays that are not `(N, 2)` (e.g., 1D arrays of event times instead of intervals).
- **Unsorted Data:** Providing intervals that are not sorted by start time, which violates the precondition for most `mir_eval` segment metrics.
- **Type Errors:** Passing lists instead of `np.ndarray` objects.

### Fix Code Hint
```python
# Ensure inputs are numpy arrays and sorted
reference_intervals = np.sort(reference_intervals, axis=0)
estimated_intervals = np.sort(estimated_intervals, axis=0)
mir_eval.segment.validate_boundary(reference_intervals, estimated_intervals, trim=True)
```

## API Test: `python:mir_eval.segment.validate_structure`

### Signature
```python
def validate_structure(reference_intervals, reference_labels, estimated_intervals, estimated_labels)
```
_Source: source/mir_eval/segment.py:121_

_Source doc:_ Check that the input annotations to a structure estimation metric (i.e.
one that takes in both segment boundaries and their labels) look like valid
segment times and labels, and throws helpful errors if not.

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2)
    reference segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
reference_labels : list, shape=(n,)
    reference segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_intervals : np.ndarray, shape=(m, 2)
    estimated segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_labels : list, shape=(m,)
    estimated segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.

### Goal
Validates that the provided reference and estimated segment annotations conform to the expected structure and format required for music structure estimation metrics.

### Parameters
- `reference_intervals`: A NumPy array of shape `(n, 2)` containing start and end times (in seconds) for reference segments.
- `reference_labels`: A list of length `n` containing the labels corresponding to each reference interval.
- `estimated_intervals`: A NumPy array of shape `(m, 2)` containing start and end times (in seconds) for estimated segments.
- `estimated_labels`: A list of length `m` containing the labels corresponding to each estimated interval.

### Input
- **Data Format:** Intervals must be provided as `(n, 2)` NumPy arrays where each row is `[start, end]`. Labels must be provided as lists of strings or identifiers.
- **Preconditions:** Inputs should be in the format produced by `mir_eval.io.load_labeled_intervals`. Time values must be in seconds.
- **Ordering:** For most metrics, intervals should be sorted by time.

### Output
Returns `None` if the inputs are valid. If the inputs are invalid (e.g., shape mismatch, incorrect types, or malformed intervals), it raises an informative exception.

### Valid Call Patterns
```python
import mir_eval
# Example inferred from signature and standard mir_eval usage
ref_intervals, ref_labels = mir_eval.io.load_labeled_intervals('ref.lab')
est_intervals, est_labels = mir_eval.io.load_labeled_intervals('est.lab')
mir_eval.segment.validate_structure(ref_intervals, ref_labels, est_intervals, est_labels)
```

### LLM Instruction Prompt
- Always use `mir_eval.segment.validate_structure` to verify inputs before passing them to `mir_eval.segment.evaluate`.
- Ensure that `reference_intervals` and `estimated_intervals` are NumPy arrays of shape `(n, 2)` and `(m, 2)` respectively.
- Ensure that `reference_labels` and `estimated_labels` are lists of length `n` and `m` respectively.

### Prompt Snippet
```text
# Validate structure before evaluation
mir_eval.segment.validate_structure(ref_intervals, ref_labels, est_intervals, est_labels)
scores = mir_eval.segment.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
```

### Common Failure Modes
- **Shape Mismatch:** Providing a list of labels that does not match the number of rows in the corresponding interval array.
- **Invalid Types:** Passing raw lists instead of NumPy arrays for intervals, or non-list types for labels.
- **Unsorted Intervals:** While `validate_structure` checks format, downstream metrics often require intervals to be sorted by start time; ensure data is pre-processed if necessary.

### Fix Code Hint
```python
# Ensure intervals are numpy arrays and labels are lists
import numpy as np
reference_intervals = np.array(reference_intervals)
estimated_intervals = np.array(estimated_intervals)
# Validate before proceeding
mir_eval.segment.validate_structure(reference_intervals, reference_labels, estimated_intervals, estimated_labels)
```

## API Test: `python:mir_eval.segment.vmeasure`

### Signature
```python
def vmeasure(reference_intervals, reference_labels, estimated_intervals, estimated_labels, frame_size=0.1, beta=1.0)
```
_Source: source/mir_eval/segment.py:1100_

_Source doc:_ Frame-clustering segmentation: v-measure

Computes cross-entropy of cluster assignment, normalized by the
marginal-entropy.

This is equivalent to `nce(..., marginal=True)`.

Examples
--------
>>> (ref_intervals,
...  ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals,
...  est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> # Trim or pad the estimate to match reference timing
>>> (ref_intervals,
...  ref_labels) = mir_eval.util.adjust_intervals(ref_intervals,
...                                               ref_labels,
...                                               t_min=0)
>>> (est_intervals,
...  est_labels) = mir_eval.util.adjust_intervals(
...     est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
>>> V_precision, V_recall, V_F = mir_eval.structure.vmeasure(ref_intervals,
...                                                          ref_labels,
...                                                          est_intervals,
...                                                          est_labels)

Parameters
----------
reference_intervals : np.ndarray, shape=(n, 2)
    reference segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
reference_labels : list, shape=(n,)
    reference segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_intervals : np.ndarray, shape=(m, 2)
    estimated segment intervals, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
estimated_labels : list, shape=(m,)
    estimated segment labels, in the format returned by
    :func:`mir_eval.io.load_labeled_intervals`.
frame_size : float > 0
    length (in seconds) of frames for clustering
    (Default value = 0.1)
beta : float > 0
    beta for F-measure
    (Default value = 1.0)

Returns
-------
V_precision
    Over-clustering score:
    ``1 - H(y_est | y_ref) / H(y_est)``

    If `|y_est|==1`, then `V_precision` will be 0.
V_recall
    Under-clustering score:
    ``1 - H(y_ref | y_est) / H(y_ref)``

    If `|y_ref|==1`, then `V_recall` will be 0.
V_F
    F-measure for (V_precision, V_recall)

### Goal
Computes the V-measure for music segmentation by evaluating the cross-entropy of cluster assignments between reference and estimated segmentations, normalized by marginal entropy.

### Parameters
- `reference_intervals`: An $N \times 2$ NumPy array of ground-truth segment start and end times in seconds.
- `reference_labels`: A list of $N$ labels corresponding to the reference intervals.
- `estimated_intervals`: An $M \times 2$ NumPy array of estimated segment start and end times in seconds.
- `estimated_labels`: A list of $M$ labels corresponding to the estimated intervals.
- `frame_size`, default `0.1`: The duration in seconds for the frames used to discretize the segmentation for clustering.
- `beta`, default `1.0`: The weighting factor for the F-measure calculation.

### Input
The caller must provide labeled intervals as NumPy arrays and lists. Preconditions include:
1. Intervals must be sorted by time.
2. Estimated intervals should be adjusted using `mir_eval.util.adjust_intervals` to ensure they span the same temporal range as the reference intervals before evaluation.

### Output
Returns a tuple containing three floats: `(V_precision, V_recall, V_F)`. `V_precision` measures over-clustering, `V_recall` measures under-clustering, and `V_F` is the weighted F-measure.

### Valid Call Patterns
```python
V_precision, V_recall, V_F = mir_eval.segment.vmeasure(
    ref_intervals, ref_labels, est_intervals, est_labels, frame_size=0.1, beta=1.0
)
```

### LLM Instruction Prompt
- Always ensure `reference_intervals` and `estimated_intervals` are pre-processed with `mir_eval.util.adjust_intervals` to align the temporal boundaries.
- Use the `mir_eval.segment` namespace for this function.
- Ensure `frame_size` and `beta` are positive floats.

### Prompt Snippet
```text
# Align intervals before calling vmeasure
ref_intervals, ref_labels = mir_eval.util.adjust_intervals(ref_intervals, ref_labels, t_min=0)
est_intervals, est_labels = mir_eval.util.adjust_intervals(est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
V_precision, V_recall, V_F = mir_eval.segment.vmeasure(ref_intervals, ref_labels, est_intervals, est_labels)
```

### Common Failure Modes
- Mismatched temporal ranges between reference and estimated intervals (results in inaccurate clustering).
- Providing unsorted intervals.
- Setting `frame_size` to a non-positive value, which will violate the `float > 0` constraint.

### Fix Code Hint
```python
# Ensure intervals are valid and aligned
import mir_eval
ref_intervals, ref_labels = mir_eval.util.adjust_intervals(ref_intervals, ref_labels, t_min=0)
est_intervals, est_labels = mir_eval.util.adjust_intervals(est_intervals, est_labels, t_min=0, t_max=ref_intervals.max())
```

## API Test: `python:mir_eval.separation.bss_eval_images`

### Signature
```python
def bss_eval_images(reference_sources, estimated_sources, compute_permutation=True)
```
_Source: source/mir_eval/separation.py:373_

_Source doc:_ Compute the bss_eval_images function from the
BSS_EVAL Matlab toolbox.

Ordering and measurement of the separation quality for estimated source
signals in terms of filtered true source, interference and artifacts.
This method also provides the ISR measure.

The decomposition allows a time-invariant filter distortion of length
512, as described in Section III.B of [#vincent2006performance]_.

Passing ``False`` for ``compute_permutation`` will improve the computation
performance of the evaluation; however, it is not always appropriate and
is not the way that the BSS_EVAL Matlab toolbox computes bss_eval_images.

Examples
--------
>>> # reference_sources[n] should be an ndarray of samples of the
>>> # n'th reference source
>>> # estimated_sources[n] should be the same for the n'th estimated
>>> # source
>>> (sdr, isr, sir, sar,
...  perm) = mir_eval.separation.bss_eval_images(reference_sources,
...                                               estimated_sources)

Parameters
----------
reference_sources : np.ndarray, shape=(nsrc, nsampl, nchan)
    matrix containing true sources
estimated_sources : np.ndarray, shape=(nsrc, nsampl, nchan)
    matrix containing estimated sources
compute_permutation : bool, optional
    compute permutation of estimate/source combinations (True by default)

Returns
-------
sdr : np.ndarray, shape=(nsrc,)
    vector of Signal to Distortion Ratios (SDR)
isr : np.ndarray, shape=(nsrc,)
    vector of source Image to Spatial distortion Ratios (ISR)
sir : np.ndarray, shape=(nsrc,)
    vector of Source to Interference Ratios (SIR)
sar : np.ndarray, shape=(nsrc,)
    vector of Sources to Artifacts Ratios (SAR)
perm : np.ndarray, shape=(nsrc,)
    vector containing the best ordering of estimated sources in
    the mean SIR sense (estimated source number ``perm[j]`` corresponds to
    true source number ``j``).  Note: ``perm`` will be ``(1,2,...,nsrc)``
    if ``compute_permutation`` is ``False``.

References
----------
.. [#] Emmanuel Vincent, Shoko Araki, Fabian J. Theis, Guido Nolte, Pau
    Bofill, Hiroshi Sawada, Alexey Ozerov, B. Vikrham Gowreesunker, Dominik
    Lutter and Ngoc Q.K. Duong, "The Signal Separation Evaluation Campaign
    (2007-2010): Achievements and remaining challenges", Signal Processing,
    92, pp. 1928-1936, 2012.

### Goal
Computes the BSS_EVAL metrics (SDR, ISR, SIR, SAR) for source separation evaluation, allowing for time-invariant filter distortion of length 512.

### Parameters
- `reference_sources`: A 3D NumPy array of shape `(nsrc, nsampl, nchan)` containing the ground-truth source signals.
- `estimated_sources`: A 3D NumPy array of shape `(nsrc, nsampl, nchan)` containing the estimated source signals.
- `compute_permutation`, default `True`: A boolean flag; if `True`, calculates the optimal permutation of estimated sources to match reference sources based on mean SIR.

### Input
- **Data Format:** Both `reference_sources` and `estimated_sources` must be `np.ndarray` with dimensions `(nsrc, nsampl, nchan)`.
- **Preconditions:** The `mir_eval.separation` module is deprecated; users are advised to use `sigsep-museval` for new projects.

### Output
Returns a tuple of five `np.ndarray` objects: `(sdr, isr, sir, sar, perm)`, each of shape `(nsrc,)`.

### Valid Call Patterns
```python
(sdr, isr, sir, sar, perm) = mir_eval.separation.bss_eval_images(
    reference_sources, estimated_sources
)
```

### LLM Instruction Prompt
- When calling `mir_eval.separation.bss_eval_images`, ensure both input arrays are 3D NumPy arrays with identical shapes `(nsrc, nsampl, nchan)`.
- Note that `compute_permutation=True` is the default and matches the behavior of the original BSS_EVAL Matlab toolbox.
- Always unpack the five returned values: `sdr`, `isr`, `sir`, `sar`, and `perm`.

### Prompt Snippet
```text
(sdr, isr, sir, sar, perm) = mir_eval.separation.bss_eval_images(reference_sources, estimated_sources)
```

### Common Failure Modes
- **Shape Mismatch:** Providing arrays where `nsrc`, `nsampl`, or `nchan` do not match between reference and estimated sources.
- **Performance:** Setting `compute_permutation=False` when the estimated source order is not guaranteed to match the reference order, leading to incorrect metric values.
- **Deprecation:** Using this module for new research; the library documentation explicitly recommends `sigsep-museval` for source separation evaluation.

### Fix Code Hint
```python
# Ensure inputs are 3D arrays and handle potential shape mismatches
import numpy as np
# Example: Ensure shape (nsrc, nsampl, nchan)
assert reference_sources.shape == estimated_sources.shape
(sdr, isr, sir, sar, perm) = mir_eval.separation.bss_eval_images(reference_sources, estimated_sources)
```

## API Test: `python:mir_eval.separation.bss_eval_images_framewise`

### Signature
```python
def bss_eval_images_framewise(reference_sources, estimated_sources, window=30 * 44100, hop=15 * 44100, compute_permutation=False)
```
_Source: source/mir_eval/separation.py:508_

_Source doc:_ Framewise computation of bss_eval_images

Please be aware that this function does not compute permutations (by
default) on the possible relations between ``reference_sources`` and
``estimated_sources`` due to the dangers of a changing permutation.
Therefore (by default), it assumes that ``reference_sources[i]``
corresponds to ``estimated_sources[i]``. To enable computing permutations
please set ``compute_permutation`` to be ``True`` and check that the
returned ``perm`` is identical for all windows.

NOTE: if ``reference_sources`` and ``estimated_sources`` would be evaluated
using only a single window or are shorter than the window length, the
result of ``bss_eval_images`` called on ``reference_sources`` and
``estimated_sources`` (with the ``compute_permutation`` parameter passed to
``bss_eval_images``) is returned

Examples
--------
>>> # reference_sources[n] should be an ndarray of samples of the
>>> # n'th reference source
>>> # estimated_sources[n] should be the same for the n'th estimated
>>> # source
>>> (sdr, isr, sir, sar,
...  perm) = mir_eval.separation.bss_eval_images_framewise(
         reference_sources,
...      estimated_sources,
         window,
....     hop)

Parameters
----------
reference_sources : np.ndarray, shape=(nsrc, nsampl, nchan)
    matrix containing true sources (must have the same shape as
    ``estimated_sources``)
estimated_sources : np.ndarray, shape=(nsrc, nchan, nsampl)
    matrix containing estimated sources (must have the same shape as
    ``reference_sources``)
window : int
    Window length for framewise evaluation
hop : int
    Hop size for framewise evaluation
compute_permutation : bool, optional
    compute permutation of estimate/source combinations for all windows
    (False by default)

Returns
-------
sdr : np.ndarray, shape=(nsrc, nframes)
    vector of Signal to Distortion Ratios (SDR)
isr : np.ndarray, shape=(nsrc, nframes)
    vector of source Image to Spatial distortion Ratios (ISR)
sir : np.ndarray, shape=(nsrc, nframes)
    vector of Source to Interference Ratios (SIR)
sar : np.ndarray, shape=(nsrc, nframes)
    vector of Sources to Artifacts Ratios (SAR)
perm : np.ndarray, shape=(nsrc, nframes)
    vector containing the best ordering of estimated sources in
    the mean SIR sense (estimated source number perm[j] corresponds to
    true source number j)
    Note: perm will be range(nsrc) for all windows if compute_permutation
    is False

### Goal
Computes BSS_EVAL metrics (SDR, ISR, SIR, SAR) for source separation outputs in a sliding-window (framewise) fashion to analyze performance over time.

### Parameters
- `reference_sources`: A 3D NumPy array of ground-truth audio samples with shape `(nsrc, nsampl, nchan)`.
- `estimated_sources`: A 3D NumPy array of estimated audio samples with shape `(nsrc, nsampl, nchan)`. Must match `reference_sources` shape.
- `window`, default `30 * 44100`: The length of the analysis window in samples.
- `hop`, default `15 * 44100`: The step size between analysis windows in samples.
- `compute_permutation`, default `False`: If `True`, calculates the optimal source-to-estimate permutation for each window.

### Input
Requires two 3D NumPy arrays (`reference_sources` and `estimated_sources`) representing audio signals. Both arrays must have identical dimensions `(nsrc, nsampl, nchan)`. Note: `mir_eval.separation` is deprecated in favor of `sigsep-museval`.

### Output
Returns a tuple of five NumPy arrays: `(sdr, isr, sir, sar, perm)`. Each array has shape `(nsrc, nframes)`, where `nframes` is the number of windows processed.

### Valid Call Patterns
```python
(sdr, isr, sir, sar, perm) = mir_eval.separation.bss_eval_images_framewise(
    reference_sources, 
    estimated_sources, 
    window=44100, 
    hop=22050
)
```

### LLM Instruction Prompt
- Always ensure `reference_sources` and `estimated_sources` have the exact same shape `(nsrc, nsampl, nchan)`.
- If `compute_permutation` is `False` (default), the function assumes index-aligned sources. If `True`, verify that the returned `perm` is consistent across windows.
- Use integer values for `window` and `hop` representing sample counts.

### Prompt Snippet
```text
mir_eval.separation.bss_eval_images_framewise(ref_arr, est_arr, window=44100, hop=22050)
```

### Common Failure Modes
- Shape mismatch between `reference_sources` and `estimated_sources` will raise a `ValueError`.
- Setting `compute_permutation=True` when the permutation changes significantly between windows can lead to misleading evaluation results.
- Using this module for new projects; it is deprecated—prefer `sigsep-museval`.

### Fix Code Hint
```python
# Ensure inputs are 3D arrays and match in shape
assert reference_sources.shape == estimated_sources.shape
# Use sigsep-museval if possible, otherwise:
sdr, isr, sir, sar, perm = mir_eval.separation.bss_eval_images_framewise(
    reference_sources, estimated_sources, window=window_size, hop=hop_size
)
```

## API Test: `python:mir_eval.separation.bss_eval_sources`

### Signature
```python
def bss_eval_sources(reference_sources, estimated_sources, compute_permutation=True)
```
_Source: source/mir_eval/separation.py:150_

_Source doc:_ Ordering and measurement of the separation quality for estimated source
signals in terms of filtered true source, interference and artifacts.

The decomposition allows a time-invariant filter distortion of length
512, as described in Section III.B of [#vincent2006performance]_.

Passing ``False`` for ``compute_permutation`` will improve the computation
performance of the evaluation; however, it is not always appropriate and
is not the way that the BSS_EVAL Matlab toolbox computes bss_eval_sources.

Examples
--------
>>> # reference_sources[n] should be an ndarray of samples of the
>>> # n'th reference source
>>> # estimated_sources[n] should be the same for the n'th estimated
>>> # source
>>> (sdr, sir, sar,
...  perm) = mir_eval.separation.bss_eval_sources(reference_sources,
...                                               estimated_sources)

Parameters
----------
reference_sources : np.ndarray, shape=(nsrc, nsampl)
    matrix containing true sources (must have same shape as
    estimated_sources)
estimated_sources : np.ndarray, shape=(nsrc, nsampl)
    matrix containing estimated sources (must have same shape as
    reference_sources)
compute_permutation : bool, optional
    compute permutation of estimate/source combinations (True by default)

Returns
-------
sdr : np.ndarray, shape=(nsrc,)
    vector of Signal to Distortion Ratios (SDR)
sir : np.ndarray, shape=(nsrc,)
    vector of Source to Interference Ratios (SIR)
sar : np.ndarray, shape=(nsrc,)
    vector of Sources to Artifacts Ratios (SAR)
perm : np.ndarray, shape=(nsrc,)
    vector containing the best ordering of estimated sources in
    the mean SIR sense (estimated source number ``perm[j]`` corresponds to
    true source number ``j``). Note: ``perm`` will be ``[0, 1, ...,
    nsrc-1]`` if ``compute_permutation`` is ``False``.

References
----------
.. [#] Emmanuel Vincent, Shoko Araki, Fabian J. Theis, Guido Nolte, Pau
    Bofill, Hiroshi Sawada, Alexey Ozerov, B. Vikrham Gowreesunker, Dominik
    Lutter and Ngoc Q.K. Duong, "The Signal Separation Evaluation Campaign
    (2007-2010): Achievements and remaining challenges", Signal Processing,
    92, pp. 1928-1936, 2012.

### Goal
Computes standard source separation quality metrics (SDR, SIR, SAR) by decomposing estimated source signals relative to ground-truth references, accounting for potential time-invariant filter distortion.

### Parameters
- `reference_sources`: A 2D NumPy array of shape `(nsrc, nsampl)` containing the ground-truth audio samples for each source.
- `estimated_sources`: A 2D NumPy array of shape `(nsrc, nsampl)` containing the estimated audio samples for each source. Must match the shape of `reference_sources`.
- `compute_permutation`, default `True`: A boolean flag. If `True`, the function finds the optimal permutation of estimated sources to match the reference sources based on mean SIR. If `False`, it assumes the input order is already aligned.

### Input
- **Data Format:** Both inputs must be `np.ndarray` objects of identical shape `(nsrc, nsampl)`.
- **Preconditions:** The `mir_eval.separation` module is deprecated in favor of `sigsep-museval`. Ensure inputs are pre-aligned in time and sample-rate matched.

### Output
Returns a tuple of four `np.ndarray` objects:
- `sdr`: Signal to Distortion Ratio (dB).
- `sir`: Source to Interference Ratio (dB).
- `sar`: Sources to Artifacts Ratio (dB).
- `perm`: The permutation index vector mapping estimated sources to reference sources.

### Valid Call Patterns
```python
(sdr, sir, sar, perm) = mir_eval.separation.bss_eval_sources(
    reference_sources, 
    estimated_sources
)
```

### LLM Instruction Prompt
- Always ensure `reference_sources` and `estimated_sources` have the exact same dimensions `(nsrc, nsampl)`.
- Note that this function is deprecated; if the environment supports it, prefer `sigsep-museval`.
- When `compute_permutation` is `True`, the returned `perm` array indicates the optimal alignment; if `False`, `perm` will be a simple range `[0, 1, ..., nsrc-1]`.

### Prompt Snippet
```text
import mir_eval.separation
sdr, sir, sar, perm = mir_eval.separation.bss_eval_sources(ref, est)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays with different `nsrc` or `nsampl` dimensions will raise a `ValueError`.
- **Performance:** Setting `compute_permutation=True` on a large number of sources can be computationally expensive.
- **Deprecation:** Users may encounter warnings or lack of support in newer environments; check if `sigsep-museval` is available as a modern alternative.

### Fix Code Hint
```python
# Ensure shapes match before calling
if reference_sources.shape != estimated_sources.shape:
    raise ValueError("Reference and estimated sources must have the same shape.")
```

## API Test: `python:mir_eval.separation.bss_eval_sources_framewise`

### Signature
```python
def bss_eval_sources_framewise(reference_sources, estimated_sources, window=30 * 44100, hop=15 * 44100, compute_permutation=False)
```
_Source: source/mir_eval/separation.py:261_

_Source doc:_ Framewise computation of bss_eval_sources

Please be aware that this function does not compute permutations (by
default) on the possible relations between reference_sources and
estimated_sources due to the dangers of a changing permutation. Therefore
(by default), it assumes that ``reference_sources[i]`` corresponds to
``estimated_sources[i]``. To enable computing permutations please set
``compute_permutation`` to be ``True`` and check that the returned ``perm``
is identical for all windows.

NOTE: if ``reference_sources`` and ``estimated_sources`` would be evaluated
using only a single window or are shorter than the window length, the
result of :func:`mir_eval.separation.bss_eval_sources` called on
``reference_sources`` and ``estimated_sources`` (with the
``compute_permutation`` parameter passed to
:func:`mir_eval.separation.bss_eval_sources`) is returned.

Examples
--------
>>> # reference_sources[n] should be an ndarray of samples of the
>>> # n'th reference source
>>> # estimated_sources[n] should be the same for the n'th estimated
>>> # source
>>> (sdr, sir, sar,
...  perm) = mir_eval.separation.bss_eval_sources_framewise(
         reference_sources,
...      estimated_sources)

Parameters
----------
reference_sources : np.ndarray, shape=(nsrc, nsampl)
    matrix containing true sources (must have the same shape as
    ``estimated_sources``)
estimated_sources : np.ndarray, shape=(nsrc, nsampl)
    matrix containing estimated sources (must have the same shape as
    ``reference_sources``)
window : int, optional
    Window length for framewise evaluation (default value is 30s at a
    sample rate of 44.1kHz)
hop : int, optional
    Hop size for framewise evaluation (default value is 15s at a
    sample rate of 44.1kHz)
compute_permutation : bool, optional
    compute permutation of estimate/source combinations for all windows
    (False by default)

Returns
-------
sdr : np.ndarray, shape=(nsrc, nframes)
    vector of Signal to Distortion Ratios (SDR)
sir : np.ndarray, shape=(nsrc, nframes)
    vector of Source to Interference Ratios (SIR)
sar : np.ndarray, shape=(nsrc, nframes)
    vector of Sources to Artifacts Ratios (SAR)
perm : np.ndarray, shape=(nsrc, nframes)
    vector containing the best ordering of estimated sources in
    the mean SIR sense (estimated source number ``perm[j]`` corresponds to
    true source number ``j``).  Note: ``perm`` will be ``range(nsrc)`` for
    all windows if ``compute_permutation`` is ``False``

### Goal
Computes BSS_EVAL source separation metrics (SDR, SIR, SAR) over sliding temporal windows to analyze the time-varying performance of source separation algorithms.

### Parameters
- `reference_sources`: A 2D NumPy array of shape `(nsrc, nsampl)` containing the ground-truth audio samples for each source.
- `estimated_sources`: A 2D NumPy array of shape `(nsrc, nsampl)` containing the estimated audio samples for each source.
- `window`, default `30 * 44100`: The length of the analysis window in samples.
- `hop`, default `15 * 44100`: The step size between consecutive analysis windows in samples.
- `compute_permutation`, default `False`: If `True`, calculates the optimal source permutation for each window; otherwise, assumes the input order is fixed.

### Input
The caller must provide two NumPy arrays of identical shape `(nsrc, nsampl)`. Note that `mir_eval.separation` is deprecated in favor of `sigsep-museval`; users should ensure their environment is compatible with the legacy `mir_eval` implementation.

### Output
Returns a tuple of four NumPy arrays: `(sdr, sir, sar, perm)`. Each array has shape `(nsrc, nframes)`, where `nframes` is the number of windows processed.

### Valid Call Patterns
```python
(sdr, sir, sar, perm) = mir_eval.separation.bss_eval_sources_framewise(
    reference_sources, 
    estimated_sources
)
```

### LLM Instruction Prompt
- Always ensure `reference_sources` and `estimated_sources` have the same dimensions before calling.
- If `compute_permutation` is set to `True`, verify that the returned `perm` is consistent across windows, as changing permutations can lead to misleading evaluation results.
- Use the default window/hop values unless the specific audio sample rate differs from 44.1kHz.

### Prompt Snippet
```text
# Example usage of framewise separation evaluation
sdr, sir, sar, perm = mir_eval.separation.bss_eval_sources_framewise(ref_arr, est_arr, compute_permutation=True)
```

### Common Failure Modes
- **Shape Mismatch:** Providing arrays where `nsrc` or `nsampl` differ between reference and estimate will raise a `ValueError`.
- **Permutation Instability:** Setting `compute_permutation=True` without verifying that the permutation remains stable across windows can result in discontinuous metric trajectories.
- **Memory Usage:** Large window sizes or very long audio files can lead to high memory consumption when generating the `(nsrc, nframes)` output arrays.

### Fix Code Hint
```python
# Ensure inputs are numpy arrays and have matching shapes
import numpy as np
reference_sources = np.asarray(reference_sources)
estimated_sources = np.asarray(estimated_sources)
if reference_sources.shape != estimated_sources.shape:
    raise ValueError("Reference and estimated sources must have the same shape.")
```

## API Test: `python:mir_eval.separation.evaluate`

### Signature
```python
def evaluate(reference_sources, estimated_sources, **kwargs)
```
_Source: source/mir_eval/separation.py:854_

_Source doc:_ Compute all metrics for the given reference and estimated signals.

NOTE: This will always compute :func:`mir_eval.separation.bss_eval_images`
for any valid input and will additionally compute
:func:`mir_eval.separation.bss_eval_sources` for valid input with fewer
than 3 dimensions.

Examples
--------
>>> # reference_sources[n] should be an ndarray of samples of the
>>> # n'th reference source
>>> # estimated_sources[n] should be the same for the n'th estimated source
>>> scores = mir_eval.separation.evaluate(reference_sources,
...                                       estimated_sources)

Parameters
----------
reference_sources : np.ndarray, shape=(nsrc, nsampl[, nchan])
    matrix containing true sources
estimated_sources : np.ndarray, shape=(nsrc, nsampl[, nchan])
    matrix containing estimated sources
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of source separation performance metrics, including BSS_EVAL images and sources, for a given set of reference and estimated audio signals.

### Parameters
- `reference_sources`: A 3D NumPy array (or 2D if single-channel) of shape `(nsrc, nsampl, nchan)` representing the ground-truth audio sources.
- `estimated_sources`: A 3D NumPy array (or 2D if single-channel) of shape `(nsrc, nsampl, nchan)` representing the separated audio sources to be evaluated.
- `kwargs`: Optional keyword arguments passed directly to the underlying metric functions (e.g., `bss_eval_images` or `bss_eval_sources`).

### Input
- **Data Format:** Both `reference_sources` and `estimated_sources` must be NumPy arrays.
- **Preconditions:** The number of sources (`nsrc`) and the number of samples (`nsampl`) must match between the reference and estimated arrays.
- **Deprecation Warning:** The `mir_eval.separation` module is deprecated; users are encouraged to use `sigsep-museval` for source separation evaluation.

### Output
Returns a `dict` where keys are strings (metric names) and values are floats (the computed scores).

### Valid Call Patterns
```python
import mir_eval
# reference_sources and estimated_sources are np.ndarrays
scores = mir_eval.separation.evaluate(reference_sources, estimated_sources)
```

### LLM Instruction Prompt
- When calling `mir_eval.separation.evaluate`, ensure that both `reference_sources` and `estimated_sources` are provided as NumPy arrays with identical dimensions.
- Note that this function automatically triggers `bss_eval_images` and, if the input has fewer than 3 dimensions, `bss_eval_sources`.

### Prompt Snippet
```text
scores = mir_eval.separation.evaluate(reference_sources, estimated_sources)
```

### Common Failure Modes
- **Dimension Mismatch:** Providing arrays where `nsrc` or `nsampl` differ between reference and estimate will raise a `ValueError`.
- **Deprecated Usage:** Relying on this module for new research projects is discouraged; prefer `sigsep-museval` as per project documentation.
- **Memory Constraints:** Large audio files loaded as full NumPy arrays may cause memory exhaustion; ensure inputs are appropriately sized.

### Fix Code Hint
```python
# Ensure inputs are numpy arrays and have matching shapes
import numpy as np
reference_sources = np.array(reference_list)
estimated_sources = np.array(estimated_list)
scores = mir_eval.separation.evaluate(reference_sources, estimated_sources)
```

## API Test: `python:mir_eval.separation.validate`

### Signature
```python
def validate(reference_sources, estimated_sources)
```
_Source: source/mir_eval/separation.py:67_

_Source doc:_ Check that the input data to a metric are valid, and throws helpful
errors if not.

Parameters
----------
reference_sources : np.ndarray, shape=(nsrc, nsampl)
    matrix containing true sources
estimated_sources : np.ndarray, shape=(nsrc, nsampl)
    matrix containing estimated sources

### Goal
Validates that the provided reference and estimated source matrices conform to the expected dimensions and structure required for source separation evaluation.

### Parameters
- `reference_sources`: A NumPy array of shape `(nsrc, nsampl)` representing the ground-truth audio sources.
- `estimated_sources`: A NumPy array of shape `(nsrc, nsampl)` representing the estimated audio sources produced by a separation system.

### Input
- **Data Format:** Both inputs must be `np.ndarray` objects.
- **Dimensions:** Both arrays must have the same shape `(nsrc, nsampl)`, where `nsrc` is the number of sources and `nsampl` is the number of audio samples.
- **Preconditions:** The inputs must represent time-domain audio signals. Note that the `mir_eval.separation` module is deprecated in favor of `sigsep-museval`.

### Output
Returns `None` if the validation passes. If the inputs are invalid (e.g., shape mismatch or incorrect type), it raises an exception with a descriptive error message.

### Valid Call Patterns
```python
import numpy as np
import mir_eval

# Example inferred from signature
ref = np.zeros((2, 44100))
est = np.zeros((2, 44100))
mir_eval.separation.validate(ref, est)
```

### LLM Instruction Prompt
- When calling `mir_eval.separation.validate`, ensure both `reference_sources` and `estimated_sources` are NumPy arrays of identical shape `(nsrc, nsampl)`.
- Do not use this function for modern source separation evaluation; prefer `sigsep-museval` as per project deprecation notices.

### Prompt Snippet
```text
mir_eval.separation.validate(reference_sources, estimated_sources)
```

### Common Failure Modes
- **Shape Mismatch:** Providing arrays where `nsrc` or `nsampl` differ between the reference and estimated sources will trigger a validation error.
- **Incorrect Type:** Passing lists or other non-NumPy array types will cause the validation to fail.
- **Deprecated Usage:** Relying on `mir_eval.separation` for new projects; the library documentation explicitly notes this module is deprecated.

### Fix Code Hint
```python
# Ensure arrays are the same shape before validation
if reference_sources.shape != estimated_sources.shape:
    # Handle or reshape data to match
    pass
mir_eval.separation.validate(reference_sources, estimated_sources)
```

## API Test: `python:mir_eval.sonify.chords`

### Signature
```python
def chords(chord_labels, intervals, fs, **kwargs)
```
_Source: source/mir_eval/sonify.py:367_

_Source doc:_ Synthesizes chord labels

Parameters
----------
chord_labels : list of str
    List of chord label strings.
intervals : np.ndarray, shape=(len(chord_labels), 2)
    Start and end times of each chord label
fs : int
    Sampling rate to synthesize at
**kwargs
    Additional keyword arguments to pass to
    :func:`mir_eval.sonify.time_frequency`

Returns
-------
output : np.ndarray
    Synthesized chord labels

### Goal
Synthesizes an audio representation of chord label annotations to facilitate qualitative "evaluation by ear" of MIR chord estimation outputs.

### Parameters
- `chord_labels`: A list of strings representing the chord labels (e.g., "C:maj", "D:min7").
- `intervals`: An $N \times 2$ NumPy array where each row contains the `[start, end]` time in seconds for the corresponding chord label.
- `fs`: The target sampling rate in Hz for the synthesized audio output.
- `kwargs`: Optional keyword arguments passed directly to `mir_eval.sonify.time_frequency` to control synthesis parameters.

### Input
- **Data Format:** `chord_labels` must be a list of strings; `intervals` must be a NumPy array of shape `(len(chord_labels), 2)`.
- **Preconditions:** Time values in `intervals` must be in seconds. Chord labels must follow standard syntax (e.g., `C:maj`) as defined in the `mir_eval.chord` module.
- **Validation:** Ensure that the number of labels matches the number of rows in the intervals array.

### Output
Returns `np.ndarray` — A 1D NumPy array representing the time-domain audio signal of the synthesized chords at the specified sampling rate.

### Valid Call Patterns
```python
# Inferred from signature:
audio = mir_eval.sonify.chords(chord_labels, intervals, fs)
```

### LLM Instruction Prompt
- When calling `mir_eval.sonify.chords`, ensure `intervals` is a 2D NumPy array of shape `(N, 2)` and `chord_labels` is a list of length `N`.
- Always provide `fs` as an integer representing the desired sampling rate.
- Pass additional synthesis parameters (such as window size or hop length) via `**kwargs` to configure the underlying `time_frequency` synthesis.

### Prompt Snippet
```text
import mir_eval
# Assuming chord_labels and intervals are prepared:
audio_signal = mir_eval.sonify.chords(chord_labels, intervals, fs=44100)
```

### Common Failure Modes
- **Label Syntax Errors:** Providing chord labels that do not conform to standard syntax (e.g., missing root or quality) may result in errors or unexpected synthesis behavior.
- **Shape Mismatch:** Passing `intervals` and `chord_labels` with different lengths will cause an index or shape mismatch error.
- **Invalid Time Units:** Providing time values in samples instead of seconds will result in incorrect audio duration.

### Fix Code Hint
```python
# Ensure intervals are sorted and labels match length
import numpy as np
# Example:
# labels = ['C:maj', 'G:maj']
# intervals = np.array([[0.0, 2.0], [2.0, 4.0]])
# audio = mir_eval.sonify.chords(labels, intervals, 44100)
```

## API Test: `python:mir_eval.sonify.chroma`

### Signature
```python
def chroma(chromagram, times, fs, **kwargs)
```
_Source: source/mir_eval/sonify.py:320_

_Source doc:_ Reverse synthesis of a chromagram (semitone matrix)

Parameters
----------
chromagram : np.ndarray, shape=(12, times.shape[0])
    Chromagram matrix, where each row represents a semitone [C->Bb]
    i.e., ``chromagram[3, j]`` is the magnitude of D# from ``times[j]`` to
    ``times[j + 1]``
times : np.ndarray, shape=(len(chord_labels),) or (len(chord_labels), 2)
    Either the start time of each column in the chromagram,
    or the time interval corresponding to each column.
fs : int
    Sampling rate to synthesize audio data at
**kwargs
    Additional keyword arguments to pass to
    :func:`mir_eval.sonify.time_frequency`

Returns
-------
output : np.ndarray
    Synthesized chromagram

### Goal
Synthesize a time-domain audio signal from a chromagram representation to facilitate qualitative evaluation by ear.

### Parameters
- `chromagram`: A 12-row NumPy array representing semitone magnitudes (C through Bb) over time.
- `times`: A 1D array of start times or an $N \times 2$ array of time intervals corresponding to the columns of the chromagram.
- `fs`: The target sampling rate in Hz for the synthesized audio output.
- `kwargs`: Optional keyword arguments passed directly to `mir_eval.sonify.time_frequency` to control synthesis parameters.

### Input
- `chromagram`: Must be a 2D `np.ndarray` with shape `(12, N)`.
- `times`: Must be a 1D array of length `N` or a 2D array of shape `(N, 2)`.
- `fs`: Must be a positive integer.
- Preconditions: Time values must be in seconds. The number of columns in `chromagram` must match the length of the `times` array.

### Output
Returns `np.ndarray` — A 1D NumPy array containing the synthesized time-domain audio signal.

### Valid Call Patterns
```python
# Inferred from signature:
audio = mir_eval.sonify.chroma(chromagram, times, fs)
```

### LLM Instruction Prompt
- When calling `mir_eval.sonify.chroma`, ensure the `chromagram` input is a 12-row matrix where rows correspond to semitones C through Bb.
- Ensure `times` is provided in seconds and matches the temporal dimension of the `chromagram`.
- Use `kwargs` to pass additional synthesis parameters if specific frequency-domain behavior is required via `time_frequency`.

### Prompt Snippet
```text
# Example usage:
import mir_eval
# chromagram: (12, N), times: (N,), fs: int
audio_signal = mir_eval.sonify.chroma(chromagram, times, fs)
```

### Common Failure Modes
- Shape mismatch: Providing a `chromagram` where the number of columns does not match the length of the `times` array will result in an error.
- Invalid `fs`: Providing a non-integer or non-positive sampling rate may cause synthesis failures.
- Time units: Providing `times` in samples instead of seconds will lead to incorrect audio duration and pitch synthesis.

### Fix Code Hint
```python
# Ensure times are in seconds and chromagram dimensions align
import numpy as np
assert chromagram.shape[1] == len(times)
audio = mir_eval.sonify.chroma(chromagram, times, fs=44100)
```

## API Test: `python:mir_eval.sonify.clicks`

### Signature
```python
def clicks(times, fs, click=None, length=None)
```
_Source: source/mir_eval/sonify.py:15_

_Source doc:_ Return a signal with the signal 'click' placed at each specified time

Parameters
----------
times : np.ndarray
    times to place clicks, in seconds
fs : int
    desired sampling rate of the output signal
click : np.ndarray
    click signal, defaults to a 1 kHz blip
length : int
    desired number of samples in the output signal,
    defaults to ``times.max()*fs + click.shape[0] + 1``

Returns
-------
click_signal : np.ndarray
    Synthesized click signal

### Goal
Synthesize an audio signal containing discrete "click" sounds at specified timestamps to facilitate qualitative "evaluation by ear" of temporal annotations.

### Parameters
- `times`: A 1D NumPy array of timestamps in seconds where clicks should be placed.
- `fs`: The integer sampling rate (in Hz) for the generated output signal.
- `click`, default `None`: An optional NumPy array representing the audio waveform of the click sound; if `None`, a default 1 kHz blip is used.
- `length`, default `None`: The total number of samples in the output array; if `None`, it defaults to `times.max()*fs + click.shape[0] + 1`.

### Input
- `times`: Must be a 1D `np.ndarray` of floats representing time in seconds.
- `fs`: Must be a positive integer.
- `click`: If provided, must be a 1D `np.ndarray` representing the audio signal of the click.
- Preconditions: The `times` array should be sorted chronologically to ensure the output signal is generated correctly.

### Output
Returns `np.ndarray` — A 1D NumPy array containing the synthesized audio signal with clicks at the requested positions.

### Valid Call Patterns
```python
# Example using default click signal
click_track = mir_eval.sonify.clicks(times, fs=44100)

# Example specifying total length
click_track = mir_eval.sonify.clicks(times, fs=44100, length=441000)
```

### LLM Instruction Prompt
- When calling `mir_eval.sonify.clicks`, ensure `times` is a 1D NumPy array of floats.
- Always provide `fs` as an integer.
- If the output signal needs to match the duration of another audio file, calculate the required `length` in samples based on that file's duration and the `fs` provided.

### Prompt Snippet
```text
import mir_eval
# Generate a click track for beat times at 44.1kHz
click_signal = mir_eval.sonify.clicks(beat_times, fs=44100)
```

### Common Failure Modes
- Providing `times` as a list instead of a `np.ndarray` may cause indexing errors.
- Providing `times` that are not sorted can lead to unexpected behavior in the synthesized signal.
- Mismatched `fs` between the `click` signal (if provided) and the `fs` parameter will result in pitch-shifted or incorrectly timed clicks.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure times are a sorted numpy array
times = np.sort(np.array(times_list))
# Generate clicks
click_signal = mir_eval.sonify.clicks(times, fs=44100)
```

## API Test: `python:mir_eval.sonify.pitch_contour`

### Signature
```python
def pitch_contour(times, frequencies, fs, amplitudes=None, function=np.sin, length=None, kind='linear')
```
_Source: source/mir_eval/sonify.py:247_

_Source doc:_ Sonify a pitch contour.

Parameters
----------
times : np.ndarray
    time indices for each frequency measurement, in seconds
frequencies : np.ndarray
    frequency measurements, in Hz.
    Non-positive measurements or NaNs will be interpreted as un-voiced samples.
fs : int
    desired sampling rate of the output signal
amplitudes : np.ndarray
    amplitude measurements, nonnegative
    defaults to ``np.ones((length,))``
function : function
    function to use to synthesize notes, should be :math:`2\pi`-periodic
length : int
    desired number of samples in the output signal,
    defaults to ``max(times)*fs``
kind : str
    Interpolation mode for the frequency and amplitude values.
    See: ``scipy.interpolate.interp1d`` for valid settings.

Returns
-------
output : np.ndarray
    synthesized version of the pitch contour

### Goal
Synthesize an audio signal from a time-varying pitch contour to enable qualitative evaluation of pitch tracking or melody extraction outputs by ear.

### Parameters
- `times`: A 1D NumPy array of time indices in seconds corresponding to each frequency measurement.
- `frequencies`: A 1D NumPy array of fundamental frequency (F0) measurements in Hz.
- `fs`: The integer sampling rate (in Hz) for the generated audio output.
- `amplitudes`, default `None`: A 1D NumPy array of nonnegative amplitude values; if `None`, defaults to a constant amplitude of 1.0.
- `function`, default `np.sin`: A callable function used for synthesis; must be :math:`2\pi`-periodic (e.g., `np.sin` or `np.cos`).
- `length`, default `None`: The total number of samples in the output signal; defaults to the duration of the `times` array multiplied by `fs`.
- `kind`, default `'linear'`: The interpolation method used to map frequency and amplitude values to the output sample rate; passed directly to `scipy.interpolate.interp1d`.

### Input
- **Data:** Requires `times` and `frequencies` as 1D NumPy arrays.
- **Preconditions:** `times` and `frequencies` must be of equal length. `frequencies` should contain positive values for voiced segments; non-positive values or `NaN`s are treated as unvoiced (silence).
- **Format:** Time values must be in seconds.

### Output
Returns a 1D `np.ndarray` containing the synthesized time-domain audio signal at the specified sampling rate `fs`.

### Valid Call Patterns
```python
# Inferred from signature:
import numpy as np
import mir_eval

# Example: Sonifying a simple pitch contour
audio = mir_eval.sonify.pitch_contour(times, frequencies, fs=44100)
```

### LLM Instruction Prompt
- When calling `mir_eval.sonify.pitch_contour`, ensure `times` and `frequencies` are 1D NumPy arrays of the same length.
- Always specify `fs` as an integer.
- If the synthesis sounds distorted, verify that the `function` provided is indeed :math:`2\pi`-periodic.
- Use `kind` to control the smoothness of pitch transitions (e.g., 'linear', 'cubic').

### Prompt Snippet
```text
# Example usage of mir_eval.sonify.pitch_contour
audio_signal = mir_eval.sonify.pitch_contour(times, frequencies, fs=22050, kind='linear')
```

### Common Failure Modes
- **Shape Mismatch:** Providing `times` and `frequencies` arrays of different lengths will raise a `ValueError`.
- **Invalid Frequencies:** Passing negative frequencies or `NaN` values is supported for unvoiced segments, but ensure the input array is cleaned if specific behavior for silence is required.
- **Non-Periodic Function:** Providing a function that is not :math:`2\pi`-periodic will result in incorrect waveform synthesis.
- **Interpolation Errors:** Using an invalid `kind` string for `scipy.interpolate.interp1d` will raise an error during the interpolation phase.

### Fix Code Hint
```python
# Ensure inputs are valid before sonification
import numpy as np
frequencies = np.nan_to_num(frequencies, nan=0.0)
frequencies[frequencies < 0] = 0.0
audio = mir_eval.sonify.pitch_contour(times, frequencies, fs=fs)
```

## API Test: `python:mir_eval.sonify.time_frequency`

### Signature
```python
def time_frequency(gram, frequencies, times, fs, function=np.sin, length=None, n_dec=1, threshold=0.01)
```
_Source: source/mir_eval/sonify.py:64_

_Source doc:_ Reverse synthesis of a time-frequency representation of a signal

Parameters
----------
gram : np.ndarray
    ``gram[n, m]`` is the magnitude of ``frequencies[n]``
    from ``times[m]`` to ``times[m + 1]``

    Non-positive magnitudes are interpreted as silence.

frequencies : np.ndarray
    array of size ``gram.shape[0]`` denoting the frequency (in Hz) of
    each row of gram

times : np.ndarray, shape= ``(gram.shape[1],)`` or ``(gram.shape[1], 2)``
    Either the start time (in seconds) of each column in the gram,
    or the time interval (in seconds) corresponding to each column.

fs : int
    desired sampling rate of the output signal

function : function
    function to use to synthesize notes, should be :math:`2\pi`-periodic

length : int
    desired number of samples in the output signal,
    defaults to ``times[-1]*fs``

n_dec : int
    the number of decimals used to approximate each sonfied frequency.
    Defaults to 1 decimal place. Higher precision will be slower.

threshold : float
    optimizes synthesis to only occur for frequencies that have a
    linear magnitude of at least one element in gram above the given threshold.

Returns
-------
output : np.ndarray
    synthesized version of the piano roll

### Goal
Synthesize an audio signal from a time-frequency representation (such as a spectrogram or piano roll) to enable qualitative "evaluation by ear" of MIR system outputs.

### Parameters
- `gram`: A 2D NumPy array where rows correspond to frequency bins and columns correspond to time segments.
- `frequencies`: A 1D NumPy array of length `gram.shape[0]` specifying the frequency in Hz for each row.
- `times`: A 1D array of start times or a 2D array of `[start, end]` intervals (in seconds) for each column in `gram`.
- `fs`: The sampling rate (in Hz) for the generated audio output.
- `function`, default `np.sin`: A $2\pi$-periodic function used to synthesize the waveform for each frequency component.
- `length`, default `None`: The total number of samples in the output array; defaults to the end time of the final interval multiplied by `fs`.
- `n_dec`, default `1`: Precision for frequency approximation; higher values increase computational cost.
- `threshold`, default `0.01`: Minimum magnitude threshold for a frequency component to be included in the synthesis.

### Input
The caller must provide a time-frequency representation as a `gram` matrix, corresponding frequency bins, and time intervals in seconds. All time-based inputs must be in seconds. The `gram` matrix should be non-negative, as non-positive values are treated as silence.

### Output
Returns a 1D `np.ndarray` containing the synthesized time-domain audio signal.

### Valid Call Patterns
```python
# Example inferred from signature
audio = mir_eval.sonify.time_frequency(gram, frequencies, times, fs)
```

### LLM Instruction Prompt
- When calling `mir_eval.sonify.time_frequency`, ensure `gram` and `frequencies` have compatible dimensions (`gram.shape[0] == len(frequencies)`).
- Ensure `times` is provided in seconds and matches the column dimension of `gram`.
- If custom synthesis is required, provide a $2\pi$-periodic function for the `function` parameter.

### Prompt Snippet
```text
# Synthesize audio from a spectrogram-like representation
audio_signal = mir_eval.sonify.time_frequency(gram_data, freq_bins, time_intervals, fs=44100)
```

### Common Failure Modes
- **Dimension Mismatch:** Providing `times` or `frequencies` arrays that do not align with the dimensions of the `gram` matrix will raise an error.
- **Performance Issues:** Setting `n_dec` to a high value significantly increases the synthesis time.
- **Invalid Time Units:** Providing time values in samples instead of seconds will result in incorrect audio duration or silence.

### Fix Code Hint
```python
# Ensure times are in seconds and gram dimensions match
import numpy as np
# Example: gram (100, 50), frequencies (100,), times (50,)
audio = mir_eval.sonify.time_frequency(gram, frequencies, times, fs=22050)
```

## API Test: `python:mir_eval.tempo.detection`

### Signature
```python
def detection(reference_tempi, reference_weight, estimated_tempi, tol=0.08)
```
_Source: source/mir_eval/tempo.py:73_

_Source doc:_ Compute the tempo detection accuracy metric.

Parameters
----------
reference_tempi : np.ndarray, shape=(2,)
    Two non-negative reference tempi
reference_weight : float > 0
    The relative strength of ``reference_tempi[0]`` vs
    ``reference_tempi[1]``.
estimated_tempi : np.ndarray, shape=(2,)
    Two non-negative estimated tempi.
tol : float in [0, 1]:
    The maximum allowable deviation from a reference tempo to
    count as a hit.
    ``|est_t - ref_t| <= tol * ref_t``
    (Default value = 0.08)

Returns
-------
p_score : float in [0, 1]
    Weighted average of recalls:
    ``reference_weight * hits[0] + (1 - reference_weight) * hits[1]``
one_correct : bool
    True if at least one reference tempo was correctly estimated
both_correct : bool
    True if both reference tempi were correctly estimated

Raises
------
ValueError
    If the input tempi are ill-formed

    If the reference weight is not in the range [0, 1]

    If ``tol < 0`` or ``tol > 1``.

### Goal
Computes the tempo detection accuracy metric by comparing estimated tempi against reference tempi using a weighted recall score based on allowable deviation tolerances.

### Parameters
- `reference_tempi`: A NumPy array of shape `(2,)` containing two non-negative reference tempi in BPM, provided in ascending order.
- `reference_weight`: A float in the range `[0, 1]` representing the relative strength or importance of the first reference tempo compared to the second.
- `estimated_tempi`: A NumPy array of shape `(2,)` containing two non-negative estimated tempi in BPM.
- `tol`, default `0.08`: A float in the range `[0, 1]` defining the maximum relative deviation from a reference tempo to count as a hit.

### Input
The caller must provide two NumPy arrays of length 2 representing tempi in BPM. Preconditions: `reference_tempi` must be sorted in ascending order, and all tempo values must be non-negative. The `reference_weight` must be a float between 0 and 1.

### Output
Returns a tuple containing:
- `p_score` (float): The weighted average of recalls.
- `one_correct` (bool): True if at least one reference tempo was correctly estimated within the tolerance.
- `both_correct` (bool): True if both reference tempi were correctly estimated within the tolerance.

### Valid Call Patterns
```python
import numpy as np
import mir_eval

# Example of computing tempo detection accuracy
reference_tempi = np.array([60.0, 120.0])
reference_weight = 0.8
estimated_tempi = np.array([62.0, 118.0])

p_score, one_correct, both_correct = mir_eval.tempo.detection(
    reference_tempi, reference_weight, estimated_tempi)
```

### LLM Instruction Prompt
When calling `mir_eval.tempo.detection`, ensure that `reference_tempi` and `estimated_tempi` are provided as 1D NumPy arrays of length 2. Always ensure `reference_tempi` is sorted in ascending order. Validate that `reference_weight` is a float between 0 and 1, and `tol` is within `[0, 1]` to avoid `ValueError`.

### Prompt Snippet
```text
p_score, one_correct, both_correct = mir_eval.tempo.detection(
    reference_tempi, reference_weight, estimated_tempi, tol=0.08)
```

### Common Failure Modes
- **ValueError:** Raised if `reference_weight` is outside `[0, 1]`, if `tol` is outside `[0, 1]`, or if input arrays are not of shape `(2,)`.
- **Incorrect Ordering:** Providing `reference_tempi` in descending order will lead to incorrect metric calculation as the function expects ascending order.
- **Negative Values:** Providing negative tempo values will trigger a `ValueError` as the function requires non-negative inputs.

### Fix Code Hint
```python
# Ensure inputs are sorted and valid
reference_tempi = np.sort(reference_tempi)
if not (0 <= reference_weight <= 1):
    reference_weight = np.clip(reference_weight, 0, 1)
```

## API Test: `python:mir_eval.tempo.evaluate`

### Signature
```python
def evaluate(reference_tempi, reference_weight, estimated_tempi, **kwargs)
```
_Source: source/mir_eval/tempo.py:138_

_Source doc:_ Compute all metrics for the given reference and estimated annotations.

Parameters
----------
reference_tempi : np.ndarray, shape=(2,)
    Two non-negative reference tempi
reference_weight : float > 0
    The relative strength of ``reference_tempi[0]`` vs
    ``reference_tempi[1]``.
estimated_tempi : np.ndarray, shape=(2,)
    Two non-negative estimated tempi.
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of tempo detection accuracy metrics by comparing reference tempo annotations against estimated tempo outputs.

### Parameters
- `reference_tempi`: A 1D NumPy array of shape `(2,)` containing two non-negative reference tempi in BPM, provided in ascending order.
- `reference_weight`: A float greater than 0 representing the relative strength or importance of the first reference tempo compared to the second.
- `estimated_tempi`: A 1D NumPy array of shape `(2,)` containing two non-negative estimated tempi in BPM.
- `kwargs`: Optional keyword arguments passed directly to underlying metric or preprocessing functions.

### Input
- **Data Format:** Inputs must be provided as NumPy arrays for tempi and a float for the weight.
- **Preconditions:** Reference tempi must be non-negative and provided in ascending order. The `reference_weight` must be a positive float.
- **Validation:** Ensure inputs are validated against the `mir_eval.tempo` module constraints before evaluation.

### Output
Returns a `dict` where keys are strings representing metric names (e.g., tempo detection accuracy scores) and values are `float` scores achieved by the estimation.

### Valid Call Patterns
```python
# Example inferred from signature and tempo module documentation
import numpy as np
import mir_eval

ref_tempi = np.array([60.0, 120.0])
ref_weight = 0.8
est_tempi = np.array([60.0, 118.0])

scores = mir_eval.tempo.evaluate(ref_tempi, ref_weight, est_tempi)
```

### LLM Instruction Prompt
- When calling `mir_eval.tempo.evaluate`, ensure `reference_tempi` and `estimated_tempi` are NumPy arrays of shape `(2,)`.
- Always provide `reference_tempi` in ascending order.
- Ensure `reference_weight` is a positive float.
- The function returns a dictionary; access specific metrics by their string keys.

### Prompt Snippet
```text
scores = mir_eval.tempo.evaluate(reference_tempi, reference_weight, estimated_tempi)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays that are not of shape `(2,)` will cause the evaluation to fail.
- **Ordering:** Providing `reference_tempi` in descending order violates the input precondition.
- **Non-positive values:** Providing negative values for tempi or a non-positive value for `reference_weight` will result in invalid metric calculations.

### Fix Code Hint
```python
# Ensure tempi are sorted and positive
ref_tempi = np.sort(np.array([t1, t2]))
# Ensure weight is positive
weight = max(0.0001, weight)
scores = mir_eval.tempo.evaluate(ref_tempi, weight, est_tempi)
```

## API Test: `python:mir_eval.tempo.validate`

### Signature
```python
def validate(reference_tempi, reference_weight, estimated_tempi)
```
_Source: source/mir_eval/tempo.py:52_

_Source doc:_ Check that the input annotations to a metric look like valid tempo
annotations.

Parameters
----------
reference_tempi : np.ndarray
    reference tempo values, in bpm
reference_weight : float
    perceptual weight of slow vs fast in reference
estimated_tempi : np.ndarray
    estimated tempo values, in bpm

### Goal
Validates that tempo annotation arrays and weights conform to the expected format and constraints required for tempo evaluation metrics.

### Parameters
- `reference_tempi`: A NumPy array containing reference tempo values in beats per minute (BPM).
- `reference_weight`: A float representing the perceptual weight of slow versus fast tempi in the reference, typically in the range [0, 1].
- `estimated_tempi`: A NumPy array containing estimated tempo values in beats per minute (BPM).

### Input
- **Data Format:** `reference_tempi` and `estimated_tempi` must be provided as NumPy arrays.
- **Preconditions:** Reference tempi must be positive values and provided in ascending order. The `reference_weight` must be a float in the range [0, 1].

### Output
Returns `None` if the inputs are valid. If the inputs do not conform to the expected format or constraints, the function will raise an exception (e.g., `ValueError`).

### Valid Call Patterns
```python
import numpy as np
import mir_eval

# Example inferred from signature
ref_tempi = np.array([60.0, 120.0])
est_tempi = np.array([62.0, 121.0])
weight = 0.5
mir_eval.tempo.validate(ref_tempi, weight, est_tempi)
```

### LLM Instruction Prompt
- When calling `mir_eval.tempo.validate`, ensure that `reference_tempi` and `estimated_tempi` are NumPy arrays.
- Verify that `reference_tempi` is sorted in ascending order and contains only positive values.
- Ensure `reference_weight` is a float between 0 and 1.
- Use this function before passing data to `mir_eval.tempo` evaluation functions to ensure data integrity.

### Prompt Snippet
```text
mir_eval.tempo.validate(reference_tempi, reference_weight, estimated_tempi)
```

### Common Failure Modes
- **Unsorted Arrays:** Passing `reference_tempi` that is not in ascending order.
- **Invalid Weight:** Providing a `reference_weight` outside the [0, 1] range.
- **Non-positive Tempi:** Including zero or negative values in the tempo arrays.
- **Type Mismatch:** Passing lists instead of NumPy arrays for the tempo arguments.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure inputs are sorted and positive
ref_tempi = np.sort(np.array(ref_tempi))
est_tempi = np.array(est_tempi)
weight = float(weight)

mir_eval.tempo.validate(ref_tempi, weight, est_tempi)
```

## API Test: `python:mir_eval.tempo.validate_tempi`

### Signature
```python
def validate_tempi(tempi, reference=True)
```
_Source: source/mir_eval/tempo.py:29_

_Source doc:_ Check that there are two non-negative tempi.
For a reference value, at least one tempo has to be greater than zero.

Parameters
----------
tempi : np.ndarray
    length-2 array of tempo, in bpm
reference : bool
    indicates a reference value

### Goal
Validates that a given tempo array conforms to the structural and logical requirements for tempo evaluation in MIR tasks.

### Parameters
- `tempi`: A `np.ndarray` of length 2 containing tempo values in beats per minute (BPM).
- `reference`, default `True`: A boolean flag indicating whether the input is a reference (ground truth) value, which enforces stricter non-zero constraints.

### Input
- **Data Format:** A 1D `np.ndarray` of length 2.
- **Preconditions:** The array must contain non-negative values. If `reference=True`, at least one of the two values must be strictly greater than zero.
- **Ordering:** Per project conventions, reference tempi should be provided in ascending order.

### Output
Returns `None` if validation succeeds. Raises an exception (e.g., `ValueError`) if the input array does not meet the length, non-negativity, or reference-specific constraints.

### Valid Call Patterns
```python
import numpy as np
import mir_eval

# Validating a reference tempo array
ref_tempi = np.array([60.0, 120.0])
mir_eval.tempo.validate_tempi(ref_tempi, reference=True)

# Validating an estimated tempo array
est_tempi = np.array([0.0, 120.0])
mir_eval.tempo.validate_tempi(est_tempi, reference=False)
```

### LLM Instruction Prompt
- Always ensure the `tempi` input is a `numpy.ndarray` of length 2.
- If the input represents ground truth, ensure `reference=True` is set to enforce the non-zero tempo requirement.
- Ensure tempo values are non-negative before passing them to this function.

### Prompt Snippet
```text
# Validate tempo inputs before evaluation
mir_eval.tempo.validate_tempi(tempi_array, reference=is_ground_truth)
```

### Common Failure Modes
- **Shape Mismatch:** Passing an array that is not length 2 will cause a validation error.
- **Negative Values:** Providing negative BPM values will fail the non-negative constraint.
- **Reference Zero-Constraint:** If `reference=True`, passing `[0.0, 0.0]` will raise an error because at least one tempo must be greater than zero.
- **Type Errors:** Passing a list instead of a `np.ndarray` may cause issues depending on the internal implementation; always cast to `np.array` first.

### Fix Code Hint
```python
import numpy as np
# Ensure input is a numpy array of length 2 and non-negative
tempi = np.array(tempi_data, dtype=float)
if tempi.size != 2:
    raise ValueError("Tempi must be a length-2 array.")
mir_eval.tempo.validate_tempi(tempi, reference=True)
```

## API Test: `python:mir_eval.transcription.average_overlap_ratio`

### Signature
```python
def average_overlap_ratio(ref_intervals, est_intervals, matching)
```
_Source: source/mir_eval/transcription.py:592_

_Source doc:_ Compute the Average Overlap Ratio between a reference and estimated
note transcription. Given a reference and corresponding estimated note,
their overlap ratio (OR) is defined as the ratio between the duration of
the time segment in which the two notes overlap and the time segment
spanned by the two notes combined (earliest onset to latest offset):

>>> OR = ((min(ref_offset, est_offset) - max(ref_onset, est_onset)) /
...     (max(ref_offset, est_offset) - min(ref_onset, est_onset)))

The Average Overlap Ratio (AOR) is given by the mean OR computed over all
matching reference and estimated notes. The metric goes from 0 (worst) to 1
(best).

Note: this function assumes the matching of reference and estimated notes
(see :func:`match_notes`) has already been performed and is provided by the
``matching`` parameter. Furthermore, it is highly recommended to validate
the intervals (see :func:`validate_intervals`) before calling this
function, otherwise it is possible (though unlikely) for this function to
attempt a divide-by-zero operation.

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
matching : list of tuples
    A list of matched reference and estimated notes.
    ``matching[i] == (i, j)`` where reference note ``i`` matches estimated
    note ``j``.

Returns
-------
avg_overlap_ratio : float
    The computed Average Overlap Ratio score

### Goal
Computes the mean overlap ratio between matched reference and estimated note intervals to quantify the temporal precision of a transcription system.

### Parameters
- `ref_intervals`: A NumPy array of shape `(n, 2)` containing the onset and offset times (in seconds) for reference notes.
- `est_intervals`: A NumPy array of shape `(m, 2)` containing the onset and offset times (in seconds) for estimated notes.
- `matching`: A list of tuples `(i, j)` where `i` is the index of a reference note and `j` is the index of the corresponding estimated note.

### Input
- **Data Format:** Intervals must be provided as `(n, 2)` NumPy arrays where each row is `[onset, offset]`.
- **Preconditions:** 
    - Time values must be in seconds.
    - It is highly recommended to run `mir_eval.transcription.validate_intervals` on both input arrays prior to calling this function to ensure valid interval structures.
    - The `matching` list must be pre-computed (e.g., using `mir_eval.transcription.match_notes`).

### Output
Returns a `float` representing the Average Overlap Ratio (AOR), ranging from 0 (no overlap) to 1 (perfect temporal alignment).

### Valid Call Patterns
```python
# Inferred from signature and documentation
aor = mir_eval.transcription.average_overlap_ratio(ref_intervals, est_intervals, matching)
```

### LLM Instruction Prompt
- Always ensure `ref_intervals` and `est_intervals` are validated using `mir_eval.transcription.validate_intervals` before passing them to this function.
- Ensure the `matching` list contains valid indices corresponding to the rows of the provided interval arrays.
- The function does not perform matching itself; ensure `match_notes` has been executed successfully first.

### Prompt Snippet
```text
# Example usage:
# 1. Validate intervals
mir_eval.transcription.validate_intervals(ref_intervals)
mir_eval.transcription.validate_intervals(est_intervals)
# 2. Compute matching
matching = mir_eval.transcription.match_notes(ref_intervals, ref_pitches, est_intervals, est_pitches)
# 3. Calculate AOR
aor = mir_eval.transcription.average_overlap_ratio(ref_intervals, est_intervals, matching)
```

### Common Failure Modes
- **Divide-by-zero:** Occurs if intervals are malformed (e.g., onset equals offset). Always validate intervals first.
- **IndexError:** Occurs if the `matching` list contains indices that are out of bounds for the provided `ref_intervals` or `est_intervals` arrays.
- **Empty Matching:** If no notes are matched, the mean calculation may fail or return NaN depending on implementation; ensure the matching process yields at least one pair.

### Fix Code Hint
```python
# Ensure intervals are valid before computation
mir_eval.transcription.validate_intervals(ref_intervals)
mir_eval.transcription.validate_intervals(est_intervals)
# Proceed with calculation
score = mir_eval.transcription.average_overlap_ratio(ref_intervals, est_intervals, matching)
```

## API Test: `python:mir_eval.transcription.evaluate`

### Signature
```python
def evaluate(ref_intervals, ref_pitches, est_intervals, est_pitches, **kwargs)
```
_Source: source/mir_eval/transcription.py:785_

_Source doc:_ Compute all metrics for the given reference and estimated annotations.

Examples
--------
>>> ref_intervals, ref_pitches = mir_eval.io.load_valued_intervals(
...    'reference.txt')
>>> est_intervals, est_pitches = mir_eval.io.load_valued_intervals(
...    'estimate.txt')
>>> scores = mir_eval.transcription.evaluate(ref_intervals, ref_pitches,
...     est_intervals, est_pitches)

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
ref_pitches : np.ndarray, shape=(n,)
    Array of reference pitch values in Hertz
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
est_pitches : np.ndarray, shape=(m,)
    Array of estimated pitch values in Hertz
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of transcription performance metrics (such as Precision, Recall, and F-measure) by comparing estimated note events against ground-truth reference annotations.

### Parameters
- `ref_intervals`: An $N \times 2$ NumPy array containing the start and end times (in seconds) for each reference note.
- `ref_pitches`: A 1D NumPy array of length $N$ containing the fundamental frequency (F0) in Hertz for each reference note.
- `est_intervals`: An $M \times 2$ NumPy array containing the start and end times (in seconds) for each estimated note.
- `est_pitches`: A 1D NumPy array of length $M$ containing the fundamental frequency (F0) in Hertz for each estimated note.
- `kwargs`: Optional keyword arguments passed to underlying metric or preprocessing functions, such as matching tolerances.

### Input
- **Data Format:** Requires NumPy arrays. Time values must be in seconds; pitch values must be in Hertz.
- **Preconditions:** Reference and estimated arrays should be sorted by time. The transcription module uses bipartite graph matching to establish correspondences between reference and estimated notes based on onset, offset, and pitch tolerances.

### Output
Returns a `dict` where keys are metric names (strings) and values are the corresponding scalar scores (floats).

### Valid Call Patterns
```python
import mir_eval
scores = mir_eval.transcription.evaluate(ref_intervals, ref_pitches, est_intervals, est_pitches)
```

### LLM Instruction Prompt
When calling `mir_eval.transcription.evaluate`, ensure that all time-based inputs are provided in seconds and pitch values are in Hertz. Always validate input arrays using `mir_eval.transcription.validate` before passing them to `evaluate` to ensure they conform to the expected shapes and constraints.

### Prompt Snippet
```text
# Ensure inputs are validated before evaluation
mir_eval.transcription.validate(ref_intervals, ref_pitches, est_intervals, est_pitches)
scores = mir_eval.transcription.evaluate(ref_intervals, ref_pitches, est_intervals, est_pitches)
```

### Common Failure Modes
- **Unsorted Inputs:** Metrics may produce incorrect results if input arrays are not sorted by onset time.
- **Validation Errors:** Passing arrays with mismatched dimensions or invalid shapes will trigger exceptions.
- **Matching Thresholds:** The default bipartite matching uses specific tolerances; if results are unexpected, check if `kwargs` are needed to adjust matching criteria (e.g., `strict` mode).
- **Empty Arrays:** Ensure that empty input arrays are handled or validated, as behavior for empty sets may vary depending on the specific metric implementation.

### Fix Code Hint
```python
# Use util to ensure intervals are sorted if necessary
import mir_eval.util
ref_intervals, ref_pitches = mir_eval.util.sort_labeled_intervals(ref_intervals, ref_pitches)
est_intervals, est_pitches = mir_eval.util.sort_labeled_intervals(est_intervals, est_pitches)
```

## API Test: `python:mir_eval.transcription.match_note_offsets`

### Signature
```python
def match_note_offsets(ref_intervals, est_intervals, offset_ratio=0.2, offset_min_tolerance=0.05, strict=False)
```
_Source: source/mir_eval/transcription.py:170_

_Source doc:_ Compute a maximum matching between reference and estimated notes,
only taking note offsets into account.

Given two note sequences represented by ``ref_intervals`` and
``est_intervals`` (see :func:`mir_eval.io.load_valued_intervals`), we seek
the largest set of correspondences ``(i, j)`` such that the offset of
reference note ``i`` has to be within ``offset_tolerance`` of the offset of
estimated note ``j``, where ``offset_tolerance`` is equal to
``offset_ratio`` times the reference note's duration, i.e.  ``offset_ratio
* ref_duration[i]`` where ``ref_duration[i] = ref_intervals[i, 1] -
ref_intervals[i, 0]``. If the resulting ``offset_tolerance`` is less than
``offset_min_tolerance`` (50 ms by default) then ``offset_min_tolerance``
is used instead.

Every reference note is matched against at most one estimated note.

Note there are separate functions :func:`match_note_onsets` and
:func:`match_notes` for matching notes based on onsets only or based on
onset, offset, and pitch, respectively. This is because the rules for
matching note onsets and matching note offsets are different.

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
offset_ratio : float > 0
    The ratio of the reference note's duration used to define the
    ``offset_tolerance``. Default is 0.2 (20%), meaning the
    ``offset_tolerance`` will equal the ``ref_duration * 0.2``, or 0.05 (50
    ms), whichever is greater.
offset_min_tolerance : float > 0
    The minimum tolerance for offset matching. See ``offset_ratio``
    description for an explanation of how the offset tolerance is
    determined.
strict : bool
    If ``strict=False`` (the default), threshold checks for offset
    matching are performed using ``<=`` (less than or equal). If
    ``strict=True``, the threshold checks are performed using ``<`` (less
    than).

Returns
-------
matching : list of tuples
    A list of matched reference and estimated notes.
    ``matching[i] == (i, j)`` where reference note ``i`` matches estimated
    note ``j``.

### Goal
Identify the optimal bipartite matching between reference and estimated note sequences based exclusively on the proximity of their offset timestamps.

### Parameters
- `ref_intervals`: A NumPy array of shape `(n, 2)` containing the `[onset, offset]` times in seconds for reference notes.
- `est_intervals`: A NumPy array of shape `(m, 2)` containing the `[onset, offset]` times in seconds for estimated notes.
- `offset_ratio`, default `0.2`: The scaling factor applied to the reference note duration to determine the dynamic offset tolerance.
- `offset_min_tolerance`, default `0.05`: The floor value (in seconds) for the offset tolerance; the tolerance used is `max(offset_ratio * duration, offset_min_tolerance)`.
- `strict`, default `False`: Boolean flag; if `True`, uses strict inequality (`<`) for threshold comparison; if `False` (default), uses inclusive inequality (`<=`).

### Input
- **Data Format:** Requires `np.ndarray` inputs for intervals.
- **Preconditions:** Inputs must be validated (e.g., using `mir_eval.transcription.validate`) to ensure correct shapes and that intervals are well-formed (onset < offset).
- **Sorting:** While not explicitly enforced by the function, standard `mir_eval` workflows assume intervals are sorted by onset time.

### Output
Returns `list of tuples`: A list of index pairs `(i, j)` representing the maximum matching, where `i` is the index of the reference note and `j` is the index of the estimated note.

### Valid Call Patterns
```python
# Inferred from signature:
matching = mir_eval.transcription.match_note_offsets(ref_intervals, est_intervals)
```

### LLM Instruction Prompt
- When calling `match_note_offsets`, ensure `ref_intervals` and `est_intervals` are `np.ndarray` objects.
- Do not use this function for onset-only or pitch-aware matching; use `match_note_onsets` or `match_notes` respectively.
- Always verify that the input arrays are sorted by time before processing.

### Prompt Snippet
```text
import mir_eval
# Ensure intervals are loaded as (n, 2) arrays
# matching = mir_eval.transcription.match_note_offsets(ref_intervals, est_intervals, ...)
```

### Common Failure Modes
- **Unsorted Inputs:** Providing unsorted intervals may lead to incorrect matching results.
- **Empty Arrays:** Passing empty arrays may result in an empty list, which should be handled by the caller.
- **Tolerance Mismatch:** Using the default `offset_min_tolerance` (50ms) may be too loose or too strict depending on the specific transcription task requirements (e.g., percussive vs. sustained notes).

### Fix Code Hint
```python
# Ensure inputs are sorted by onset time before matching
ref_intervals = ref_intervals[ref_intervals[:, 0].argsort()]
est_intervals = est_intervals[est_intervals[:, 0].argsort()]
matching = mir_eval.transcription.match_note_offsets(ref_intervals, est_intervals)
```

## API Test: `python:mir_eval.transcription.match_note_onsets`

### Signature
```python
def match_note_onsets(ref_intervals, est_intervals, onset_tolerance=0.05, strict=False)
```
_Source: source/mir_eval/transcription.py:263_

_Source doc:_ Compute a maximum matching between reference and estimated notes,
only taking note onsets into account.

Given two note sequences represented by ``ref_intervals`` and
``est_intervals`` (see :func:`mir_eval.io.load_valued_intervals`), we see
the largest set of correspondences ``(i,j)`` such that the onset of
reference note ``i`` is within ``onset_tolerance`` of the onset of
estimated note ``j``.

Every reference note is matched against at most one estimated note.

Note there are separate functions :func:`match_note_offsets` and
:func:`match_notes` for matching notes based on offsets only or based on
onset, offset, and pitch, respectively. This is because the rules for
matching note onsets and matching note offsets are different.

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
onset_tolerance : float > 0
    The tolerance for an estimated note's onset deviating from the
    reference note's onset, in seconds. Default is 0.05 (50 ms).
strict : bool
    If ``strict=False`` (the default), threshold checks for onset matching
    are performed using ``<=`` (less than or equal). If ``strict=True``,
    the threshold checks are performed using ``<`` (less than).

Returns
-------
matching : list of tuples
    A list of matched reference and estimated notes.
    ``matching[i] == (i, j)`` where reference note ``i`` matches estimated
    note ``j``.

### Goal
Compute a maximum bipartite matching between reference and estimated note sequences based solely on the temporal proximity of their onsets.

### Parameters
- `ref_intervals`: A NumPy array of shape `(n, 2)` containing the ground-truth note onset and offset times in seconds.
- `est_intervals`: A NumPy array of shape `(m, 2)` containing the estimated note onset and offset times in seconds.
- `onset_tolerance`, default `0.05`: The maximum allowed temporal deviation (in seconds) between a reference onset and an estimated onset to consider them a match.
- `strict`, default `False`: Boolean flag determining the comparison operator for the tolerance threshold; `False` uses `<=`, `True` uses `<`.

### Input
- **Data Format:** Intervals should be provided as `(n, 2)` NumPy arrays where each row is `[onset, offset]`.
- **Preconditions:** Input arrays must be validated (e.g., using `mir_eval.transcription.validate`) to ensure they contain valid time intervals. Arrays should be sorted by onset time.

### Output
Returns a `list` of `tuples`, where each tuple `(i, j)` represents a match between the reference note at index `i` and the estimated note at index `j`.

### Valid Call Patterns
```python
# Inferred from signature:
matching = mir_eval.transcription.match_note_onsets(ref_intervals, est_intervals, onset_tolerance=0.05, strict=False)
```

### LLM Instruction Prompt
- Always ensure `ref_intervals` and `est_intervals` are `np.ndarray` objects of shape `(n, 2)`.
- Ensure time values are in seconds.
- Use this function only when evaluating onset-based performance; do not use it if pitch or offset accuracy is required (use `match_notes` instead).

### Prompt Snippet
```text
# Example usage:
import mir_eval
# Assuming ref_intervals and est_intervals are loaded as (n, 2) arrays
matches = mir_eval.transcription.match_note_onsets(ref_intervals, est_intervals, onset_tolerance=0.05)
```

### Common Failure Modes
- **Unsorted Inputs:** Providing unsorted interval arrays may lead to incorrect matching results.
- **Incorrect Dimensions:** Passing arrays that are not `(n, 2)` will cause shape mismatch errors.
- **Tolerance Mismatch:** Using an inappropriate `onset_tolerance` for the specific musical tempo or genre can lead to overly aggressive or overly conservative matching.
- **Strictness Confusion:** Misunderstanding the `strict` parameter can lead to off-by-one-sample errors in thresholding.

### Fix Code Hint
```python
# Ensure inputs are sorted by onset time before matching
ref_intervals = ref_intervals[ref_intervals[:, 0].argsort()]
est_intervals = est_intervals[est_intervals[:, 0].argsort()]
matches = mir_eval.transcription.match_note_onsets(ref_intervals, est_intervals)
```

## API Test: `python:mir_eval.transcription.match_notes`

### Signature
```python
def match_notes(ref_intervals, ref_pitches, est_intervals, est_pitches, onset_tolerance=0.05, pitch_tolerance=50.0, offset_ratio=0.2, offset_min_tolerance=0.05, strict=False)
```
_Source: source/mir_eval/transcription.py:336_

_Source doc:_ Compute a maximum matching between reference and estimated notes,
subject to onset, pitch and (optionally) offset constraints.

Given two note sequences represented by ``ref_intervals``, ``ref_pitches``,
``est_intervals`` and ``est_pitches``
(see :func:`mir_eval.io.load_valued_intervals`), we seek the largest set
of correspondences ``(i, j)`` such that:

1. The onset of reference note ``i`` is within ``onset_tolerance`` of the
   onset of estimated note ``j``.
2. The pitch of reference note ``i`` is within ``pitch_tolerance`` of the
   pitch of estimated note ``j``.
3. If ``offset_ratio`` is not ``None``, the offset of reference note ``i``
   has to be within ``offset_tolerance`` of the offset of estimated note
   ``j``, where ``offset_tolerance`` is equal to ``offset_ratio`` times the
   reference note's duration, i.e. ``offset_ratio * ref_duration[i]`` where
   ``ref_duration[i] = ref_intervals[i, 1] - ref_intervals[i, 0]``.  If the
   resulting ``offset_tolerance`` is less than 0.05 (50 ms), 0.05 is used
   instead.
4. If ``offset_ratio`` is ``None``, note offsets are ignored, and only
   criteria 1 and 2 are taken into consideration.

Every reference note is matched against at most one estimated note.

This is useful for computing precision/recall metrics for note
transcription.

Note there are separate functions :func:`match_note_onsets` and
:func:`match_note_offsets` for matching notes based on onsets only or based
on offsets only, respectively.

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
ref_pitches : np.ndarray, shape=(n,)
    Array of reference pitch values in Hertz
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
est_pitches : np.ndarray, shape=(m,)
    Array of estimated pitch values in Hertz
onset_tolerance : float > 0
    The tolerance for an estimated note's onset deviating from the
    reference note's onset, in seconds. Default is 0.05 (50 ms).
pitch_tolerance : float > 0
    The tolerance for an estimated note's pitch deviating from the
    reference note's pitch, in cents. Default is 50.0 (50 cents).
offset_ratio : float > 0 or None
    The ratio of the reference note's duration used to define the
    offset_tolerance. Default is 0.2 (20%), meaning the
    ``offset_tolerance`` will equal the ``ref_duration * 0.2``, or 0.05 (50
    ms), whichever is greater. If ``offset_ratio`` is set to ``None``,
    offsets are ignored in the matching.
offset_min_tolerance : float > 0
    The minimum tolerance for offset matching. See offset_ratio description
    for an explanation of how the offset tolerance is determined. Note:
    this parameter only influences the results if ``offset_ratio`` is not
    ``None``.
strict : bool
    If ``strict=False`` (the default), threshold checks for onset, offset,
    and pitch matching are performed using ``<=`` (less than or equal). If
    ``strict=True``, the threshold checks are performed using ``<`` (less
    than).

Returns
-------
matching : list of tuples
    A list of matched reference and estimated notes.
    ``matching[i] == (i, j)`` where reference note ``i`` matches estimated
    note ``j``.

### Goal
Computes the optimal bipartite matching between reference and estimated note sequences based on onset, pitch, and duration-dependent offset constraints for transcription evaluation.

### Parameters
- `ref_intervals`: `np.ndarray` of shape `(n, 2)` containing `[onset, offset]` times in seconds for reference notes.
- `ref_pitches`: `np.ndarray` of shape `(n,)` containing fundamental frequencies in Hertz for reference notes.
- `est_intervals`: `np.ndarray` of shape `(m, 2)` containing `[onset, offset]` times in seconds for estimated notes.
- `est_pitches`: `np.ndarray` of shape `(m,)` containing fundamental frequencies in Hertz for estimated notes.
- `onset_tolerance`, default `0.05`: Maximum allowed deviation in seconds between reference and estimated note onsets.
- `pitch_tolerance`, default `50.0`: Maximum allowed deviation in cents between reference and estimated note pitches.
- `offset_ratio`, default `0.2`: Ratio of reference duration used to calculate offset tolerance; if `None`, offsets are ignored.
- `offset_min_tolerance`, default `0.05`: Minimum threshold in seconds for offset matching when `offset_ratio` is active.
- `strict`, default `False`: If `True`, uses `<` for threshold comparisons; if `False`, uses `<=`.

### Input
Inputs must be validated NumPy arrays. Reference and estimated intervals should be sorted by onset time. Time values must be in seconds, and pitches in Hertz. Use `mir_eval.io.load_valued_intervals` to prepare data from standard text formats.

### Output
Returns a `list` of `tuples`, where each tuple `(i, j)` represents a match between the `i`-th reference note and the `j`-th estimated note.

### Valid Call Patterns
```python
# Inferred from signature and documentation
matching = mir_eval.transcription.match_notes(
    ref_intervals, ref_pitches, est_intervals, est_pitches
)
```

### LLM Instruction Prompt
- Always ensure `ref_intervals` and `est_intervals` are `(n, 2)` and `(m, 2)` NumPy arrays respectively.
- Ensure `ref_pitches` and `est_pitches` match the first dimension of their corresponding interval arrays.
- If performing transcription evaluation, ensure inputs are sorted by onset time.
- Use `offset_ratio=None` if the evaluation task does not require offset matching.

### Prompt Snippet
```text
# Example of matching notes with custom tolerances
matches = mir_eval.transcription.match_notes(
    ref_intervals, ref_pitches, est_intervals, est_pitches,
    onset_tolerance=0.05, pitch_tolerance=50.0, offset_ratio=0.2
)
```

### Common Failure Modes
- Passing unsorted interval arrays, which may lead to incorrect matching results.
- Providing pitch values in MIDI instead of Hertz, causing `pitch_tolerance` to fail.
- Mismatched array lengths between intervals and pitches.
- Assuming `offset_ratio` is ignored when it is not set to `None`.

### Fix Code Hint
```python
# Ensure inputs are sorted by onset
idx = np.argsort(ref_intervals[:, 0])
ref_intervals, ref_pitches = ref_intervals[idx], ref_pitches[idx]
```

## API Test: `python:mir_eval.transcription.offset_precision_recall_f1`

### Signature
```python
def offset_precision_recall_f1(ref_intervals, est_intervals, offset_ratio=0.2, offset_min_tolerance=0.05, strict=False, beta=1.0)
```
_Source: source/mir_eval/transcription.py:706_

_Source doc:_ Compute the Precision, Recall and F-measure of note offsets: an
estimated offset is considered correct if it is within +-50ms (or 20% of
the ref note duration, which ever is greater) of a reference offset. Note
that this metric completely ignores note onsets and note pitch. This means
an estimated offset will be considered correct if it matches a
reference offset, even if the offsets come from notes with completely
different pitches (i.e. notes that would not match with
:func:`match_notes`).

Examples
--------
>>> ref_intervals, _ = mir_eval.io.load_valued_intervals(
...     'reference.txt')
>>> est_intervals, _ = mir_eval.io.load_valued_intervals(
...     'estimated.txt')
>>> (offset_precision,
...  offset_recall,
...  offset_f_measure) = mir_eval.transcription.offset_precision_recall_f1(
...      ref_intervals, est_intervals)

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
offset_ratio : float > 0 or None
    The ratio of the reference note's duration used to define the
    offset_tolerance. Default is 0.2 (20%), meaning the
    ``offset_tolerance`` will equal the ``ref_duration * 0.2``, or
    ``offset_min_tolerance`` (0.05 by default, i.e. 50 ms), whichever is
    greater.
offset_min_tolerance : float > 0
    The minimum tolerance for offset matching. See ``offset_ratio``
    description for an explanation of how the offset tolerance is
    determined.
strict : bool
    If ``strict=False`` (the default), threshold checks for onset matching
    are performed using ``<=`` (less than or equal). If ``strict=True``,
    the threshold checks are performed using ``<`` (less than).
beta : float > 0
    Weighting factor for f-measure (default value = 1.0).

Returns
-------
precision : float
    The computed precision score
recall : float
    The computed recall score
f_measure : float
    The computed F-measure score

### Goal
Computes the precision, recall, and F-measure of note offsets by evaluating how many estimated note offsets fall within a dynamic tolerance window of reference note offsets, independent of pitch or onset timing.

### Parameters
- `ref_intervals`: A NumPy array of shape `(n, 2)` containing reference note `[onset, offset]` times in seconds.
- `est_intervals`: A NumPy array of shape `(m, 2)` containing estimated note `[onset, offset]` times in seconds.
- `offset_ratio`, default `0.2`: The percentage of the reference note duration used to calculate the tolerance window.
- `offset_min_tolerance`, default `0.05`: The absolute minimum time (in seconds) allowed for an offset to be considered a match.
- `strict`, default `False`: Determines if the threshold comparison is inclusive (`<=`) or exclusive (`<`).
- `beta`, default `1.0`: The weighting factor for the F-measure calculation.

### Input
Requires two NumPy arrays of shape `(n, 2)` and `(m, 2)` respectively. Inputs must be in seconds. Precondition: arrays should be validated for correct shape and format using `mir_eval.transcription.validate()` before evaluation.

### Output
Returns a tuple of three floats: `(precision, recall, f_measure)`.

### Valid Call Patterns
```python
offset_precision, offset_recall, offset_f_measure = mir_eval.transcription.offset_precision_recall_f1(
    ref_intervals, est_intervals
)
```

### LLM Instruction Prompt
- Always ensure `ref_intervals` and `est_intervals` are NumPy arrays of shape `(N, 2)`.
- Do not assume pitch or onset information is considered; this metric is strictly for offset timing.
- Use the default `offset_ratio` and `offset_min_tolerance` unless specific research requirements dictate otherwise.

### Prompt Snippet
```text
# Example usage:
precision, recall, f_measure = mir_eval.transcription.offset_precision_recall_f1(ref_intervals, est_intervals)
```

### Common Failure Modes
- Passing arrays that are not sorted by time, which may lead to incorrect matching results.
- Providing intervals where the onset is greater than the offset, which violates the `(n, 2)` interval structure.
- Failing to validate input arrays, which can cause runtime errors if the input shapes are mismatched.

### Fix Code Hint
```python
# Ensure intervals are sorted by onset time before evaluation
ref_intervals = ref_intervals[ref_intervals[:, 0].argsort()]
est_intervals = est_intervals[est_intervals[:, 0].argsort()]
# Validate inputs
mir_eval.transcription.validate(ref_intervals, est_intervals)
```

## API Test: `python:mir_eval.transcription.onset_precision_recall_f1`

### Signature
```python
def onset_precision_recall_f1(ref_intervals, est_intervals, onset_tolerance=0.05, strict=False, beta=1.0)
```
_Source: source/mir_eval/transcription.py:644_

_Source doc:_ Compute the Precision, Recall and F-measure of note onsets: an estimated
onset is considered correct if it is within +-50ms of a reference onset.
Note that this metric completely ignores note offset and note pitch. This
means an estimated onset will be considered correct if it matches a
reference onset, even if the onsets come from notes with completely
different pitches (i.e. notes that would not match with
:func:`match_notes`).

Examples
--------
>>> ref_intervals, _ = mir_eval.io.load_valued_intervals(
...     'reference.txt')
>>> est_intervals, _ = mir_eval.io.load_valued_intervals(
...     'estimated.txt')
>>> (onset_precision,
...  onset_recall,
...  onset_f_measure) = mir_eval.transcription.onset_precision_recall_f1(
...      ref_intervals, est_intervals)

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
onset_tolerance : float > 0
    The tolerance for an estimated note's onset deviating from the
    reference note's onset, in seconds. Default is 0.05 (50 ms).
strict : bool
    If ``strict=False`` (the default), threshold checks for onset matching
    are performed using ``<=`` (less than or equal). If ``strict=True``,
    the threshold checks are performed using ``<`` (less than).
beta : float > 0
    Weighting factor for f-measure (default value = 1.0).

Returns
-------
precision : float
    The computed precision score
recall : float
    The computed recall score
f_measure : float
    The computed F-measure score

### Goal
Computes the precision, recall, and F-measure of note onsets by evaluating the temporal alignment of estimated onsets against reference onsets, ignoring pitch and offset information.

### Parameters
- `ref_intervals`: A NumPy array of shape `(n, 2)` containing ground-truth note intervals (onset and offset times in seconds).
- `est_intervals`: A NumPy array of shape `(m, 2)` containing estimated note intervals (onset and offset times in seconds).
- `onset_tolerance`, default `0.05`: The maximum allowed temporal deviation (in seconds) between an estimated onset and a reference onset to be considered a match.
- `strict`, default `False`: Determines the comparison operator for the tolerance threshold; `False` uses `<=`, `True` uses `<`.
- `beta`, default `1.0`: The weighting factor for the F-measure calculation.

### Input
- **Data Format:** Requires `np.ndarray` inputs representing time intervals in seconds.
- **Preconditions:** Inputs should be validated for correct shape and format. While not strictly enforced by the function, it is standard practice in `mir_eval` to ensure arrays are sorted by onset time before evaluation.

### Output
Returns a tuple of three floats: `(precision, recall, f_measure)`.

### Valid Call Patterns
```python
(onset_precision, onset_recall, onset_f_measure) = mir_eval.transcription.onset_precision_recall_f1(
    ref_intervals, est_intervals
)
```

### LLM Instruction Prompt
- Always ensure `ref_intervals` and `est_intervals` are provided as `np.ndarray` objects.
- Remember that this metric is instrument-agnostic and ignores pitch/offset; do not use this if pitch-specific matching is required (use `match_notes` instead).
- Ensure time values are in seconds.

### Prompt Snippet
```text
# Example usage for onset evaluation
import mir_eval
ref_intervals, _ = mir_eval.io.load_valued_intervals('ref.txt')
est_intervals, _ = mir_eval.io.load_valued_intervals('est.txt')
p, r, f = mir_eval.transcription.onset_precision_recall_f1(ref_intervals, est_intervals)
```

### Common Failure Modes
- **Unsorted Inputs:** Providing unsorted intervals may lead to unexpected matching behavior.
- **Incorrect Units:** Providing time in samples instead of seconds will cause the `onset_tolerance` to fail.
- **Empty Arrays:** Passing empty arrays may result in division by zero or undefined scores depending on the implementation context.

### Fix Code Hint
```python
# Ensure intervals are sorted by onset time
ref_intervals = ref_intervals[ref_intervals[:, 0].argsort()]
est_intervals = est_intervals[est_intervals[:, 0].argsort()]
```

## API Test: `python:mir_eval.transcription.precision_recall_f1_overlap`

### Signature
```python
def precision_recall_f1_overlap(ref_intervals, ref_pitches, est_intervals, est_pitches, onset_tolerance=0.05, pitch_tolerance=50.0, offset_ratio=0.2, offset_min_tolerance=0.05, strict=False, beta=1.0)
```
_Source: source/mir_eval/transcription.py:477_

### Goal
Computes standard transcription accuracy metrics (Precision, Recall, F-measure) and the Average Overlap Ratio by performing bipartite graph matching between reference and estimated note events.

### Parameters
- `ref_intervals`: `np.ndarray` of shape `(n, 2)` containing ground-truth note onset and offset times in seconds.
- `ref_pitches`: `np.ndarray` of shape `(n,)` containing ground-truth pitch values in Hertz.
- `est_intervals`: `np.ndarray` of shape `(m, 2)` containing estimated note onset and offset times in seconds.
- `est_pitches`: `np.ndarray` of shape `(m,)` containing estimated pitch values in Hertz.
- `onset_tolerance`, default `0.05`: Maximum allowed deviation in seconds between reference and estimated onsets.
- `pitch_tolerance`, default `50.0`: Maximum allowed deviation in cents between reference and estimated pitches.
- `offset_ratio`, default `0.2`: Ratio of reference duration used to calculate offset tolerance; if `None`, offsets are ignored.
- `offset_min_tolerance`, default `0.05`: Minimum threshold in seconds for offset matching when `offset_ratio` is active.
- `strict`, default `False`: If `True`, uses `<` for threshold comparisons; if `False`, uses `<=`.
- `beta`, default `1.0`: Weighting factor for the F-measure calculation.

### Input
- **Data:** Requires NumPy arrays for intervals and pitches.
- **Preconditions:** `ref_intervals` and `est_intervals` must be validated (e.g., sorted by time).
- **Compatibility:** Use `mir_eval.io.load_valued_intervals` to load data from standard text files.

### Output
Returns a tuple of four floats: `(precision, recall, f_measure, avg_overlap_ratio)`.

### Valid Call Patterns
```python
(precision, recall, f_measure, avg_overlap) = mir_eval.transcription.precision_recall_f1_overlap(
    ref_intervals, ref_pitches, est_intervals, est_pitches
)
```

### LLM Instruction Prompt
- Always ensure `ref_intervals` and `est_intervals` are `np.ndarray` objects.
- When evaluating transcription, ensure time units are in seconds and pitch units are in Hertz.
- If `offset_ratio` is set to `None`, the function will ignore offset timing in the matching logic.

### Prompt Snippet
```text
Use mir_eval.transcription.precision_recall_f1_overlap(ref_intervals, ref_pitches, est_intervals, est_pitches) to compute transcription metrics.
```

### Common Failure Modes
- **Unsorted Inputs:** Passing unsorted intervals will lead to incorrect matching results; ensure arrays are sorted by onset time.
- **Unit Mismatch:** Providing pitch in MIDI instead of Hertz, or time in milliseconds instead of seconds.
- **Empty Arrays:** Passing empty arrays may cause issues; ensure inputs are validated using `mir_eval.transcription.validate()` before calling.

### Fix Code Hint
```python
# Ensure intervals are sorted by onset time before evaluation
idx = np.argsort(ref_intervals[:, 0])
ref_intervals = ref_intervals[idx]
ref_pitches = ref_pitches[idx]
```

## API Test: `python:mir_eval.transcription.validate`

### Signature
```python
def validate(ref_intervals, ref_pitches, est_intervals, est_pitches)
```
_Source: source/mir_eval/transcription.py:117_

_Source doc:_ Check that the input annotations to a metric look like time intervals
and a pitch list, and throws helpful errors if not.

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
ref_pitches : np.ndarray, shape=(n,)
    Array of reference pitch values in Hertz
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
est_pitches : np.ndarray, shape=(m,)
    Array of estimated pitch values in Hertz

### Goal
Validates that reference and estimated transcription data (intervals and pitches) conform to the expected NumPy array shapes and types required for transcription evaluation metrics.

### Parameters
- `ref_intervals`: A NumPy array of shape `(n, 2)` containing ground-truth note onset and offset times in seconds.
- `ref_pitches`: A NumPy array of shape `(n,)` containing ground-truth fundamental frequency values in Hertz.
- `est_intervals`: A NumPy array of shape `(m, 2)` containing estimated note onset and offset times in seconds.
- `est_pitches`: A NumPy array of shape `(m,)` containing estimated fundamental frequency values in Hertz.

### Input
- **Data Format:** All inputs must be NumPy arrays.
- **Preconditions:** `ref_intervals` and `est_intervals` must have a second dimension of size 2. The number of intervals must match the number of corresponding pitch values (i.e., `ref_intervals.shape[0] == ref_pitches.shape[0]`).
- **Time/Frequency:** Time values must be in seconds; pitch values must be in Hertz.

### Output
Returns `None` if validation succeeds. If the inputs are malformed, it raises an exception with a descriptive error message.

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example usage with valid arrays
ref_intervals = np.array([[0.0, 1.0], [1.0, 2.0]])
ref_pitches = np.array([440.0, 440.0])
est_intervals = np.array([[0.1, 1.1], [1.1, 2.1]])
est_pitches = np.array([442.0, 440.0])

mir_eval.transcription.validate(ref_intervals, ref_pitches, est_intervals, est_pitches)
```

### LLM Instruction Prompt
- Always call `mir_eval.transcription.validate` before passing data to `mir_eval.transcription.evaluate` or `mir_eval.transcription.match_notes`.
- Ensure that `ref_intervals` and `est_intervals` are `(n, 2)` arrays and that pitch arrays are 1D and match the length of their respective interval arrays.

### Prompt Snippet
```text
# Validate transcription inputs before evaluation
mir_eval.transcription.validate(ref_intervals, ref_pitches, est_intervals, est_pitches)
```

### Common Failure Modes
- **Shape Mismatch:** Passing arrays where the number of intervals does not match the number of pitch values (e.g., `ref_intervals.shape[0] != ref_pitches.shape[0]`).
- **Incorrect Dimensions:** Passing 1D arrays for intervals or multi-dimensional arrays for pitches.
- **Data Type Errors:** Passing lists instead of NumPy arrays.
- **Unsorted Data:** While `validate` checks structure, many downstream metrics require the intervals to be sorted by onset time; ensure data is pre-sorted if necessary.

### Fix Code Hint
```python
# Ensure arrays are properly shaped and sorted before validation
ref_intervals = np.atleast_2d(ref_intervals)
ref_pitches = np.atleast_1d(ref_pitches)
# Sort by onset time
idx = np.argsort(ref_intervals[:, 0])
ref_intervals = ref_intervals[idx]
ref_pitches = ref_pitches[idx]
mir_eval.transcription.validate(ref_intervals, ref_pitches, est_intervals, est_pitches)
```

## API Test: `python:mir_eval.transcription.validate_intervals`

### Signature
```python
def validate_intervals(ref_intervals, est_intervals)
```
_Source: source/mir_eval/transcription.py:148_

_Source doc:_ Check that the input annotations to a metric look like time intervals,
and throws helpful errors if not.

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)

### Goal
Validates that reference and estimated note interval arrays conform to the expected `(N, 2)` NumPy array structure required for transcription evaluation metrics.

### Parameters
- `ref_intervals`: A NumPy array of shape `(n, 2)` containing the ground-truth onset and offset times in seconds.
- `est_intervals`: A NumPy array of shape `(m, 2)` containing the estimated onset and offset times in seconds.

### Input
- **Data Format:** Both inputs must be `np.ndarray` objects.
- **Structure:** Each array must have exactly two columns representing `[onset, offset]`.
- **Preconditions:** Time values must be in seconds. While this function checks the shape and structure, it is typically called before matching logic (e.g., `match_notes`) to ensure data integrity.

### Output
Returns `None`. If the inputs do not conform to the expected structure (e.g., incorrect dimensions or non-numeric types), the function raises an informative error.

### Valid Call Patterns
```python
import numpy as np
from mir_eval.transcription import validate_intervals

# Example with valid interval arrays
ref = np.array([[0.1, 0.5], [0.6, 1.0]])
est = np.array([[0.12, 0.48], [0.65, 0.95]])
validate_intervals(ref, est)
```

### LLM Instruction Prompt
- When implementing transcription evaluation, always call `mir_eval.transcription.validate_intervals` before passing data to `match_notes` or evaluation functions.
- Ensure that input arrays are `np.ndarray` with shape `(n, 2)`.
- Do not attempt to catch the errors raised by this function; allow them to propagate to inform the user of malformed input data.

### Prompt Snippet
```text
# Validate inputs before transcription evaluation
mir_eval.transcription.validate_intervals(ref_intervals, est_intervals)
```

### Common Failure Modes
- **Shape Mismatch:** Passing a 1D array or an array with more than 2 columns will trigger a validation error.
- **Data Type:** Passing lists instead of `np.ndarray` may cause failures in downstream processing; ensure inputs are cast to NumPy arrays first.
- **Empty Arrays:** While the function validates structure, ensure that empty arrays (shape `(0, 2)`) are handled appropriately by your logic if they are possible outputs from your system.

### Fix Code Hint
```python
import numpy as np
# Ensure inputs are numpy arrays before validation
ref_intervals = np.array(ref_intervals)
est_intervals = np.array(est_intervals)
mir_eval.transcription.validate_intervals(ref_intervals, est_intervals)
```

## API Test: `python:mir_eval.transcription_velocity.evaluate`

### Signature
```python
def evaluate(ref_intervals, ref_pitches, ref_velocities, est_intervals, est_pitches, est_velocities, **kwargs)
```
_Source: source/mir_eval/transcription_velocity.py:359_

_Source doc:_ Compute all metrics for the given reference and estimated annotations.

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
ref_pitches : np.ndarray, shape=(n,)
    Array of reference pitch values in Hertz
ref_velocities : np.ndarray, shape=(n,)
    Array of MIDI velocities (i.e. between 0 and 127) of reference notes
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
est_pitches : np.ndarray, shape=(m,)
    Array of estimated pitch values in Hertz
est_velocities : np.ndarray, shape=(n,)
    Array of MIDI velocities (i.e. between 0 and 127) of estimated notes
**kwargs
    Additional keyword arguments which will be passed to the
    appropriate metric or preprocessing functions.

Returns
-------
scores : dict
    Dictionary of scores, where the key is the metric name (str) and
    the value is the (float) score achieved.

### Goal
Computes a comprehensive suite of transcription accuracy metrics, including velocity-aware precision, recall, and F-measure, by comparing estimated note events against ground-truth reference annotations.

### Parameters
- `ref_intervals`: `np.ndarray` of shape `(n, 2)` containing `[onset, offset]` times in seconds for reference notes.
- `ref_pitches`: `np.ndarray` of shape `(n,)` containing fundamental frequencies in Hertz for reference notes.
- `ref_velocities`: `np.ndarray` of shape `(n,)` containing MIDI velocities (0–127) for reference notes.
- `est_intervals`: `np.ndarray` of shape `(m, 2)` containing `[onset, offset]` times in seconds for estimated notes.
- `est_pitches`: `np.ndarray` of shape `(m,)` containing fundamental frequencies in Hertz for estimated notes.
- `est_velocities`: `np.ndarray` of shape `(m,)` containing MIDI velocities (0–127) for estimated notes.
- `kwargs`: Optional keyword arguments passed to underlying matching and metric functions.

### Input
- **Data Formats:** All time-based inputs must be in seconds. Pitches must be in Hz. Velocities must be in the range `[0, 127]`.
- **Preconditions:** Reference and estimated arrays must be validated for shape and content. Reference velocities are rescaled to `[0, 1]`. Estimated velocities are rescaled via linear regression to minimize L2 distance to reference velocities before thresholding.
- **Matching:** Uses bipartite graph matching to establish correspondences between reference and estimated notes based on onset, offset, and pitch.

### Output
Returns a `dict` mapping metric names (e.g., `Precision`, `Recall`, `F-measure`) to their corresponding `float` scores.

### Valid Call Patterns
```python
# Example inferred from signature and module documentation
scores = mir_eval.transcription_velocity.evaluate(
    ref_intervals, ref_pitches, ref_velocities,
    est_intervals, est_pitches, est_velocities
)
```

### LLM Instruction Prompt
- Always ensure input arrays are sorted by onset time before calling.
- Ensure `ref_intervals` and `est_intervals` are `(N, 2)` NumPy arrays.
- Use `mir_eval.util.validate` or module-specific `validate()` functions to ensure inputs conform to expected shapes before passing to `evaluate`.

### Prompt Snippet
```text
# Ensure inputs are prepared as numpy arrays
# ref_intervals: (n, 2), ref_pitches: (n,), ref_velocities: (n,)
# est_intervals: (m, 2), est_pitches: (m,), est_velocities: (m,)
scores = mir_eval.transcription_velocity.evaluate(ref_intervals, ref_pitches, ref_velocities, est_intervals, est_pitches, est_velocities)
```

### Common Failure Modes
- **Shape Mismatch:** Providing arrays where the number of intervals does not match the number of pitches or velocities.
- **Unsorted Inputs:** Failing to sort intervals by onset time, which is a common precondition for `mir_eval` matching logic.
- **Velocity Range:** Providing velocities outside the `[0, 127]` range, which may cause unexpected behavior during the linear regression rescaling step.

### Fix Code Hint
```python
# Ensure arrays are sorted by onset time
idx = ref_intervals[:, 0].argsort()
ref_intervals, ref_pitches, ref_velocities = ref_intervals[idx], ref_pitches[idx], ref_velocities[idx]
```

## API Test: `python:mir_eval.transcription_velocity.match_notes`

### Signature
```python
def match_notes(ref_intervals, ref_pitches, ref_velocities, est_intervals, est_pitches, est_velocities, onset_tolerance=0.05, pitch_tolerance=50.0, offset_ratio=0.2, offset_min_tolerance=0.05, strict=False, velocity_tolerance=0.1)
```
_Source: source/mir_eval/transcription_velocity.py:107_

_Source doc:_ Match notes, taking note velocity into consideration.

This function first calls :func:`mir_eval.transcription.match_notes` to
match notes according to the supplied intervals, pitches, onset, offset,
and pitch tolerances. The velocities of the matched notes are then used to
estimate a slope and intercept which can rescale the estimated velocities
so that they are as close as possible (in L2 sense) to their matched
reference velocities. Velocities are then normalized to the range [0, 1]. A
estimated note is then further only considered correct if its velocity is
within ``velocity_tolerance`` of its matched (according to pitch and
timing) reference note.

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
ref_pitches : np.ndarray, shape=(n,)
    Array of reference pitch values in Hertz
ref_velocities : np.ndarray, shape=(n,)
    Array of MIDI velocities (i.e. between 0 and 127) of reference notes
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
est_pitches : np.ndarray, shape=(m,)
    Array of estimated pitch values in Hertz
est_velocities : np.ndarray, shape=(m,)
    Array of MIDI velocities (i.e. between 0 and 127) of estimated notes
onset_tolerance : float > 0
    The tolerance for an estimated note's onset deviating from the
    reference note's onset, in seconds. Default is 0.05 (50 ms).
pitch_tolerance : float > 0
    The tolerance for an estimated note's pitch deviating from the
    reference note's pitch, in cents. Default is 50.0 (50 cents).
offset_ratio : float > 0 or None
    The ratio of the reference note's duration used to define the
    offset_tolerance. Default is 0.2 (20%), meaning the
    ``offset_tolerance`` will equal the ``ref_duration * 0.2``, or 0.05 (50
    ms), whichever is greater. If ``offset_ratio`` is set to ``None``,
    offsets are ignored in the matching.
offset_min_tolerance : float > 0
    The minimum tolerance for offset matching. See offset_ratio description
    for an explanation of how the offset tolerance is determined. Note:
    this parameter only influences the results if ``offset_ratio`` is not
    ``None``.
strict : bool
    If ``strict=False`` (the default), threshold checks for onset, offset,
    and pitch matching are performed using ``<=`` (less than or equal). If
    ``strict=True``, the threshold checks are performed using ``<`` (less
    than).
velocity_tolerance : float > 0
    Estimated notes are considered correct if, after rescaling and
    normalization to [0, 1], they are within ``velocity_tolerance`` of a
    matched reference note.

Returns
-------
matching : list of tuples
    A list of matched reference and estimated notes.
    ``matching[i] == (i, j)`` where reference note ``i`` matches estimated
    note ``j``.

### Goal
Computes the optimal correspondence between reference and estimated notes by performing bipartite graph matching based on timing, pitch, and velocity-rescaled intensity.

### Parameters
- `ref_intervals`: `np.ndarray` of shape `(n, 2)` containing `[onset, offset]` pairs in seconds.
- `ref_pitches`: `np.ndarray` of shape `(n,)` containing fundamental frequencies in Hz.
- `ref_velocities`: `np.ndarray` of shape `(n,)` containing MIDI velocities (0-127).
- `est_intervals`: `np.ndarray` of shape `(m, 2)` containing `[onset, offset]` pairs in seconds.
- `est_pitches`: `np.ndarray` of shape `(m,)` containing fundamental frequencies in Hz.
- `est_velocities`: `np.ndarray` of shape `(m,)` containing MIDI velocities (0-127).
- `onset_tolerance`, default `0.05`: Maximum allowed deviation in seconds for note onsets.
- `pitch_tolerance`, default `50.0`: Maximum allowed deviation in cents for note pitches.
- `offset_ratio`, default `0.2`: Ratio of reference duration used to calculate offset tolerance; if `None`, offsets are ignored.
- `offset_min_tolerance`, default `0.05`: Minimum threshold in seconds for offset matching.
- `strict`, default `False`: If `False`, uses `<=` for threshold comparisons; if `True`, uses `<`.
- `velocity_tolerance`, default `0.1`: Maximum allowed difference in normalized velocity (0-1) after linear regression rescaling.

### Input
Inputs must be validated `numpy` arrays. Reference and estimated intervals must be sorted by time. Reference velocities are rescaled to `[0, 1]`, and estimated velocities are rescaled via linear regression to minimize L2 distance to reference velocities before thresholding.

### Output
Returns a `list` of `tuples`, where each tuple `(i, j)` indicates that reference note index `i` matches estimated note index `j`.

### Valid Call Patterns
```python
# Example inferred from signature
matching = mir_eval.transcription_velocity.match_notes(
    ref_intervals, ref_pitches, ref_velocities, 
    est_intervals, est_pitches, est_velocities
)
```

### LLM Instruction Prompt
- Always ensure `ref_intervals` and `est_intervals` are sorted by onset time before calling.
- Use `mir_eval.transcription_velocity.match_notes` when evaluating note-level transcription accuracy that includes velocity dynamics.
- Note that this function performs internal linear regression to align estimated velocity scales to reference scales.

### Prompt Snippet
```text
Use mir_eval.transcription_velocity.match_notes(ref_intervals, ref_pitches, ref_velocities, est_intervals, est_pitches, est_velocities) to compute note correspondences.
```

### Common Failure Modes
- Passing unsorted intervals, which violates the precondition for matching logic.
- Providing empty arrays without prior validation, which may lead to unexpected behavior in the bipartite matching algorithm.
- Misinterpreting `velocity_tolerance` as raw MIDI velocity difference; it applies to the normalized `[0, 1]` range after regression.

### Fix Code Hint
```python
# Ensure inputs are sorted by onset
idx = np.argsort(ref_intervals[:, 0])
ref_intervals, ref_pitches, ref_velocities = ref_intervals[idx], ref_pitches[idx], ref_velocities[idx]
# Repeat for est_intervals...
```

## API Test: `python:mir_eval.transcription_velocity.precision_recall_f1_overlap`

### Signature
```python
def precision_recall_f1_overlap(ref_intervals, ref_pitches, ref_velocities, est_intervals, est_pitches, est_velocities, onset_tolerance=0.05, pitch_tolerance=50.0, offset_ratio=0.2, offset_min_tolerance=0.05, strict=False, velocity_tolerance=0.1, beta=1.0)
```
_Source: source/mir_eval/transcription_velocity.py:230_

_Source doc:_ Compute the Precision, Recall and F-measure of correct vs incorrectly
transcribed notes, and the Average Overlap Ratio for correctly transcribed
notes (see :func:`mir_eval.transcription.average_overlap_ratio`).
"Correctness" is determined based on note onset, velocity, pitch and
(optionally) offset. An estimated note is considered correct if

1. Its onset is within ``onset_tolerance`` (default +-50ms) of a
   reference note
2. Its pitch (F0) is within +/- ``pitch_tolerance`` (default one
   quarter tone, 50 cents) of the corresponding reference note
3. Its velocity, after normalizing reference velocities to the range
   [0, 1] and globally rescaling estimated velocities to minimize L2
   distance between matched reference notes, is within
   ``velocity_tolerance`` (default 0.1) the corresponding reference note
4. If ``offset_ratio`` is ``None``, note offsets are ignored in the
   comparison. Otherwise, on top of the above requirements, a correct
   returned note is required to have an offset value within
   `offset_ratio`` (default 20%) of the reference note's duration around
   the reference note's offset, or within ``offset_min_tolerance``
   (default 50 ms), whichever is larger.

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
ref_pitches : np.ndarray, shape=(n,)
    Array of reference pitch values in Hertz
ref_velocities : np.ndarray, shape=(n,)
    Array of MIDI velocities (i.e. between 0 and 127) of reference notes
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
est_pitches : np.ndarray, shape=(m,)
    Array of estimated pitch values in Hertz
est_velocities : np.ndarray, shape=(n,)
    Array of MIDI velocities (i.e. between 0 and 127) of estimated notes
onset_tolerance : float > 0
    The tolerance for an estimated note's onset deviating from the
    reference note's onset, in seconds. Default is 0.05 (50 ms).
pitch_tolerance : float > 0
    The tolerance for an estimated note's pitch deviating from the
    reference note's pitch, in cents. Default is 50.0 (50 cents).
offset_ratio : float > 0 or None
    The ratio of the reference note's duration used to define the
    offset_tolerance. Default is 0.2 (20%), meaning the
    ``offset_tolerance`` will equal the ``ref_duration * 0.2``, or
    ``offset_min_tolerance`` (0.05 by default, i.e. 50 ms), whichever is
    greater. If ``offset_ratio`` is set to ``None``, offsets are ignored in
    the evaluation.
offset_min_tolerance : float > 0
    The minimum tolerance for offset matching. See ``offset_ratio``
    description for an explanation of how the offset tolerance is
    determined. Note: this parameter only influences the results if
    ``offset_ratio`` is not ``None``.
strict : bool
    If ``strict=False`` (the default), threshold checks for onset, offset,
    and pitch matching are performed using ``<=`` (less than or equal). If
    ``strict=True``, the threshold checks are performed using ``<`` (less
    than).
velocity_tolerance : float > 0
    Estimated notes are considered correct if, after rescaling and
    normalization to [0, 1], they are within ``velocity_tolerance`` of a
    matched reference note.
beta : float > 0
    Weighting factor for f-measure (default value = 1.0).

Returns
-------
precision : float
    The computed precision score
recall : float
    The computed recall score
f_measure : float
    The computed F-measure score
avg_overlap_ratio : float
    The computed Average Overlap Ratio score

### Goal
Evaluates the accuracy of a note transcription system by comparing estimated notes against reference ground truth, incorporating onset, pitch, offset, and velocity matching criteria.

### Parameters
- `ref_intervals`: `np.ndarray` of shape `(n, 2)` containing `[onset, offset]` times in seconds.
- `ref_pitches`: `np.ndarray` of shape `(n,)` containing fundamental frequencies in Hz.
- `ref_velocities`: `np.ndarray` of shape `(n,)` containing MIDI velocities (0-127).
- `est_intervals`: `np.ndarray` of shape `(m, 2)` containing estimated `[onset, offset]` times in seconds.
- `est_pitches`: `np.ndarray` of shape `(m,)` containing estimated fundamental frequencies in Hz.
- `est_velocities`: `np.ndarray` of shape `(m,)` containing estimated MIDI velocities (0-127).
- `onset_tolerance`, default `0.05`: Maximum allowed deviation in seconds for onset matching.
- `pitch_tolerance`, default `50.0`: Maximum allowed deviation in cents for pitch matching.
- `offset_ratio`, default `0.2`: Ratio of reference duration used to define offset tolerance; set to `None` to ignore offsets.
- `offset_min_tolerance`, default `0.05`: Minimum threshold in seconds for offset matching.
- `strict`, default `False`: If `True`, uses `<` for threshold comparisons; if `False`, uses `<=`.
- `velocity_tolerance`, default `0.1`: Maximum allowed deviation for normalized velocity matching.
- `beta`, default `1.0`: Weighting factor for the F-measure calculation.

### Input
Inputs must be validated NumPy arrays. Reference and estimated intervals should be sorted by time. Reference velocities are normalized to `[0, 1]`, and estimated velocities are globally rescaled via linear regression to minimize L2 distance to reference velocities before thresholding.

### Output
Returns a tuple of four floats: `(precision, recall, f_measure, avg_overlap_ratio)`.

### Valid Call Patterns
```python
precision, recall, f_measure, avg_overlap_ratio = mir_eval.transcription_velocity.precision_recall_f1_overlap(
    ref_intervals, ref_pitches, ref_velocities, 
    est_intervals, est_pitches, est_velocities
)
```

### LLM Instruction Prompt
- Ensure all time-based inputs are in seconds.
- Ensure pitch inputs are in Hz.
- Ensure velocity inputs are in the range `[0, 127]`.
- Always validate input arrays using `mir_eval.transcription_velocity.validate()` before calling this function.

### Prompt Snippet
```text
# Example usage:
precision, recall, f_measure, avg_overlap_ratio = mir_eval.transcription_velocity.precision_recall_f1_overlap(
    ref_intervals, ref_pitches, ref_velocities, est_intervals, est_pitches, est_velocities)
```

### Common Failure Modes
- Passing unsorted intervals, which violates the precondition for matching logic.
- Providing velocities outside the `[0, 127]` range, which may lead to incorrect normalization.
- Mismatched array lengths between intervals, pitches, and velocities for the same set (e.g., `ref_intervals` length must match `ref_pitches` length).

### Fix Code Hint
```python
# Ensure inputs are sorted by onset time
idx = np.argsort(ref_intervals[:, 0])
ref_intervals, ref_pitches, ref_velocities = ref_intervals[idx], ref_pitches[idx], ref_velocities[idx]
```

## API Test: `python:mir_eval.transcription_velocity.validate`

### Signature
```python
def validate(ref_intervals, ref_pitches, ref_velocities, est_intervals, est_pitches, est_velocities)
```
_Source: source/mir_eval/transcription_velocity.py:62_

_Source doc:_ Check that the input annotations have valid time intervals, pitches,
and velocities, and throws helpful errors if not.

Parameters
----------
ref_intervals : np.ndarray, shape=(n,2)
    Array of reference notes time intervals (onset and offset times)
ref_pitches : np.ndarray, shape=(n,)
    Array of reference pitch values in Hertz
ref_velocities : np.ndarray, shape=(n,)
    Array of MIDI velocities (i.e. between 0 and 127) of reference notes
est_intervals : np.ndarray, shape=(m,2)
    Array of estimated notes time intervals (onset and offset times)
est_pitches : np.ndarray, shape=(m,)
    Array of estimated pitch values in Hertz
est_velocities : np.ndarray, shape=(m,)
    Array of MIDI velocities (i.e. between 0 and 127) of estimated notes

### Goal
Validates that reference and estimated note transcription data (intervals, pitches, and velocities) conform to the expected shapes and value ranges required for velocity-aware transcription evaluation.

### Parameters
- `ref_intervals`: A NumPy array of shape `(n, 2)` containing ground-truth note onset and offset times in seconds.
- `ref_pitches`: A NumPy array of shape `(n,)` containing ground-truth fundamental frequencies in Hertz.
- `ref_velocities`: A NumPy array of shape `(n,)` containing ground-truth MIDI velocities (integer or float values in the range `[0, 127]`).
- `est_intervals`: A NumPy array of shape `(m, 2)` containing estimated note onset and offset times in seconds.
- `est_pitches`: A NumPy array of shape `(m,)` containing estimated fundamental frequencies in Hertz.
- `est_velocities`: A NumPy array of shape `(m,)` containing estimated MIDI velocities (integer or float values in the range `[0, 127]`).

### Input
The caller must provide six NumPy arrays. Preconditions include:
- Intervals must be provided as `[onset, offset]` pairs in seconds.
- Pitches must be in Hertz.
- Velocities must be within the valid MIDI range of `[0, 127]`.
- Arrays must be consistent in length (e.g., `ref_intervals` and `ref_pitches` must have the same number of rows `n`).

### Output
Returns `None` if validation succeeds. If validation fails, it raises an exception with a descriptive error message.

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example usage with dummy data
ref_intervals = np.array([[0.1, 0.5], [0.6, 1.0]])
ref_pitches = np.array([440.0, 493.88])
ref_velocities = np.array([100, 110])
est_intervals = np.array([[0.12, 0.52], [0.65, 1.05]])
est_pitches = np.array([442.0, 490.0])
est_velocities = np.array([95, 105])

mir_eval.transcription_velocity.validate(
    ref_intervals, ref_pitches, ref_velocities, 
    est_intervals, est_pitches, est_velocities
)
```

### LLM Instruction Prompt
- Always ensure that the input arrays are NumPy arrays before calling `validate`.
- Verify that the number of intervals, pitches, and velocities match for both reference and estimated sets.
- Ensure all time values are in seconds and velocities are within the `[0, 127]` range.

### Prompt Snippet
```text
mir_eval.transcription_velocity.validate(ref_intervals, ref_pitches, ref_velocities, est_intervals, est_pitches, est_velocities)
```

### Common Failure Modes
- **Shape Mismatch:** Providing arrays of different lengths for intervals, pitches, or velocities (e.g., `ref_intervals` has 10 rows but `ref_pitches` has 9).
- **Invalid Velocity Range:** Providing velocity values outside the `[0, 127]` range.
- **Incorrect Dimensions:** Providing 1D arrays for intervals instead of `(n, 2)` arrays.

### Fix Code Hint
```python
# Ensure arrays are properly shaped before validation
ref_intervals = np.atleast_2d(ref_intervals)
est_intervals = np.atleast_2d(est_intervals)
# Check for velocity bounds
if np.any(ref_velocities < 0) or np.any(ref_velocities > 127):
    raise ValueError("Reference velocities must be between 0 and 127.")
```

## API Test: `python:mir_eval.util.adjust_events`

### Signature
```python
def adjust_events(events, labels=None, t_min=0.0, t_max=None, label_prefix='__')
```
_Source: source/mir_eval/util.py:359_

_Source doc:_ Adjust the given list of event times to span the range
``[t_min, t_max]``.

Any event times outside of the specified range will be removed.

If the times do not span ``[t_min, t_max]``, additional events will be
added with the prefix ``label_prefix``.

Parameters
----------
events : np.ndarray
    Array of event times (seconds)
labels : list or None
    List of labels
    (Default value = None)
t_min : float or None
    Minimum valid event time.
    (Default value = 0.0)
t_max : float or None
    Maximum valid event time.
    (Default value = None)
label_prefix : str
    Prefix string to use for synthetic labels
    (Default value = '__')

Returns
-------
new_times : np.ndarray
    Event times corrected to the given range.

### Goal
Ensures that a sequence of event timestamps is strictly contained within a specified temporal window `[t_min, t_max]` by trimming outliers and padding the boundaries with synthetic events.

### Parameters
- `events`: A 1D `np.ndarray` containing event timestamps in seconds.
- `labels`, default `None`: An optional list of labels corresponding to the input `events`.
- `t_min`, default `0.0`: The lower bound of the time range in seconds.
- `t_max`, default `None`: The upper bound of the time range in seconds. If `None`, no upper bound is enforced.
- `label_prefix`, default `'__'`: The string prefix used to label any synthetic events added to satisfy the `t_min` or `t_max` boundaries.

### Input
- **Data Format:** `events` must be a 1D NumPy array of floats representing time in seconds.
- **Preconditions:** For consistent evaluation, input `events` should be sorted by time. If `labels` are provided, they must have the same length as `events`.

### Output
Returns `np.ndarray` — A 1D array of event times that have been truncated or padded to fit exactly within the `[t_min, t_max]` range.

### Valid Call Patterns
```python
# Example inferred from signature (not verified in test suite)
import numpy as np
from mir_eval.util import adjust_events

events = np.array([0.5, 1.5, 2.5])
adjusted = adjust_events(events, t_min=1.0, t_max=2.0)
```

### LLM Instruction Prompt
- When calling `adjust_events`, ensure `events` is a 1D NumPy array.
- If `t_max` is provided, ensure it is greater than `t_min`.
- Note that this function modifies the event sequence to force alignment with the specified window; ensure this behavior is desired for your specific evaluation metric.

### Prompt Snippet
```text
# Adjust events to a specific window
new_events = mir_eval.util.adjust_events(events, t_min=start_time, t_max=end_time)
```

### Common Failure Modes
- **Mismatched Lengths:** Providing `labels` that do not match the length of the `events` array will result in an error.
- **Unsorted Input:** While the function processes the array, many downstream `mir_eval` metrics require sorted event times; ensure the output is sorted if the input was not.
- **Invalid Range:** Providing a `t_min` greater than `t_max` will result in an empty or invalid event set.

### Fix Code Hint
```python
# Ensure events are sorted before adjustment
events = np.sort(events)
adjusted_events = mir_eval.util.adjust_events(events, t_min=0.0, t_max=30.0)
```

## API Test: `python:mir_eval.util.adjust_intervals`

### Signature
```python
def adjust_intervals(intervals, labels=None, t_min=0.0, t_max=None, start_label='__T_MIN', end_label='__T_MAX')
```
_Source: source/mir_eval/util.py:261_

_Source doc:_ Adjust a list of time intervals to span the range ``[t_min, t_max]``.

Any intervals lying completely outside the specified range will be removed.

Any intervals lying partially outside the specified range will be cropped.

If the specified range exceeds the span of the provided data in either
direction, additional intervals will be appended.  If an interval is
appended at the beginning, it will be given the label ``start_label``; if
an interval is appended at the end, it will be given the label
``end_label``.

Parameters
----------
intervals : np.ndarray, shape=(n_events, 2)
    Array of interval start and end-times
labels : list, len=n_events or None
    List of labels
    (Default value = None)
t_min : float or None
    Minimum interval start time.
    (Default value = 0.0)
t_max : float or None
    Maximum interval end time.
    (Default value = None)
start_label : str or float or int
    Label to give any intervals appended at the beginning
    (Default value = '__T_MIN')
end_label : str or float or int
    Label to give any intervals appended at the end
    (Default value = '__T_MAX')

Returns
-------
new_intervals : np.ndarray
    Intervals spanning ``[t_min, t_max]``
new_labels : list
    List of labels for ``new_labels``

### Goal
Ensures that a set of labeled or unlabeled time intervals is strictly constrained to a specific temporal range `[t_min, t_max]` by cropping, removing, or padding intervals as necessary for consistent evaluation.

### Parameters
- `intervals`: A NumPy array of shape `(n_events, 2)` containing start and end times in seconds.
- `labels`, default `None`: A list of labels corresponding to each interval; if provided, the returned list will include labels for any newly appended intervals.
- `t_min`, default `0.0`: The desired start time for the interval set.
- `t_max`, default `None`: The desired end time for the interval set.
- `start_label`, default `'__T_MIN'`: The label assigned to any padding interval created if the original data starts after `t_min`.
- `end_label`, default `'__T_MAX'`: The label assigned to any padding interval created if the original data ends before `t_max`.

### Input
- **Data Format:** `intervals` must be a NumPy array of shape `(n_events, 2)`.
- **Preconditions:** Intervals should be sorted by start time. This function is typically used as a preprocessing step to ensure estimated intervals align with reference intervals before computing metrics.

### Output
Returns a tuple containing:
- `new_intervals`: A NumPy array of shape `(m, 2)` representing the adjusted intervals.
- `new_labels`: A list of length `m` containing the original labels plus any labels assigned to appended padding intervals.

### Valid Call Patterns
```python
# Example inferred from signature and project usage patterns
new_intervals, new_labels = mir_eval.util.adjust_intervals(
    intervals, labels=labels, t_min=0.0, t_max=30.0
)
```

### LLM Instruction Prompt
- Always ensure `intervals` is a NumPy array of shape `(n_events, 2)`.
- If `labels` are provided, ensure the length of the list matches the number of rows in `intervals`.
- Use this function to normalize estimated intervals to match the duration of reference intervals before passing them to `mir_eval` evaluation functions.

### Prompt Snippet
```text
# Normalize intervals to reference duration
adj_est_int, adj_est_lab = mir_eval.util.adjust_intervals(
    est_intervals, labels=est_labels, t_min=ref_intervals.min(), t_max=ref_intervals.max()
)
```

### Common Failure Modes
- **Shape Mismatch:** Passing `intervals` that are not `(n, 2)` or providing a `labels` list that does not match the number of intervals.
- **Unsorted Input:** Providing unsorted intervals may lead to unexpected behavior in downstream evaluation metrics that assume chronological order.
- **Invalid Range:** Setting `t_min` greater than `t_max` will result in an empty or invalid interval set.

### Fix Code Hint
```python
# Ensure intervals are sorted before adjustment
idx = np.argsort(intervals[:, 0])
intervals = intervals[idx]
if labels is not None:
    labels = [labels[i] for i in idx]
new_intervals, new_labels = mir_eval.util.adjust_intervals(intervals, labels, t_min, t_max)
```

## API Test: `python:mir_eval.util.boundaries_to_intervals`

### Signature
```python
def boundaries_to_intervals(boundaries)
```
_Source: source/mir_eval/util.py:239_

_Source doc:_ Convert an array of event times into intervals

Parameters
----------
boundaries : list-like
    List-like of event times.  These are assumed to be unique
    timestamps in ascending order.

Returns
-------
intervals : np.ndarray, shape=(n_intervals, 2)
    Start and end time for each interval

### Goal
Converts a sequence of discrete event timestamps into a series of contiguous intervals, where each interval is defined by consecutive event times.

### Parameters
- `boundaries`: A list-like object (e.g., `list`, `np.ndarray`) containing event timestamps in seconds.

### Input
- **Data Format:** A 1D array or list of floats representing time in seconds.
- **Preconditions:** The input `boundaries` must be sorted in ascending order and contain unique timestamps. If the input is not sorted, the resulting intervals will not represent valid chronological segments.

### Output
Returns `np.ndarray` of shape `(n_intervals, 2)`:
- Each row represents an interval `[start, end]`, where `start` is `boundaries[i]` and `end` is `boundaries[i+1]`.
- The number of intervals returned is `len(boundaries) - 1`.

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example: Converting segment boundaries to intervals
boundaries = np.array([0.0, 5.5, 12.0, 20.0])
intervals = mir_eval.util.boundaries_to_intervals(boundaries)
# Result: np.array([[0.0, 5.5], [5.5, 12.0], [12.0, 20.0]])
```

### LLM Instruction Prompt
- When calling `mir_eval.util.boundaries_to_intervals`, ensure the input `boundaries` is a 1D array of floats sorted in ascending order.
- The function expects at least two timestamps to produce a valid interval; if fewer than two are provided, the output array will be empty or malformed.
- Always verify that the input timestamps are unique to avoid zero-length intervals.

### Prompt Snippet
```text
# Ensure boundaries are sorted before conversion
boundaries = np.sort(boundaries)
intervals = mir_eval.util.boundaries_to_intervals(boundaries)
```

### Common Failure Modes
- **Unsorted Input:** Providing unsorted timestamps will result in intervals with negative durations (e.g., `[10.0, 5.0]`), which will cause errors in downstream evaluation functions.
- **Duplicate Timestamps:** Including duplicate timestamps will result in zero-length intervals, which may violate assumptions in other `mir_eval` modules.
- **Insufficient Data:** Providing an empty list or a single timestamp will result in an empty array, which may cause index errors if the calling code expects at least one interval.

### Fix Code Hint
```python
# Ensure input is sorted and unique to prevent invalid intervals
clean_boundaries = np.unique(np.sort(boundaries))
if len(clean_boundaries) > 1:
    intervals = mir_eval.util.boundaries_to_intervals(clean_boundaries)
else:
    intervals = np.empty((0, 2))
```

## API Test: `python:mir_eval.util.deprecated`

### Signature
```python
def deprecated(*, version, version_removed)
```
_Source: source/mir_eval/util.py:946_

_Source doc:_ Mark a function as deprecated.

Using the decorated (old) function will result in a warning.

### Goal
Provides a decorator to mark legacy functions as deprecated, ensuring users receive a warning when invoking outdated MIR evaluation utilities.

### Parameters
- `version`: The version of `mir_eval` in which the function was first marked as deprecated.
- `version_removed`: The version of `mir_eval` in which the function is scheduled to be removed.

### Input
- The decorator is applied to a function definition.
- Both `version` and `version_removed` must be provided as keyword arguments.

### Output
Returns `unspecified` — The decorator returns a wrapped version of the original function that issues a warning upon execution.

### Valid Call Patterns
```python
from mir_eval.util import deprecated

@deprecated(version='0.1', version_removed='0.2')
def old_function():
    pass
```
*(Note: This call pattern is inferred from the signature as no explicit test-suite example was provided.)*

### LLM Instruction Prompt
- Use `mir_eval.util.deprecated` as a decorator for functions that are no longer recommended for use.
- You must provide both `version` and `version_removed` as keyword-only arguments.
- Do not use this decorator for active, supported functions.

### Prompt Snippet
```text
@mir_eval.util.deprecated(version='X.Y', version_removed='A.B')
def my_legacy_function(...):
    ...
```

### Common Failure Modes
- Providing positional arguments instead of keyword-only arguments, which will raise a `TypeError`.
- Omitting either `version` or `version_removed`, which are required parameters.
- Applying the decorator to a function that is still intended for long-term support, causing unnecessary user confusion.

### Fix Code Hint
```python
# Ensure keyword arguments are used
@mir_eval.util.deprecated(version='0.4', version_removed='0.5')
def legacy_metric_calculation():
    # Implementation
    pass
```

## API Test: `python:mir_eval.util.f_measure`

### Signature
```python
def f_measure(precision, recall, beta=1.0)
```
_Source: source/mir_eval/util.py:197_

_Source doc:_ Compute the f-measure from precision and recall scores.

Parameters
----------
precision : float in (0, 1]
    Precision
recall : float in (0, 1]
    Recall
beta : float > 0
    Weighting factor for f-measure
    (Default value = 1.0)

Returns
-------
f_measure : float
    The weighted f-measure

### Goal
Computes the weighted F-measure (harmonic mean) from provided precision and recall scores to evaluate the accuracy of MIR system outputs.

### Parameters
- `precision`: A float representing the precision score, expected to be in the range (0, 1].
- `recall`: A float representing the recall score, expected to be in the range (0, 1].
- `beta`, default `1.0`: A float greater than 0 that determines the weighting factor for the F-measure; a value of 1.0 corresponds to the standard F1-score.

### Input
The function expects two scalar floats (`precision` and `recall`) derived from system evaluation. Precondition: Inputs must be within the range (0, 1].

### Output
Returns a `float` representing the weighted F-measure score.

### Valid Call Patterns
```python
import mir_eval
# Example using default beta (F1-score)
score = mir_eval.util.f_measure(0.85, 0.90)

# Example using a custom beta value
score = mir_eval.util.f_measure(0.85, 0.90, beta=0.5)
```

### LLM Instruction Prompt
- When calling `mir_eval.util.f_measure`, ensure that `precision` and `recall` are provided as floats between 0 and 1.
- If the goal is to compute the standard F1-score, omit the `beta` argument or set it explicitly to 1.0.
- Ensure `beta` is a positive float; values <= 0 are not supported.

### Prompt Snippet
```text
# Compute F-measure using mir_eval
f_score = mir_eval.util.f_measure(precision_val, recall_val, beta=1.0)
```

### Common Failure Modes
- Passing values outside the (0, 1] range for `precision` or `recall`, which may lead to mathematically invalid F-measure results.
- Providing a non-positive value for `beta`, which violates the `beta > 0` constraint.
- Passing arrays instead of scalar floats; the function expects scalar inputs for precision and recall.

### Fix Code Hint
```python
# Ensure inputs are valid floats before calling
precision = max(0.0, min(1.0, precision))
recall = max(0.0, min(1.0, recall))
f_score = mir_eval.util.f_measure(precision, recall, beta=1.0)
```

## API Test: `python:mir_eval.util.filter_kwargs`

### Signature
```python
def filter_kwargs(_function, *args, **kwargs)
```
_Source: source/mir_eval/util.py:860_

_Source doc:_ Given a function and args and keyword args to pass to it, call the function
but using only the keyword arguments which it accepts.  This is equivalent
to redefining the function with an additional \*\*kwargs to accept slop
keyword args.

If the target function already accepts \*\*kwargs parameters, no filtering
is performed.

Parameters
----------
_function : callable
    Function to call.  Can take in any number of args or kwargs
*args
**kwargs
    Arguments and keyword arguments to _function.

### Goal
`filter_kwargs` enables robust function execution by automatically stripping unsupported keyword arguments from a call, preventing `TypeError` exceptions when passing "slop" arguments to functions with fixed signatures.

### Parameters
- `_function`: A callable object (function or method) that will be executed.
- `args`: Positional arguments to be passed directly to `_function`.
- `kwargs`: A collection of keyword arguments; only those explicitly accepted by `_function` will be passed through, while others are discarded.

### Input
- **Data:** Any callable `_function` and arbitrary arguments.
- **Preconditions:** If `_function` already includes `**kwargs` in its signature, the function will be called with all provided arguments without filtering.

### Output
Returns the result of the executed `_function`. The return type is determined by the return value of the provided `_function`.

### Valid Call Patterns
```python
# Example: Calling a function with extra keyword arguments that it does not accept
def my_metric(a, b):
    return a + b

# This would normally raise a TypeError if 'c' was passed
result = mir_eval.util.filter_kwargs(my_metric, 1, 2, c=3)
```

### LLM Instruction Prompt
- Use `mir_eval.util.filter_kwargs` when you need to pass a generic set of configuration parameters to a function that may not support all of them.
- Do not assume the function will accept all provided `kwargs`; this utility is specifically for handling "slop" arguments.
- Ensure the first argument is a callable.

### Prompt Snippet
```text
# Use filter_kwargs to safely pass configuration to a metric function
from mir_eval.util import filter_kwargs
result = filter_kwargs(target_function, *args, **kwargs)
```

### Common Failure Modes
- **Non-callable input:** Passing a non-callable object as the first argument will raise a `TypeError`.
- **Positional argument mismatch:** `filter_kwargs` does not filter positional arguments; if the number of `args` does not match the required positional arguments of `_function`, a `TypeError` will still occur.
- **Over-filtering:** If a function uses `**kwargs` to dynamically handle arguments, `filter_kwargs` will pass all arguments through, which might lead to unexpected behavior if the target function logic relies on specific keyword presence.

### Fix Code Hint
```python
# If you encounter a TypeError: 'unexpected keyword argument', 
# wrap the call in filter_kwargs:
from mir_eval.util import filter_kwargs
# Instead of: func(a, b, c=3)
# Use:
filter_kwargs(func, a, b, c=3)
```

## API Test: `python:mir_eval.util.generate_labels`

### Signature
```python
def generate_labels(items, prefix='__')
```
_Source: source/mir_eval/util.py:53_

_Source doc:_ Given an array of items (e.g. events, intervals), create a synthetic label
for each event of the form '(label prefix)(item number)'

Parameters
----------
items : list-like
    A list or array of events or intervals
prefix : str
    This prefix will be prepended to all synthetically generated labels
    (Default value = '__')

Returns
-------
labels : list of str
    Synthetically generated labels

### Goal
Generates a sequence of unique, synthetic string labels for a collection of events or intervals to facilitate standardized labeling in MIR evaluation tasks.

### Parameters
- `items`: A list-like object (e.g., a list or NumPy array) containing the events or intervals for which labels are to be generated.
- `prefix`, default `'__'`: A string to prepend to each generated label, serving as a namespace or identifier for the synthetic labels.

### Input
The caller must provide a list-like structure of items. While the function accepts any list-like input, it is typically used in conjunction with event timestamps or interval arrays loaded via `mir_eval.io` utilities. No specific sorting is required for the input, as the function generates labels based on the order of the provided items.

### Output
Returns a `list` of `str` objects, where each string is formatted as `(prefix)(index)`, with the index corresponding to the position of the item in the input list.

### Valid Call Patterns
```python
import mir_eval
# Example using a list of events
events = [0.5, 1.2, 2.5]
labels = mir_eval.util.generate_labels(events, prefix='event_')
# Result: ['event_0', 'event_1', 'event_2']
```

### LLM Instruction Prompt
- When calling `mir_eval.util.generate_labels`, ensure the `items` argument is a list-like object.
- Use the `prefix` argument to distinguish between different sets of labels if multiple annotation types are being processed in the same evaluation pipeline.
- The function returns a list of strings; ensure this list is compatible with any downstream functions expecting labeled data (e.g., `mir_eval.segment.evaluate`).

### Prompt Snippet
```text
# Generate synthetic labels for a set of intervals
labels = mir_eval.util.generate_labels(intervals, prefix='segment_')
```

### Common Failure Modes
- Passing a non-iterable object as `items` will raise a `TypeError`.
- If the `prefix` is not provided, the default `__` prefix may lead to ambiguous labels if multiple event lists are concatenated or compared.
- The function does not validate the content of `items`; it only uses the length of the input to generate the index, so ensure the input list is not empty if labels are required.

### Fix Code Hint
```python
# Ensure items is a list or array before calling
if items is not None and len(items) > 0:
    labels = mir_eval.util.generate_labels(items, prefix='my_label_')
else:
    labels = []
```

## API Test: `python:mir_eval.util.has_kwargs`

### Signature
```python
def has_kwargs(function)
```
_Source: source/mir_eval/util.py:838_

_Source doc:_ Determine whether a function has \*\*kwargs.

Parameters
----------
function : callable
    The function to test

Returns
-------
True if function accepts arbitrary keyword arguments.
False otherwise.

### Goal
Determine programmatically whether a given callable object supports arbitrary keyword arguments (`**kwargs`), facilitating dynamic function inspection within evaluation pipelines.

### Parameters
- `function`: A `callable` object (e.g., a function, method, or class constructor) to be inspected for the presence of a variable keyword argument parameter.

### Input
- **Data:** A valid Python callable.
- **Preconditions:** The object must be inspectable by the Python `inspect` module (which this utility wraps).

### Output
Returns `bool`: `True` if the provided function signature includes a `**kwargs` parameter, and `False` otherwise.

### Valid Call Patterns
```python
import mir_eval.util

# Example: Checking a function with kwargs
def my_func(a, **kwargs):
    pass

result = mir_eval.util.has_kwargs(my_func)
# result is True
```

### LLM Instruction Prompt
- Use `mir_eval.util.has_kwargs(function)` to verify if a callable accepts arbitrary keyword arguments before attempting to pass extra parameters to it.
- Do not assume the function signature; use this utility to handle dynamic dispatch or decorator logic safely.

### Prompt Snippet
```text
# Check if the function supports arbitrary keyword arguments
if mir_eval.util.has_kwargs(my_callable):
    # Safe to pass extra keyword arguments
    my_callable(data, **extra_params)
else:
    # Fallback or handle without extra arguments
    my_callable(data)
```

### Common Failure Modes
- **Non-callable input:** Passing an object that is not a function or callable (e.g., a string or integer) will raise a `TypeError` from the underlying `inspect` module.
- **Built-in functions:** Some built-in functions implemented in C may not expose their signature in a way that `inspect` can parse, potentially leading to unexpected `False` results.

### Fix Code Hint
```python
# Ensure the input is a callable before checking
if callable(my_obj):
    if mir_eval.util.has_kwargs(my_obj):
        # Proceed with kwargs
        pass
```

## API Test: `python:mir_eval.util.hz_to_midi`

### Signature
```python
def hz_to_midi(freqs)
```
_Source: source/mir_eval/util.py:913_

_Source doc:_ Convert Hz to MIDI numbers

Parameters
----------
freqs : number or ndarray
    Frequency/frequencies in Hz

Returns
-------
midi : number or ndarray
    MIDI note numbers corresponding to input frequencies.
    Note that these may be fractional.

### Goal
Converts fundamental frequencies (F0) from Hertz (Hz) into MIDI note numbers to facilitate pitch-based evaluation and comparison in MIR tasks.

### Parameters
- `freqs`: A scalar number or a NumPy `ndarray` containing frequency values in Hz.

### Input
- **Data:** Frequency values representing pitch.
- **Preconditions:** Input must be a valid numeric type or a NumPy array. While the function handles scalar or array inputs, ensure that the input frequencies are positive, as MIDI conversion is mathematically undefined for non-positive frequencies.

### Output
Returns `number or ndarray` — The corresponding MIDI note numbers. The output preserves the shape of the input `freqs` array. Note that the returned values are floating-point numbers, allowing for fractional MIDI values (e.g., microtonal deviations).

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example with a single frequency
midi_val = mir_eval.util.hz_to_midi(440.0)

# Example with an array of frequencies
freq_array = np.array([440.0, 880.0, 220.0])
midi_array = mir_eval.util.hz_to_midi(freq_array)
```

### LLM Instruction Prompt
- Use `mir_eval.util.hz_to_midi` when you need to map raw frequency data (e.g., from pitch tracking or melody extraction) into the MIDI scale.
- Always pass the frequency data as a NumPy array if processing multiple time points to ensure efficient vectorized computation.
- Remember that the output is a float; if you require integer MIDI notes, you must explicitly cast the result using `np.round()`.

### Prompt Snippet
```text
# Convert frequency array to MIDI for pitch evaluation
midi_estimates = mir_eval.util.hz_to_midi(estimated_frequencies)
```

### Common Failure Modes
- **Non-positive frequencies:** Passing 0 or negative values will result in mathematically invalid MIDI outputs (typically negative infinity or NaN depending on the implementation details of the conversion formula).
- **Type Mismatch:** Passing non-numeric types (e.g., strings or lists of strings) will raise a `TypeError` or `ValueError` during the internal NumPy calculation.
- **Shape Mismatch:** If the input is a multi-dimensional array, the output will maintain that shape; ensure downstream evaluation functions are prepared to handle the dimensionality of the returned MIDI array.

### Fix Code Hint
```python
# Ensure frequencies are positive before conversion
freqs = np.maximum(freqs, 1e-6)
midi = mir_eval.util.hz_to_midi(freqs)
```

## API Test: `python:mir_eval.util.index_labels`

### Signature
```python
def index_labels(labels, case_sensitive=False)
```
_Source: source/mir_eval/util.py:14_

_Source doc:_ Convert a list of string identifiers into numerical indices.

Parameters
----------
labels : list of strings, shape=(n,)
    A list of annotations, e.g., segment or chord labels from an
    annotation file.
case_sensitive : bool
    Set to True to enable case-sensitive label indexing
    (Default value = False)

Returns
-------
indices : list, shape=(n,)
    Numerical representation of ``labels``
index_to_label : dict
    Mapping to convert numerical indices back to labels.
    ``labels[i] == index_to_label[indices[i]]``

### Goal
Converts a sequence of categorical string labels into a corresponding sequence of unique numerical indices, facilitating numerical processing of symbolic annotation data.

### Parameters
- `labels`: A list of strings representing annotations (e.g., chord names or segment identifiers).
- `case_sensitive`, default `False`: A boolean flag; if `True`, distinct casing (e.g., "C:maj" vs "c:maj") results in different numerical indices. If `False`, labels are treated as case-insensitive.

### Input
- **Data:** A list of strings of length $n$.
- **Preconditions:** The input must be a list of strings. This function is typically used after loading annotations via `mir_eval.io` functions (e.g., `load_labeled_intervals`) to prepare categorical data for algorithms requiring numerical input.

### Output
Returns a tuple containing:
- `indices`: A list of integers of length $n$ representing the numerical mapping of the input labels.
- `index_to_label`: A dictionary mapping the generated integer indices back to their original string labels.

### Valid Call Patterns
```python
# Example inferred from signature
labels = ['C:maj', 'G:maj', 'C:maj', 'F:maj']
indices, index_to_label = mir_eval.util.index_labels(labels, case_sensitive=False)
```

### LLM Instruction Prompt
- Use `mir_eval.util.index_labels` when you need to transform categorical string annotations into a numerical format suitable for mathematical evaluation or machine learning pipelines.
- Always capture both return values: the list of indices and the dictionary mapping.
- If the evaluation task requires distinguishing between label cases, explicitly set `case_sensitive=True`.

### Prompt Snippet
```text
# Convert labels to indices for numerical processing
indices, index_to_label = mir_eval.util.index_labels(labels, case_sensitive=False)
```

### Common Failure Modes
- **Type Mismatch:** Passing non-string elements within the `labels` list will cause errors during indexing.
- **Case Sensitivity Confusion:** If `case_sensitive` is `False` (default), labels like "A" and "a" will be mapped to the same index; ensure this matches the requirements of your specific MIR task.
- **Empty Input:** Passing an empty list will return an empty list of indices and an empty dictionary.

### Fix Code Hint
```python
# Ensure labels are strings before indexing
labels = [str(l) for l in labels]
indices, index_to_label = mir_eval.util.index_labels(labels)
```

## API Test: `python:mir_eval.util.interpolate_intervals`

### Signature
```python
def interpolate_intervals(intervals, labels, time_points, fill_value=None)
```
_Source: source/mir_eval/util.py:118_

_Source doc:_ Assign labels to a set of points in time given a set of intervals.

Time points that do not lie within an interval are mapped to `fill_value`.

Parameters
----------
intervals : np.ndarray, shape=(n, 2)
    An array of time intervals, as returned by
    :func:`mir_eval.io.load_intervals()`.
    The ``i`` th interval spans time ``intervals[i, 0]`` to
    ``intervals[i, 1]``.

    Intervals are assumed to be disjoint.

labels : list, shape=(n,)
    The annotation for each interval

time_points : array_like, shape=(m,)
    Points in time to assign labels.  These must be in
    non-decreasing order.

fill_value : type(labels[0])
    Object to use for the label with out-of-range time points.
    (Default value = None)

Returns
-------
aligned_labels : list
    Labels corresponding to the given time points.

Raises
------
ValueError
    If `time_points` is not in non-decreasing order.

### Goal
Maps discrete time-based annotations (labeled intervals) onto a specific set of time points to create a synchronized label sequence.

### Parameters
- `intervals`: A NumPy array of shape `(n, 2)` where each row represents `[start, end]` time in seconds. Intervals must be disjoint.
- `labels`: A list of length `n` containing the annotation associated with each corresponding interval.
- `time_points`: An array-like object of length `m` containing the timestamps (in seconds) for which labels are requested.
- `fill_value`, default `None`: The value assigned to any `time_points` that do not fall within any of the provided `intervals`.

### Input
- **Data Format:** `intervals` should be a NumPy array of floats; `labels` should be a list of strings or objects; `time_points` should be a 1D array of floats.
- **Preconditions:** `time_points` must be sorted in non-decreasing order. `intervals` must be disjoint. All time values must be in seconds.

### Output
Returns `aligned_labels` (list): A list of length `m` where each element is the label corresponding to the interval containing the respective `time_point`, or `fill_value` if no interval contains that point.

### Valid Call Patterns
```python
import numpy as np
from mir_eval.util import interpolate_intervals

# Example: Mapping labels to specific time points
intervals = np.array([[0.0, 1.0], [1.0, 2.0]])
labels = ['A', 'B']
time_points = np.array([0.5, 1.5, 2.5])
aligned = interpolate_intervals(intervals, labels, time_points, fill_value='None')
# Result: ['A', 'B', 'None']
```

### LLM Instruction Prompt
- Ensure `time_points` is sorted before passing to the function.
- Ensure `intervals` are disjoint; overlapping intervals may lead to undefined behavior.
- Ensure the length of `labels` matches the number of rows in `intervals`.

### Prompt Snippet
```text
mir_eval.util.interpolate_intervals(intervals, labels, time_points, fill_value=None)
```

### Common Failure Modes
- **ValueError:** Raised if `time_points` is not in non-decreasing order.
- **IndexError:** Occurs if the length of `labels` does not match the number of rows in `intervals`.
- **Logic Error:** Providing overlapping intervals, which violates the assumption that intervals are disjoint.

### Fix Code Hint
```python
# Ensure time_points are sorted
time_points = np.sort(time_points)
# Ensure intervals are disjoint (if necessary, use other util functions to clean)
aligned = mir_eval.util.interpolate_intervals(intervals, labels, time_points, fill_value='unknown')
```

## API Test: `python:mir_eval.util.intersect_files`

### Signature
```python
def intersect_files(flist1, flist2)
```
_Source: source/mir_eval/util.py:427_

_Source doc:_ Return the intersection of two sets of filepaths, based on the file name
(after the final '/') and ignoring the file extension.

Examples
--------
 >>> flist1 = ['/a/b/abc.lab', '/c/d/123.lab', '/e/f/xyz.lab']
 >>> flist2 = ['/g/h/xyz.npy', '/i/j/123.txt', '/k/l/456.lab']
 >>> sublist1, sublist2 = mir_eval.util.intersect_files(flist1, flist2)
 >>> print sublist1
 ['/e/f/xyz.lab', '/c/d/123.lab']
 >>> print sublist2
 ['/g/h/xyz.npy', '/i/j/123.txt']

Parameters
----------
flist1 : list
    first list of filepaths
flist2 : list
    second list of filepaths

Returns
-------
sublist1 : list
    subset of filepaths with matching stems from ``flist1``
sublist2 : list
    corresponding filepaths from ``flist2``

### Goal
Identify and return the subset of file paths from two lists that share the same filename stem, facilitating the alignment of ground-truth and estimated annotation files regardless of their directory structure or file extensions.

### Parameters
- `flist1`: A list of strings representing absolute or relative file paths for the first set of data (e.g., reference annotations).
- `flist2`: A list of strings representing absolute or relative file paths for the second set of data (e.g., estimated outputs).

### Input
The function expects two lists of strings. The input paths are parsed by splitting at the final forward slash (`/`) and stripping the file extension. Precondition: The lists should contain valid file path strings; the function does not verify the existence of these files on the filesystem.

### Output
Returns a tuple of two lists (`sublist1`, `sublist2`). Each list contains the subset of paths from the original input lists that have a matching filename stem. The order of elements in the returned lists corresponds to the order of matches found.

### Valid Call Patterns
```python
import mir_eval
flist1 = ['/a/b/abc.lab', '/c/d/123.lab', '/e/f/xyz.lab']
flist2 = ['/g/h/xyz.npy', '/i/j/123.txt', '/k/l/456.lab']
sublist1, sublist2 = mir_eval.util.intersect_files(flist1, flist2)
```

### LLM Instruction Prompt
When using `mir_eval.util.intersect_files`, ensure that both inputs are provided as lists of strings. The function is intended for matching files by name stem; do not rely on it to validate file existence or content. Use the returned sublists to iterate through pairs of corresponding reference and estimated files for batch evaluation.

### Prompt Snippet
```text
# Example of using intersect_files to prepare for batch evaluation
sublist1, sublist2 = mir_eval.util.intersect_files(reference_files, estimated_files)
for ref_path, est_path in zip(sublist1, sublist2):
    # Load and evaluate...
```

### Common Failure Modes
- **Path Formatting:** If file paths use backslashes (`\`) instead of forward slashes (`/`), the stem extraction logic may fail to identify the filename correctly on some systems.
- **Ambiguous Stems:** If multiple files in the same list share the same stem (e.g., `path/to/track1.lab` and `other/path/track1.txt`), the intersection logic may produce unexpected results or partial matches.
- **Empty Intersections:** If no files share a common stem, the function returns two empty lists; ensure your code handles empty lists to avoid errors in subsequent processing loops.

### Fix Code Hint
```python
# Ensure paths are normalized to use forward slashes if necessary
import os
flist1 = [p.replace(os.sep, '/') for p in flist1]
flist2 = [p.replace(os.sep, '/') for p in flist2]
sublist1, sublist2 = mir_eval.util.intersect_files(flist1, flist2)
```

## API Test: `python:mir_eval.util.intervals_to_boundaries`

### Signature
```python
def intervals_to_boundaries(intervals, q=5)
```
_Source: source/mir_eval/util.py:221_

_Source doc:_ Convert interval times into boundaries.

Parameters
----------
intervals : np.ndarray, shape=(n_events, 2)
    Array of interval start and end-times
q : int
    Number of decimals to round to. (Default value = 5)

Returns
-------
boundaries : np.ndarray
    Interval boundary times, including the end of the final interval

### Goal
Converts a set of disjoint interval start and end-times into a sorted, unique array of boundary timestamps suitable for segmentation evaluation.

### Parameters
- `intervals`: A NumPy array of shape `(n_events, 2)` containing `[start, end]` time pairs in seconds.
- `q`, default `5`: The number of decimal places to which the resulting boundary timestamps are rounded.

### Input
- **Data Format:** Requires a 2D NumPy array where each row represents an interval.
- **Preconditions:** Intervals should be disjoint. The function assumes time is provided in seconds.

### Output
Returns a 1D `np.ndarray` containing the unique boundary times, including the start of the first interval and the end of the final interval, rounded to `q` decimal places.

### Valid Call Patterns
```python
import numpy as np
import mir_eval

# Example: Converting labeled intervals to boundary points
intervals = np.array([[0.0, 2.5], [2.5, 5.0], [5.0, 10.0]])
boundaries = mir_eval.util.intervals_to_boundaries(intervals, q=3)
```

### LLM Instruction Prompt
- When calling `mir_eval.util.intervals_to_boundaries`, ensure the input `intervals` is a 2D NumPy array of shape `(n, 2)`.
- The function is intended for use when preparing segment-based evaluation data; ensure the input intervals are sorted and disjoint to maintain logical consistency in the output boundaries.

### Prompt Snippet
```text
# Use mir_eval.util.intervals_to_boundaries to extract unique time boundaries from intervals
boundaries = mir_eval.util.intervals_to_boundaries(intervals, q=5)
```

### Common Failure Modes
- **Shape Mismatch:** Passing a 1D array or an array not shaped `(n, 2)` will result in a `ValueError` or incorrect indexing.
- **Non-Disjoint Intervals:** If intervals overlap, the resulting boundary array may contain redundant or unexpected points, which can skew segmentation metrics.
- **Data Type:** Passing non-numeric types in the NumPy array will cause a failure during the rounding or sorting operations.

### Fix Code Hint
```python
# Ensure intervals are sorted by start time before conversion
intervals = intervals[intervals[:, 0].argsort()]
boundaries = mir_eval.util.intervals_to_boundaries(intervals)
```

## API Test: `python:mir_eval.util.intervals_to_durations`

### Signature
```python
def intervals_to_durations(intervals)
```
_Source: source/mir_eval/util.py:892_

_Source doc:_ Convert an array of n intervals to their n durations.

Parameters
----------
intervals : np.ndarray, shape=(n, 2)
    An array of time intervals, as returned by
    :func:`mir_eval.io.load_intervals()`.
    The ``i`` th interval spans time ``intervals[i, 0]`` to
    ``intervals[i, 1]``.

Returns
-------
durations : np.ndarray, shape=(n,)
    Array of the duration of each interval.

### Goal
Calculates the temporal length of each interval in a collection of start-end time pairs, facilitating duration-based analysis in MIR evaluation workflows.

### Parameters
- `intervals`: A NumPy array of shape `(n, 2)` where each row represents an interval `[start, end]` in seconds.

### Input
- **Data Format:** Must be a `np.ndarray` of floats with shape `(n, 2)`.
- **Preconditions:** The input array should be formatted as `[onset, offset]` pairs. While not strictly enforced by the function, it is standard practice in `mir_eval` that intervals are sorted by time and represent valid, non-negative durations.

### Output
Returns a `np.ndarray` of shape `(n,)` containing the calculated duration (`end - start`) for each corresponding interval.

### Valid Call Patterns
```python
import mir_eval
import numpy as np

# Example: Converting a set of intervals to durations
intervals = np.array([[0.0, 1.5], [1.5, 3.0], [3.0, 5.0]])
durations = mir_eval.util.intervals_to_durations(intervals)
# Result: array([1.5, 1.5, 2.0])
```

### LLM Instruction Prompt
- When calling `mir_eval.util.intervals_to_durations`, ensure the input is a 2D NumPy array with exactly two columns.
- The function assumes the input represents time in seconds; ensure your input data is normalized to this unit before processing.
- Use this function when you need to compute the length of segments or notes for statistical analysis or duration-weighted metric calculations.

### Prompt Snippet
```text
# Calculate durations from intervals
durations = mir_eval.util.intervals_to_durations(intervals)
```

### Common Failure Modes
- **Shape Mismatch:** Passing a 1D array or an array with a number of columns other than 2 will result in a `ValueError` or incorrect indexing during the subtraction operation.
- **Negative Durations:** If `intervals[i, 1] < intervals[i, 0]`, the function will return negative values, which may cause downstream errors in metrics expecting positive durations.
- **Non-NumPy Input:** Passing a list of lists instead of a `np.ndarray` may cause the subtraction operation to fail or behave unexpectedly; always cast inputs to `np.array` first.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure input is a numpy array of the correct shape
intervals = np.array(intervals)
if intervals.ndim == 1:
    intervals = intervals.reshape(-1, 2)
durations = mir_eval.util.intervals_to_durations(intervals)
```

## API Test: `python:mir_eval.util.intervals_to_samples`

### Signature
```python
def intervals_to_samples(intervals, labels, offset=0, sample_size=0.1, fill_value=None)
```
_Source: source/mir_eval/util.py:74_

_Source doc:_ Convert an array of labeled time intervals to annotated samples.

Parameters
----------
intervals : np.ndarray, shape=(n, d)
    An array of time intervals, as returned by
    :func:`mir_eval.io.load_intervals()` or
    :func:`mir_eval.io.load_labeled_intervals()`.
    The ``i`` th interval spans time ``intervals[i, 0]`` to
    ``intervals[i, 1]``.
labels : list, shape=(n,)
    The annotation for each interval
offset : float > 0
    Phase offset of the sampled time grid (in seconds)
    (Default value = 0)
sample_size : float > 0
    duration of each sample to be generated (in seconds)
    (Default value = 0.1)
fill_value : type(labels[0])
    Object to use for the label with out-of-range time points.
    (Default value = None)

Returns
-------
sample_times : list
    list of sample times
sample_labels : list
    array of labels for each generated sample

Notes
-----
    Intervals will be rounded down to the nearest multiple
    of ``sample_size``.

### Goal
Converts continuous labeled time intervals into a discrete, regularly sampled time series representation suitable for frame-based evaluation.

### Parameters
- `intervals`: An $N \times 2$ NumPy array where each row represents a start and end time in seconds.
- `labels`: A list of $N$ annotations corresponding to each interval.
- `offset`, default `0`: A float representing the phase shift of the sampling grid in seconds.
- `sample_size`, default `0.1`: A float defining the duration of each discrete sample in seconds.
- `fill_value`, default `None`: The value assigned to time points that fall outside the provided interval range.

### Input
- **Data:** Requires `intervals` as an $N \times 2$ NumPy array and `labels` as a list of length $N$.
- **Preconditions:** Intervals are assumed to be disjoint. The function rounds interval boundaries down to the nearest multiple of `sample_size`.

### Output
Returns a tuple containing:
- `sample_times`: A list of timestamps representing the center or start of each generated sample.
- `sample_labels`: A list of labels corresponding to each generated sample time.

### Valid Call Patterns
```python
# Inferred from signature:
sample_times, sample_labels = mir_eval.util.intervals_to_samples(
    intervals, labels, offset=0.0, sample_size=0.1, fill_value=None
)
```

### LLM Instruction Prompt
- When calling `mir_eval.util.intervals_to_samples`, ensure `intervals` is a NumPy array of shape `(n, 2)` and `labels` is a list of length `n`.
- Always specify `sample_size` if the default 0.1s resolution is not appropriate for the specific MIR task (e.g., beat tracking vs. segmentation).
- Ensure `fill_value` matches the data type of the elements in `labels`.

### Prompt Snippet
```text
import mir_eval.util
# Assuming intervals and labels are loaded via mir_eval.io
sample_times, sample_labels = mir_eval.util.intervals_to_samples(intervals, labels, sample_size=0.05)
```

### Common Failure Modes
- **Mismatched Lengths:** Providing `intervals` and `labels` with different lengths will cause an error.
- **Rounding Artifacts:** Because intervals are rounded down to the nearest multiple of `sample_size`, very short intervals may disappear if they are smaller than the `sample_size`.
- **Type Mismatch:** Providing a `fill_value` that is incompatible with the existing `labels` list type may cause downstream processing errors.

### Fix Code Hint
```python
# Ensure intervals are sorted and labels match length
import numpy as np
intervals = np.array([[0.0, 1.0], [1.0, 2.0]])
labels = ['A', 'B']
# Use a consistent sample size for the task
times, sampled_labels = mir_eval.util.intervals_to_samples(intervals, labels, sample_size=0.1)
```

## API Test: `python:mir_eval.util.match_events`

### Signature
```python
def match_events(ref, est, window, distance=None)
```
_Source: source/mir_eval/util.py:644_

_Source doc:_ Compute a maximum matching between reference and estimated event times,
subject to a window constraint.

Given two lists of event times ``ref`` and ``est``, we seek the largest set
of correspondences ``(ref[i], est[j])`` such that
``distance(ref[i], est[j]) <= window``, and each
``ref[i]`` and ``est[j]`` is matched at most once.

This is useful for computing precision/recall metrics in beat tracking,
onset detection, and segmentation.

Parameters
----------
ref : np.ndarray, shape=(n,)
    Array of reference values
est : np.ndarray, shape=(m,)
    Array of estimated values
window : float > 0
    Size of the window.
distance : function
    function that computes the outer distance of ref and est.
    By default uses ``|ref[i] - est[j]|``

Returns
-------
matching : list of tuples
    A list of matched reference and event numbers.
    ``matching[i] == (i, j)`` where ``ref[i]`` matches ``est[j]``.

### Goal
Computes the optimal bipartite matching between reference and estimated event timestamps to facilitate precision and recall calculations in MIR tasks like beat tracking and onset detection.

### Parameters
- `ref`: A 1D NumPy array of reference event timestamps (in seconds).
- `est`: A 1D NumPy array of estimated event timestamps (in seconds).
- `window`: A positive float defining the maximum allowable distance for a valid match.
- `distance`, default `None`: An optional function to compute the distance matrix between `ref` and `est`. If `None`, defaults to the absolute difference `|ref[i] - est[j]|`.

### Input
- **Data:** Requires two 1D NumPy arrays of floats representing time in seconds.
- **Preconditions:** Input arrays should be sorted by time. The function assumes events are discrete points in time.

### Output
Returns `list of tuples`: A list of index pairs `(i, j)` where `ref[i]` is matched to `est[j]`.

### Valid Call Patterns
```python
# Example inferred from signature
import numpy as np
import mir_eval

ref = np.array([1.0, 2.0, 3.0])
est = np.array([1.05, 2.1, 3.05])
window = 0.1
matching = mir_eval.util.match_events(ref, est, window)
```

### LLM Instruction Prompt
- When calling `mir_eval.util.match_events`, ensure `ref` and `est` are 1D NumPy arrays sorted by time.
- The `window` parameter must be a positive float.
- If providing a custom `distance` function, ensure it accepts two arguments and returns a distance matrix compatible with the `window` threshold.

### Prompt Snippet
```text
# Use mir_eval.util.match_events to find correspondences
matching = mir_eval.util.match_events(ref_events, est_events, window=0.05)
```

### Common Failure Modes
- **Unsorted Inputs:** Providing unsorted arrays may lead to incorrect matching results; ensure inputs are sorted by time.
- **Empty Arrays:** Passing empty arrays will return an empty list; ensure logic handles empty results gracefully.
- **Window Size:** Setting an inappropriately small `window` may result in zero matches, while an excessively large `window` may result in incorrect, non-meaningful matches.

### Fix Code Hint
```python
# Ensure inputs are sorted before matching
ref_sorted = np.sort(ref)
est_sorted = np.sort(est)
matching = mir_eval.util.match_events(ref_sorted, est_sorted, window=0.1)
```

## API Test: `python:mir_eval.util.merge_labeled_intervals`

### Signature
```python
def merge_labeled_intervals(x_intervals, x_labels, y_intervals, y_labels)
```
_Source: source/mir_eval/util.py:481_

_Source doc:_ Merge the time intervals of two sequences.

Parameters
----------
x_intervals : np.ndarray
    Array of interval times (seconds)
x_labels : list or None
    List of labels
y_intervals : np.ndarray
    Array of interval times (seconds)
y_labels : list or None
    List of labels

Returns
-------
new_intervals : np.ndarray
    New interval times of the merged sequences.
new_x_labels : list
    New labels for the sequence ``x``
new_y_labels : list
    New labels for the sequence ``y``

### Goal
Merges two sets of labeled time intervals into a single, unified timeline of intervals, propagating the original labels across the newly created segment boundaries.

### Parameters
- `x_intervals`: An $N \times 2$ NumPy array of start and end times in seconds for the first sequence.
- `x_labels`: A list of $N$ labels corresponding to the `x_intervals`.
- `y_intervals`: An $M \times 2$ NumPy array of start and end times in seconds for the second sequence.
- `y_labels`: A list of $M$ labels corresponding to the `y_intervals`.

### Input
- **Data Format:** Intervals must be provided as $N \times 2$ NumPy arrays where each row is `[start, end]`. Labels should be provided as lists of equal length to their respective interval arrays.
- **Preconditions:** Intervals are assumed to be disjoint. For consistent results, ensure input arrays are sorted by time before processing.

### Output
Returns a tuple containing:
- `new_intervals`: An $K \times 2$ NumPy array representing the union of all time boundaries from both input sequences.
- `new_x_labels`: A list of labels for the first sequence, expanded to match the new interval boundaries.
- `new_y_labels`: A list of labels for the second sequence, expanded to match the new interval boundaries.

### Valid Call Patterns
```python
# Example inferred from signature (not verified by test suite)
new_intervals, new_x_labels, new_y_labels = mir_eval.util.merge_labeled_intervals(
    x_intervals, x_labels, y_intervals, y_labels
)
```

### LLM Instruction Prompt
- When calling `mir_eval.util.merge_labeled_intervals`, ensure that `x_intervals` and `y_intervals` are NumPy arrays of shape `(n, 2)` and `(m, 2)` respectively.
- Always pass the corresponding label lists as the second and fourth arguments.
- Use this function when you need to align two different segmentation or annotation tracks to a common temporal grid.

### Prompt Snippet
```text
import mir_eval
# Assuming x_intervals, x_labels, y_intervals, y_labels are defined
intervals, x_labs, y_labs = mir_eval.util.merge_labeled_intervals(x_intervals, x_labels, y_intervals, y_labels)
```

### Common Failure Modes
- **Shape Mismatch:** Passing label lists that do not match the length of the corresponding interval arrays will result in index errors or inconsistent output.
- **Unsorted Intervals:** If input intervals are not sorted by time, the resulting merged intervals may not represent a valid chronological sequence.
- **Non-NumPy Inputs:** Passing standard Python lists instead of NumPy arrays for intervals may cause failures in internal array operations.

### Fix Code Hint
```python
import numpy as np
# Ensure intervals are sorted before merging
idx = np.argsort(x_intervals[:, 0])
x_intervals = x_intervals[idx]
x_labels = [x_labels[i] for i in idx]
```

## API Test: `python:mir_eval.util.midi_to_hz`

### Signature
```python
def midi_to_hz(midi)
```
_Source: source/mir_eval/util.py:930_

_Source doc:_ Convert MIDI numbers to Hz

Parameters
----------
midi : number or ndarray
    MIDI notes

Returns
-------
freqs : number or ndarray
    Frequency/frequencies in Hz corresponding to `midi`

### Goal
Converts MIDI note numbers into their corresponding fundamental frequencies in Hertz (Hz) to facilitate pitch-based evaluation and signal processing tasks.

### Parameters
- `midi`: A numeric value or a NumPy array of MIDI note numbers (e.g., 69 corresponds to A4, 440 Hz).

### Input
- **Data:** Accepts either a scalar number or a `numpy.ndarray` of arbitrary shape containing MIDI note values.
- **Preconditions:** The input should represent standard MIDI note numbers. No specific sorting is required, as the operation is applied element-wise.

### Output
Returns `number or ndarray` — The frequency or frequencies in Hz corresponding to the input MIDI values, matching the shape of the input.

### Valid Call Patterns
```python
import mir_eval
# Example using a scalar
freq = mir_eval.util.midi_to_hz(69)

# Example using a numpy array
import numpy as np
midi_notes = np.array([60, 62, 64])
freqs = mir_eval.util.midi_to_hz(midi_notes)
```

### LLM Instruction Prompt
- When calling `mir_eval.util.midi_to_hz`, ensure the input is a numeric type or a NumPy array.
- The function is element-wise; if processing large datasets, ensure the input is a NumPy array for efficient vectorized computation.
- Use this function when preparing ground-truth or estimated pitch data that is represented in MIDI format for comparison against frequency-based metrics.

### Prompt Snippet
```text
import mir_eval.util
# Convert MIDI note numbers to Hz
frequencies = mir_eval.util.midi_to_hz(midi_data)
```

### Common Failure Modes
- **Type Errors:** Passing non-numeric types (e.g., strings or lists of strings) will result in a `TypeError` during the mathematical conversion.
- **Input Shape:** While the function handles arrays, it does not perform validation on the range of MIDI values; extremely high or low MIDI numbers will produce mathematically valid but physically unrealistic frequencies.
- **Missing Dependencies:** Ensure `numpy` is installed and imported, as the function relies on it for array operations.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure input is a numpy array if it is a list
midi_data = np.array([60, 64, 67])
frequencies = mir_eval.util.midi_to_hz(midi_data)
```

## API Test: `python:mir_eval.util.sort_labeled_intervals`

### Signature
```python
def sort_labeled_intervals(intervals, labels=None)
```
_Source: source/mir_eval/util.py:171_

_Source doc:_ Sort intervals, and optionally, their corresponding labels
according to start time.

Parameters
----------
intervals : np.ndarray, shape=(n, 2)
    The input intervals
labels : list, optional
    Labels for each interval

Returns
-------
intervals_sorted or (intervals_sorted, labels_sorted)
    Labels are only returned if provided as input

### Goal
Sorts a set of time intervals (and their associated labels) in ascending order based on their start times to ensure chronological consistency for downstream MIR evaluation metrics.

### Parameters
- `intervals`: A NumPy array of shape `(n, 2)` where each row represents an `[onset, offset]` pair in seconds.
- `labels`, default `None`: An optional list of length `n` containing labels corresponding to each interval.

### Input
- **Data Format:** `intervals` must be a 2D NumPy array. `labels` should be a list or array-like structure of length `n`.
- **Preconditions:** The function assumes `intervals` are valid time-based segments. While the function performs the sorting, many `mir_eval` evaluation modules require inputs to be pre-sorted; this utility is the standard way to satisfy that requirement.

### Output
Returns a single `np.ndarray` of sorted intervals if `labels` is `None`, or a tuple `(intervals_sorted, labels_sorted)` if `labels` are provided.

### Valid Call Patterns
```python
# Sorting intervals only
sorted_intervals = mir_eval.util.sort_labeled_intervals(intervals)

# Sorting intervals and labels together
sorted_intervals, sorted_labels = mir_eval.util.sort_labeled_intervals(intervals, labels)
```

### LLM Instruction Prompt
- When evaluating MIR tasks, always ensure that reference and estimated intervals are sorted by start time using `mir_eval.util.sort_labeled_intervals` before passing them to `evaluate()` functions.
- If `labels` are provided, ensure the length of the `labels` list matches the number of rows in the `intervals` array.
- The function returns a tuple only when `labels` is provided; handle the return type dynamically based on the presence of the `labels` argument.

### Prompt Snippet
```text
# Ensure chronological order for evaluation
intervals, labels = mir_eval.util.sort_labeled_intervals(intervals, labels)
```

### Common Failure Modes
- **Shape Mismatch:** Passing a `labels` list that does not have the same length as the number of rows in `intervals` will result in an error during the sorting process.
- **Invalid Input Types:** Passing non-NumPy arrays for `intervals` may cause indexing errors.
- **Unsorted Inputs:** Failing to sort intervals before calling task-specific `evaluate()` functions can lead to incorrect metric calculations, as many algorithms assume chronological order.

### Fix Code Hint
```python
import numpy as np
import mir_eval

# Ensure intervals are sorted before evaluation
if labels is not None:
    intervals, labels = mir_eval.util.sort_labeled_intervals(intervals, labels)
else:
    intervals = mir_eval.util.sort_labeled_intervals(intervals)
```

## API Test: `python:mir_eval.util.validate_events`

### Signature
```python
def validate_events(events, max_time=30000.0)
```
_Source: source/mir_eval/util.py:763_

_Source doc:_ Check that a 1-d event location ndarray is well-formed, and raises
errors if not.

Parameters
----------
events : np.ndarray, shape=(n,)
    Array of event times
max_time : float
    If an event is found above this time, a ValueError will be raised.
    (Default value = 30000.)

### Goal
Validates that a 1D NumPy array of event timestamps is well-formed and within a specified temporal boundary for use in MIR evaluation tasks.

### Parameters
- `events`: A 1D `np.ndarray` containing event timestamps in seconds.
- `max_time`, default `30000.0`: A float representing the maximum allowable timestamp; events exceeding this value will trigger a `ValueError`.

### Input
- **Data Format:** A 1D `np.ndarray` of floats.
- **Preconditions:** The array must be 1-dimensional. While not explicitly enforced by this function, MIR evaluation workflows typically require event arrays to be sorted by time.

### Output
Returns `None` if the input array is valid. If the input is malformed (e.g., not a 1D array) or contains values exceeding `max_time`, it raises a `ValueError`.

### Valid Call Patterns
```python
import numpy as np
import mir_eval

# Example: Validating a set of onset timestamps
events = np.array([0.1, 0.5, 1.2, 2.5])
mir_eval.util.validate_events(events, max_time=10.0)
```

### LLM Instruction Prompt
- Use `mir_eval.util.validate_events` to verify event arrays before passing them to task-specific evaluation functions (e.g., `mir_eval.beat.evaluate`).
- Ensure the input `events` is a 1D `np.ndarray`.
- If the data is expected to be within a specific duration, set `max_time` accordingly to catch outliers.

### Prompt Snippet
```text
# Validate event array before evaluation
mir_eval.util.validate_events(estimated_events, max_time=track_duration)
```

### Common Failure Modes
- **Dimensionality Mismatch:** Passing a multi-dimensional array (e.g., an $N \times 2$ interval array) instead of a 1D event array will cause a validation error.
- **Out-of-Bounds Events:** Providing timestamps that exceed the `max_time` threshold (default 30,000 seconds) will raise a `ValueError`.
- **Non-Array Inputs:** Passing lists or other non-NumPy types may cause failures in downstream processing if not converted to `np.ndarray` first.

### Fix Code Hint
```python
# Ensure input is a 1D numpy array before validation
events = np.asanyarray(events)
if events.ndim != 1:
    events = events.flatten()
mir_eval.util.validate_events(events)
```

## API Test: `python:mir_eval.util.validate_frequencies`

### Signature
```python
def validate_frequencies(frequencies, max_freq, min_freq, allow_negatives=False)
```
_Source: source/mir_eval/util.py:794_

_Source doc:_ Check that a 1-d frequency ndarray is well-formed, and raises
errors if not.

Parameters
----------
frequencies : np.ndarray, shape=(n,)
    Array of frequency values
max_freq : float
    If a frequency is found above this pitch, a ValueError will be raised.
    (Default value = 5000.)
min_freq : float
    If a frequency is found below this pitch, a ValueError will be raised.
    (Default value = 20.)
allow_negatives : bool
    Whether or not to allow negative frequency values.

### Goal
Validates that a 1D NumPy array of frequency values (in Hz) conforms to specified range constraints to ensure data integrity before MIR metric computation.

### Parameters
- `frequencies`: A 1D `np.ndarray` containing frequency values in Hertz.
- `max_freq`: A float representing the upper bound for valid frequencies; values exceeding this will trigger a `ValueError`.
- `min_freq`: A float representing the lower bound for valid frequencies; values below this will trigger a `ValueError`.
- `allow_negatives`, default `False`: A boolean flag; if `False`, any negative value in the input array will trigger a `ValueError`.

### Input
- **Data Format:** A 1D `np.ndarray` of floats.
- **Preconditions:** The input must be a 1D array. Frequencies are expected to be in Hertz.

### Output
Returns `None` if the validation passes. If the input array violates the specified constraints, the function raises a `ValueError`.

### Valid Call Patterns
```python
import numpy as np
import mir_eval

# Validate a standard frequency array with default bounds
freqs = np.array([440.0, 880.0, 220.0])
mir_eval.util.validate_frequencies(freqs, max_freq=5000.0, min_freq=20.0)

# Validate allowing negative values (e.g., for specific signal processing representations)
freqs_with_neg = np.array([440.0, -1.0, 220.0])
mir_eval.util.validate_frequencies(freqs_with_neg, 5000.0, 20.0, allow_negatives=True)
```

### LLM Instruction Prompt
- When calling `mir_eval.util.validate_frequencies`, ensure the `frequencies` argument is a 1D NumPy array.
- Always specify `max_freq` and `min_freq` explicitly if the default values (5000.0 and 20.0) are not appropriate for the specific audio domain (e.g., sub-bass or ultrasonic analysis).
- Use this function as a pre-check before passing frequency data into `mir_eval` task modules like `melody` or `multipitch`.

### Prompt Snippet
```text
# Validate frequency data before processing
mir_eval.util.validate_frequencies(frequencies, max_freq=8000.0, min_freq=50.0)
```

### Common Failure Modes
- **Shape Mismatch:** Passing a multi-dimensional array (e.g., `(n, m)`) instead of a 1D array will cause validation to fail or raise an error.
- **Out-of-Bounds:** Providing frequencies outside the `[min_freq, max_freq]` range will raise a `ValueError`.
- **Negative Values:** If `allow_negatives` is `False` (default), the presence of any negative frequency (often resulting from signal processing artifacts or uninitialized buffers) will raise a `ValueError`.

### Fix Code Hint
```python
# Ensure input is 1D and within expected range
frequencies = np.atleast_1d(frequencies)
mir_eval.util.validate_frequencies(frequencies, max_freq=5000.0, min_freq=20.0)
```

## API Test: `python:mir_eval.util.validate_intervals`

### Signature
```python
def validate_intervals(intervals)
```
_Source: source/mir_eval/util.py:738_

_Source doc:_ Check that an (n, 2) interval ndarray is well-formed, and raises errors
if not.

Parameters
----------
intervals : np.ndarray, shape=(n, 2)
    Array of interval start/end locations.

### Goal
Validates that a given NumPy array of interval start/end locations conforms to the expected structure required for MIR evaluation tasks.

### Parameters
- `intervals`: A NumPy array of shape `(n, 2)` where each row represents an interval defined by `[start, end]` timestamps in seconds.

### Input
- **Data Format:** A 2D `np.ndarray` of floats.
- **Preconditions:** The array must have exactly two columns. While this function checks for structural well-formedness, many downstream `mir_eval` functions further require that intervals are sorted by start time and that start times are less than or equal to end times.

### Output
Returns `None` if the input is valid. If the input is malformed (e.g., incorrect shape or dimensions), it raises an error.

### Valid Call Patterns
```python
import numpy as np
import mir_eval

# Example: Validating a 2x2 interval array
intervals = np.array([[0.0, 1.0], [1.0, 2.0]])
mir_eval.util.validate_intervals(intervals)
```

### LLM Instruction Prompt
- Use `mir_eval.util.validate_intervals` to verify interval data before passing it to task-specific evaluation functions like `mir_eval.segment.evaluate` or `mir_eval.chord.evaluate`.
- Ensure the input is a NumPy array with shape `(n, 2)`.
- Do not assume this function performs semantic checks (like checking for overlapping intervals or negative durations); it is primarily for structural validation.

### Prompt Snippet
```text
# Ensure intervals are valid before evaluation
mir_eval.util.validate_intervals(intervals)
scores = mir_eval.segment.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
```

### Common Failure Modes
- **Shape Mismatch:** Passing an array that is not `(n, 2)` (e.g., a 1D array of events or a 3D array) will trigger an error.
- **Data Type:** Passing a list instead of a `np.ndarray` may cause validation failures depending on the specific implementation constraints.
- **Missing Pre-processing:** This function does not check if `start > end` or if intervals are sorted; ensure data is pre-processed using `mir_eval.util.adjust_intervals` or manual sorting if required by the specific task module.

### Fix Code Hint
```python
import numpy as np
from mir_eval.util import validate_intervals

# Ensure input is a numpy array and has the correct shape
intervals = np.array(intervals)
if intervals.ndim != 2 or intervals.shape[1] != 2:
    intervals = intervals.reshape(-1, 2)
validate_intervals(intervals)
```

