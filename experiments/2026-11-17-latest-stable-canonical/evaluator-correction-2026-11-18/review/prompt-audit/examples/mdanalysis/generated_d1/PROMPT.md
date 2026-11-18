# Recorded system prompt

You write Python code that will be spliced into a runnable test harness.
A runnable headless Python test harness is already in scope. The snippet is inserted inside a function and the preamble variables listed under available inputs are already defined. Write executable statements only. Import MDAnalysis submodules or optional dependencies only when the documented public call requires them. Do not define another function or process entry point. Assert a deterministic property and print a compact correctness witness containing a shape, scalar, or length.

Requested target declaration (frozen canonical selection):
Qualified name: MDAnalysis.lib.distances.calc_bonds
Owner: 
Declaration: def calc_bonds(coords1: Union[npt.NDArray, 'AtomGroup'], coords2: Union[npt.NDArray, 'AtomGroup'], box: Optional[npt.NDArray]=None, result: Optional[npt.NDArray]=None, backend: str='serial')
Parameters in declaration order (5): coords1: Union[npt.NDArray, 'AtomGroup']; coords2: Union[npt.NDArray, 'AtomGroup']; box: Optional[npt.NDArray]; result: Optional[npt.NDArray]; backend: str
Write the requested call against this owner and declaration, with its indicated parameter list.
Verified public access paths for the same defining API: MDAnalysis.analysis.atomicdistances.calc_bonds, MDAnalysis.analysis.bat.calc_bonds, MDAnalysis.analysis.distances.calc_bonds, MDAnalysis.analysis.dssp.pydssp_numpy.calc_bonds, MDAnalysis.analysis.hydrogenbonds.hbond_autocorrel.calc_bonds, MDAnalysis.analysis.nucleicacids.calc_bonds, MDAnalysis.analysis.polymer.calc_bonds, MDAnalysis.lib.distances.calc_bonds. Use a public access path when the defining namespace is internal.

Pick the input variable(s) whose type matches the API's parameters. Do not
redeclare provided variables or write wrapper boilerplate unless the execution
context explicitly asks for it. Output ONLY the body statements that exercise the
API. Use ONLY the documentation provided. Output only code, no markdown fences.

Role: an expert molecular-simulation researcher and scientific Python engineer using MDAnalysis for reproducible trajectory and structure analysis.
Project: MDAnalysis (Python) - MDAnalysis 2.11.0, an object-oriented scientific Python library for reading molecular structures and trajectories, selecting atoms, transforming coordinates, and running molecular-dynamics analyses.
Domain: Molecular-dynamics trajectory and structural analysis in Python, including topology/coordinate I/O, atom selections, geometric measurements, trajectory transformations, and reusable analysis algorithms.
Target users: computational chemists and molecular-simulation researchers; scientific Python developers analyzing proteins and materials
Use cases: Load a topology and trajectory into a Universe and select atoms.; Compute structural properties such as centers of mass and radii of gyration.; Iterate over trajectory frames and analyze changing coordinates.; Run RMSD, distance, contact, and other MDAnalysis.analysis workflows.
Constraints: A Universe owns topology and trajectory state.; AtomGroup methods operate on selected atoms at the current trajectory frame.; Analysis classes generally require construction followed by run().; Use only the five read-only fixture copies byte-verified against pinned MDAnalysisTests 2.11.0: PSF, DCD, PDB, GRO, and XTC; never substitute downloaded data.; The PSF/DCD pair is preloaded for general trajectory analysis; format-specific APIs may use the matching PDB, GRO, or XTC in mdanalysis_fixture_dir. That directory contains exactly these five approved fixtures.; Some readers and converters require optional dependencies; a missing optional package is an infrastructure outcome, not evidence that the documentation is wrong.; The adk_dims.dcd trajectory has no periodic box dimensions; use a checked-in periodic fixture when an API requires periodic boundaries.; Do not download data, invoke a GUI, or write large trajectories.; Use every name in the frozen 435-name canonical manifest without sampling; selection is structural filtering and same-name maximum arity, not a proof of arbitrary semantic equivalence.; Treat the shared fixture directory as read-only. Create any temporary or output files only in output_dir. Source-checkout fixture paths are not execution inputs.

# Recorded user prompt

Documentation:
## API Test: `python:MDAnalysis.lib.distances.calc_bonds`

### Signature
```python
def calc_bonds(coords1: Union[npt.NDArray, 'AtomGroup'], coords2: Union[npt.NDArray, 'AtomGroup'], box: Optional[npt.NDArray]=None, result: Optional[npt.NDArray]=None, backend: str='serial')
```
_Source: source/package/MDAnalysis/lib/distances.py:1678_

_Source doc:_ Calculates the bond lengths between pairs of atom positions from the two
coordinate arrays `coords1` and `coords2`, which must contain the same
number of coordinates. ``coords1[i]`` and ``coords2[i]`` represent the
positions of atoms connected by the ``i``-th bond. If single coordinates are
supplied, a single distance will be returned.

In comparison to :meth:`distance_array` and :meth:`self_distance_array`,
which calculate distances between all possible combinations of coordinates,
:meth:`calc_bonds` only calculates distances between pairs of coordinates,
similar to::

   numpy.linalg.norm(a - b) for a, b in zip(coords1, coords2)

If the optional argument `box` is supplied, the minimum image convention is
applied when calculating distances. Either orthogonal or triclinic boxes are
supported.

If a numpy array of dtype ``numpy.float64`` with shape ``(n,)`` (for ``n``
coordinate pairs) is provided in `result`, then this preallocated array is
filled. This can speed up calculations.

Parameters
----------
coords1 : numpy.ndarray or :class:`~MDAnalysis.core.groups.AtomGroup`
    Coordinate array of shape ``(3,)`` or ``(n, 3)`` for one half of a
    single or ``n`` bonds, respectively (dtype is arbitrary, will be
    converted to ``numpy.float32`` internally).  Also accepts an
    :class:`~MDAnalysis.core.groups.AtomGroup`.
coords2 : numpy.ndarray or :class:`~MDAnalysis.core.groups.AtomGroup`
    Coordinate array of shape ``(3,)`` or ``(n, 3)`` for the other half of
    a single or ``n`` bonds, respectively (dtype is arbitrary, will be
    converted to ``numpy.float32`` internally). Also accepts an
    :class:`~MDAnalysis.core.groups.AtomGroup`.
box : numpy.ndarray, optional
    The unitcell dimensions of the system, which can be orthogonal or
    triclinic and must be provided in the same format as returned by
    :attr:`MDAnalysis.coordinates.timestep.Timestep.dimensions`:
    ``[lx, ly, lz, alpha, beta, gamma]``.
result : numpy.ndarray, optional
    Preallocated result array of dtype ``numpy.float64`` and shape ``(n,)``
    (for ``n`` coordinate pairs). Avoids recreating the array in repeated
    function calls.
backend : {'serial', 'OpenMP', 'distopia'}, optional
    Keyword selecting the type of acceleration. Defaults to 'serial'.

Returns
-------
bondlengths : numpy.ndarray (``dtype=numpy.float64``, ``shape=(n,)``) or
    numpy.float64 Array containing the bond lengths between each pair of
    coordinates. If two single coordinates were supplied, their distance is
    returned as a single number instead of an array.


.. versionadded:: 0.8
.. versionchanged:: 0.13.0
   Added *backend* keyword.
.. versionchanged:: 0.19.0
   Internal dtype conversion of input coordinates to ``numpy.float32``.
   Now also accepts single coordinates as input.
.. versionchanged:: 2.3.0
   Can now accept an :class:`~MDAnalysis.core.groups.AtomGroup` as an
   argument in any position and checks inputs using type hinting.
.. versionchanged:: 2.5.0
   Can now optionally use the fast distance functions from distopia

### Goal
Calculates the Euclidean distances between corresponding pairs of atoms or coordinate points, optionally applying periodic boundary conditions.

### Parameters
- `coords1` (`Union[npt.NDArray, 'AtomGroup']`): Coordinate array of shape `(3,)` or `(n, 3)` representing the first set of points.
- `coords2` (`Union[npt.NDArray, 'AtomGroup']`): Coordinate array of shape `(3,)` or `(n, 3)` representing the second set of points. Must have the same number of coordinates as `coords1`.
- `box` (`Optional[npt.NDArray]`), default `None`: Unit cell dimensions `[lx, ly, lz, alpha, beta, gamma]` used to apply the minimum image convention.
- `result` (`Optional[npt.NDArray]`), default `None`: A preallocated `numpy.float64` array of shape `(n,)` to store the output, improving performance in iterative workflows.
- `backend` (`str`), default `'serial'`: Acceleration backend to use; options are `'serial'`, `'OpenMP'`, or `'distopia'`.

### Input
- `coords1` and `coords2` must contain the same number of coordinates.
- If `box` is provided, it must match the format of `Timestep.dimensions`.
- Inputs are internally converted to `numpy.float32` for calculation.

### Output
Returns `npt.NDArray` — A `numpy.float64` array of shape `(n,)` containing the calculated bond lengths. If single coordinates were provided, returns a single `numpy.float64` scalar.

### Valid Call Patterns
```python
# Inferred from signature:
import MDAnalysis.lib.distances as dists
bond_lengths = dists.calc_bonds(ag1, ag2, box=u.dimensions)
```

### LLM Instruction Prompt
- Always ensure `coords1` and `coords2` have the same number of elements.
- If performing analysis over a trajectory, use the `result` parameter with a preallocated array to optimize performance.
- If periodic boundary conditions are required, ensure the `box` parameter is provided using the `Universe.dimensions` attribute.

### Prompt Snippet
```text
Use MDAnalysis.lib.distances.calc_bonds(coords1, coords2, box=None, result=None, backend='serial') to compute pairwise distances between two sets of coordinates.
```

### Common Failure Modes
- Providing `coords1` and `coords2` with mismatched lengths, which raises a `ValueError`.
- Providing a `box` array with incorrect dimensions or format (must be 6 elements).
- Passing a `result` array with an incorrect shape or `dtype` (must be `float64`).

### Fix Code Hint
```python
# Ensure inputs are aligned and box is provided for PBC
import numpy as np
n_bonds = len(ag1)
result_array = np.zeros(n_bonds, dtype=np.float64)
dists = MDAnalysis.lib.distances.calc_bonds(ag1, ag2, box=u.dimensions, result=result_array)
```

Available input path variables already in scope (choose the matching one(s) by type):
Pre-loaded and already in scope — use these directly, do NOT re-load:
- MDAnalysis: module
- numpy: module
- universe: MDAnalysis.Universe
- atoms: MDAnalysis.core.groups.AtomGroup
- protein: MDAnalysis.core.groups.AtomGroup
- backbone: MDAnalysis.core.groups.AtomGroup
- trajectory: MDAnalysis.coordinates.base.ReaderBase
- timestep: MDAnalysis.coordinates.base.Timestep
(raw input path strings also in scope if needed: psf_path, dcd_path, pdb_path, gro_path, xtc_path, mdanalysis_fixture_dir, output_dir)

RECEIVER — call `python:MDAnalysis.lib.distances.calc_bonds` on the RIGHT type (calling it on the wrong receiver is
the #1 failure; if it is an instance method, first obtain a value of the owner type,
do NOT call it on an unrelated preloaded input):
(receiver type not resolved)

(none yet)

Write minimal body statements that use `python:MDAnalysis.lib.distances.calc_bonds` correctly per the docs,
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
  `__CHECK__ python:MDAnalysis.lib.distances.calc_bonds ` followed by the witness, using the language's normal
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
materialize `python:MDAnalysis.lib.distances.calc_bonds`, but deliberately fail the assertion with a short message
stating that the documented contract is insufficient to verify the result. This is
a documentation-comprehension test: an unverifiable contract must not earn a pass.
If `python:MDAnalysis.lib.distances.calc_bonds` is itself a writer/output API, use an output binding only when one
is listed among the available inputs or execution context; then read back a small
part of the output, assert a known content/aggregate relation when the documented
contract permits it, and print the same structured line.
Do not call other heavyweight operations unless `python:MDAnalysis.lib.distances.calc_bonds` is the writer; keep the
body focused on `python:MDAnalysis.lib.distances.calc_bonds` so the run isolates that one call.
Use the preloaded Universe, AtomGroups, trajectory, and the pinned molecular fixture paths. Keep atom selections and frame ranges small. For analysis classes construct the documented class, call run() when required, and validate a stable scalar, shape, or length. The PSF/DCD pair has no periodic box; use a matching configured periodic fixture only when the target contract requires it. Write any small output only under output_dir; do not modify source fixtures, download data, or open a GUI.
