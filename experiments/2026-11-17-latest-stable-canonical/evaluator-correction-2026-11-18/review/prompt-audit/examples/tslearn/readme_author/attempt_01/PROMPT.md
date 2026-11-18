# Recorded author system prompt

You write LLM-facing API documentation in an exact markdown template.
You ground every fact in the provided API facts and context. You NEVER invent
parameters, types, return values, or APIs that are not given. If something is
unknown, say so rather than guessing.

Role: An expert Python time-series machine-learning engineer using tslearn and scikit-learn conventions. Write small deterministic executable checks for every frozen selected public API identity, including low-level backend helpers.
Project: tslearn (Python) - A scientific machine-learning toolkit for time-series data, including distance and alignment metrics, clustering, classification, forecasting, barycenters, preprocessing, shapelets, serialization, and backend helpers.
Domain: time-series machine learning
Target users: time-series researchers and data scientists; ML engineers familiar with NumPy and scikit-learn; coding agents generating executable time-series workflows
Use cases: Compute time-series distances, similarities, alignments, and barycenters.; Train compact clustering, classification, and forecasting estimators.; Convert, normalize, resample, serialize, and inspect time-series datasets.; Exercise public NumPy and PyTorch backend helpers with small arrays.
Constraints: Use only the checked-in Trace fixture and deterministic in-memory derivatives.; Do not download datasets, plot interactively, or access the network.; Keep estimator sizes, iteration counts, and thread counts small.; Import the target explicitly; the shared scaffold does not pre-import tested APIs.; Assert a falsifiable property and print the configured correctness witness.; Use every name in the frozen 116-name canonical manifest without sampling; selection is structural filtering and same-name maximum arity, not a proof of arbitrary semantic equivalence.

# Recorded author user prompt

Document the Python function `python:tslearn.metrics._dtw.dtw` of tslearn.

Authoritative API facts (JSON — do not contradict; do not add parameters or
types that are not listed here):
```json
{
  "name": "python:tslearn.metrics._dtw.dtw",
  "signature": "def dtw(s1, s2, global_constraint=None, sakoe_chiba_radius=None, itakura_max_slope=None, be=None)",
  "params": [
    {
      "name": "s1",
      "type": "",
      "default": null,
      "required": true,
      "kind": "positional_or_keyword"
    },
    {
      "name": "s2",
      "type": "",
      "default": null,
      "required": true,
      "kind": "positional_or_keyword"
    },
    {
      "name": "global_constraint",
      "type": "",
      "default": "None",
      "required": false,
      "kind": "positional_or_keyword"
    },
    {
      "name": "sakoe_chiba_radius",
      "type": "",
      "default": "None",
      "required": false,
      "kind": "positional_or_keyword"
    },
    {
      "name": "itakura_max_slope",
      "type": "",
      "default": "None",
      "required": false,
      "kind": "positional_or_keyword"
    },
    {
      "name": "be",
      "type": "",
      "default": "None",
      "required": false,
      "kind": "positional_or_keyword"
    }
  ],
  "returns": null,
  "source_doc": "Compute Dynamic Time Warping (DTW) similarity measure between\n(possibly multidimensional) time series and return it.\n\nDTW is computed as the Euclidean distance between aligned time series,\ni.e., if :math:`\\pi` is the optimal alignment path:\n\n.. math::\n\n    DTW(X, Y) = \\sqrt{\\sum_{(i, j) \\in \\pi} \\|X_{i} - Y_{j}\\|^2}\n\nNote that this formula is still valid for the multivariate case.\n\nIt is not required that both time series share the same size, but they must\nbe the same dimension. DTW was originally presented in [1]_ and is\ndiscussed in more details in our :ref:`dedicated user-guide page <dtw>`.\n\nParameters\n----------\ns1 : array-like, shape=(sz1, d) or (sz1,)\n    A time series. If shape is (sz1,), the time series is assumed to be univariate.\n\ns2 : array-like, shape=(sz2, d) or (sz2,)\n    Another time series. If shape is (sz2,), the time series is assumed to be univariate.\n\nglobal_constraint : {\"itakura\", \"sakoe_chiba\"} or None (default: None)\n    Global constraint to restrict admissible paths for DTW.\n\nsakoe_chiba_radius : int or None (default: None)\n    Radius to be used for Sakoe-Chiba band global constraint.\n    The Sakoe-Chiba radius corresponds to the parameter :math:`\\delta` mentioned in [1]_,\n    it controls how far in time we can go in order to match a given\n    point from one time series to a point in another time series.\n    If None and `global_constraint` is set to \"sakoe_chiba\", a radius of\n    1 is used.\n    If both `sakoe_chiba_radius` and `itakura_max_slope` are set,\n    `global_constraint` is used to infer which constraint to use among the\n    two. In this case, if `global_constraint` corresponds to no global\n    constraint, a `RuntimeWarning` is raised and no global constraint is\n    used.\n\nitakura_max_slope : float or None (default: None)\n    Maximum slope for the Itakura parallelogram constraint.\n    If None and `global_constraint` is set to \"itakura\", a maximum slope\n    of 2. is used.\n    If both `sakoe_chiba_radius` and `itakura_max_slope` are set,\n    `global_constraint` is used to infer which constraint to use among the\n    two. In this case, if `global_constraint` corresponds to no global\n    constraint, a `RuntimeWarning` is raised and no global constraint is\n    used.\n\nbe : Backend object or string or None\n    Backend. If `be` is an instance of the class `NumPyBackend` or the string `\"numpy\"`,\n    the NumPy backend is used.\n    If `be` is an instance of the class `PyTorchBackend` or the string `\"pytorch\"`,\n    the PyTorch backend is used.\n    If `be` is `None`, the backend is determined by the input arrays.\n    See our :ref:`dedicated user-guide page <backend>` for more information.\n\nReturns\n-------\nfloat\n    Similarity score\n\nExamples\n--------\n>>> dtw([1, 2, 3], [1., 2., 2., 3.])\n0.0\n>>> dtw([1, 2, 3], [1., 2., 2., 3., 4.])\n1.0\n\nThe PyTorch backend can be used to compute gradients:\n\n>>> import torch\n>>> s1 = torch.tensor([[1.0], [2.0], [3.0]], requires_grad=True)\n>>> s2 = torch.tensor([[3.0], [4.0], [-3.0]])\n>>> sim = dtw(s1, s2, be=\"pytorch\")\n>>> print(sim)\ntensor(6.4807, dtype=torch.float64, grad_fn=<SqrtBackward0>)\n>>> sim.backward()\n>>> print(s1.grad)\ntensor([[-0.3086],\n        [-0.1543],\n        [ 0.7715]])\n\n>>> s1_2d = torch.tensor([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]], requires_grad=True)\n>>> s2_2d = torch.tensor([[3.0, 3.0], [4.0, 4.0], [-3.0, -3.0]])\n>>> sim = dtw(s1_2d, s2_2d, be=\"pytorch\")\n>>> print(sim)\ntensor(9.1652, dtype=torch.float64, grad_fn=<SqrtBackward0>)\n>>> sim.backward()\n>>> print(s1_2d.grad)\ntensor([[-0.2182, -0.2182],\n        [-0.1091, -0.1091],\n        [ 0.5455,  0.5455]])\n\nSee Also\n--------\ndtw_path : Get both the matching path and the similarity score for DTW\ncdist_dtw : Cross similarity matrix between time series datasets\n\nReferences\n----------\n.. [1] H. Sakoe, S. Chiba, \"Dynamic programming algorithm optimization for\n       spoken word recognition,\" IEEE Transactions on Acoustics, Speech and\n       Signal Processing, vol. 26(1), pp. 43--49, 1978.",
  "overloads": [],
  "api_id": "python:tslearn.metrics._dtw.dtw",
  "display_name": "dtw",
  "identity_version": "language_qualified_api_v1",
  "parameter_count": 6,
  "parameter_count_status": "declared",
  "exposure_ids": [
    "python:tslearn.metrics._dtw.dtw",
    "python:tslearn.metrics.dtw",
    "python:tslearn.metrics.softdtw_variants.dtw"
  ],
  "preferred_public_path": "tslearn.metrics.dtw",
  "public_access_paths": [
    "tslearn.metrics._dtw.dtw",
    "tslearn.metrics.dtw",
    "tslearn.metrics.softdtw_variants.dtw"
  ],
  "qualified_name": "tslearn.metrics._dtw.dtw",
  "source": {
    "file": "source/tslearn/metrics/_dtw.py",
    "line": 30,
    "site_id": "Python:tslearn:tslearn/metrics/_dtw.py:508:function:dtw"
  },
  "definition_sites": [
    {
      "signature": "def dtw(s1, s2, global_constraint=None, sakoe_chiba_radius=None, itakura_max_slope=None, be=None)",
      "qualified_name": "tslearn.metrics._dtw.dtw",
      "source": {
        "file": "source/tslearn/metrics/_dtw.py",
        "line": 30,
        "site_id": "Python:tslearn:tslearn/metrics/_dtw.py:508:function:dtw"
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
===== Original documentation part 1/3 =====
### 1. Project purpose
`tslearn` is a Python machine-learning toolkit designed for time-series data. It provides a comprehensive suite of tools for time-series analysis, including distance metrics, alignment algorithms, clustering, classification, forecasting, barycenter computation, and preprocessing. It integrates seamlessly with NumPy and scikit-learn, and offers PyTorch-compatible backend helpers for differentiable loss functions.

### 2. Main workflows
*   **Distance and Similarity:** Compute cross-similarity matrices using metrics like DTW, Soft-DTW, Frechet, and Global Alignment Kernel (GAK).
*   **Clustering:** Perform time-series clustering using `TimeSeriesKMeans`, `KShape`, `KernelKMeans`, and `TimeSeriesDBSCAN`.
*   **Forecasting:** Use statistical models (`VARIMA`, `AutoVARIMA`) or pre-trained foundation models (`ZeroShotForecaster`, `LinearProbeForecaster`) to predict future values.
*   **Barycenters:** Compute representative time series (averages) using DBA (DTW Barycenter Averaging) or Soft-DTW geometry.
*   **Preprocessing/Validation:** Scale, normalize, and validate time-series datasets, including silhouette analysis for clustering.
*   **Foundation Models:** Embed time series using frozen pre-trained models via `TimeSeriesFoundationEmbedder`.

### 3. Important APIs and usage patterns
*   **Estimators:** Follow the scikit-learn `fit`/`predict`/`transform` pattern.
*   **Metrics:** `cdist_*` functions compute cross-similarity matrices between datasets.
*   **Persistence:** Most estimators support `to_hdf5`, `to_json`, and `to_pickle` (and corresponding `from_*` class methods).
*   **Backend:** Many metrics accept a `be` parameter to switch between `numpy` and `pytorch` backends.
*   **Forecasting:** `ScaledForecastingPipeline` wraps forecasters to handle scaling/unscaling automatically.

### 4. Inputs and file formats
*   **Data Structure:** Time-series datasets are typically `numpy.ndarray` of shape `(n_ts, sz, d)`, where `n_ts` is the number of series, `sz` is the length, and `d` is the number of dimensions (features).
*   **Serialization:** Supports HDF5 (requires `h5py`), JSON, and Pickle.
*   **Datasets:** `CachedDatasets` and `UCR_UEA_datasets` provide access to standard time-series benchmarks.

### 5. Outputs and generated artifacts
*   **Clustering:** `labels_`, `cluster_centers_`, `inertia_`.
*   **Forecasting:** Forecasted arrays of shape `(n_ts, n, d)`.
*   **Metrics:** Cross-similarity matrices of shape `(n_ts1, n_ts2)`.
*   **Embeddings:** Feature matrices of shape `(n_ts, embedding_size)`.

### 6. Configuration and environment assumptions
*   **Parallelization:** Many estimators and metrics accept `n_jobs` to leverage `joblib`.
*   **Randomness:** Estimators accept `random_state` for reproducibility.
*   **Dependencies:** Standard scientific stack (NumPy, scikit-learn, SciPy). PyTorch is required for `SoftDTWLossPyTorch` and foundation model features.

### 7. Commands and examples

**DTW Barycenter Averaging:**
```python
from tslearn.barycenters import dtw_barycenter_averaging
time_series = [[1, 2, 3, 4], [1, 2, 4, 5]]
dtw_barycenter_averaging(time_series, max_iter=5)
```

**K-Means Clustering:**
```python
from tslearn.clustering import TimeSeriesKMeans
from tslearn.generators import random_walks
X = random_walks(n_ts=50, sz=32, d=1)
km = TimeSeriesKMeans(n_clusters=3, metric="euclidean", max_iter=5, random_state=0).fit(X)
```

**Soft-DTW Loss (PyTorch):**
```python
import torch
from tslearn.metrics import SoftDTWLossPyTorch
soft_dtw_loss = SoftDTWLossPyTorch(gamma=0.1)
x = torch.zeros((4, 3, 2), requires_grad=True)
y = torch.arange(0, 24).reshape(4, 3, 2)
loss = soft_dtw_loss(x, y).mean()
loss.backward()
```

**Foundation Model Linear Probe:**
```python
from tslearn.foundation import LinearProbeForecaster
model = LinearProbeForecaster(pretrained_model, horizon=24)
model.fit(X_train)
preds = model.predict(X_test)
```

### 8. Constraints, preconditions, compatibility rules
*   **Equal Lengths:** `euclidean_barycenter`, `KShape`, and `TimeSeriesDBSCAN` (with Euclidean metric) require datasets of equal-sized time series.
*   **Foundation Models:** `TimeSeriesFoundationEmbedder` does not support variable-length time series due to NaN padding propagation.
*   **Memory:** `KernelKMeans` saves training data to disk during serialization; large datasets result in large model files.
*   **Horizon:** `LinearProbeForecaster` requires `n` (forecast horizon) to be within the `horizon` defined at fit time.

### 9. Facts to preserve in the final README
*   `tslearn` is the standard for time-series ML in the scikit-learn ecosystem.
*   Supports both univariate and multivariate time series.
*   Provides differentiable loss functions for deep learning via PyTorch.
*   Includes built-in access to the UCR/UEA archive.

### 10. Missing or weak documentation
*   The `be` (backend) parameter documentation is inconsistent across different `cdist_*` functions.
*   The `tokens` parameter in `TimeSeriesFoundationEmbedder` lacks detailed examples for specific popular models (e.g., Chronos).
*   `set_output` API usage is mentioned but lacks comprehensive examples for all transformers.

===== Original documentation part 2/3 =====
### 1. Project purpose
`tslearn` is a Python machine-learning toolkit specifically designed for time-series data. It provides a comprehensive suite of tools for time-series analysis, including distance metrics, alignment algorithms, clustering, classification, regression, and forecasting. It integrates seamlessly with `scikit-learn` and `NumPy`, and supports `PyTorch` for gradient-based optimization in differentiable time-series metrics.

### 2. Main workflows
*   **Distance and Alignment:** Computing similarity between time series using DTW, Soft-DTW, Frechet, GAK, and LCSS.
*   **Supervised Learning:** Classification and regression using k-Nearest Neighbors (k-NN) with time-series-specific metrics or Multi-Layer Perceptrons (MLP).
*   **Symbolic Representation:** Transforming time series into symbolic representations (e.g., 1d-SAX) for dimensionality reduction and indexing.
*   **Performance Evaluation:** Calculating forecasting/regression error metrics (MAE, MSE, MASE).
*   **Differentiable Loss:** Using Soft-DTW or Frechet distance with PyTorch backends to compute gradients for optimization.

### 3. Important APIs and usage patterns
*   **Metrics:** All metric functions (e.g., `dtw`, `soft_dtw`, `lcss`, `frechet`) follow a consistent signature: `(s1, s2, **params)`.
*   **Estimators:** `KNeighborsTimeSeries`, `KNeighborsTimeSeriesClassifier`, `KNeighborsTimeSeriesRegressor`, `TimeSeriesMLPClassifier`, and `TimeSeriesMLPRegressor` follow the `scikit-learn` `fit`/`predict` pattern.
*   **Backends:** Most metrics accept a `be` parameter (string or object) to toggle between `NumPyBackend` and `PyTorchBackend`.
*   **Serialization:** Estimators provide `to_hdf5`, `to_json`, and `to_pickle` methods for persistence.

### 4. Inputs and file formats
*   **Time Series:** Typically `array-like` with shape `(n_ts, sz, d)` (dataset) or `(sz, d)` (single series), where `sz` is the length and `d` is the dimension.
*   **Serialization:** Supports HDF5 (requires `h5py`), JSON, and Pickle.
*   **Metrics:** Some metrics (e.g., `dtw_path_from_metric`) accept precomputed distance matrices.

### 5. Outputs and generated artifacts
*   **Similarity Scores:** Scalar floats representing distance or kernel values.
*   **Alignment Paths:** Lists of integer index pairs `[(i, j), ...]` representing the optimal warping path.
*   **Models:** Serialized files containing fitted parameters.
*   **Transformations:** Symbolic representations (e.g., 1d-SAX arrays).

### 6. Configuration and environment assumptions
*   **Parallelization:** Uses `n_jobs` parameter (compatible with `joblib`).
*   **Backend:** If `be=None`, the backend is inferred from the input array type (NumPy vs. PyTorch).
*   **Constraints:** Global constraints (Sakoe-Chiba, Itakura) are supported across most distance metrics to restrict the search space.

### 7. Commands and examples

**DTW with PyTorch for Gradient Computation:**
```python
import torch
from tslearn.metrics import dtw
s1 = torch.tensor([[1.0], [2.0], [3.0]], requires_grad=True)
s2 = torch.tensor([[3.0], [4.0], [-3.0]])
sim = dtw(s1, s2, be="pytorch")
sim.backward()
print(s1.grad)
```

**Soft-DTW Alignment:**
```python
from tslearn.metrics import soft_dtw_alignment
a, dist = soft_dtw_alignment([1, 2, 2, 3], [1., 2., 3., 4.], gamma=1.)
```

**k-NN Classification:**
```python
from tslearn.neighbors import KNeighborsTimeSeriesClassifier
clf = KNeighborsTimeSeriesClassifier(n_neighbors=2, metric="dtw")
clf.fit([[1, 2, 3], [1, 1.2, 3.2], [3, 2, 1]], y=[0, 0, 1])
pred = clf.predict([[1, 2.2, 3.5]])
```

**1d-SAX Transformation:**
```python
from tslearn.piecewise import OneD_SymbolicAggregateApproximation
one_d_sax = OneD_SymbolicAggregateApproximation(n_segments=3, alphabet_size_avg=2)
data = [[-1., 2., 0.1, -1., 1., -1.], [1., 3.2, -1., -3., 1., -1.]]
one_d_sax_data = one_d_sax.fit_transform(data)
```

### 8. Constraints, preconditions, compatibility rules
*   **Dimension Matching:** Most metrics require time series to have the same dimension `d`, though they may differ in length `sz`.
*   **Constraint Conflict:** If both `sakoe_chiba_radius` and `itakura_max_slope` are provided, `global_constraint` is used to determine which to apply.
*   **SAX Normalization:** When using `sax` as a metric in `KNeighborsTimeSeries`, data must be normalized (zero mean, unit variance).
*   **MLP Constraints:** `TimeSeriesMLP` estimators require equal-sized time series.

### 9. Facts to preserve in the final README
*   `tslearn` is the standard toolkit for time-series ML in Python.
*   Supports both CPU (NumPy) and GPU/Autograd (PyTorch) workflows.
*   Implements standard alignment metrics (DTW, Soft-DTW, GAK, Frechet, LCSS).
*   Provides `scikit-learn` compatible estimators for classification, regression, and neighbor search.

### 10. Missing or weak documentation
*   The documentation for `metric_params` in `KNeighborsTimeSeries` is sparse regarding specific dictionary keys for different metrics.
*   The distinction between `soft_dtw` and `soft_dtw_normalized` could be clarified with more explicit mathematical examples.
*   The `be` (backend) parameter documentation is consistent but could benefit from a centralized table of which metrics support which backends.

===== Original documentation part 3/3 =====
### 1. Project purpose
`tslearn` is a specialized Python machine-learning toolkit designed for time-series analysis. It provides a comprehensive suite of algorithms for time-series clustering, classification, regression, and forecasting, while maintaining full compatibility with the `scikit-learn` API. It supports both univariate and multivariate time series, including variable-length datasets.

### 2. Main workflows
* **Data Preparation:** Converting raw data into the `tslearn` 3D format (`n_ts, sz, d`) using utility functions or external format converters.
* **Preprocessing:** Normalizing, resampling, imputing missing values, or applying piecewise approximations (PAA/SAX) to prepare data for modeling.
* **Modeling:** Training estimators for classification (e.g., `KNeighborsTimeSeriesClassifier`, `TimeSeriesSVC`), clustering (e.g., `TimeSeriesKMeans`, `KShape`), or regression (e.g., `TimeSeriesSVR`).
* **Analysis:** Computing distances, barycenters, and matrix profiles, or performing shapelet-based feature extraction.

### 3. Important APIs and usage patterns
* **Estimator API:** Follows `scikit-learn` conventions (`fit`, `transform`, `fit_transform`, `predict`, `score`).
* **Serialization:** Models support `to_hdf5`, `to_json`, and `to_pickle` (with corresponding `from_*` class methods). Note: `LearningShapelets` does not support HDF5.
* **Output Configuration:** The `set_output(transform=...)` method allows configuring output containers (e.g., `pandas`, `polars`).
* **Metadata Routing:** Estimators support `get_metadata_routing()` and specific request configuration methods (e.g., `set_transform_request`, `set_score_request`) for meta-estimator integration.

### 4. Inputs and file formats
* **Internal Format:** 3D `numpy.ndarray` of shape `(n_ts, sz, d)`.
* **External Converters:** Utilities exist to convert from `cesium`, `pyflux`, `pyts`, `seglearn`, `sktime`, `stumpy`, and `tsfresh` formats.
* **Persistence:** Supports HDF5 (requires `h5py`), JSON, and Pickle.

### 5. Outputs and generated artifacts
* **Transformations:** Return `numpy.ndarray` (or `pandas`/`polars` if configured).
* **Predictions:** Return class labels, probabilities, or regression targets.
* **Model State:** Attributes like `support_vectors_`, `shapelets_`, or `mean_` are exposed after fitting.

### 6. Configuration and environment assumptions
* **Dependencies:** Requires `numpy` and `scikit-learn`. Some features require `h5py` (HDF5), `pandas` (data conversion), or `keras` (for `LearningShapelets`).
* **Backend:** Supports NumPy and PyTorch backends (determined by input arrays or explicit `be` parameter).
* **Python:** 3.10+.

### 7. Commands and examples

**Data Formatting:**
```python
from tslearn.utils import to_time_series_dataset
X = to_time_series_dataset([[1, 3, 4, 2], [1, 2, 4, 2], [1, 2, 4, 2, 2]])
```

**Preprocessing (Scaling):**
```python
from tslearn.preprocessing import TimeSeriesScalerMinMax
X_scaled = TimeSeriesScalerMinMax().fit_transform(X)
```

**Classification:**
```python
from tslearn.neighbors import KNeighborsTimeSeriesClassifier
knn = KNeighborsTimeSeriesClassifier(n_neighbors=1)
knn.fit(X_scaled, [0, 1, 1])
preds = knn.predict(X_scaled)
```

**Piecewise Approximation (PAA):**
```python
from tslearn.piecewise import PiecewiseAggregateApproximation
paa = PiecewiseAggregateApproximation(n_segments=3)
paa_data = paa.fit_transform(data)
```

### 8. Constraints, preconditions, compatibility rules
* **Dimensions:** Input must be `(n_ts, sz, d)`. Univariate series are automatically wrapped if provided as `(sz,)`.
* **Missing Values:** `TimeSeriesImputer` handles `NaN` values. `TimeSeriesScaler` ignores `NaN`s during mean/std calculation.
* **Variable Length:** Supported via padding (e.g., `to_time_series_dataset`). `TimeSeriesImputer` can preserve trailing `NaN`s as padding.
* **Compatibility:** `TimeSeriesSVC` and `TimeSeriesSVR` use `gak` (Global Alignment Kernel) by default.

### 9. Facts to preserve in the final README
* `tslearn` is fully compatible with `scikit-learn` pipelines and hyper-parameter tuning.
* The library supports both univariate and multivariate time series.
* The `to_time_series_dataset` utility is the primary entry point for data formatting.
* Cite the JMLR 2020 paper for scholarly use.

### 10. Missing or weak documentation
* The `set_output` API documentation refers to external `scikit-learn` guides rather than providing exhaustive internal examples.
* `LearningShapelets` HDF5 serialization limitation is noted but not explained in terms of alternative migration paths.
* Some `fit` methods are marked as "dummy" for `sklearn` compliance; the distinction between stateless and stateful transformers could be clarified further in the user guide.

Real usage from the project's existing test suite (these compile and pass — base
the Valid Call Patterns and realistic Common Failure Modes on them; may be empty):
```Python
(no existing test found for this API)
```

Verbatim code example(s) from the ORIGINAL project README that call `python:tslearn.metrics._dtw.dtw`
(the project's real, documented usage — may be empty):
```Python
===== Shared original document: pinned-root-readme:README.md =====
<!-- Our logo and description -->
<div align="center">
  <p><a href="https://tslearn.readthedocs.io"><image src="https://raw.githubusercontent.com/tslearn-team/tslearn/main/docs/_static/tslearn_logo_white_background.png?cache-control=no-cache" width="20%" alt="tslearn logo"/></a></p>
  <h1>The machine learning toolkit for time series analysis in Python</h1>
</div>

<!-- The badges -->
<p align="center">
    <a href="https://badge.fury.io/py/tslearn">
        <img alt="PyPI" src="https://badge.fury.io/py/tslearn.svg?cache-control=no-cache">
    </a>
    <a href="https://www.python.org/downloads/">
        <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10+-blue.svg">
    </a>
    <a href="http://tslearn.readthedocs.io/en/stable/?badge=stable">
        <img alt="Documentation" src="https://app.readthedocs.org/projects/tslearn/badge/?version=stable">
    </a>
    <a href="https://dev.azure.com/romaintavenard/tslearn/_build">
        <img alt="Build (Azure Pipelines)" src="https://dev.azure.com/romaintavenard/tslearn/_apis/build/status/tslearn-team.tslearn?branchName=main">
    </a>
    <a href="https://codecov.io/gh/tslearn-team/tslearn">
        <img alt="Codecov" src="https://codecov.io/gh/tslearn-team/tslearn/branch/main/graph/badge.svg">
    </a>
    <a href="https://pepy.tech/project/tslearn">
        <img alt="Downloads" src="https://pepy.tech/badge/tslearn">
    </a>
</p>

<!-- Draw horizontal rule -->
<hr>

<!-- Table of content -->

| Section | Description |
|-|-|
| [Installation](#installation) | Installing the dependencies and tslearn |
| [Getting started](#getting-started) | A quick introduction on how to use tslearn |
| [Available features](#available-features) | An extensive overview of tslearn's functionalities |
| [Documentation](#documentation) | A link to our API reference and a gallery of examples |
| [Contributing](#contributing) | A guide for heroes willing to contribute |
| [Citation](#referencing-tslearn) | A citation for tslearn for scholarly articles |

## Installation<a id="installation"></a>
There are different alternatives to install tslearn:
* PyPi: `python -m pip install tslearn`
* Conda: `conda install -c conda-forge tslearn`
* Git: `python -m pip install https://github.com/tslearn-team/tslearn/archive/main.zip`

In order for the installation to be successful, the required dependencies must be installed. For a more detailed guide on how to install tslearn, please see the [Documentation](https://tslearn.readthedocs.io/en/stable/?badge=stable#installation).

## Getting started<a id="getting-started"></a>

### 1. Getting the data in the right format
tslearn expects a time series dataset to be formatted as a 3D `numpy` array. The three dimensions correspond to the number of time series, the number of measurements per time series and the number of dimensions respectively (`n_ts, max_sz, d`). In order to get the data in the right format, different solutions exist:
* [You can use the utility functions such as `to_time_series_dataset`.](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.utils.html#module-tslearn.utils)
* [You can convert from other popular time series toolkits in Python.](https://tslearn.readthedocs.io/en/stable/integration_other_software.html)
* [You can load any of the UCR datasets in the required format.](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.datasets.html#module-tslearn.datasets)
* [You can generate synthetic data using the `generators` module.](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.generators.html#module-tslearn.generators)

It should further be noted that tslearn [supports variable-length timeseries](https://tslearn.readthedocs.io/en/stable/variablelength.html).

```python3
>>> from tslearn.utils import to_time_series_dataset
>>> my_first_time_series = [1, 3, 4, 2]
>>> my_second_time_series = [1, 2, 4, 2]
>>> my_third_time_series = [1, 2, 4, 2, 2]
>>> X = to_time_series_dataset([my_first_time_series,
                                my_second_time_series,
                                my_third_time_series])
>>> y = [0, 1, 1]
```

### 2. Data preprocessing and transformations
Optionally, tslearn has several utilities to preprocess the data. In order to facilitate the convergence of different algorithms, you can [scale time series](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.preprocessing.html#module-tslearn.preprocessing). Alternatively, in order to speed up training times, one can [resample](https://tslearn.readthedocs.io/en/stable/gen_modules/preprocessing/tslearn.preprocessing.TimeSeriesResampler.html#tslearn.preprocessing.TimeSeriesResampler) the data or apply a [piece-wise transformation](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.piecewise.html#module-tslearn.piecewise).

```python3
>>> from tslearn.preprocessing import TimeSeriesScalerMinMax
>>> X_scaled = TimeSeriesScalerMinMax().fit_transform(X)
>>> print(X_scaled)
[[[0.] [0.667] [1.] [0.333] [nan]]
 [[0.] [0.333] [1.] [0.333] [nan]]
 [[0.] [0.333] [1.] [0.333] [0.333]]]
```

### 3. Training a model

After getting the data in the right format, a model can be trained. Depending on the use case, tslearn supports different tasks: classification, clustering and regression. For an extensive overview of possibilities, check out our [gallery of examples](https://tslearn.readthedocs.io/en/stable/auto_examples/index.html).

```python3
>>> from tslearn.neighbors import KNeighborsTimeSeriesClassifier
>>> knn = KNeighborsTimeSeriesClassifier(n_neighbors=1)
>>> knn.fit(X_scaled, y)
>>> print(knn.predict(X_scaled))
[0 1 1]
```

As can be seen, the models in tslearn follow the same API as those of the well-known scikit-learn. Moreover, they are fully compatible with it, allowing to use different scikit-learn utilities such as [hyper-parameter tuning and pipelines](https://tslearn.readthedocs.io/en/stable/auto_examples/neighbors/plot_knnts_sklearn.html).

### 4. More analyses

tslearn further allows to perform all different types of analysis. Examples include [calculating barycenters](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.barycenters.html#module-tslearn.barycenters) of a group of time series or calculate the distances between time series using a [variety of distance metrics](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.metrics.html#module-tslearn.metrics).

## Available features<a id="available-features"></a>

| data                                                                                                                                                                                         | processing                                                                                                              | clustering                                                                                                                                                       | classification                                                                                                                                                                          | regression                                                                                                                                                                           | metrics                                                                                                                              |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| [UCR Datasets](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.datasets.html#module-tslearn.datasets)                                                                           | [Scaling](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.preprocessing.html#module-tslearn.preprocessing) | [TimeSeriesKMeans](https://tslearn.readthedocs.io/en/stable/gen_modules/clustering/tslearn.clustering.TimeSeriesKMeans.html#tslearn.clustering.TimeSeriesKMeans) | [KNN Classifier](https://tslearn.readthedocs.io/en/stable/gen_modules/neighbors/tslearn.neighbors.KNeighborsTimeSeriesClassifier.html#tslearn.neighbors.KNeighborsTimeSeriesClassifier) | [KNN Regressor](https://tslearn.readthedocs.io/en/stable/gen_modules/neighbors/tslearn.neighbors.KNeighborsTimeSeriesRegressor.html#tslearn.neighbors.KNeighborsTimeSeriesRegressor) | [Dynamic Time Warping](https://tslearn.readthedocs.io/en/stable/gen_modules/metrics/tslearn.metrics.dtw.html#tslearn.metrics.dtw)    |
| [Generators](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.generators.html#module-tslearn.generators)                                                                         | [Piecewise](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.piecewise.html#module-tslearn.piecewise)       | [KShape](https://tslearn.readthedocs.io/en/stable/gen_modules/clustering/tslearn.clustering.KShape.html#tslearn.clustering.KShape)                               | [TimeSeriesSVC](https://tslearn.readthedocs.io/en/stable/gen_modules/svm/tslearn.svm.TimeSeriesSVC.html#tslearn.svm.TimeSeriesSVC)                                                      | [TimeSeriesSVR](https://tslearn.readthedocs.io/en/stable/gen_modules/svm/tslearn.svm.TimeSeriesSVR.html#tslearn.svm.TimeSeriesSVR)                                                   | [Global Alignment Kernel](https://tslearn.readthedocs.io/en/stable/gen_modules/metrics/tslearn.metrics.gak.html#tslearn.metrics.gak) |
| Conversion([1](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.utils.html#module-tslearn.utils), [2](https://tslearn.readthedocs.io/en/stable/integration_other_software.html)) |                                                                                                                         | [KernelKmeans](https://tslearn.readthedocs.io/en/stable/gen_modules/clustering/tslearn.clustering.KernelKMeans.html#tslearn.clustering.KernelKMeans)             | [LearningShapelets](https://tslearn.readthedocs.io/en/stable/gen_modules/shapelets/tslearn.shapelets.LearningShapelets.html)                                    | [MLP](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.neural_network.html#module-tslearn.neural_network)                                                                | [Barycenters](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.barycenters.html#module-tslearn.barycenters)              |
|                                                                                                                                                                                              |                                                                                                                         |                                                                                                                                                                  | [Early Classification](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.early_classification.html#module-tslearn.early_classification)                                      |                                                                                                                                                                                      | [Matrix Profile](https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.matrix_profile.html#module-tslearn.matrix_profile)     |


## Documentation<a id="documentation"></a>

The documentation is hosted at [readthedocs](http://tslearn.readthedocs.io/en/stable/index.html). It includes an [API](https://tslearn.readthedocs.io/en/stable/reference.html), [gallery of examples](https://tslearn.readthedocs.io/en/stable/auto_examples/index.html) and a [user guide](https://tslearn.readthedocs.io/en/stable/user_guide/userguide.html).

## Contributing<a id="contributing"></a>

If you would like to contribute to `tslearn`, please have a look at [our contribution guidelines](https://github.com/tslearn-team/tslearn/blob/main/CONTRIBUTING.rst). A list of interesting TODO's can be found [here](https://github.com/tslearn-team/tslearn/issues?utf8=✓&q=is%3Aissue%20is%3Aopen%20label%3A%22new%20feature%22%20). **If you want other ML methods for time series to be added to this TODO list, do not hesitate to [open an issue](https://github.com/tslearn-team/tslearn/issues/new/choose)!**

## Referencing tslearn<a id="referencing-tslearn"></a>

If you use `tslearn` in a scientific publication, we would appreciate citations:

```bibtex
@article{JMLR:v21:20-091,
  author  = {Romain Tavenard and Johann Faouzi and Gilles Vandewiele and 
             Felix Divo and Guillaume Androz and Chester Holtz and 
             Marie Payne and Roman Yurchak and Marc Ru{\ss}wurm and 
             Kushal Kolar and Eli Woods},
  title   = {Tslearn, A Machine Learning Toolkit for Time Series Data},
  journal = {Journal of Machine Learning Research},
  year    = {2020},
  volume  = {21},
  number  = {118},
  pages   = {1-6},
  url     = {https://www.jmlr.org/papers/v21/20-091.html}
}
```

#### Acknowledgments
Authors would like to thank Mathieu Blondel for providing code for [Kernel k-means](https://gist.github.com/mblondel/6230787) and [Soft-DTW](https://github.com/mblondel/soft-dtw), and to Mehran Maghoumi for his [`torch`-compatible implementation of SoftDTW](https://github.com/Maghoumi/pytorch-softdtw-cuda).


===== https://tslearn.readthedocs.io/en/stable/gen_modules/metrics/tslearn.metrics.dtw.html#tslearn.metrics.dtw =====
tslearn.metrics.dtw(s1, s2, global_constraint=None, sakoe_chiba_radius=None, itakura_max_slope=None, be=None)[source]

Compute Dynamic Time Warping (DTW) similarity measure between (possibly multidimensional) time series and return it.

DTW is computed as the Euclidean distance between aligned time series, i.e., if \(\pi\) is the optimal alignment path:

 \[DTW(X, Y) = \sqrt{\sum_{(i, j) \in \pi} \|X_{i} - Y_{j}\|^2}\]

Note that this formula is still valid for the multivariate case.

It is not required that both time series share the same size, but they must be the same dimension. DTW was originally presented in [1] and is discussed in more details in our dedicated user-guide page.

Parameters:

s1array-like, shape=(sz1, d) or (sz1,)

A time series. If shape is (sz1,), the time series is assumed to be univariate.

s2array-like, shape=(sz2, d) or (sz2,)

Another time series. If shape is (sz2,), the time series is assumed to be univariate.

global_constraint{“itakura”, “sakoe_chiba”} or None (default: None)

Global constraint to restrict admissible paths for DTW.

sakoe_chiba_radiusint or None (default: None)

Radius to be used for Sakoe-Chiba band global constraint. The Sakoe-Chiba radius corresponds to the parameter \(\delta\) mentioned in [1], it controls how far in time we can go in order to match a given point from one time series to a point in another time series. If None and global_constraint is set to “sakoe_chiba”, a radius of 1 is used. If both sakoe_chiba_radius and itakura_max_slope are set, global_constraint is used to infer which constraint to use among the two. In this case, if global_constraint corresponds to no global constraint, a RuntimeWarning is raised and no global constraint is used.

itakura_max_slopefloat or None (default: None)

Maximum slope for the Itakura parallelogram constraint. If None and global_constraint is set to “itakura”, a maximum slope of 2. is used. If both sakoe_chiba_radius and itakura_max_slope are set, global_constraint is used to infer which constraint to use among the two. In this case, if global_constraint corresponds to no global constraint, a RuntimeWarning is raised and no global constraint is used.

beBackend object or string or None

Backend. If be is an instance of the class NumPyBackend or the string “numpy”, the NumPy backend is used. If be is an instance of the class PyTorchBackend or the string “pytorch”, the PyTorch backend is used. If be is None, the backend is determined by the input arrays. See our dedicated user-guide page for more information.

Returns:

float

Similarity score

See also

dtw_path

Get both the matching path and the similarity score for DTW

cdist_dtw

Cross similarity matrix between time series datasets

References

 [1] (1,2)
H. Sakoe, S. Chiba, “Dynamic programming algorithm optimization for spoken word recognition,” IEEE Transactions on Acoustics, Speech and Signal Processing, vol. 26(1), pp. 43–49, 1978.

Examples

>>> dtw([1, 2, 3], [1., 2., 2., 3.])
0.0
>>> dtw([1, 2, 3], [1., 2., 2., 3., 4.])
1.0

The PyTorch backend can be used to compute gradients:

>>> import torch
>>> s1 = torch.tensor([[1.0], [2.0], [3.0]], requires_grad=True)
>>> s2 = torch.tensor([[3.0], [4.0], [-3.0]])
>>> sim = dtw(s1, s2, be="pytorch")
>>> print(sim)
tensor(6.4807, dtype=torch.float64, grad_fn=<SqrtBackward0>)
>>> sim.backward()
>>> print(s1.grad)
tensor([[-0.3086],
        [-0.1543],
        [ 0.7715]])

>>> s1_2d = torch.tensor([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]], requires_grad=True)
>>> s2_2d = torch.tensor([[3.0, 3.0], [4.0, 4.0], [-3.0, -3.0]])
>>> sim = dtw(s1_2d, s2_2d, be="pytorch")
>>> print(sim)
tensor(9.1652, dtype=torch.float64, grad_fn=<SqrtBackward0>)
>>> sim.backward()
>>> print(s1_2d.grad)
tensor([[-0.2182, -0.2182],
        [-0.1091, -0.1091],
        [ 0.5455,  0.5455]])

```

GROUND THE CALL FORM by combining the sources above, in this priority order — and
NEVER invent a call shape that appears in none of them:
1. If a test-suite example is shown, its call form is authoritative (it compiles
   and passes) — reproduce that exact receiver and argument order.
2. Otherwise use the original-README example's call form.
3. If BOTH are shown, reproduce a real form verbatim (either compiles); when they
   differ, the instance/implicit form `value.python:tslearn.metrics._dtw.dtw(...)` is the most portable.
4. If NEITHER is shown, derive the call from the Signature/API facts and say in the
   entry that the example is inferred from the signature (not verified).
Preserve the receiver/qualifier EXACTLY as written — if it is
`value.python:tslearn.metrics._dtw.dtw(...)` or `Object.python:tslearn.metrics._dtw.dtw(...)`, keep it; do NOT collapse it to
a bare `python:tslearn.metrics._dtw.dtw(...)`, which usually will not compile.

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

Examples
--------
>>> dtw([1, 2, 3], [1., 2., 2., 3.])
0.0
>>> dtw([1, 2, 3], [1., 2., 2., 3., 4.])
1.0

The PyTorch backend can be used to compute gradients:

>>> import torch
>>> s1 = torch.tensor([[1.0], [2.0], [3.0]], requires_grad=True)
>>> s2 = torch.tensor([[3.0], [4.0], [-3.0]])
>>> sim = dtw(s1, s2, be="pytorch")
>>> print(sim)
tensor(6.4807, dtype=torch.float64, grad_fn=<SqrtBackward0>)
>>> sim.backward()
>>> print(s1.grad)
tensor([[-0.3086],
        [-0.1543],
        [ 0.7715]])

>>> s1_2d = torch.tensor([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]], requires_grad=True)
>>> s2_2d = torch.tensor([[3.0, 3.0], [4.0, 4.0], [-3.0, -3.0]])
>>> sim = dtw(s1_2d, s2_2d, be="pytorch")
>>> print(sim)
tensor(9.1652, dtype=torch.float64, grad_fn=<SqrtBackward0>)
>>> sim.backward()
>>> print(s1_2d.grad)
tensor([[-0.2182, -0.2182],
        [-0.1091, -0.1091],
        [ 0.5455,  0.5455]])

See Also
--------
dtw_path : Get both the matching path and the similarity score for DTW
cdist_dtw : Cross similarity matrix between time series datasets

References
----------
.. [1] H. Sakoe, S. Chiba, "Dynamic programming algorithm optimization for
       spoken word recognition," IEEE Transactions on Acoustics, Speech and
       Signal Processing, vol. 26(1), pp. 43--49, 1978.

### Goal
TODO: one sentence describing what `python:tslearn.metrics._dtw.dtw` does, in the project's domain terms.

### Parameters
- `s1`: TODO — what this argument means / expected values.
- `s2`: TODO — what this argument means / expected values.
- `global_constraint`, default `None`: TODO — what this argument means / expected values.
- `sakoe_chiba_radius`, default `None`: TODO — what this argument means / expected values.
- `itakura_max_slope`, default `None`: TODO — what this argument means / expected values.
- `be`, default `None`: TODO — what this argument means / expected values.

### Input
TODO: the data, file formats, and preconditions the caller must provide.

### Output
Returns `unspecified` — TODO: what the value represents and its format.

### Valid Call Patterns
```python
TODO
```

### LLM Instruction Prompt
- TODO: rules an LLM must follow when calling `python:tslearn.metrics._dtw.dtw`.

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

