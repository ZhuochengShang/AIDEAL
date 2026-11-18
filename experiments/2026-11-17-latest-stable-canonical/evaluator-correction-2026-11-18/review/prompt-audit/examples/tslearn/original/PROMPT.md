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
