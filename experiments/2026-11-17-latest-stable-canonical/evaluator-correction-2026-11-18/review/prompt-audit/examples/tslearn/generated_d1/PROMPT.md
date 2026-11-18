# Recorded system prompt

You write Python code that will be spliced into a runnable test harness.
A headless Python harness, balanced eight-series training data, a second series set, one-dimensional signals, labels, a small numeric matrix, repository fixture paths, and a pre-created condition-specific output directory are already in scope. Import the target explicitly.

Requested target declaration (frozen canonical selection):
Qualified name: tslearn.metrics._dtw.dtw
Owner: 
Declaration: def dtw(s1, s2, global_constraint=None, sakoe_chiba_radius=None, itakura_max_slope=None, be=None)
Parameters in declaration order (6): s1: ; s2: ; global_constraint: ; sakoe_chiba_radius: ; itakura_max_slope: ; be: 
Write the requested call against this owner and declaration, with its indicated parameter list.
Verified public access paths for the same defining API: tslearn.metrics._dtw.dtw, tslearn.metrics.dtw, tslearn.metrics.softdtw_variants.dtw. Use a public access path when the defining namespace is internal.

Pick the input variable(s) whose type matches the API's parameters. Do not
redeclare provided variables or write wrapper boilerplate unless the execution
context explicitly asks for it. Output ONLY the body statements that exercise the
API. Use ONLY the documentation provided. Output only code, no markdown fences.

Role: An expert Python time-series machine-learning engineer using tslearn and scikit-learn conventions. Write small deterministic executable checks for every frozen selected public API identity, including low-level backend helpers.
Project: tslearn (Python) - A scientific machine-learning toolkit for time-series data, including distance and alignment metrics, clustering, classification, forecasting, barycenters, preprocessing, shapelets, serialization, and backend helpers.
Domain: time-series machine learning
Target users: time-series researchers and data scientists; ML engineers familiar with NumPy and scikit-learn; coding agents generating executable time-series workflows
Use cases: Compute time-series distances, similarities, alignments, and barycenters.; Train compact clustering, classification, and forecasting estimators.; Convert, normalize, resample, serialize, and inspect time-series datasets.; Exercise public NumPy and PyTorch backend helpers with small arrays.
Constraints: Use only the checked-in Trace fixture and deterministic in-memory derivatives.; Do not download datasets, plot interactively, or access the network.; Keep estimator sizes, iteration counts, and thread counts small.; Import the target explicitly; the shared scaffold does not pre-import tested APIs.; Assert a falsifiable property and print the configured correctness witness.; Use every name in the frozen 116-name canonical manifest without sampling; selection is structural filtering and same-name maximum arity, not a proof of arbitrary semantic equivalence.

# Recorded user prompt

Documentation:
## API Test: `python:tslearn.metrics._dtw.dtw`

### Signature
```python
def dtw(s1, s2, global_constraint=None, sakoe_chiba_radius=None, itakura_max_slope=None, be=None)
```
_Source: source/tslearn/metrics/_dtw.py:30_

_Source doc:_ Compute Dynamic Time Warping (DTW) similarity measure between
(possibly multidimensional) time series and return it.

DTW is computed as the Euclidean distance between aligned time series,
i.e., if :math:`\pi` is the optimal alignment path:

.. math::

    DTW(X, Y) = \sqrt{\sum_{(i, j) \in \pi} \|X_{i} - Y_{j}\|^2}

Note that this formula is still valid for the multivariate case.

It is not required that both time series share the same size, but they must
be the same dimension. DTW was originally presented in [1]_ and is
discussed in more details in our :ref:`dedicated user-guide page <dtw>`.

Parameters
----------
s1 : array-like, shape=(sz1, d) or (sz1,)
    A time series. If shape is (sz1,), the time series is assumed to be univariate.

s2 : array-like, shape=(sz2, d) or (sz2,)
    Another time series. If shape is (sz2,), the time series is assumed to be univariate.

global_constraint : {"itakura", "sakoe_chiba"} or None (default: None)
    Global constraint to restrict admissible paths for DTW.

sakoe_chiba_radius : int or None (default: None)
    Radius to be used for Sakoe-Chiba band global constraint.
    The Sakoe-Chiba radius corresponds to the parameter :math:`\delta` mentioned in [1]_,
    it controls how far in time we can go in order to match a given
    point from one time series to a point in another time series.
    If None and `global_constraint` is set to "sakoe_chiba", a radius of
    1 is used.
    If both `sakoe_chiba_radius` and `itakura_max_slope` are set,
    `global_constraint` is used to infer which constraint to use among the
    two. In this case, if `global_constraint` corresponds to no global
    constraint, a `RuntimeWarning` is raised and no global constraint is
    used.

itakura_max_slope : float or None (default: None)
    Maximum slope for the Itakura parallelogram constraint.
    If None and `global_constraint` is set to "itakura", a maximum slope
    of 2. is used.
    If both `sakoe_chiba_radius` and `itakura_max_slope` are set,
    `global_constraint` is used to infer which constraint to use among the
    two. In this case, if `global_constraint` corresponds to no global
    constraint, a `RuntimeWarning` is raised and no global constraint is
    used.

be : Backend object or string or None
    Backend. If `be` is an instance of the class `NumPyBackend` or the string `"numpy"`,
    the NumPy backend is used.
    If `be` is an instance of the class `PyTorchBackend` or the string `"pytorch"`,
    the PyTorch backend is used.
    If `be` is `None`, the backend is determined by the input arrays.
    See our :ref:`dedicated user-guide page <backend>` for more information.

Returns
-------
float
    Similarity score

### Goal
Computes the Dynamic Time Warping (DTW) distance between two time series, providing a flexible alignment-based similarity measure that supports both univariate and multivariate data.

### Parameters
- `s1`: The first time series, provided as an array-like object of shape `(sz1, d)` or `(sz1,)`.
- `s2`: The second time series, provided as an array-like object of shape `(sz2, d)` or `(sz2,)`.
- `global_constraint`, default `None`: Specifies the global path constraint to apply ("itakura" or "sakoe_chiba").
- `sakoe_chiba_radius`, default `None`: The integer radius for the Sakoe-Chiba band constraint.
- `itakura_max_slope`, default `None`: The float maximum slope for the Itakura parallelogram constraint.
- `be`, default `None`: The backend to use for computation; accepts "numpy", "pytorch", or a backend object.

### Input
- **Format:** Time series must be provided as `numpy.ndarray` or `torch.Tensor` of shape `(sz, d)` or `(sz,)`.
- **Preconditions:** Both time series must have the same number of dimensions `d`. They do not need to have the same length `sz`.

### Output
- Returns a `float` representing the DTW similarity score (the square root of the sum of squared Euclidean distances along the optimal warping path).

### Valid Call Patterns
```python
from tslearn.metrics import dtw
# Basic usage
dist = dtw([1, 2, 3], [1., 2., 2., 3.])

# PyTorch backend for gradients
import torch
s1 = torch.tensor([[1.0], [2.0], [3.0]], requires_grad=True)
s2 = torch.tensor([[3.0], [4.0], [-3.0]])
sim = dtw(s1, s2, be="pytorch")
```

### LLM Instruction Prompt
- Always ensure `s1` and `s2` have the same number of dimensions `d`.
- If using PyTorch for gradient computation, ensure the input tensors have `requires_grad=True` and explicitly set `be="pytorch"`.
- When applying constraints, ensure `global_constraint` is set to match the provided `sakoe_chiba_radius` or `itakura_max_slope` to avoid `RuntimeWarning`s.

### Prompt Snippet
```text
from tslearn.metrics import dtw
# Example: dtw(s1, s2, global_constraint="sakoe_chiba", sakoe_chiba_radius=2)
```

### Common Failure Modes
- **Dimension Mismatch:** Passing time series with different dimensions `d` will raise a `ValueError`.
- **Constraint Conflict:** Providing both `sakoe_chiba_radius` and `itakura_max_slope` without a valid `global_constraint` will trigger a `RuntimeWarning` and ignore the constraints.
- **Backend Mismatch:** Attempting to use a PyTorch-specific feature (like `backward()`) without setting `be="pytorch"` or passing PyTorch tensors will result in errors.

### Fix Code Hint
```python
# Ensure dimensions match
s1 = s1.reshape(-1, 1) if s1.ndim == 1 else s1
s2 = s2.reshape(-1, 1) if s2.ndim == 1 else s2
# Use explicit backend if needed
dist = dtw(s1, s2, be="numpy")
```

Available input path variables already in scope (choose the matching one(s) by type):
Pre-loaded and already in scope — use these directly, do NOT re-load:
- _trace: (see preamble)
- _balanced: (see preamble)
- X: balanced time-series dataset ndarray (8, 40, 1)
- X2: second dataset ndarray (4, 32, 1)
- s1: 1-D series ndarray (40,)
- s2: 1-D series ndarray (40,)
- y: four balanced labels, two examples per class
- tiny_matrix: deterministic numeric matrix
(raw input path strings also in scope if needed: trace_npz, output_dir)

RECEIVER — call `python:tslearn.metrics._dtw.dtw` on the RIGHT type (calling it on the wrong receiver is
the #1 failure; if it is an instance method, first obtain a value of the owner type,
do NOT call it on an unrelated preloaded input):
(receiver type not resolved)

(none yet)

Write minimal body statements that use `python:tslearn.metrics._dtw.dtw` correctly per the docs,
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
  `__CHECK__ python:tslearn.metrics._dtw.dtw ` followed by the witness, using the language's normal
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
materialize `python:tslearn.metrics._dtw.dtw`, but deliberately fail the assertion with a short message
stating that the documented contract is insufficient to verify the result. This is
a documentation-comprehension test: an unverifiable contract must not earn a pass.
If `python:tslearn.metrics._dtw.dtw` is itself a writer/output API, use an output binding only when one
is listed among the available inputs or execution context; then read back a small
part of the output, assert a known content/aggregate relation when the documented
contract permits it, and print the same structured line.
Do not call other heavyweight operations unless `python:tslearn.metrics._dtw.dtw` is the writer; keep the
body focused on `python:tslearn.metrics._dtw.dtw` so the run isolates that one call.
Use small deterministic parameters. For file-writing APIs, write only below output_dir. Optional-dependency failures must remain explicit infrastructure outcomes. End with a meaningful assertion and print a compact __CHECK__ witness.
