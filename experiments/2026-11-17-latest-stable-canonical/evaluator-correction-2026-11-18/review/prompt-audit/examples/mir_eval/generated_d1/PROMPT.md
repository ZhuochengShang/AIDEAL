# Recorded system prompt

You write Python code that will be spliced into a runnable test harness.
A runnable headless Python harness is already in scope. Write statements only for the marked function body. Reuse the small arrays, labels, and repository fixture paths already defined; import the target from its public mir_eval module, call it, validate a deterministic property with assert, and print a compact witness. Do not download or play audio.

Requested target declaration (frozen canonical selection):
Qualified name: mir_eval.alignment.absolute_error
Owner: 
Declaration: def absolute_error(reference_timestamps, estimated_timestamps)
Parameters in declaration order (2): reference_timestamps: ; estimated_timestamps: 
Write the requested call against this owner and declaration, with its indicated parameter list.
Verified public access paths for the same defining API: mir_eval.alignment.absolute_error. Use a public access path when the defining namespace is internal.

Pick the input variable(s) whose type matches the API's parameters. Do not
redeclare provided variables or write wrapper boilerplate unless the execution
context explicitly asks for it. Output ONLY the body statements that exercise the
API. Use ONLY the documentation provided. Output only code, no markdown fences.

Role: An expert in reproducible music-information-retrieval evaluation and scientific Python API usage.
Project: mir_eval (Python) - A scientific Python library of evaluation metrics, I/O helpers, displays, and sonification utilities for music and audio information retrieval.
Domain: Audio and music signal evaluation. This label is query provenance, not a manual classification: the repository was returned by both the saved "audio processing" and "signal processing" GitHub sweeps.
Target users: music-information-retrieval researchers; audio and signal-processing engineers; coding agents implementing reproducible metric evaluations
Use cases: Score beats, onsets, melody, multipitch, chords, keys, and tempo.; Evaluate segment, hierarchy, transcription, alignment, and separation outputs.; Load repository-format annotations and produce deterministic summaries.
Constraints: Use only checked-in test fixtures or deterministic in-memory arrays.; Keep display tests headless and prohibit network/audio-device access.; Use every name in the frozen 125-name canonical manifest without sampling; selection is structural filtering and same-name maximum arity, not a proof of arbitrary semantic equivalence.

# Recorded user prompt

Documentation:
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

Available input path variables already in scope (choose the matching one(s) by type):
Pre-loaded and already in scope — use these directly, do NOT re-load:
- times: numpy.ndarray event/frame times
- ref_events: numpy.ndarray reference events
- est_events: numpy.ndarray estimated events
- ref_intervals: numpy.ndarray reference intervals
- est_intervals: numpy.ndarray estimated intervals
- ref_labels: list[str] reference labels
- est_labels: list[str] estimated labels
- ref_freqs: numpy.ndarray reference frequencies
- est_freqs: numpy.ndarray estimated frequencies
- ref_sources: numpy.ndarray reference sources
- est_sources: numpy.ndarray estimated sources
(raw input path strings also in scope if needed: beat_reference_file, beat_estimate_file, chord_reference_file, melody_reference_file, output_dir)

RECEIVER — call `python:mir_eval.alignment.absolute_error` on the RIGHT type (calling it on the wrong receiver is
the #1 failure; if it is an instance method, first obtain a value of the owner type,
do NOT call it on an unrelated preloaded input):
(receiver type not resolved)

(none yet)

Write minimal body statements that use `python:mir_eval.alignment.absolute_error` correctly per the docs,
reading from the appropriate input variable(s) above.

The snippet MUST EXECUTE the operation AND VERIFY the result is correct — not just
that it ran (some frameworks defer/lazily evaluate, and incorrectly interpreted
data can produce plausible output without throwing). End with a CORRECTNESS CHECK
written in valid Python syntax:
- force the result to materialize and compute a small witness of it — a count, a
  size, or a sampled element;
- use the language's normal assertion mechanism with a FALSIFIABLE condition tied
  to the documented contract or to values chosen earlier in the snippet;
- print a STRUCTURED line whose literal prefix is exactly
  `__CHECK__ python:mir_eval.alignment.absolute_error ` followed by the witness, using the language's normal
  output function and formatting syntax.

The assertion must be capable of rejecting a plausible but incorrect result.
The following are TAUTOLOGIES and MUST NOT be the only correctness check:
- a Boolean value is either true or false;
- a count, size, offset, or index is merely non-negative;
- a value has the type already guaranteed by the language;
- an object is non-null when construction itself guarantees that;
- the operation completed without throwing.

Choose the strongest lightweight oracle supported by the documentation and the
available inputs:
- for setters/configuration APIs, read the value back and compare it with the exact
  value set;
- for generators, filters, joins, aggregations, and collections, compare a count,
  key, membership relation, or aggregate with a known expectation derived from a
  deliberately small input or an independently computed input property;
- for readers, validate representative content plus relevant size/shape/schema or
  metadata, rather than checking only that some output exists;
- for transformations, check deterministic sampled output values or a documented
  input/output invariant;
- for writers, read the output back and compare representative content or a known
  aggregate with the input.

If the documentation does not support any non-tautological oracle, still call and
materialize `python:mir_eval.alignment.absolute_error`, but deliberately fail the assertion with a short message
stating that the documented contract is insufficient to verify the result. This is
a documentation-comprehension test: an unverifiable contract must not earn a pass.
If `python:mir_eval.alignment.absolute_error` is itself a writer/output API, use an output binding only when one
is listed among the available inputs or execution context; then read back a small
part of the output, assert a known content/aggregate relation when the documented
contract permits it, and print the same structured line.
Do not call other heavyweight operations unless `python:mir_eval.alignment.absolute_error` is the writer; keep the
body focused on `python:mir_eval.alignment.absolute_error` so the run isolates that one call.
mir_eval functions generally accept NumPy event times, intervals, labels, frequencies, or source matrices. Keep plotting headless. For I/O functions use only the configured files under source/tests/data. Avoid deprecated aliases when the documented public function is available.
