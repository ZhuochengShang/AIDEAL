# Recorded author system prompt

You write LLM-facing API documentation in an exact markdown template.
You ground every fact in the provided API facts and context. You NEVER invent
parameters, types, return values, or APIs that are not given. If something is
unknown, say so rather than guessing.

Role: An expert in reproducible music-information-retrieval evaluation and scientific Python API usage.
Project: mir_eval (Python) - A scientific Python library of evaluation metrics, I/O helpers, displays, and sonification utilities for music and audio information retrieval.
Domain: Audio and music signal evaluation. This label is query provenance, not a manual classification: the repository was returned by both the saved "audio processing" and "signal processing" GitHub sweeps.
Target users: music-information-retrieval researchers; audio and signal-processing engineers; coding agents implementing reproducible metric evaluations
Use cases: Score beats, onsets, melody, multipitch, chords, keys, and tempo.; Evaluate segment, hierarchy, transcription, alignment, and separation outputs.; Load repository-format annotations and produce deterministic summaries.
Constraints: Use only checked-in test fixtures or deterministic in-memory arrays.; Keep display tests headless and prohibit network/audio-device access.; Use every name in the frozen 125-name canonical manifest without sampling; selection is structural filtering and same-name maximum arity, not a proof of arbitrary semantic equivalence.

# Recorded author user prompt

Document the Python function `python:mir_eval.alignment.absolute_error` of mir_eval.

Authoritative API facts (JSON — do not contradict; do not add parameters or
types that are not listed here):
```json
{
  "name": "python:mir_eval.alignment.absolute_error",
  "signature": "def absolute_error(reference_timestamps, estimated_timestamps)",
  "params": [
    {
      "name": "reference_timestamps",
      "type": "",
      "default": null,
      "required": true,
      "kind": "positional_or_keyword"
    },
    {
      "name": "estimated_timestamps",
      "type": "",
      "default": null,
      "required": true,
      "kind": "positional_or_keyword"
    }
  ],
  "returns": null,
  "source_doc": "Compute the absolute deviations between estimated and reference timestamps,\nand then returns the median and average over all events\n\nExamples\n--------\n>>> reference_timestamps = mir_eval.io.load_events('reference.txt')\n>>> estimated_timestamps = mir_eval.io.load_events('estimated.txt')\n>>> mae, aae = mir_eval.align.absolute_error(reference_onsets, estimated_timestamps)\n\nParameters\n----------\nreference_timestamps : np.ndarray\n    reference timestamps, in seconds\nestimated_timestamps : np.ndarray\n    estimated timestamps, in seconds\n\nReturns\n-------\nmae : float\n    Median absolute error\naae: float\n    Average absolute error",
  "overloads": [],
  "api_id": "python:mir_eval.alignment.absolute_error",
  "display_name": "absolute_error",
  "identity_version": "language_qualified_api_v1",
  "parameter_count": 2,
  "parameter_count_status": "declared",
  "exposure_ids": [
    "python:mir_eval.alignment.absolute_error"
  ],
  "preferred_public_path": "mir_eval.alignment.absolute_error",
  "public_access_paths": [
    "mir_eval.alignment.absolute_error"
  ],
  "qualified_name": "mir_eval.alignment.absolute_error",
  "source": {
    "file": "source/mir_eval/alignment.py",
    "line": 115,
    "site_id": "Python:mir_eval:mir_eval/alignment.py:4886:function:absolute_error"
  },
  "definition_sites": [
    {
      "signature": "def absolute_error(reference_timestamps, estimated_timestamps)",
      "qualified_name": "mir_eval.alignment.absolute_error",
      "source": {
        "file": "source/mir_eval/alignment.py",
        "line": 115,
        "site_id": "Python:mir_eval:mir_eval/alignment.py:4886:function:absolute_error"
      }
    }
  ],
  "definition_site_count": 1,
  "definition_sites_truncated": false,
  "overloads_total": 0,
  "overloads_truncated": false
}
```

Project context distilled from the original README (grounding — may say none exists):
===== Original documentation part 1/2 =====
### 1. Project purpose
`mir_eval` is a scientific Python library designed for the reproducible evaluation of Music Information Retrieval (MIR) systems. It provides standardized implementations of metrics for common MIR tasks, I/O utilities for loading standard annotation formats, and visualization/sonification tools to assist in qualitative analysis.

### 2. Main workflows
*   **Annotation Loading:** Use `mir_eval.io` to load ground-truth and estimated data from text files into NumPy arrays.
*   **Metric Computation:** Pass loaded arrays to task-specific modules (e.g., `mir_eval.beat`, `mir_eval.chord`, `mir_eval.melody`) to compute performance scores.
*   **Evaluation Aggregation:** Use the `evaluate()` function provided in most modules to compute a comprehensive suite of metrics for a given task.
*   **Visualization:** Use `mir_eval.display` to generate plots (e.g., piano rolls, pitch contours, segmentations) using Matplotlib.
*   **Sonification:** Use `mir_eval.sonify` to create audio representations of annotations for "evaluation by ear."

### 3. Important APIs and usage patterns
*   **Task Modules:** Each task (e.g., `beat`, `chord`, `melody`, `onset`, `segment`, `hierarchy`, `multipitch`, `pattern`, `alignment`, `key`, `separation`) contains a `validate()` function to check input formats and an `evaluate()` function for batch metric calculation.
*   **Data Structures:**
    *   **Events:** 1D NumPy arrays of timestamps (seconds).
    *   **Intervals:** $N \times 2$ NumPy arrays (start, end).
    *   **Labeled Intervals:** $N \times 2$ intervals + list of $N$ labels.
    *   **Ragged Time Series:** Used for multi-pitch/multi-source data where the number of values per timestamp varies.
*   **Chord Encoding:** The `mir_eval.chord` module provides complex utilities to parse, encode, and compare chord labels using sub-alphabets (e.g., `majmin`, `triads`, `sevenths`).

### 4. Inputs and file formats
*   **Delimited Text:** `mir_eval.io.load_delimited` is the base loader.
*   **Specific Loaders:**
    *   `load_events`: Single column of floats.
    *   `load_labeled_events`: Time (float) + Label (str).
    *   `load_intervals`: Start (float) + End (float).
    *   `load_labeled_intervals`: Start (float) + End (float) + Label (str).
    *   `load_ragged_time_series`: Time (float) + variable number of values.
    *   `load_patterns`: MIREX 2013 format (list of lists of tuples).

### 5. Outputs and generated artifacts
*   **Metric Scores:** Most `evaluate()` functions return a dictionary mapping metric names (strings) to scores (floats).
*   **Visualizations:** Matplotlib `Axes` objects.
*   **Audio:** NumPy arrays representing synthesized signals (e.g., click tracks, piano rolls).

### 6. Configuration and environment assumptions
*   **Dependencies:** Requires `numpy`, `scipy`, and `matplotlib`.
*   **Conventions:** Time is always in seconds. Frequencies are in Hz (or cents for melody). Chord labels follow standard syntax (e.g., `C:maj`).

### 7. Commands and examples

**Beat Evaluation:**
```python
>>> reference_beats = mir_eval.io.load_events('reference.txt')
>>> reference_beats = mir_eval.beat.trim_beats(reference_beats)
>>> estimated_beats = mir_eval.io.load_events('estimated.txt')
>>> estimated_beats = mir_eval.beat.trim_beats(estimated_beats)
>>> scores = mir_eval.beat.evaluate(reference_beats, estimated_beats)
```

**Chord Evaluation:**
```python
>>> (ref_intervals, ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals, est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> scores = mir_eval.chord.evaluate(ref_intervals, ref_labels,
...                                  est_intervals, est_labels)
```

**Melody Evaluation:**
```python
>>> ref_time, ref_freq = mir_eval.io.load_time_series('ref.txt')
>>> est_time, est_freq = mir_eval.io.load_time_series('est.txt')
>>> scores = mir_eval.melody.evaluate(ref_time, ref_freq,
...                                   est_time, est_freq)
```

**Segmentation Evaluation:**
```python
>>> (ref_intervals, ref_labels) = mir_eval.io.load_labeled_intervals('ref.lab')
>>> (est_intervals, est_labels) = mir_eval.io.load_labeled_intervals('est.lab')
>>> scores = mir_eval.segment.evaluate(ref_intervals, ref_labels,
...                                    est_intervals, est_labels)
```

### 8. Constraints, preconditions, compatibility rules
*   **Preconditions:** For most metrics, reference and estimated arrays must be sorted by time.
*   **Interval Adjustment:** Use `mir_eval.util.adjust_intervals` to ensure estimated intervals span the same duration as reference intervals before evaluation.
*   **Deprecation:** `mir_eval.io.load_wav` is deprecated; use `soundfile` instead. `mir_eval.separation` is deprecated; use `sigsep-museval`.
*   **Chord Labels:** Invalid labels raise `InvalidChordException`.

### 9. Facts to preserve in the final README
*   `mir_eval` is the standard for reproducible MIR research.
*   Metrics are based on established literature (e.g., MIREX, BSS_EVAL).
*   The library supports both flat and hierarchical structure evaluation.
*   All time-based inputs must be in seconds.

### 10. Missing or weak documentation
*   The `mir_eval.sonify.pitch_contour` documentation is truncated in the provided source.
*   The `mir_eval.display` module lacks comprehensive examples for all plot types.
*   The distinction between "transitive" and "reduced" modes in `hierarchy` metrics could be explained with more theoretical depth.

===== Original documentation part 2/2 =====
### 1. Project purpose
`mir_eval` is a scientific Python library designed to provide transparent, reproducible, and standardized implementations of common evaluation metrics for Music Information Retrieval (MIR) and audio signal processing tasks. It serves as a centralized repository for metrics used in research, ensuring that evaluation procedures (such as those used in MIREX) are consistent across different studies.

### 2. Main workflows
*   **Metric Evaluation:** Comparing reference (ground truth) annotations against estimated outputs using task-specific modules (e.g., `tempo`, `transcription`, `transcription_velocity`).
*   **Data Preprocessing:** Normalizing, validating, and transforming annotation formats (e.g., converting intervals to samples, adjusting event times to specific ranges, or converting frequency to MIDI).
*   **Sonification:** Synthesizing audio from symbolic or feature-based representations (e.g., pitch contours, chromagrams, or chord labels) for verification or debugging.
*   **Matching:** Computing optimal correspondences between reference and estimated events (onsets, offsets, notes) using bipartite graph matching.

### 3. Important APIs and usage patterns
*   **Task Modules:** Each task (e.g., `mir_eval.tempo`, `mir_eval.transcription`) provides an `evaluate()` function that acts as a high-level entry point, returning a dictionary of all relevant metrics.
*   **Validation:** Every module includes `validate()` functions to ensure input arrays (intervals, pitches, velocities) conform to expected shapes and constraints before computation.
*   **Matching Logic:** The `transcription` and `transcription_velocity` modules use `match_notes()` to establish correspondences based on onset, offset, pitch, and (optionally) velocity tolerances before calculating precision/recall.
*   **Utility Functions:** The `mir_eval.util` module provides cross-task helpers for label indexing, interval manipulation, and mathematical conversions (e.g., `hz_to_midi`).

### 4. Inputs and file formats
*   **Intervals:** `np.ndarray` of shape `(n, 2)` representing `[onset, offset]` pairs.
*   **Pitches:** `np.ndarray` of shape `(n,)` representing fundamental frequency (F0) in Hertz.
*   **Velocities:** `np.ndarray` of shape `(n,)` representing MIDI velocities in the range `[0, 127]`.
*   **Tempi:** `np.ndarray` of length 2 (ascending order) representing BPM.
*   **Chromagrams:** `np.ndarray` of shape `(12, n_times)`.

### 5. Outputs and generated artifacts
*   **Metrics:** Scalar values (floats) for Precision, Recall, F-measure, and Average Overlap Ratio.
*   **Dictionaries:** The `evaluate()` functions return a `dict` mapping metric names to their computed values.
*   **Synthesized Audio:** `np.ndarray` representing time-domain audio signals generated from symbolic inputs.

### 6. Configuration and environment assumptions
*   **Dependencies:** Requires `numpy`, `scipy`, and `decorator`.
*   **Headless Operation:** The library is designed for non-interactive, headless evaluation environments.
*   **Deterministic Matching:** Uses bipartite graph matching for note-tracking, which differs from the greedy matching used in some legacy MIREX scripts.

### 7. Commands and examples

**Transcription Evaluation:**
```python
ref_intervals, ref_pitches = mir_eval.io.load_valued_intervals('reference.txt')
est_intervals, est_pitches = mir_eval.io.load_valued_intervals('estimated.txt')
scores = mir_eval.transcription.evaluate(ref_intervals, ref_pitches,
    est_intervals, est_pitches)
```

**Tempo Detection:**
```python
# Example of computing tempo detection accuracy
p_score, one_correct, both_correct = mir_eval.tempo.detection(
    reference_tempi, reference_weight, estimated_tempi)
```

**File Intersection Utility:**
```python
flist1 = ['/a/b/abc.lab', '/c/d/123.lab', '/e/f/xyz.lab']
flist2 = ['/g/h/xyz.npy', '/i/j/123.txt', '/k/l/456.lab']
sublist1, sublist2 = mir_eval.util.intersect_files(flist1, flist2)
```

### 8. Constraints, preconditions, compatibility rules, and type-selection rules
*   **Transcription Matching:** `match_notes()` requires `ref_intervals` and `est_intervals` to be validated. The `strict` parameter toggles between `<` (strict) and `<=` (default) for threshold comparisons.
*   **Velocity Normalization:** In `transcription_velocity`, reference velocities are rescaled to `[0, 1]`. Estimated velocities are rescaled via linear regression to minimize L2 distance to reference velocities before thresholding.
*   **Tempo:** Reference tempi must be positive and provided in ascending order. `reference_weight` must be a float in `[0, 1]`.
*   **Intervals:** Intervals are assumed to be disjoint in many utility functions. `intervals_to_samples` rounds intervals down to the nearest multiple of `sample_size`.

### 9. Facts to preserve in the final README
*   **Citation:** Users must cite: Raffel, C., McFee, B., Humphrey, E. J., Salamon, J., Nieto, O., Liang, D., & Ellis, D. P. W. (2014). "mir_eval: A Transparent Implementation of Common MIR Metrics".
*   **MIREX Differences:** Note that `mir_eval` uses bipartite matching and 4-decimal point rounding, which may result in slightly different scores compared to legacy MIREX scripts.
*   **Instrument Agnostic:** The transcription module is instrument-agnostic; all estimated notes are compared against all reference notes.

### 10. Missing or weak documentation
*   The documentation for `mir_eval.io` is referenced in docstrings (e.g., `load_valued_intervals`) but is not explicitly detailed in the provided text.
*   Specific behavior for empty input arrays in `evaluate()` functions is not explicitly defined, though `validate()` functions are present.
*   The `sonify` module parameters (e.g., `function=<ufunc 'sin'>`) lack detailed examples of custom synthesis functions.

Real usage from the project's existing test suite (these compile and pass — base
the Valid Call Patterns and realistic Common Failure Modes on them; may be empty):
```Python
(no existing test found for this API)
```

Verbatim code example(s) from the ORIGINAL project README that call `python:mir_eval.alignment.absolute_error`
(the project's real, documented usage — may be empty):
```Python
===== Shared original document: pinned-root-readme:README.rst =====
.. image:: https://anaconda.org/conda-forge/mir_eval/badges/version.svg 
    :target: https://anaconda.org/conda-forge/mir_eval

.. image:: https://img.shields.io/pypi/v/mir_eval.svg
    :target: https://pypi.python.org/pypi/mir_eval

.. image:: https://github.com/mir-evaluation/mir_eval/actions/workflows/test.yml/badge.svg
    :target: https://github.com/mir-evaluation/mir_eval/actions/workflows/test.yml

.. image:: https://codecov.io/gh/mir-evaluation/mir_eval/graph/badge.svg?token=OzRL3aW7TX 
    :target: https://codecov.io/gh/mir-evaluation/mir_eval

.. image:: https://img.shields.io/pypi/l/mir_eval.svg
    :target: https://github.com/mir-evaluation/mir_eval/blob/main/LICENSE.txt


mir_eval
========

Python library for computing common heuristic accuracy scores for various music/audio information retrieval/signal processing tasks.

Documentation, including installation and usage information: https://mir-evaluation.github.io/mir_eval/

Dependencies:

* `Scipy/Numpy <http://www.scipy.org/>`_
* `decorator <https://github.com/micheles/decorator>`_

If you use mir_eval in a research project, please cite the following paper:

Colin Raffel, Brian McFee, Eric J. Humphrey, Justin Salamon, Oriol Nieto, Dawen Liang, and Daniel P. W. Ellis, "`mir_eval: A Transparent Implementation of Common MIR Metrics <http://colinraffel.com/publications/ismir2014mir_eval.pdf>`_", Proceedings of the 15th International Conference on Music Information Retrieval, 2014.




===== https://mir-eval.readthedocs.io/stable/api/alignment.html#mir_eval.alignment.absolute_error =====
mir_eval.alignment.absolute_error(reference_timestamps, estimated_timestamps)

Compute the absolute deviations between estimated and reference timestamps, and then returns the median and average over all events

Parameters:

reference_timestampsnp.ndarray

reference timestamps, in seconds

estimated_timestampsnp.ndarray

estimated timestamps, in seconds

Returns:

maefloat

Median absolute error

aae: float

Average absolute error

Examples

>>> reference_timestamps = mir_eval.io.load_events('reference.txt')
>>> estimated_timestamps = mir_eval.io.load_events('estimated.txt')
>>> mae, aae = mir_eval.align.absolute_error(reference_onsets, estimated_timestamps)

```

GROUND THE CALL FORM by combining the sources above, in this priority order — and
NEVER invent a call shape that appears in none of them:
1. If a test-suite example is shown, its call form is authoritative (it compiles
   and passes) — reproduce that exact receiver and argument order.
2. Otherwise use the original-README example's call form.
3. If BOTH are shown, reproduce a real form verbatim (either compiles); when they
   differ, the instance/implicit form `value.python:mir_eval.alignment.absolute_error(...)` is the most portable.
4. If NEITHER is shown, derive the call from the Signature/API facts and say in the
   entry that the example is inferred from the signature (not verified).
Preserve the receiver/qualifier EXACTLY as written — if it is
`value.python:mir_eval.alignment.absolute_error(...)` or `Object.python:mir_eval.alignment.absolute_error(...)`, keep it; do NOT collapse it to
a bare `python:mir_eval.alignment.absolute_error(...)`, which usually will not compile.

Fill in the template below. Replace every TODO. Keep the Signature block and the
pre-filled Parameters types and Output type exactly as given; add the meaning of
each parameter, the Input (data/formats/preconditions), and what the Output
represents. Tailor Goal, examples, and Common Failure Modes to the target users
and use cases above, honoring the project constraints.

If the context states PRECONDITIONS or compatibility rules (conditions under which
the call is valid, or inputs that must be made compatible or converted/prepared
first with another operation) or TYPE-PARAMETER selection rules (which generic /
type argument to use for a given input type), you MUST state them explicitly under
Input and Common Failure Modes. These rules are what make generated code correct —
do not drop them. Output ONLY the filled template, nothing else.

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
TODO: one sentence describing what `python:mir_eval.alignment.absolute_error` does, in the project's domain terms.

### Parameters
- `reference_timestamps`: TODO — what this argument means / expected values.
- `estimated_timestamps`: TODO — what this argument means / expected values.

### Input
TODO: the data, file formats, and preconditions the caller must provide.

### Output
Returns `unspecified` — TODO: what the value represents and its format.

### Valid Call Patterns
```python
TODO
```

### LLM Instruction Prompt
- TODO: rules an LLM must follow when calling `python:mir_eval.alignment.absolute_error`.

### Prompt Snippet
```text
TODO
```

### Common Failure Modes
- TODO

### Fix Code Hint
```python
TODO
```

