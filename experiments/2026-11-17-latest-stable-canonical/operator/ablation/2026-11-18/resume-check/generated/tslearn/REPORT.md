# Fix-loop report — result

_Generated 2026-11-18 10:48 by `aideal fix-report`._

- kind: **comprehension**  ·  run_id: `20261118-173456Z`  ·  models: audience=google:gemini-3.1-flash-lite, fixer=google:gemini-3.1-flash-lite
- pass **231/362** raw (63.8%)  ·  scored **231/354** (65.3%) after excluding 8 infra
- wall 1.23 h  ·  tokens in 911,049 / out 97,318 ·  llm calls 362  ·  max_fix_rounds 0
- pass-by-round: r0:231  ·  **0 rescued by the fix loop** (pass@0 = 231)

## Failure clusters (one issue, many APIs)

_Current failures grouped by normalized error signature (identifiers masked). Fixing the top cluster's root cause pays across all its APIs._

- **12x** [runtime] AttributeError: <name> object has no attribute <name>
  - `python:tslearn.backend.backend.Backend.get_backend`, `python:tslearn.backend.backend.Backend.set_backend`, `python:tslearn.backend.pytorch_backend.PyTorchBackend.iscomplex`, `python:tslearn.backend.pytorch_backend.PyTorchBackend.tril_indices`, `python:tslearn.bases.bases.BaseModelPackage.to_pickle`, `python:tslearn.neighbors.neighbors.KNeighborsTimeSeries.fit`, `python:tslearn.piecewise.piecewise.OneD_SymbolicAggregateApproximation.__sklearn_tags__`, `python:tslearn.piecewise.piecewise.OneD_SymbolicAggregateApproximation.fit`, `python:tslearn.piecewise.piecewise.SymbolicAggregateApproximation.__sklearn_tags__`, `python:tslearn.preprocessing.preprocessing.TimeSeriesScalerMeanVariance.__sklearn_tags__`, `python:tslearn.preprocessing.preprocessing.TimeSeriesScalerMinMax.fit`, `python:tslearn.svm.svm.TimeSeriesSVC.fit`
- **9x** [runtime] AssertionError:
  - `python:tslearn.backend.backend.Backend`, `python:tslearn.early_classification.early_classification.NonMyopicEarlyClassifier`, `python:tslearn.early_classification.early_classification.NonMyopicEarlyClassifier.early_predict_proba`, `python:tslearn.forecasting._arima.compute_var`, `python:tslearn.metrics.sax.cdist_sax`, `python:tslearn.piecewise.piecewise.SymbolicAggregateApproximation.fit`, `python:tslearn.shapelets.shapelets.LearningShapelets.get_weights`, `python:tslearn.svm.svm.TimeSeriesSVC`, `python:tslearn.svm.svm.TimeSeriesSVMMixin.__sklearn_tags__`
- **9x** [api-import] ImportError: cannot import name <name> from <name> (<path>)
  - `python:tslearn.metrics._dtw.accumulated_matrix`, `python:tslearn.metrics._frechet.accumulated_matrix`, `python:tslearn.shapelets.shapelets.GlobalArgminPooling1D`, `python:tslearn.shapelets.shapelets.GlobalArgminPooling1D.compute_output_shape`, `python:tslearn.shapelets.shapelets.GlobalMinPooling1D`, `python:tslearn.shapelets.shapelets.LocalSquaredDistanceLayer.build`, `python:tslearn.shapelets.shapelets.LocalSquaredDistanceLayer.compute_mask`, `python:tslearn.shapelets.shapelets.PatchingLayer.compute_output_shape`, `python:tslearn.shapelets.shapelets.PatchingLayer.get_config`
- **8x** [infra] missing module/import: No module named <name>
  - `python:tslearn.clustering.utils.TimeSeriesCentroidBasedClusteringMixin`, `python:tslearn.forecasting._pipeline.ScaledForecastingPipeline.fit`, `python:tslearn.forecasting._pipeline.ScaledForecastingPipeline.predict`, `python:tslearn.neighbors.neighbors.KNeighborsTimeSeriesMixin`, `python:tslearn.shapelets.shapelets.GlobalMinPooling1D.call`, `python:tslearn.shapelets.shapelets.LocalSquaredDistanceLayer`, `python:tslearn.shapelets.shapelets.PatchingLayer`, `python:tslearn.shapelets.shapelets.PatchingLayer.call`
- **4x** [runtime] TypingError: Failed in nopython mode pipeline (step: nopython frontend)
  - `python:tslearn.metrics.cysax.cydist_1d_sax`, `python:tslearn.metrics.cysax.cydist_sax`, `python:tslearn.metrics.cysax.inv_transform_1d_sax`, `python:tslearn.metrics.cysax.inv_transform_sax`
- **3x** [runtime] TypeError: TimeSeriesFoundationEmbedder.__init__() got an unexpected keyword argument <name>
  - `python:tslearn.foundation._embedding.TimeSeriesFoundationEmbedder.__sklearn_tags__`, `python:tslearn.foundation._embedding.TimeSeriesFoundationEmbedder.fit`, `python:tslearn.foundation._embedding.TimeSeriesFoundationEmbedder.transform`
- **3x** [runtime] TypeError: ZeroShotForecaster.__init__() missing 1 required positional argument: <name>
  - `python:tslearn.foundation._forecasting.ZeroShotForecaster.fit`, `python:tslearn.foundation._forecasting.ZeroShotForecaster.predict`, `python:tslearn.foundation._forecasting._BaseFoundationForecaster.fit_predict`
- **3x** [runtime] TypeError: LocalSquaredDistanceLayer.__init__() missing 1 required positional argument: <name>
  - `python:tslearn.shapelets.shapelets.LocalSquaredDistanceLayer.call`, `python:tslearn.shapelets.shapelets.LocalSquaredDistanceLayer.compute_output_shape`, `python:tslearn.shapelets.shapelets.LocalSquaredDistanceLayer.get_config`
- **2x** [runtime] AssertionError: Expected shape (4, 4), got torch.Size([4, 32, 32])
  - `python:tslearn.backend.pytorch_backend.PyTorchBackend.cdist`, `python:tslearn.backend.pytorch_backend.PyTorchBackend.pairwise_distances`
- **2x** [runtime] TypeError: isinstance() arg 2 must be a type, a tuple of types, or a union
  - `python:tslearn.backend.pytorch_backend.PyTorchBackend.is_float32`, `python:tslearn.backend.pytorch_backend.PyTorchBackend.is_float64`
- **2x** [runtime] TypeError: TimeSeriesDBSCAN.__init__() got an unexpected keyword argument <name>
  - `python:tslearn.clustering.dbscan.TimeSeriesDBSCAN.fit`, `python:tslearn.clustering.dbscan.TimeSeriesDBSCAN.fit_predict`
- **2x** [runtime] TypeError: argument of type <name> is not iterable
  - `python:tslearn.clustering.kmeans.TimeSeriesKMeans.__sklearn_tags__`, `python:tslearn.shapelets.shapelets.LearningShapelets.__sklearn_tags__`

## Why each API fails (131 failing)

### `python:tslearn.backend.backend.Backend` — runtime

- canonical source: `source/tslearn/backend/backend.py:55`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:tslearn.backend.backend.Backend.__getattr__` — runtime

- canonical source: `source/tslearn/backend/backend.py:72`
- last error: TypeError: Backend.__init__() got an unexpected keyword argument 'be'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: Backend.__init__() got an unexpected keyword argument 'be'

### `python:tslearn.backend.backend.Backend.get_backend` — runtime

- canonical source: `source/tslearn/backend/backend.py:84`
- last error: AttributeError: 'TimeSeriesKMeans' object has no attribute 'get_backend'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'TimeSeriesKMeans' object has no attribute 'get_backend'

### `python:tslearn.backend.backend.Backend.set_backend` — runtime

- canonical source: `source/tslearn/backend/backend.py:87`
- last error: AttributeError: 'NumPyBackend' object has no attribute '__name__'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'NumPyBackend' object has no attribute '__name__'

### `python:tslearn.backend.backend.instantiate_backend` — runtime

- canonical source: `source/tslearn/backend/backend.py:7`
- last error: AssertionError: Expected NumPyBackend, got Backend
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected NumPyBackend, got Backend

### `python:tslearn.backend.backend.select_backend` — runtime

- canonical source: `source/tslearn/backend/backend.py:31`
- last error: AssertionError: Expected NumpyBackend, got NumPyBackend
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected NumpyBackend, got NumPyBackend

### `python:tslearn.backend.check_keras_backend` — runtime

- canonical source: `source/tslearn/backend/__init__.py:12`
- last error: AttributeError: module 'tslearn.backend' has no attribute 'get_backend'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: module 'tslearn.backend' has no attribute 'get_backend'

### `python:tslearn.backend.numpy_backend.NumPyBackend.is_float32` — runtime

- canonical source: `source/tslearn/backend/numpy_backend.py:111`
- last error: AssertionError: Expected True for float32 array
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected True for float32 array

### `python:tslearn.backend.numpy_backend.NumPyBackend.to_numpy` — runtime

- canonical source: `source/tslearn/backend/numpy_backend.py:123`
- last error: AssertionError: Result must be a numpy array
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Result must be a numpy array

### `python:tslearn.backend.pytorch_backend.PyTorchBackend.all` — runtime

- canonical source: `source/tslearn/backend/pytorch_backend.py:91`
- last error: AssertionError: Global all() failed to identify all True values
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Global all() failed to identify all True values

### `python:tslearn.backend.pytorch_backend.PyTorchBackend.cdist` — runtime

- canonical source: `source/tslearn/backend/pytorch_backend.py:136`
- last error: AssertionError: Expected shape (4, 4), got torch.Size([4, 32, 32])
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected shape (4, 4), got torch.Size([4, 32, 32])

### `python:tslearn.backend.pytorch_backend.PyTorchBackend.is_float32` — runtime

- canonical source: `source/tslearn/backend/pytorch_backend.py:166` · reached: `source/tslearn/backend/pytorch_backend.py:167`
- last error: TypeError: isinstance() arg 2 must be a type, a tuple of types, or a union
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: isinstance() arg 2 must be a type, a tuple of types, or a union

### `python:tslearn.backend.pytorch_backend.PyTorchBackend.is_float64` — runtime

- canonical source: `source/tslearn/backend/pytorch_backend.py:170` · reached: `source/tslearn/backend/pytorch_backend.py:171`
- last error: TypeError: isinstance() arg 2 must be a type, a tuple of types, or a union
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: isinstance() arg 2 must be a type, a tuple of types, or a union

### `python:tslearn.backend.pytorch_backend.PyTorchBackend.iscomplex` — runtime

- canonical source: `source/tslearn/backend/pytorch_backend.py:154`
- last error: AttributeError: 'bool' object has no attribute 'any'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'bool' object has no attribute 'any'

### `python:tslearn.backend.pytorch_backend.PyTorchBackend.pairwise_distances` — runtime

- canonical source: `source/tslearn/backend/pytorch_backend.py:178`
- last error: AssertionError: Expected shape (4, 4), got torch.Size([4, 32, 32])
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected shape (4, 4), got torch.Size([4, 32, 32])

### `python:tslearn.backend.pytorch_backend.PyTorchBackend.pdist` — runtime

- canonical source: `source/tslearn/backend/pytorch_backend.py:194` · reached: `source/tslearn/backend/pytorch_backend.py:196`
- last error: RuntimeError: pdist only supports 2D tensors, got: 3D
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] RuntimeError: pdist only supports 2D tensors, got: 3D

### `python:tslearn.backend.pytorch_backend.PyTorchBackend.tril_indices` — runtime

- canonical source: `source/tslearn/backend/pytorch_backend.py:222`
- last error: AttributeError: 'tuple' object has no attribute 'shape'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'tuple' object has no attribute 'shape'

### `python:tslearn.bases.bases.BaseModelPackage.to_hdf5` — runtime

- canonical source: `source/tslearn/bases/bases.py:210`
- last error: AssertionError: Saved model missing expected cluster_centers_ key.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Saved model missing expected cluster_centers_ key.

### `python:tslearn.bases.bases.BaseModelPackage.to_json` — runtime

- canonical source: `source/tslearn/bases/bases.py:259`
- last error: AssertionError: Serialized JSON missing cluster_centers_.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Serialized JSON missing cluster_centers_.

### `python:tslearn.bases.bases.BaseModelPackage.to_pickle` — runtime

- canonical source: `source/tslearn/bases/bases.py:307`
- last error: AttributeError: 'dict' object has no attribute 'cluster_centers_'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'dict' object has no attribute 'cluster_centers_'

### `python:tslearn.bases.bases.TsLearnTags` — runtime

- canonical source: `source/tslearn/bases/bases.py:29` · reached: `source/tslearn/bases/bases.py:33`
- last error: TypeError: Tags.__init__() got an unexpected keyword argument 'allow_nan'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: Tags.__init__() got an unexpected keyword argument 'allow_nan'

### `python:tslearn.clustering.dbscan.TimeSeriesDBSCAN.fit` — runtime

- canonical source: `source/tslearn/clustering/dbscan.py:111`
- last error: TypeError: TimeSeriesDBSCAN.__init__() got an unexpected keyword argument 'min_samples'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: TimeSeriesDBSCAN.__init__() got an unexpected keyword argument 'min_samples'

### `python:tslearn.clustering.dbscan.TimeSeriesDBSCAN.fit_predict` — runtime

- canonical source: `source/tslearn/clustering/dbscan.py:195`
- last error: TypeError: TimeSeriesDBSCAN.__init__() got an unexpected keyword argument 'min_samples'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: TimeSeriesDBSCAN.__init__() got an unexpected keyword argument 'min_samples'

### `python:tslearn.clustering.kmeans.TimeSeriesKMeans.__sklearn_tags__` — runtime

- canonical source: `source/tslearn/clustering/kmeans.py:946`
- last error: TypeError: argument of type 'TsLearnTags' is not iterable
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: argument of type 'TsLearnTags' is not iterable

### `python:tslearn.clustering.utils.EmptyClusterError` — runtime

- canonical source: `source/tslearn/clustering/utils.py:20`
- last error: AssertionError: Expected message 'Cluster 0 is empty.', got 'Cluster assignments lead to at least one empty cluster (Cluster 0 is empty.)'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected message 'Cluster 0 is empty.', got 'Cluster assignments lead to at least one empty cluster (Cluster 0 is empty.)'

### `python:tslearn.clustering.utils.TimeSeriesCentroidBasedClusteringMixin` — infra

- canonical source: `source/tslearn/clustering/utils.py:390`
- last error: missing module/import: No module named 'tslearn.base'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [infra] missing module/import: No module named 'tslearn.base'

### `python:tslearn.datasets.datasets.extract_from_zip_url` — runtime

- canonical source: `source/tslearn/datasets/datasets.py:16` · reached: `source/tslearn/datasets/datasets.py:39`
- last error: URLError: <urlopen error [Errno -2] Name or service not known>
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] URLError: <urlopen error [Errno -2] Name or service not known>

### `python:tslearn.datasets.ucr_uea.UCR_UEA_datasets.cache_all` — timeout

- canonical source: `source/tslearn/datasets/ucr_uea.py:377`
- last error: execution timed out
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [timeout] execution timed out

### `python:tslearn.early_classification.early_classification.NonMyopicEarlyClassifier` — runtime

- canonical source: `source/tslearn/early_classification/early_classification.py:18`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:tslearn.early_classification.early_classification.NonMyopicEarlyClassifier.early_predict_proba` — runtime

- canonical source: `source/tslearn/early_classification/early_classification.py:600`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:tslearn.early_classification.early_classification.NonMyopicEarlyClassifier.fit` — runtime

- canonical source: `source/tslearn/early_classification/early_classification.py:130`
- last error: AssertionError: NonMyopicEarlyClassifier failed to set internal state after fit.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: NonMyopicEarlyClassifier failed to set internal state after fit.

### `python:tslearn.early_classification.early_classification.NonMyopicEarlyClassifier.get_cluster_probas` — runtime

- canonical source: `source/tslearn/early_classification/early_classification.py:215` · reached: `source/tslearn/early_classification/early_classification.py:172`
- last error: ValueError: Found input variables with inconsistent numbers of samples: [4, 4, 2]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Found input variables with inconsistent numbers of samples: [4, 4, 2]

### `python:tslearn.early_classification.early_classification.NonMyopicEarlyClassifier.predict_proba` — runtime

- canonical source: `source/tslearn/early_classification/early_classification.py:491`
- last error: AssertionError: Expected shape (8, 2), got (8, 4)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected shape (8, 2), got (8, 4)

### `python:tslearn.forecasting._arima.AutoVARIMA.__sklearn_tags__` — runtime

- canonical source: `source/tslearn/forecasting/_arima.py:793`
- last error: AssertionError: Expected 'requires_y' tag to be present in TsLearnTags(estimator_type=None, target_tags=TargetTags(required=False, one_d_labels=False, two_d_labels=False, positive_only=False, multi_output=False, single_output=True), transformer_tags=None, classifier_tags=None, regressor_tags=None, a
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected 'requires_y' tag to be present in TsLearnTags(estimator_type=None, target_tags=TargetTags(required=False, one_d_labels=False,

### `python:tslearn.forecasting._arima.AutoVARIMA.fit` — runtime

- canonical source: `source/tslearn/forecasting/_arima.py:537`
- last error: AssertionError: AutoVARIMA failed to store the fitted model object.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: AutoVARIMA failed to store the fitted model object.

### `python:tslearn.forecasting._arima.AutoVARIMA.predict` — runtime

- canonical source: `source/tslearn/forecasting/_arima.py:595`
- last error: TypeError: AutoVARIMA.__init__() got an unexpected keyword argument 'sp'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: AutoVARIMA.__init__() got an unexpected keyword argument 'sp'

### `python:tslearn.forecasting._arima.VARIMA.fit` — runtime

- canonical source: `source/tslearn/forecasting/_arima.py:182`
- last error: AssertionError: VARIMA model should have a 'model_' attribute after fitting.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: VARIMA model should have a 'model_' attribute after fitting.

### `python:tslearn.forecasting._arima.VARIMA.fit_predict` — runtime

- canonical source: `source/tslearn/forecasting/_arima.py:433`
- last error: TypeError: VARIMA.__init__() got an unexpected keyword argument 'maxiter'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: VARIMA.__init__() got an unexpected keyword argument 'maxiter'

### `python:tslearn.forecasting._arima.VARIMA.predict` — runtime

- canonical source: `source/tslearn/forecasting/_arima.py:353`
- last error: TypeError: VARIMA.__init__() got an unexpected keyword argument 'maxiter'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: VARIMA.__init__() got an unexpected keyword argument 'maxiter'

### `python:tslearn.forecasting._arima.compute_var` — runtime

- canonical source: `source/tslearn/forecasting/_arima.py:21`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:tslearn.forecasting._pipeline.ScaledForecastingPipeline.fit` — infra

- canonical source: `source/tslearn/forecasting/_pipeline.py:117`
- last error: missing module/import: No module named 'tslearn.forecasting.sarimax'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [infra] missing module/import: No module named 'tslearn.forecasting.sarimax'

### `python:tslearn.forecasting._pipeline.ScaledForecastingPipeline.fit_predict` — runtime

- canonical source: `source/tslearn/forecasting/_pipeline.py:179` · reached: `source/tslearn/forecasting/_pipeline.py:196`, `source/tslearn/forecasting/_pipeline.py:139`
- last error: TypeError: LinearRegression.fit() missing 1 required positional argument: 'y'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: LinearRegression.fit() missing 1 required positional argument: 'y'

### `python:tslearn.forecasting._pipeline.ScaledForecastingPipeline.predict` — infra

- canonical source: `source/tslearn/forecasting/_pipeline.py:142`
- last error: missing module/import: No module named 'tslearn.forecasting.tf_utils'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [infra] missing module/import: No module named 'tslearn.forecasting.tf_utils'

### `python:tslearn.foundation._embedding.TimeSeriesFoundationEmbedder.__sklearn_tags__` — runtime

- canonical source: `source/tslearn/foundation/_embedding.py:569`
- last error: TypeError: TimeSeriesFoundationEmbedder.__init__() got an unexpected keyword argument 'pretrained_model'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: TimeSeriesFoundationEmbedder.__init__() got an unexpected keyword argument 'pretrained_model'

### `python:tslearn.foundation._embedding.TimeSeriesFoundationEmbedder.fit` — runtime

- canonical source: `source/tslearn/foundation/_embedding.py:490`
- last error: TypeError: TimeSeriesFoundationEmbedder.__init__() got an unexpected keyword argument 'pretrained_model'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: TimeSeriesFoundationEmbedder.__init__() got an unexpected keyword argument 'pretrained_model'

### `python:tslearn.foundation._embedding.TimeSeriesFoundationEmbedder.fit_transform` — runtime

- canonical source: `source/tslearn/foundation/_embedding.py:551`
- last error: TypeError: TimeSeriesFoundationEmbedder.__init__() missing 1 required positional argument: 'model'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: TimeSeriesFoundationEmbedder.__init__() missing 1 required positional argument: 'model'

### `python:tslearn.foundation._embedding.TimeSeriesFoundationEmbedder.transform` — runtime

- canonical source: `source/tslearn/foundation/_embedding.py:521`
- last error: TypeError: TimeSeriesFoundationEmbedder.__init__() got an unexpected keyword argument 'model_name'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: TimeSeriesFoundationEmbedder.__init__() got an unexpected keyword argument 'model_name'

### `python:tslearn.foundation._forecasting.LinearProbeForecaster` — runtime

- canonical source: `source/tslearn/foundation/_forecasting.py:515` · reached: `source/tslearn/foundation/_forecasting.py:752`, `source/tslearn/foundation/_embedding.py:567`, `source/tslearn/foundation/_embedding.py:515`
- last error: IndexError: too many indices for tensor of dimension 2
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IndexError: too many indices for tensor of dimension 2

### `python:tslearn.foundation._forecasting.LinearProbeForecaster.fit` — runtime

- canonical source: `source/tslearn/foundation/_forecasting.py:732`
- last error: TypeError: LinearProbeForecaster.__init__() got an unexpected keyword argument 'pretrained_model'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: LinearProbeForecaster.__init__() got an unexpected keyword argument 'pretrained_model'

### `python:tslearn.foundation._forecasting.LinearProbeForecaster.predict` — runtime

- canonical source: `source/tslearn/foundation/_forecasting.py:761`
- last error: TypeError: LinearProbeForecaster.__init__() got an unexpected keyword argument 'pretrained_model'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: LinearProbeForecaster.__init__() got an unexpected keyword argument 'pretrained_model'

### `python:tslearn.foundation._forecasting.LinearProbeForecaster.score` — runtime

- canonical source: `source/tslearn/foundation/_forecasting.py:806`
- last error: TypeError: LinearProbeForecaster.__init__() missing 1 required positional argument: 'model'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: LinearProbeForecaster.__init__() missing 1 required positional argument: 'model'

### `python:tslearn.foundation._forecasting.ZeroShotForecaster.fit` — runtime

- canonical source: `source/tslearn/foundation/_forecasting.py:432`
- last error: TypeError: ZeroShotForecaster.__init__() missing 1 required positional argument: 'model'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: ZeroShotForecaster.__init__() missing 1 required positional argument: 'model'

### `python:tslearn.foundation._forecasting.ZeroShotForecaster.predict` — runtime

- canonical source: `source/tslearn/foundation/_forecasting.py:455`
- last error: TypeError: ZeroShotForecaster.__init__() missing 1 required positional argument: 'model'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: ZeroShotForecaster.__init__() missing 1 required positional argument: 'model'

### `python:tslearn.foundation._forecasting._BaseFoundationForecaster.__sklearn_tags__` — runtime

- canonical source: `source/tslearn/foundation/_forecasting.py:247`
- last error: TypeError: ZeroShotForecaster.__init__() got an unexpected keyword argument 'pretrained_model'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: ZeroShotForecaster.__init__() got an unexpected keyword argument 'pretrained_model'

### `python:tslearn.foundation._forecasting._BaseFoundationForecaster.fit_predict` — runtime

- canonical source: `source/tslearn/foundation/_forecasting.py:228`
- last error: TypeError: ZeroShotForecaster.__init__() missing 1 required positional argument: 'model'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: ZeroShotForecaster.__init__() missing 1 required positional argument: 'model'

### `python:tslearn.hdftools.hdftools.load_dict` — runtime

- canonical source: `source/tslearn/hdftools/hdftools.py:118`
- last error: TypeError: save_dict() missing 1 required positional argument: 'group'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: save_dict() missing 1 required positional argument: 'group'

### `python:tslearn.matrix_profile.matrix_profile.MatrixProfile.__sklearn_tags__` — runtime

- canonical source: `source/tslearn/matrix_profile/matrix_profile.py:259`
- last error: TypeError: object of type 'TsLearnTags' has no len()
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: object of type 'TsLearnTags' has no len()

### `python:tslearn.matrix_profile.matrix_profile.MatrixProfile.fit` — runtime

- canonical source: `source/tslearn/matrix_profile/matrix_profile.py:138`
- last error: TypeError: MatrixProfile.__init__() got an unexpected keyword argument 'window_size'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: MatrixProfile.__init__() got an unexpected keyword argument 'window_size'

### `python:tslearn.metrics._dtw.accumulated_matrix` — api-import

- canonical source: `source/tslearn/metrics/_dtw.py:286`
- last error: ImportError: cannot import name 'accumulated_matrix' from 'tslearn.metrics' (/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable/lib64/python3.12/site-packages/tslearn/metrics/__init__.py)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [api-import] ImportError: cannot import name 'accumulated_matrix' from 'tslearn.metrics' (/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable/lib64/python3.12

### `python:tslearn.metrics._frechet.accumulated_matrix` — api-import

- canonical source: `source/tslearn/metrics/_frechet.py:288`
- last error: ImportError: cannot import name 'accumulated_matrix' from 'tslearn.metrics' (/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable/lib64/python3.12/site-packages/tslearn/metrics/__init__.py)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [api-import] ImportError: cannot import name 'accumulated_matrix' from 'tslearn.metrics' (/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable/lib64/python3.12

### `python:tslearn.metrics._soft_dtw.cdist_soft_dtw` — runtime

- canonical source: `source/tslearn/metrics/_soft_dtw.py:738`
- last error: AssertionError: Soft-DTW values must be non-negative
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Soft-DTW values must be non-negative

### `python:tslearn.metrics.cycc.cdist_normalized_cc` — runtime

- canonical source: `source/tslearn/metrics/cycc.py:54`
- last error: AssertionError: Distance values out of expected range [0, 2]
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Distance values out of expected range [0, 2]

### `python:tslearn.metrics.cysax.cydist_1d_sax` — runtime

- canonical source: `source/tslearn/metrics/cysax.py:123` · reached: `source/tslearn/metrics/cysax.py:164`
- last error: TypingError: Failed in nopython mode pipeline (step: nopython frontend)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypingError: Failed in nopython mode pipeline (step: nopython frontend)

### `python:tslearn.metrics.cysax.cydist_sax` — runtime

- canonical source: `source/tslearn/metrics/cysax.py:38` · reached: `source/tslearn/metrics/cysax.py:71`
- last error: TypingError: Failed in nopython mode pipeline (step: nopython frontend)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypingError: Failed in nopython mode pipeline (step: nopython frontend)

### `python:tslearn.metrics.cysax.cyslopes` — runtime

- canonical source: `source/tslearn/metrics/cysax.py:106`
- last error: AssertionError: Calculated slope 0.001562498123827392 does not match expected 0.0023023076923076903
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Calculated slope 0.001562498123827392 does not match expected 0.0023023076923076903

### `python:tslearn.metrics.cysax.inv_transform_1d_sax` — runtime

- canonical source: `source/tslearn/metrics/cysax.py:177` · reached: `source/tslearn/metrics/cysax.py:207`
- last error: TypingError: Failed in nopython mode pipeline (step: nopython frontend)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypingError: Failed in nopython mode pipeline (step: nopython frontend)

### `python:tslearn.metrics.cysax.inv_transform_sax` — runtime

- canonical source: `source/tslearn/metrics/cysax.py:78` · reached: `source/tslearn/metrics/cysax.py:100`
- last error: TypingError: Failed in nopython mode pipeline (step: nopython frontend)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypingError: Failed in nopython mode pipeline (step: nopython frontend)

### `python:tslearn.metrics.dtw_variants.dtw_limited_warping_length` — runtime

- canonical source: `source/tslearn/metrics/dtw_variants.py:159`
- last error: AssertionError: Expected distance 0.0 for identical series, got 0.271990249089926
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected distance 0.0 for identical series, got 0.271990249089926

### `python:tslearn.metrics.sax.cdist_sax` — runtime

- canonical source: `source/tslearn/metrics/sax.py:10` · reached: `source/tslearn/metrics/sax.py:74`, `source/tslearn/metrics/sax.py:96`, `source/tslearn/barycenters/utils.py:179`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:tslearn.metrics.softdtw_variants.SoftDTW.compute` — runtime

- canonical source: `source/tslearn/metrics/softdtw_variants.py:696`
- last error: TypeError: SoftDTW.__init__() got multiple values for argument 'gamma'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: SoftDTW.__init__() got multiple values for argument 'gamma'

### `python:tslearn.metrics.softdtw_variants.SoftDTW.grad` — runtime

- canonical source: `source/tslearn/metrics/softdtw_variants.py:722`
- last error: AssertionError: Gradient sum should be 1.0, got 4.163457887752244
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Gradient sum should be 1.0, got 4.163457887752244

### `python:tslearn.metrics.softdtw_variants.SquaredEuclidean` — runtime

- canonical source: `source/tslearn/metrics/softdtw_variants.py:761`
- last error: TypeError: SquaredEuclidean.compute() takes 1 positional argument but 3 were given
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: SquaredEuclidean.compute() takes 1 positional argument but 3 were given

### `python:tslearn.metrics.softdtw_variants.SquaredEuclidean.compute` — runtime

- canonical source: `source/tslearn/metrics/softdtw_variants.py:793` · reached: `source/tslearn/metrics/softdtw_variants.py:801`
- last error: ValueError: Found array with dim 3, while dim <= 2 is required by check_pairwise_arrays.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Found array with dim 3, while dim <= 2 is required by check_pairwise_arrays.

### `python:tslearn.metrics.softdtw_variants.SquaredEuclidean.jacobian_product` — runtime

- canonical source: `source/tslearn/metrics/softdtw_variants.py:803`
- last error: TypeError: SquaredEuclidean.__init__() missing 2 required positional arguments: 'X' and 'Y'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: SquaredEuclidean.__init__() missing 2 required positional arguments: 'X' and 'Y'

### `python:tslearn.metrics.softdtw_variants.cdist_soft_dtw` — runtime

- canonical source: `source/tslearn/metrics/softdtw_variants.py:338`
- last error: AssertionError: Soft-DTW distances must be non-negative
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Soft-DTW distances must be non-negative

### `python:tslearn.metrics.softdtw_variants.soft_dtw` — runtime

- canonical source: `source/tslearn/metrics/softdtw_variants.py:91`
- last error: AssertionError: Soft-DTW similarity (squared Euclidean) should be non-negative
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Soft-DTW similarity (squared Euclidean) should be non-negative

### `python:tslearn.metrics.softdtw_variants.soft_dtw_alignment` — runtime

- canonical source: `source/tslearn/metrics/softdtw_variants.py:208`
- last error: AssertionError: Similarity should be non-negative, got -65.99491371336846
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Similarity should be non-negative, got -65.99491371336846

### `python:tslearn.neighbors.neighbors.KNeighborsTimeSeries.fit` — runtime

- canonical source: `source/tslearn/neighbors/neighbors.py:330`
- last error: AttributeError: 'KNeighborsTimeSeries' object has no attribute 'data_fit_'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'KNeighborsTimeSeries' object has no attribute 'data_fit_'

### `python:tslearn.neighbors.neighbors.KNeighborsTimeSeriesClassifier.fit` — runtime

- canonical source: `source/tslearn/neighbors/neighbors.py:553`
- last error: AssertionError: Stored training data shape mismatch
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Stored training data shape mismatch

### `python:tslearn.neighbors.neighbors.KNeighborsTimeSeriesMixin` — infra

- canonical source: `source/tslearn/neighbors/neighbors.py:28`
- last error: missing module/import: No module named 'tslearn.base'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [infra] missing module/import: No module named 'tslearn.base'

_… 51 more failing APIs omitted (--max-api-detail to raise)._

**Infra failures excluded from doc-quality scoring (8):** `python:tslearn.clustering.utils.TimeSeriesCentroidBasedClusteringMixin`, `python:tslearn.forecasting._pipeline.ScaledForecastingPipeline.fit`, `python:tslearn.forecasting._pipeline.ScaledForecastingPipeline.predict`, `python:tslearn.neighbors.neighbors.KNeighborsTimeSeriesMixin`, `python:tslearn.shapelets.shapelets.GlobalMinPooling1D.call`, `python:tslearn.shapelets.shapelets.LocalSquaredDistanceLayer`, `python:tslearn.shapelets.shapelets.PatchingLayer`, `python:tslearn.shapelets.shapelets.PatchingLayer.call`
