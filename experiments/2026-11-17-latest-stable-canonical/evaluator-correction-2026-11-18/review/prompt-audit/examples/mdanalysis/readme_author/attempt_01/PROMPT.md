# Recorded author system prompt

You write LLM-facing API documentation in an exact markdown template.
You ground every fact in the provided API facts and context. You NEVER invent
parameters, types, return values, or APIs that are not given. If something is
unknown, say so rather than guessing.

Role: an expert molecular-simulation researcher and scientific Python engineer using MDAnalysis for reproducible trajectory and structure analysis.
Project: MDAnalysis (Python) - MDAnalysis 2.11.0, an object-oriented scientific Python library for reading molecular structures and trajectories, selecting atoms, transforming coordinates, and running molecular-dynamics analyses.
Domain: Molecular-dynamics trajectory and structural analysis in Python, including topology/coordinate I/O, atom selections, geometric measurements, trajectory transformations, and reusable analysis algorithms.
Target users: computational chemists and molecular-simulation researchers; scientific Python developers analyzing proteins and materials
Use cases: Load a topology and trajectory into a Universe and select atoms.; Compute structural properties such as centers of mass and radii of gyration.; Iterate over trajectory frames and analyze changing coordinates.; Run RMSD, distance, contact, and other MDAnalysis.analysis workflows.
Constraints: A Universe owns topology and trajectory state.; AtomGroup methods operate on selected atoms at the current trajectory frame.; Analysis classes generally require construction followed by run().; Use only the five read-only fixture copies byte-verified against pinned MDAnalysisTests 2.11.0: PSF, DCD, PDB, GRO, and XTC; never substitute downloaded data.; The PSF/DCD pair is preloaded for general trajectory analysis; format-specific APIs may use the matching PDB, GRO, or XTC in mdanalysis_fixture_dir. That directory contains exactly these five approved fixtures.; Some readers and converters require optional dependencies; a missing optional package is an infrastructure outcome, not evidence that the documentation is wrong.; The adk_dims.dcd trajectory has no periodic box dimensions; use a checked-in periodic fixture when an API requires periodic boundaries.; Do not download data, invoke a GUI, or write large trajectories.; Use every name in the frozen 435-name canonical manifest without sampling; selection is structural filtering and same-name maximum arity, not a proof of arbitrary semantic equivalence.; Treat the shared fixture directory as read-only. Create any temporary or output files only in output_dir. Source-checkout fixture paths are not execution inputs.

# Recorded author user prompt

Document the Python function `python:MDAnalysis.lib.distances.calc_bonds` of MDAnalysis.

Authoritative API facts (JSON — do not contradict; do not add parameters or
types that are not listed here):
```json
{
  "name": "python:MDAnalysis.lib.distances.calc_bonds",
  "signature": "def calc_bonds(coords1: Union[npt.NDArray, 'AtomGroup'], coords2: Union[npt.NDArray, 'AtomGroup'], box: Optional[npt.NDArray]=None, result: Optional[npt.NDArray]=None, backend: str='serial')",
  "params": [
    {
      "name": "coords1",
      "type": "Union[npt.NDArray, 'AtomGroup']",
      "default": null,
      "required": true,
      "kind": "positional_or_keyword"
    },
    {
      "name": "coords2",
      "type": "Union[npt.NDArray, 'AtomGroup']",
      "default": null,
      "required": true,
      "kind": "positional_or_keyword"
    },
    {
      "name": "box",
      "type": "Optional[npt.NDArray]",
      "default": "None",
      "required": false,
      "kind": "positional_or_keyword"
    },
    {
      "name": "result",
      "type": "Optional[npt.NDArray]",
      "default": "None",
      "required": false,
      "kind": "positional_or_keyword"
    },
    {
      "name": "backend",
      "type": "str",
      "default": "'serial'",
      "required": false,
      "kind": "positional_or_keyword"
    }
  ],
  "returns": "npt.NDArray",
  "source_doc": "Calculates the bond lengths between pairs of atom positions from the two\ncoordinate arrays `coords1` and `coords2`, which must contain the same\nnumber of coordinates. ``coords1[i]`` and ``coords2[i]`` represent the\npositions of atoms connected by the ``i``-th bond. If single coordinates are\nsupplied, a single distance will be returned.\n\nIn comparison to :meth:`distance_array` and :meth:`self_distance_array`,\nwhich calculate distances between all possible combinations of coordinates,\n:meth:`calc_bonds` only calculates distances between pairs of coordinates,\nsimilar to::\n\n   numpy.linalg.norm(a - b) for a, b in zip(coords1, coords2)\n\nIf the optional argument `box` is supplied, the minimum image convention is\napplied when calculating distances. Either orthogonal or triclinic boxes are\nsupported.\n\nIf a numpy array of dtype ``numpy.float64`` with shape ``(n,)`` (for ``n``\ncoordinate pairs) is provided in `result`, then this preallocated array is\nfilled. This can speed up calculations.\n\nParameters\n----------\ncoords1 : numpy.ndarray or :class:`~MDAnalysis.core.groups.AtomGroup`\n    Coordinate array of shape ``(3,)`` or ``(n, 3)`` for one half of a\n    single or ``n`` bonds, respectively (dtype is arbitrary, will be\n    converted to ``numpy.float32`` internally).  Also accepts an\n    :class:`~MDAnalysis.core.groups.AtomGroup`.\ncoords2 : numpy.ndarray or :class:`~MDAnalysis.core.groups.AtomGroup`\n    Coordinate array of shape ``(3,)`` or ``(n, 3)`` for the other half of\n    a single or ``n`` bonds, respectively (dtype is arbitrary, will be\n    converted to ``numpy.float32`` internally). Also accepts an\n    :class:`~MDAnalysis.core.groups.AtomGroup`.\nbox : numpy.ndarray, optional\n    The unitcell dimensions of the system, which can be orthogonal or\n    triclinic and must be provided in the same format as returned by\n    :attr:`MDAnalysis.coordinates.timestep.Timestep.dimensions`:\n    ``[lx, ly, lz, alpha, beta, gamma]``.\nresult : numpy.ndarray, optional\n    Preallocated result array of dtype ``numpy.float64`` and shape ``(n,)``\n    (for ``n`` coordinate pairs). Avoids recreating the array in repeated\n    function calls.\nbackend : {'serial', 'OpenMP', 'distopia'}, optional\n    Keyword selecting the type of acceleration. Defaults to 'serial'.\n\nReturns\n-------\nbondlengths : numpy.ndarray (``dtype=numpy.float64``, ``shape=(n,)``) or\n    numpy.float64 Array containing the bond lengths between each pair of\n    coordinates. If two single coordinates were supplied, their distance is\n    returned as a single number instead of an array.\n\n\n.. versionadded:: 0.8\n.. versionchanged:: 0.13.0\n   Added *backend* keyword.\n.. versionchanged:: 0.19.0\n   Internal dtype conversion of input coordinates to ``numpy.float32``.\n   Now also accepts single coordinates as input.\n.. versionchanged:: 2.3.0\n   Can now accept an :class:`~MDAnalysis.core.groups.AtomGroup` as an\n   argument in any position and checks inputs using type hinting.\n.. versionchanged:: 2.5.0\n   Can now optionally use the fast distance functions from distopia",
  "overloads": [],
  "api_id": "python:MDAnalysis.lib.distances.calc_bonds",
  "display_name": "calc_bonds",
  "identity_version": "language_qualified_api_v1",
  "parameter_count": 5,
  "parameter_count_status": "declared",
  "exposure_ids": [
    "python:MDAnalysis.analysis.atomicdistances.calc_bonds",
    "python:MDAnalysis.analysis.bat.calc_bonds",
    "python:MDAnalysis.analysis.distances.calc_bonds",
    "python:MDAnalysis.analysis.dssp.pydssp_numpy.calc_bonds",
    "python:MDAnalysis.analysis.hydrogenbonds.hbond_autocorrel.calc_bonds",
    "python:MDAnalysis.analysis.nucleicacids.calc_bonds",
    "python:MDAnalysis.analysis.polymer.calc_bonds",
    "python:MDAnalysis.lib.distances.calc_bonds"
  ],
  "preferred_public_path": "MDAnalysis.analysis.bat.calc_bonds",
  "public_access_paths": [
    "MDAnalysis.analysis.atomicdistances.calc_bonds",
    "MDAnalysis.analysis.bat.calc_bonds",
    "MDAnalysis.analysis.distances.calc_bonds",
    "MDAnalysis.analysis.dssp.pydssp_numpy.calc_bonds",
    "MDAnalysis.analysis.hydrogenbonds.hbond_autocorrel.calc_bonds",
    "MDAnalysis.analysis.nucleicacids.calc_bonds",
    "MDAnalysis.analysis.polymer.calc_bonds",
    "MDAnalysis.lib.distances.calc_bonds"
  ],
  "qualified_name": "MDAnalysis.lib.distances.calc_bonds",
  "source": {
    "file": "source/package/MDAnalysis/lib/distances.py",
    "line": 1678,
    "site_id": "Python:mdanalysis:package/MDAnalysis/lib/distances.py:66122:function:calc_bonds"
  },
  "definition_sites": [
    {
      "signature": "def calc_bonds(coords1: Union[npt.NDArray, 'AtomGroup'], coords2: Union[npt.NDArray, 'AtomGroup'], box: Optional[npt.NDArray]=None, result: Optional[npt.NDArray]=None, backend: str='serial')",
      "qualified_name": "MDAnalysis.lib.distances.calc_bonds",
      "source": {
        "file": "source/package/MDAnalysis/lib/distances.py",
        "line": 1678,
        "site_id": "Python:mdanalysis:package/MDAnalysis/lib/distances.py:66122:function:calc_bonds"
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
===== Original documentation part 1/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library designed for the analysis of molecular dynamics (MD) trajectories and structural data. It provides a robust framework for loading topologies and trajectories, performing geometric measurements, calculating structural properties, and executing complex analysis workflows (e.g., RMSD, contacts, dihedral angles, and density maps) in a reproducible manner.

### 2. Main workflows
*   **Universe Management:** Loading topology and trajectory files into a `Universe` object, which serves as the central container for simulation state.
*   **Coordinate Alignment:** Superimposing structures or trajectories onto a reference frame using RMSD minimization (QCP algorithm).
*   **Trajectory Analysis:** Iterating over frames to compute time-series data (e.g., contacts, dihedrals, distances).
*   **Volumetric Analysis:** Generating 3D density grids from atom selections and exporting them to formats like OpenDX.
*   **Parallel Execution:** Leveraging `multiprocessing` or `dask` backends to distribute frame-based analysis tasks across multiple CPU cores.
*   **Custom Analysis:** Extending `AnalysisBase` to create new, reusable analysis tools that integrate with the library's progress bars, frame selection, and parallelization infrastructure.

### 3. Important APIs and usage patterns
*   **`Universe(topology, trajectory)`**: The primary entry point for loading simulation data.
*   **`AnalysisBase`**: The base class for all multi-frame analysis tools. Subclasses must implement `_single_frame()` and optionally `_prepare()` and `_conclude()`.
*   **`results` attribute**: All analysis classes store output in a `Results` container (a dictionary-like object accessible via attributes).
*   **`run()` method**: Executes the analysis. Supports `start`, `stop`, `step`, and `frames` (list of indices or boolean masks) for trajectory slicing, and `backend` for parallelization.
*   **`AtomGroup`**: The core object for selecting and manipulating atoms. Methods like `select_atoms()` and `center_of_mass()` operate on the current trajectory frame.

### 4. Inputs and file formats
*   **Topology/Trajectory:** Supports standard formats including PSF, DCD, PDB, GRO, and XTC.
*   **Sequence Alignment:** FASTA files for residue mapping via `fasta2select()`.
*   **Volumetric Data:** Exports to OpenDX (.dx), MRC/CCP4, and OpenVDB formats.
*   **Numpy Binary:** Used for saving/loading BAT coordinates and distance matrices.

### 5. Outputs and generated artifacts
*   **Time Series:** Stored in `results.timeseries` or specific attributes like `results.rmsd`, `results.angles`, or `results.bat`.
*   **Volumetric Grids:** `Density` objects containing 3D arrays, grid edges, and metadata.
*   **Transformation Matrices:** Rotation matrices for coordinate alignment.

### 6. Configuration and environment assumptions
*   **Dependencies:** Requires `numpy`. Optional dependencies include `dask` (for parallelization) and `Biopython` (for sequence alignment).
*   **Periodic Boundaries:** Many analyses (e.g., `AtomicDistances`, `Contacts`) default to using PBC.
*   **Parallelization:** Parallel backends (`multiprocessing`, `dask`) require the analysis class to be marked as parallelizable.

### 7. Commands and examples

**RMS-fitting a trajectory:**
```python
import MDAnalysis as mda
from MDAnalysis.analysis import align
from MDAnalysis.tests.datafiles import PSF, DCD, PDB_small

ref = mda.Universe(PSF, PDB_small)
trj = mda.Universe(PSF, DCD)
alignment = align.AlignTraj(trj, ref, filename='rmsfit.dcd')
alignment.run()
```

**Calculating native contacts:**
```python
import MDAnalysis as mda
from MDAnalysis.analysis import contacts
from MDAnalysis.tests.datafiles import PSF, DCD

u = mda.Universe(PSF, DCD)
sel_basic = "(resname ARG LYS) and (name NH* NZ)"
sel_acidic = "(resname ASP GLU) and (name OE* OD*)"
acidic = u.select_atoms(sel_acidic)
basic = u.select_atoms(sel_basic)

ca1 = contacts.Contacts(u, select=(sel_acidic, sel_basic),
                        refgroup=(acidic, basic), radius=6.0)
ca1.run()
```

**Generating a density map:**
```python
from MDAnalysis.analysis.density import DensityAnalysis
u = mda.Universe(TPR, XTC)
ow = u.select_atoms("name OW")
D = DensityAnalysis(ow, delta=1.0)
D.run()
D.results.density.export("water.dx", type="double")
```

### 8. Constraints, preconditions, compatibility rules
*   **Universe Ownership:** A `Universe` owns the topology and trajectory state.
*   **AtomGroup Ordering:** `alignto()` and `get_matching_atoms()` require careful handling of atom ordering; using `select='all'` preserves order, while other selections sort by index.
*   **Parallelization:** Custom analysis classes must implement `get_supported_backends()` and ensure `_single_frame()` is thread-safe/process-safe.
*   **Preconditions:** Trajectories for density analysis must be centered, made whole, and remapped to the solute reference frame before processing.

### 9. Facts to preserve in the final README
*   MDAnalysis 2.11.0 is an object-oriented library for molecular simulation analysis.
*   Analysis classes follow a consistent `instantiate -> run() -> access results` pattern.
*   Results are stored in `AnalysisBase.results` (a `Results` object).
*   Parallel execution is supported via `run(backend='dask'|'multiprocessing')`.
*   The library provides extensive support for coordinate fitting, contact analysis, dihedral calculations, and volumetric density generation.

### 10. Missing or weak documentation
*   The `fasta2select` function documentation lacks detailed examples for complex residue numbering scenarios.
*   The `Density` object's algebraic manipulation capabilities are mentioned but lack explicit examples of unit-safe arithmetic.
*   The distinction between `results.timeseries` and specific result attributes (like `results.rmsd`) is inconsistent across older vs. newer analysis classes.

===== Original documentation part 2/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library designed for the analysis of molecular dynamics (MD) trajectories and structural data. It provides tools for I/O, atom selection, coordinate transformations, and a suite of reusable analysis algorithms for structural and dynamical properties.

### 2. Main workflows
*   **Trajectory Analysis:** Loading a `Universe` (topology + trajectory), performing atom selections, and iterating over frames to compute properties.
*   **Structural Analysis:** Computing distances, contact matrices, secondary structure assignment (DSSP), and elastic network models (GNM).
*   **Ensemble Comparison:** Comparing structural ensembles using similarity measures (HES, CES, DRES), clustering, and dimensionality reduction (PCA, SPE).
*   **Hydrogen Bond Analysis:** Identifying hydrogen bonds based on geometric criteria and calculating their lifetimes and autocorrelation functions.
*   **Parallelization:** Utilizing `serial`, `multiprocessing`, or `dask` backends for computationally intensive analysis tasks.

### 3. Important APIs and usage patterns
*   **`Universe`:** The central object owning topology and trajectory state.
*   **`AnalysisBase`:** The base class for analysis algorithms. Workflows typically follow a `Constructor -> run() -> results` pattern.
*   **`run()`:** The primary method for executing analysis. Supports `start`, `stop`, `step`, `frames` (for slicing), and `backend` (for parallelization).
*   **`results`:** An attribute on analysis instances containing computed data (e.g., `results.angles`, `results.dssp`, `results.eigenvalues`).
*   **`get_supported_backends()`:** A class method to query available parallel backends.

### 4. Inputs and file formats
*   **Topology/Trajectory:** Supports standard formats like PSF, DCD, PDB, GRO, XTC, TPR, and PRMTOP.
*   **Selections:** Uses MDAnalysis selection strings (e.g., `'name CA'`, `'resname TIP3'`).
*   **Distance Matrices:** Often represented as `encore.utils.TriangularMatrix` for memory efficiency.

### 5. Outputs and generated artifacts
*   **Numerical Data:** NumPy arrays (e.g., contact matrices, distance arrays, eigenvectors).
*   **Metadata:** Dictionaries or objects (e.g., `ClusterCollection`, `solution` dicts for H-bond autocorrelation).
*   **Files:** Optional output files for vectors or matrices (e.g., `ReportVector` in GNM, `save_matrix` in ENCORE).

### 6. Configuration and environment assumptions
*   **Dependencies:** Some modules (e.g., `dask`, `scikit-learn`) are optional and must be installed separately.
*   **Topology:** Accurate bond information in the topology file is critical for identifying donor-hydrogen pairs in H-bond analysis.
*   **Parallelization:** `n_workers` and `n_parts` control parallel execution; `unsupported_backend=True` is required for custom backends on non-standard classes.

### 7. Commands and examples

**Secondary Structure Assignment (DSSP):**
```python
from MDAnalysis.analysis.dssp import DSSP
import MDAnalysis as mda
from MDAnalysis.tests.datafiles import PDB
u = mda.Universe(PDB)
run = DSSP(u).run()
print("".join(run.results.dssp[0, :20]))
```

**Hydrogen Bond Analysis:**
```python
from MDAnalysis.analysis.hydrogenbonds.hbond_analysis import HydrogenBondAnalysis as HBA
import MDAnalysis
u = MDAnalysis.Universe(psf, trajectory)
hbonds = HBA(universe=u)
hbonds.run()
```

**Ensemble Similarity (HES):**
```python
from MDAnalysis import Universe
import MDAnalysis.analysis.encore as encore
from MDAnalysis.tests.datafiles import PSF, DCD, DCD2
ens1 = Universe(PSF, DCD)
ens2 = Universe(PSF, DCD2)
HES, details = encore.hes([ens1, ens2])
print(HES)
```

**Distance Array Calculation:**
```python
from MDAnalysis.analysis.distances import distance_array
d = distance_array(ref_atoms, conf_atoms, box=box)
```

### 8. Constraints, preconditions, compatibility rules
*   **Universe Ownership:** A `Universe` owns the topology and trajectory; analysis classes operate on these.
*   **Parallelization:** Only classes with `parallelizable=True` support non-serial backends.
*   **H-Bond Preconditions:** `hydrogens` and `donors` selections must be aligned (index-matched). If topology lacks bond info, use `guess_bonds()` or `d_h_cutoff`.
*   **Deprecation:** The `encore` module is deprecated in favor of the `mdaencore` MDAKit and will be removed in 3.0.0.
*   **DSSP:** Requires at least 6 protein residues. Prolines are explicitly excluded from the H-bond network.

### 9. Facts to preserve in the final README
*   MDAnalysis 2.11.0 is the target version.
*   The library is object-oriented and designed for reproducibility.
*   Analysis classes follow the `run()` pattern.
*   Parallelization is integrated via the `backend` keyword in `run()`.
*   The `encore` module is deprecated.

### 10. Missing or weak documentation
*   Specific performance benchmarks for different backends (`dask` vs `multiprocessing`) are not detailed.
*   The exact behavior of `unsupported_backend=True` for user-defined backends lacks extensive examples.
*   Some legacy modules (e.g., `encore`) have limited documentation on migration paths to newer MDAKits.

===== Original documentation part 3/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library designed for the analysis of molecular dynamics (MD) trajectories and structural data. It provides tools for I/O, atom selection, coordinate transformations, and a suite of reusable analysis algorithms (e.g., RMSD, RDF, PCA, hydrogen bonding, and polymer analysis).

### 2. Main workflows
*   **Trajectory Analysis:** Load a `Universe` (topology + trajectory), select atoms, and iterate over frames to compute properties.
*   **Analysis Classes:** Most analyses follow a pattern: instantiate the class with a `Universe` or `AtomGroup`, configure parameters, call `.run()`, and access results via the `.results` attribute.
*   **Parallelization:** Many analysis classes support parallel execution via `run(backend=...)` (e.g., 'multiprocessing', 'dask').
*   **Trajectory Transformations:** Apply on-the-fly transformations (e.g., `NoJump`) to trajectories before analysis.

### 3. Important APIs and usage patterns
*   **`Universe`:** The central object owning topology and trajectory state.
*   **`AnalysisBase`:** The base class for analysis algorithms.
*   **`results`:** A container (similar to `sklearn.utils.Bunch`) for storing analysis output. Access via `results.attribute` or `results['attribute']`.
*   **`run()`:** The standard method to execute calculations. Supports `start`, `stop`, `step`, `frames` (for slicing), and `backend` (for parallelization).
*   **`get_supported_backends()`:** Class method to check available parallel backends.

### 4. Inputs and file formats
*   **Topology/Trajectory:** Supports standard formats (PSF, DCD, PDB, GRO, XTC).
*   **Selections:** Uses MDAnalysis selection strings (e.g., `"backbone"`, `"name CA"`, `"resid 1-29"`).
*   **Weights:** Many analyses (RMSD, RDF) accept `weights` (e.g., `"mass"` or custom arrays).

### 5. Outputs and generated artifacts
*   **`results` attribute:** Stores data as `numpy.ndarray` or other structures.
*   **Legacy Aliases:** Many attributes (e.g., `results.rmsd`) have deprecated aliases (e.g., `rmsd`) slated for removal in 3.0.0.
*   **Visualization:** Some classes provide `.plot()` methods (e.g., `PersistenceLength`, `X3DNA`).

### 6. Configuration and environment assumptions
*   **Dependencies:** Some features require optional packages (e.g., `networkx` for `LeafletFinder`, `tidynamics` for `EinsteinMSD` with `fft=True`).
*   **Parallelization:** Requires `mdanalysis[dask]` for the 'dask' backend.
*   **Periodic Boundaries:** Many analyses (e.g., `EinsteinMSD`, `InterRDF`) require handling PBCs (e.g., using `NoJump` or ensuring molecules are "whole").

### 7. Commands and examples
**RMSD Analysis:**
```python
import MDAnalysis
from MDAnalysis.analysis.rms import RMSD
u = MDAnalysis.Universe(PSF, DCD)
R = RMSD(u, select="backbone")
R.run()
print(R.results.rmsd)
```

**Hydrogen Bond Analysis:**
```python
from MDAnalysis.analysis.hydrogenbonds import HydrogenBondAnalysis
hbonds = HydrogenBondAnalysis(u)
hbonds.run()
print(hbonds.results.hbonds)
```

**PCA Analysis:**
```python
from MDAnalysis.analysis.pca import PCA
pca = PCA(u, select='backbone').run()
pca_space = pca.transform(u.select_atoms('backbone'), n_components=3)
```

**Polymer Persistence Length:**
```python
from MDAnalysis.analysis import polymer
sorted_backbones = [polymer.sort_backbone(chain.select_atoms('not name O* H*')) for chain in u.atoms.fragments]
persistence_length = polymer.PersistenceLength(sorted_backbones).run()
print(persistence_length.results.lp)
```

### 8. Constraints, preconditions, compatibility rules
*   **Universe Ownership:** A `Universe` owns the topology and trajectory.
*   **AtomGroup Methods:** Operate on the current trajectory frame.
*   **Unwrapped Coordinates:** `EinsteinMSD` requires unwrapped (no-jump) coordinates.
*   **Residue Names:** Nucleic acid analysis (e.g., `WatsonCrickDist`) matches residue names exactly; multi-character names (e.g., "GUA") must be passed via keyword arguments.
*   **Parallelization:** Only classes with `parallelizable=True` support non-serial backends.

### 9. Facts to preserve in the final README
*   MDAnalysis 2.11.0 is the target version.
*   `results` objects are the standard for data access.
*   Deprecated attributes (e.g., `results.rdf` vs `rdf`) will be removed in 3.0.0.
*   Parallel backends ('serial', 'multiprocessing', 'dask') are available for most analysis classes.

### 10. Missing or weak documentation
*   `X3DNA` is marked as legacy/unmaintained and difficult to test.
*   `optimize_cutoff` in `LeafletFinder` is noted as potentially unstable.
*   Some density units in `LinearDensity` are subject to change.
*   `RMSF` documentation lacks explicit examples of the required structural alignment.

===== Original documentation part 4/13 =====
### 1. Project purpose
MDAnalysis (version 2.11.0) is an object-oriented Python library designed for the analysis of molecular dynamics (MD) trajectories and structural data. It provides tools for reading/writing various file formats, selecting atoms, performing geometric measurements, and executing reusable analysis algorithms.

### 2. Main workflows
*   **Universe Initialization:** Loading topology and trajectory files into a `Universe` object.
*   **Atom Selection:** Filtering atoms using selection strings (e.g., `"protein"`, `"name CA"`).
*   **Trajectory Transformation:** Applying on-the-fly coordinate transformations (e.g., `unwrap`, `center_in_box`) via `u.trajectory.add_transformations()`.
*   **Analysis Execution:** Instantiating analysis classes (e.g., `RMSF`, `WaterBridgeAnalysis`), configuring parameters, and calling `.run()`.
*   **Auxiliary Data Integration:** Attaching non-trajectory time-series data (e.g., energies from `.edr` or `.xvg` files) to trajectory frames.
*   **Format Conversion:** Converting between MDAnalysis structures and external objects (e.g., `ParmEd`, `RDKit`, `OpenMM`).

### 3. Important APIs and usage patterns
*   **`Universe`:** The central object owning topology and trajectory state.
*   **`AnalysisBase`:** The base class for analysis algorithms. Workflows follow a `Class(universe, ...).run()` pattern.
*   **`run()` method:** The standard interface for executing analysis. Supports parallelization via `backend` (e.g., `'serial'`, `'multiprocessing'`, `'dask'`).
*   **`AtomGroup`:** A collection of atoms. Methods operate on the current trajectory frame.
*   **`add_auxiliary()`:** Attaches external data to a trajectory, accessible via `ts.aux`.
*   **`convert_to()`:** Method on `AtomGroup` or `Universe` to export data to external libraries.

### 4. Inputs and file formats
*   **Topology/Coordinates:** PSF, DCD, PDB, GRO, XTC, CRD, DLPoly (Config/History), DMS, FHI-AIMS.
*   **Auxiliary Data:** EDR (GROMACS binary), XVG (Grace format).
*   **External Objects:** OpenMM (`Topology`, `Simulation`, `Modeller`), ParmEd (`Structure`), RDKit (`Mol`).

### 5. Outputs and generated artifacts
*   **Analysis Results:** Stored in `results` attributes (e.g., `results.rmsf`, `results.timeseries`, `results.network`).
*   **Data Tables:** Generated via methods like `generate_table()` (e.g., for `WaterBridgeAnalysis`).
*   **Converted Objects:** Native objects from RDKit, ParmEd, or OpenMM.

### 6. Configuration and environment assumptions
*   **Dependencies:** Some readers/converters require optional packages (e.g., `pyedr` for EDR, `mdanalysis[dask]` for parallelization).
*   **Units:** MDAnalysis uses Ångström (length), ps (time), and AKMA (time for DCD) as base units. Converters provide `units` dictionaries for native-to-base unit mapping.
*   **Memory:** Large trajectories may require `in_memory=True` or writing intermediate files.

### 7. Commands and examples

**RMSF Calculation:**
```python
from MDAnalysis.analysis.rms import RMSF
calphas = protein.select_atoms("name CA")
rmsfer = RMSF(calphas, verbose=True).run()
plt.plot(calphas.resnums, rmsfer.results.rmsf)
```

**Water Bridge Analysis:**
```python
from MDAnalysis.analysis.hydrogenbonds import WaterBridgeAnalysis
w = WaterBridgeAnalysis(u, 'resname ARG', 'resname ASP')
w.run()
# Access results
print(w.results.timeseries)
```

**Adding Auxiliary Data:**
```python
u.trajectory.add_auxiliary({"epot": "Potential", "angle": "Angle"}, aux)
# Access via ts.aux
print(u.trajectory.ts.aux.epot)
```

**Trajectory Transformations:**
```python
import MDAnalysis.transformations as trans
transforms = [trans.unwrap(protein), trans.center_in_box(protein, wrap=True)]
u.trajectory.add_transformations(*transforms)
```

### 8. Constraints, preconditions, compatibility rules
*   **Universe:** A `Universe` owns the topology and trajectory.
*   **Parallelization:** Only classes with `parallelizable=True` support non-serial backends.
*   **DCD:** The DCD format is not strictly defined; unit cell conventions (NAMD vs. CHARMM) may vary.
*   **RDKit:** The converter requires `Elements` and `Bonds` attributes. Hydrogens should be explicit.
*   **Auxiliary Data:** Assumed to be time-ordered with no duplicates.

### 9. Facts to preserve in the final README
*   MDAnalysis 2.11.0 is object-oriented and supports complex trajectory transformations.
*   The `AnalysisBase` API provides a consistent interface for parallelized analysis.
*   Extensive support for interoperability with RDKit, ParmEd, and OpenMM.
*   Auxiliary data readers (EDR, XVG) allow integration of energy/pressure data into trajectory analysis.

### 10. Missing or weak documentation
*   The DCD unit cell convention is noted as "not well defined," requiring user caution.
*   The `RDKitConverter` is explicitly labeled as "experimental."
*   Some legacy attributes (e.g., `timeseries`, `network`) are deprecated in favor of `results.*` attributes.
*   The `WaterBridgeAnalysis` documentation notes that default atom names for force fields may require customization for non-standard ligands.

===== Original documentation part 5/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library for the analysis of molecular dynamics (MD) trajectories and structural data. It provides a unified interface for reading/writing various file formats, selecting atoms, performing geometric measurements, and managing trajectory transformations.

### 2. Main workflows
*   **Universe Initialization:** Load topology and trajectory files into a `Universe` object.
*   **Trajectory Iteration:** Iterate through frames to perform analysis or coordinate transformations.
*   **Auxiliary Data:** Attach time-series data (e.g., energy, pull forces) to a trajectory for filtering or analysis.
*   **Coordinate Transformation:** Apply transformations to `Timestep` objects during iteration.
*   **Streaming Analysis:** Connect to live simulations via the IMD protocol for real-time monitoring.
*   **Parallel I/O:** Utilize MPI-IO for H5MD files.

### 3. Important APIs and usage patterns
*   **`MDAnalysis.Universe(topology, trajectory, ...)`**: The central object managing topology and trajectory state.
*   **`AtomGroup`**: Represents a selection of atoms. Methods operate on the current trajectory frame.
*   **`trajectory.add_auxiliary(...)`**: Attaches external data to the trajectory.
*   **`trajectory.add_transformations(...)`**: Registers functions to modify `Timestep` objects on-the-fly.
*   **`timeseries(...)`**: Extracts coordinate data for an `AtomGroup` into a NumPy array.
*   **`Writer`**: Used for exporting trajectories or frames.

### 4. Inputs and file formats
*   **FHI-AIMS:** `FHIAIMSReader` / `FHIAIMSWriter` (geometry, positions, velocities).
*   **GAMESS:** `GMSReader` (output files, supports compressed `.bz2`/`.gz`).
*   **GROMACS:** `GROReader` / `GROWriter` (structure files).
*   **HOOMD-blue:** `GSDReader` (topology and trajectory).
*   **H5MD:** `H5MDReader` / `H5MDWriter` (HDF5-based, supports parallel I/O).
*   **IMD:** `IMDReader` (streaming protocol v3).
*   **Amber:** `INPReader` (restart files).
*   **LAMMPS:** `DCDReader` / `DCDWriter` (binary trajectories), `DATAReader` (data files).

### 5. Outputs and generated artifacts
*   Trajectory files (e.g., `.h5md`, `.gro`, `.dcd`).
*   NumPy arrays via `timeseries()`.
*   Auxiliary data stored in `ts.aux`.

### 6. Configuration and environment assumptions
*   **Dependencies:** H5MD requires `h5py` and optionally `mpi4py` for parallel features. IMD requires `imdclient`.
*   **Units:** MDAnalysis uses base units (typically Å for length, ps for time). Readers/Writers handle conversion; users can override via `timeunit`, `lengthunit`, etc.
*   **Memory:** Streaming readers (IMD) do not support random access or rewinding.

### 7. Commands and examples
**Loading a Universe with auxiliary data:**
```python
u = MDAnalysis.Universe(PDB, XTC)
u.trajectory.add_auxiliary('pull', 'pull-force.xvg')
# Access via:
# u.trajectory.ts.aux.pull
```

**Applying trajectory transformations:**
```python
u = MDAnalysis.Universe(topology, coordinates)
workflow = [some_transform, another_transform, this_transform]
u.trajectory.add_transformations(*workflow)
```

**Writing a subset of a Universe to GRO:**
```python
u = mda.Universe()
u.atoms.write('out.gro', reindex=False)
```

**Streaming IMD data:**
```python
import MDAnalysis as mda
u = mda.Universe("topol.tpr", "imd://localhost:8889")
for ts in u.trajectory:
    print(f'{ts.time:8.3f} {ts.positions[0]}')
```

### 8. Constraints, preconditions, compatibility rules
*   **Universe:** Owns topology and trajectory state.
*   **Fixed Particles:** Most readers (e.g., GSD, H5MD) assume a fixed number of particles per frame.
*   **Streaming:** IMD readers do not support `rewind()`, `copy()`, or `timeseries()`.
*   **GRO:** Precision is hard-coded to 3 decimal places for positions.
*   **H5MD:** Requires `h5py`. Parallel writing is not supported.
*   **Type Selection:** Use `AtomGroup` or `Universe` as input for `write()` methods; `Timestep` support is deprecated.

### 9. Facts to preserve in the final README
*   MDAnalysis 2.11.0 is the target version.
*   `FHIAIMSWriter` format strings are stored in `fmt` dictionary.
*   `GROWriter` renumbers atom IDs by default; use `reindex=False` to preserve original IDs.
*   H5MD chunking defaults to `(1, n_atoms, 3)` for performance.
*   IMDReader requires `imdclient` and is forward-only.

### 10. Missing or weak documentation
*   Direct `h5py.File` usage in `Universe` is noted as not working (Issue #2884).
*   GMSReader lacks a rigid format definition; users may need to tweak it.
*   Lennard-Jones units are not implemented for LAMMPS.
*   Parallel writing for H5MD is not supported.

===== Original documentation part 6/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library for the analysis of molecular dynamics (MD) trajectories and structural data. It provides a unified interface for reading various file formats, selecting atoms, performing geometric calculations, and managing trajectory transformations.

### 2. Main workflows
*   **Universe Initialization:** Loading topology and trajectory files into a `Universe` object.
*   **Trajectory Iteration:** Stepping through frames using `next()` or direct indexing (`u.trajectory[i]`).
*   **Auxiliary Data Integration:** Attaching non-coordinate time-series data (e.g., energy, pull forces) to the trajectory for filtering or analysis.
*   **Coordinate Transformations:** Applying custom or built-in transformations to `Timestep` objects during iteration.
*   **Data Export:** Writing selections or full trajectories to various formats (PDB, LAMMPS, etc.).

### 3. Important APIs and usage patterns
*   **`Universe(topology, coordinates)`**: The primary container for system state.
*   **`trajectory.add_auxiliary(...)`**: Attaches external data files (e.g., `.xvg`, `.edr`) to the trajectory.
*   **`trajectory.add_transformations(*transformations)`**: Registers a pipeline of functions to modify coordinates on-the-fly.
*   **`AtomGroup.write(filename)`**: Exports selected atoms to a file.
*   **`Writer(filename, ...)`**: Context manager for writing multi-frame trajectories.
*   **`timeseries(...)`**: Extracts coordinate data for an `AtomGroup` into a NumPy array.

### 4. Inputs and file formats
*   **Supported Formats:** PDB, MMCIF, MOL2, NAMDBIN, PDBQT, PQR, TNG, TRC, AMBER (NCDF/TRJ).
*   **Compression:** Many readers (e.g., PDB, PDBQT, TRC) support transparent reading of `.gz` and `.bz2` files.
*   **Metadata:** Readers handle unit cell dimensions (CRYST1 in PDB/PDBQT, TRC blocks, NCDF periodic info).

### 5. Outputs and generated artifacts
*   **Coordinate Files:** PDB, MOL2, NAMDBIN, PDBQT, PQR, NCDF.
*   **Auxiliary Data:** Stored in `ts.aux` namespace.
*   **Transformations:** Applied to `Timestep` objects; modifications are reflected in subsequent analysis.

### 6. Configuration and environment assumptions
*   **Units:** MDAnalysis uses internal base units (typically Å for length, ps for time). Readers handle conversion from native units (e.g., LAMMPS "real" units, AMBER kcal/mol).
*   **Dependencies:** Some formats require optional packages (e.g., `gemmi` for MMCIF, `pytng` for TNG, `scipy` for NCDF).
*   **Memory:** `NCDFReader` supports `mmap=True` for memory-efficient access.

### 7. Commands and examples
**Adding auxiliary data:**
```python
u = MDAnalysis.Universe(PDB, XTC)
u.trajectory.add_auxiliary('pull', 'pull-force.xvg')
# Access via:
# u.trajectory.ts.aux.pull
```

**Adding trajectory transformations:**
```python
u = MDAnalysis.Universe(topology, coordinates)
workflow = [some_transform, another_transform, this_transform]
u.trajectory.add_transformations(*workflow)
```

**Writing a multi-frame PDB:**
```python
calphas = universe.select_atoms("name CA")
with MDAnalysis.Writer("calpha_traj.pdb", multiframe=True) as W:
    for ts in u.trajectory:
        W.write(calphas)
```

**Reading additional columns from LAMMPS dump:**
```python
u = mda.Universe('structure.data', 'traj.lammpsdump',
                 additional_columns=['q', 'l'])
for ts in u.trajectory:
    charges = ts.data['q']
```

### 8. Constraints, preconditions, compatibility rules
*   **Transformations:** `add_transformations` can only be called once per `Universe` lifecycle.
*   **PDB Writing:** Writing bonds (CONECT records) is only supported when writing a whole `Universe` with existing topology bond information.
*   **PDBQT/PQR:** These formats are whitespace-delimited; strict column alignment is not required, but whitespace separation is mandatory.
*   **TNG:** Currently read-only; no writer implementation exists.
*   **AMBER TRJ:** Does not contain time information; defaults to 1 ps per frame unless `dt` is provided.
*   **Slice Indices:** `check_slice_indices` follows `range()` conventions; caution is required when using `stop=None` and `step=-1`.

### 9. Facts to preserve in the final README
*   MDAnalysis is object-oriented and uses a `Universe` to manage topology and trajectory.
*   Trajectory readers are extensible via the `add_auxiliary` and `add_transformations` APIs.
*   The library handles unit conversions automatically based on the file format's native units.
*   Multi-frame writing is supported for formats like PDB and NCDF.

### 10. Missing or weak documentation
*   **TNG Writer:** Documentation notes that no writer is currently implemented.
*   **AMBER TRJ:** Support is labeled "experimental."
*   **PDB/PDBQT:** Specifics on handling of `altLoc` and `iCode` are inconsistent across readers.
*   **Slice Discrepancy:** The warning regarding `check_slice_indices` behavior with `slice(start, stop, step)` vs `range()` is critical but complex for users to implement correctly.

===== Original documentation part 7/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library designed for the analysis of molecular dynamics (MD) trajectories and structural data. It provides a unified interface for reading/writing various trajectory formats, performing coordinate transformations, and managing auxiliary data streams.

### 2. Main workflows
*   **Trajectory Loading:** Initialize a `Universe` with a topology and trajectory file.
*   **Data Access:** Iterate through trajectory frames, access coordinates via `Timestep` objects, or extract bulk coordinate data using `timeseries()`.
*   **Auxiliary Data Integration:** Attach external time-series data (e.g., energy, forces) to a trajectory to filter frames or perform correlated analysis.
*   **Coordinate Transformation:** Apply custom transformation functions to `Timestep` objects during iteration.
*   **Trajectory Writing:** Export processed coordinates to supported formats using `Writer` classes.

### 3. Important APIs and usage patterns
*   **`Universe`:** The central object owning topology and trajectory state.
*   **`Reader` classes:** Handle I/O for specific formats (e.g., `XTCReader`, `TRRReader`, `TRJReader`, `XYZReader`).
*   **`Timestep`:** Represents the state of the system at a specific frame.
*   **`add_auxiliary()`:** Attaches external data to the trajectory.
*   **`add_transformations()`:** Registers a list of functions to modify `Timestep` objects on-the-fly.
*   **`timeseries()`:** Extracts coordinate data for an `AtomGroup` into a NumPy array.
*   **`check_slice_indices()`:** Validates and clips frame indices for slicing.

### 4. Inputs and file formats
*   **Supported Formats:** AMBER TRJ (ASCII), GROMACS TRR (lossless, supports velocities/forces), GROMACS XTC (compressed), IBIsCO/YASP TRZ (binary, little-endian), Tinker TXYZ/ARC, and XYZ (VMD-compatible).
*   **Auxiliary Data:** Supports `AuxReader` instances or files (e.g., `.xvg`, `.edr`).
*   **Units:** MDAnalysis uses base units (length: nm, time: ps, velocity: nm/ps, force: kJ/(mol*nm)). Readers handle conversion from native format units.

### 5. Outputs and generated artifacts
*   **Trajectory Files:** Written via `Writer` classes (e.g., `TRRWriter`, `XTCWriter`, `XYZWriter`).
*   **Offset Files:** XDR-based readers (XTC/TRR) generate hidden `*_offsets.npz` files to enable efficient random access.
*   **Data Arrays:** Extracted via `timeseries()` or `ts.aux` attributes.

### 6. Configuration and environment assumptions
*   **Offsets:** XDR readers require write access to the directory to cache offsets. If unavailable, offsets are rebuilt on every load.
*   **Dependencies:** Some readers require optional dependencies; missing packages are treated as infrastructure outcomes.
*   **Byte Order:** TRZ trajectories are strictly read/written in little-endian byte order.

### 7. Commands and examples

**Loading and adding auxiliary data:**
```python
u = MDAnalysis.Universe(PDB, XTC)
u.trajectory.add_auxiliary('pull', 'pull-force.xvg')
# Accessing auxiliary data
print(u.trajectory.ts.aux.pull)
```

**Applying transformations:**
```python
u = MDAnalysis.Universe(topology, coordinates)
workflow = [some_transform, another_transform, this_transform]
u.trajectory.add_transformations(*workflow)
```

**Filtering frames based on auxiliary data:**
```python
term_dict = {"temp": "Temperature", "epot": "Potential"}
u.trajectory.add_auxiliary(term_dict, "ener.edr")
selected_frames = np.array([ts.frame for ts in u.trajectory
                            if ts.aux.epot < some_threshold])
subset = u.trajectory[selected_frames]
```

**Extracting a timeseries:**
```python
# Returns array of shape (frame, number of atoms, coordinates)
data = u.trajectory.timeseries(atomgroup=u.select_atoms("protein"), order="fac")
```

### 8. Constraints, preconditions, compatibility rules
*   **`n_atoms`:** For formats like AMBER TRJ, `n_atoms` must be explicitly provided to the constructor.
*   **Transformations:** `add_transformations()` can only be called once per reader instance.
*   **Streaming:** `StreamReaderBase` does not support random access, `rewind()`, `copy()`, or `timeseries()`.
*   **Slicing:** `check_slice_indices()` follows Python `range()` conventions; caution is required when `stop=None` and `step=-1`.
*   **Deprecations:** TRZ Reader/Writer are deprecated as of 2.7.0. `asel` argument in `timeseries()` is deprecated in favor of `atomgroup`.

### 9. Facts to preserve in the final README
*   MDAnalysis uses 0-based indexing for trajectory frames.
*   XDR-based readers (XTC/TRR) perform a full file scan to build offsets on the first load, which may take time for large files.
*   `Universe` objects own the trajectory state; `AtomGroup` methods operate on the current `Timestep`.
*   `totaltime` is calculated as `(n_frames - 1) * dt`.

### 10. Missing or weak documentation
*   The specific behavior of `XYZReader` regarding "optional data" columns is loosely defined and may require user-side adjustments.
*   The `StreamReaderBase` constraints are extensive; documentation on how to detect if a reader is a stream-based reader is implicit rather than explicit.
*   The discrepancy between `range()` and `slice()` behavior in `check_slice_indices()` is noted as a warning but lacks a clear "best practice" for developers to avoid the pitfall.

===== Original documentation part 8/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library designed for the analysis of molecular dynamics (MD) trajectories and structural data. It provides a unified interface for reading various file formats, selecting atoms, performing geometric calculations, and managing trajectory data in memory or via streaming.

### 2. Main workflows
*   **Universe Initialization:** Loading topology and trajectory files into a `Universe` object.
*   **Atom Selection:** Filtering atoms using selection strings (e.g., `select_atoms("protein")`) to create `AtomGroup` instances.
*   **Trajectory Iteration:** Processing frames sequentially via the `trajectory` attribute.
*   **In-memory Analysis:** Transferring trajectories to memory for faster access or modification using `MemoryReader`.
*   **Coordinate Transformations:** Applying transformations to coordinates (e.g., rotation, translation, PBC wrapping) and calculating structural properties (e.g., center of mass, radius of gyration).
*   **Auxiliary Data:** Integrating non-coordinate data (e.g., energy terms) into the trajectory analysis.

### 3. Important APIs and usage patterns
*   **`Universe`**: The central container for topology and trajectory.
*   **`AtomGroup`**: The primary container for subsets of atoms. It supports set operations (`|`, `&`, `-`, `^`) and concatenation (`+`).
*   **`Timestep`**: Holds coordinate, velocity, and force data for a single frame.
*   **`MemoryReader`**: Enables in-memory trajectory operations.
*   **`Writer`**: Handles output of trajectories. Note: Streaming readers do not support writing.
*   **`select_atoms()`**: The primary method for filtering atoms. Supports dynamic selections via `updating=True`.
*   **`convert_to`**: An accessor for converting `AtomGroup` objects to other formats (e.g., `ag.convert_to.parmed()`).

### 4. Inputs and file formats
*   **Topology/Trajectory:** MDAnalysis supports a wide range of formats (e.g., PSF, DCD, PDB, GRO, XTC, TRR, LAMMPSDUMP).
*   **Chemfiles:** Interoperability with the `chemfiles` library allows reading/writing additional formats by setting `format="CHEMFILES"`.
*   **Memory:** `MemoryReader` accepts `numpy.ndarray` for coordinates, velocities, and forces.

### 5. Outputs and generated artifacts
*   **Trajectory Files:** Created via `Writer` instances.
*   **Calculated Properties:** Methods like `center_of_mass()`, `radius_of_gyration()`, and `dipole_moment()` return `numpy.ndarray` or scalar values.
*   **Pickled Objects:** `Universe` and `AtomGroup` objects support pickling.

### 6. Configuration and environment assumptions
*   **Units:** MDAnalysis uses internal units (Å for length, ps for time).
*   **Dependencies:** Some readers/converters require optional dependencies (e.g., `chemfiles`, `RDKit`).
*   **Memory:** In-memory operations require sufficient RAM to hold the trajectory.

### 7. Commands and examples

**Loading a Universe:**
```python
import MDAnalysis as mda
from MDAnalysis.tests.datafiles import TPR, XTC
u = mda.Universe(TPR, XTC)
```

**Selecting atoms and calculating center of mass:**
```python
protein = u.select_atoms("protein")
com = protein.center_of_mass()
```

**Using MemoryReader:**
```python
from MDAnalysis.coordinates.memory import MemoryReader
u.transfer_to_memory()
# Or create from array
u2 = mda.Universe(PSF, coordinates, format=MemoryReader, order='afc')
```

**Adding auxiliary data:**
```python
u.trajectory.add_auxiliary('pull', 'pull-force.xvg')
# Access via ts.aux
for ts in u.trajectory:
    print(ts.aux.pull)
```

**Converting AtomGroup to another package:**
```python
parmed_structure = u.atoms.convert_to.parmed()
```

### 8. Constraints, preconditions, compatibility rules
*   **Streaming Constraints:** Streaming readers (e.g., standard file readers) do not support `rewind()`, `copy()`, or `timeseries()` extraction.
*   **Writer Support:** `Writer` creation is not supported for streaming trajectories.
*   **AtomGroup Binding:** `AtomGroup` instances are bound to a `Universe` and cannot exist in isolation.
*   **PBC:** Methods like `wrap()`, `unwrap()`, and `pack_into_box()` handle periodic boundary conditions. `wrap` is the preferred keyword (replacing `pbc`).
*   **Topology Requirements:** Methods like `center_of_mass()` and `radius_of_gyration()` require mass information in the topology.

### 9. Facts to preserve in the final README
*   `AtomGroup` is the core object for analysis.
*   `Universe` owns the topology and trajectory state.
*   `MemoryReader` is essential for high-performance, in-memory trajectory manipulation.
*   MDAnalysis uses 0-based indexing for frames and atoms.
*   `select_atoms()` supports complex boolean logic and dynamic updates.

### 10. Missing or weak documentation
*   The distinction between `AtomGroup` methods that return views vs. copies is occasionally subtle.
*   Specific behavior of `check_slice_indices` when `stop=None` and `step=-1` is noted as potentially problematic for downstream code.
*   The `MemoryReader` documentation mentions that only fixed unit cell dimensions are currently supported.

===== Original documentation part 9/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library designed for the analysis of molecular dynamics (MD) trajectories and structural data. It provides a unified framework for loading topologies and trajectories, performing atom selections, calculating geometric and structural properties, and executing reusable analysis algorithms.

### 2. Main workflows
*   **Universe Initialization:** Loading a topology and trajectory into a `Universe` object, which serves as the central container for system state.
*   **Atom Selection:** Filtering atoms using a domain-specific selection language (e.g., `u.select_atoms('name CA')`) to create `AtomGroup` instances.
*   **Trajectory Iteration:** Traversing trajectory frames to perform time-dependent analysis.
*   **Geometric/Structural Analysis:** Computing properties like centers of mass/geometry, radii of gyration, dipole moments, and principal axes.
*   **Coordinate Transformation:** Manipulating coordinates via wrapping/unwrapping (PBC), rotation, and translation.
*   **Topology Manipulation:** Accessing and modifying bonded connections, residue/segment information, and atomic attributes.

### 3. Important APIs and usage patterns
*   **`Universe`:** The primary object owning topology and trajectory data.
*   **`AtomGroup` / `ResidueGroup` / `SegmentGroup`:** The core containers for selections. These support set-like operations (`&`, `|`, `-`, `^`) and concatenation (`+`).
*   **`select_atoms()`:** The primary method for creating selections.
*   **`accumulate()`:** A flexible method for aggregating attributes (e.g., mass, charge) across compounds (residues, segments, etc.).
*   **`wrap()` / `unwrap()` / `pack_into_box()`:** Methods for handling periodic boundary conditions.
*   **`write()`:** Exporting selections or trajectories to various formats (PDB, GRO, XTC, etc.).
*   **`UpdatingAtomGroup`:** A specialized `AtomGroup` that dynamically re-evaluates its selection at each trajectory frame.

### 4. Inputs and file formats
*   **Topology/Coordinate Formats:** PSF, PDB, GRO, and others supported by MDAnalysis parsers.
*   **Trajectory Formats:** DCD, XTC, and others.
*   **Configuration:** Unit cell dimensions are handled via `Timestep.dimensions` (format: `[lx, ly, lz, alpha, beta, gamma]`).

### 5. Outputs and generated artifacts
*   **Numerical Data:** NumPy arrays for coordinates, centers, moments, and accumulated attributes.
*   **Files:** Coordinate files (PDB, GRO), trajectory files (XTC), and selection files (NDX) generated via `AtomGroup.write()`.
*   **Sequence Data:** Amino acid sequences as `Bio.SeqRecord` or strings.

### 6. Configuration and environment assumptions
*   **Dependencies:** Requires `numpy`. Optional dependencies include `Biopython` (for sequence analysis) and `RDKit` (for SMARTS-based selections).
*   **PBC:** Many geometric methods (e.g., `center_of_mass`, `radius_of_gyration`) accept a `wrap` parameter to handle periodic boundaries.
*   **Topology Requirements:** Methods like `center_of_mass` or `moment_of_inertia` require mass information; `total_charge` requires charge information. A `NoDataError` is raised if required attributes are missing.

### 7. Commands and examples

**Writing an AtomGroup to a file:**
```python
ag = u.atoms
ag.write('selection.ndx')  # Write a gromacs index file
ag.write('coordinates.pdb')  # Write the current frame as PDB
# Write the trajectory in XTC format
ag.write('trajectory.xtc', frames='all')
# Write every other frame of the trajectory in PDB format
ag.write('trajectory.pdb', frames=u.trajectory[::2])
```

**Accumulating attributes:**
```python
# Total charge of an AtomGroup
sel = u.select_atoms('prop mass > 4.0')
sel.accumulate('charges')

# Total mass per residue of all CA Atoms
sel = u.select_atoms('name CA')
sel.accumulate('masses', compound='residues')
```

**Wrapping coordinates:**
```python
# Wrap atoms into the primary unit cell
ag.wrap(compound='atoms', center='com', box=None, inplace=True)
```

**UpdatingAtomGroup usage:**
```python
water_shell = u.select_atoms("name OW and around 3.5 protein", updating=True)
water_shell_prev = water_shell.atoms

for ts in u.trajectory:
    exchanged = water_shell - water_shell_prev
    # ... analysis logic ...
    water_shell_prev = water_shell.atoms
```

### 8. Constraints, preconditions, compatibility rules
*   **Universe Ownership:** A `Universe` owns the topology and trajectory state.
*   **AtomGroup Methods:** Operate on the current trajectory frame.
*   **Data Availability:** Methods requiring specific topology attributes (masses, charges, names) will raise `NoDataError` if those attributes are not present in the topology.
*   **PBC:** `wrap()` is faster for `AtomGroup` than for `ResidueGroup` or `SegmentGroup`.
*   **Deprecated APIs:** `pbc` keyword arguments are deprecated in favor of `wrap` (to be removed in 3.0).

### 9. Facts to preserve in the final README
*   MDAnalysis is object-oriented and array-based.
*   Selections are powerful and support complex logic (e.g., `around`, `protein`, `resname`).
*   The library handles both orthogonal and triclinic simulation boxes.
*   `UpdatingAtomGroup` is essential for tracking dynamic selections across trajectories.

### 10. Missing or weak documentation
*   The `Topology` object documentation is marked as "TODO: Add in-depth discussion."
*   Specific behavior of `TransTable` and its internal mapping logic is sparsely documented for end-users.
*   The distinction between `AtomGroup.write()` and `Universe.atoms.write()` could be clarified for beginners.

===== Original documentation part 10/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library designed for the analysis of molecular dynamics (MD) trajectories and structural data. It provides a unified framework for reading various topology and trajectory formats, selecting atoms, performing geometric and structural calculations, and implementing reusable analysis algorithms.

### 2. Main workflows
*   **System Initialization:** Loading topology and trajectory files into a `Universe` object.
*   **Atom Selection:** Filtering atoms using the `select_atoms()` method to create `AtomGroup` instances.
*   **Topology Manipulation:** Adding, deleting, or guessing topology attributes (bonds, angles, dihedrals, masses, types) using `Universe` methods or `Guesser` classes.
*   **Geometric Analysis:** Computing centers of mass/charge, radii of gyration, moments of inertia, and dipole/quadrupole moments.
*   **Distance/Correlation Analysis:** Calculating inter-atomic distances, bond lengths, angles, and dihedrals, often utilizing accelerated backends (serial, OpenMP, or `distopia`).
*   **Trajectory Iteration:** Stepping through frames to perform time-dependent analysis.

### 3. Important APIs and usage patterns
*   **`Universe(topology, trajectory)`**: The primary entry point.
*   **`AtomGroup`**: The core object for atom-wise operations. Methods like `center_of_mass()`, `dipole_vector()`, and `select_atoms()` are central.
*   **`guess_TopologyAttrs()`**: The standard API for inferring missing topology information (masses, types, bonds) using a `Guesser`.
*   **`MDAnalysis.lib.distances`**: Provides high-performance functions (`distance_array`, `calc_bonds`, `calc_angles`, `calc_dihedrals`) that accept `AtomGroup` or `numpy.ndarray` inputs.
*   **`MDAnalysis.lib.NeighborSearch`**: Used for efficient spatial queries (e.g., finding atoms within a radius).

### 4. Inputs and file formats
*   **Topology:** PSF, PDB, GRO, TPR, CRD, XYZ.
*   **Trajectory:** DCD, XTC, TRR, XYZ, NC (NetCDF).
*   **Data Structures:** `Universe` (container), `AtomGroup`, `ResidueGroup`, `SegmentGroup`, `TopologyAttr` (attributes like `Masses`, `Charges`, `Bonds`).

### 5. Outputs and generated artifacts
*   **Calculated Properties:** `numpy.ndarray` objects representing coordinates, distances, angles, or moments.
*   **Topology Files:** Modified structures can be written using `AtomGroup.write()`.
*   **Sequences:** FASTA files via `Bio.SeqIO` integration.
*   **In-memory Trajectories:** `MemoryReader` allows for coordinate manipulation and writing.

### 6. Configuration and environment assumptions
*   **Dependencies:** Requires `numpy`. Optional dependencies include `Biopython` (for sequence handling), `rdkit` (for SMILES/aromaticity), and `distopia` (for SIMD-accelerated distance calculations).
*   **Context:** `Guesser` classes use context-specific logic (e.g., `DefaultGuesser`) to infer attributes.
*   **PBC:** Periodic boundary conditions are handled via the `box` parameter in distance functions and `wrap`/`unwrap` parameters in geometric methods.

### 7. Commands and examples

**Loading a Universe:**
```python
import MDAnalysis as mda
u = mda.Universe("topology.psf", "trajectory.dcd")
```

**Adding Topology Attributes:**
```python
u.add_TopologyAttr('tempfactors')
u.guess_TopologyAttrs(context='default', to_guess=['masses', 'types'])
```

**Geometric Analysis:**
```python
protein = u.select_atoms("protein")
com = protein.center_of_mass(compound='residues')
```

**Distance Calculation:**
```python
from MDAnalysis.lib.distances import distance_array
dists = distance_array(ag1.positions, ag2.positions, box=u.dimensions, backend='serial')
```

**Neighbor Search:**
```python
from MDAnalysis.lib.NeighborSearch import AtomNeighborSearch
ns = AtomNeighborSearch(u.atoms)
nearby = ns.search(query_atoms, radius=5.0, level='A')
```

### 8. Constraints, preconditions, compatibility rules, and type-selection rules
*   **Universe Ownership:** A `Universe` owns the topology and trajectory state.
*   **AtomGroup Methods:** Operate on selected atoms at the current trajectory frame.
*   **Analysis Classes:** Require construction followed by `run()`.
*   **PBC:** Use `wrap=True` or `unwrap=True` in geometric methods to handle periodic boundaries.
*   **Guessing:** `guess_bonds` and related methods rely on `vdwradii` and `fudge_factor`.
*   **Compatibility:** `Merge()` requires common topology attributes.
*   **Type Selection:** `backend` keyword in `MDAnalysis.lib.distances` supports `serial`, `OpenMP`, and `distopia`.

### 9. Facts to preserve in the final README
*   MDAnalysis 2.11.0 is the current version.
*   `Universe` is the central object for all analysis.
*   Distance calculations support multiple backends for performance.
*   `guess_TopologyAttrs` is the preferred way to handle missing topology data.
*   `AtomGroup` is the primary interface for atom-wise selection and calculation.

### 10. Missing or weak documentation
*   The `MDAnalysis.guesser.tables` module documentation is sparse regarding how to extend the hard-coded tables for custom atom types.
*   The distinction between `tempfactors` and `bfactors` is noted as deprecated/aliased, but the transition path for legacy code is not explicitly detailed beyond warnings.
*   `NeighborSearch` performance characteristics for very large systems are not explicitly benchmarked in the provided docs.

===== Original documentation part 11/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library designed for the analysis of molecular dynamics (MD) trajectories and structural data. It provides a unified framework for reading diverse topology and trajectory formats, performing atom selections, executing geometric and structural calculations, and managing trajectory transformations. It is a core tool for computational chemists and biophysicists, facilitating reproducible analysis workflows.

### 2. Main workflows
*   **Universe Initialization:** Loading topology and trajectory files into a `Universe` object, which serves as the central container for system state.
*   **Atom Selection:** Filtering atoms using a domain-specific selection language to create `AtomGroup` objects.
*   **Trajectory Iteration:** Traversing trajectory frames to compute time-dependent properties.
*   **Geometric Analysis:** Calculating distances, angles, dihedrals, centers of mass, and radii of gyration.
*   **Neighbor Searching:** Performing efficient $O(N)$ neighbor searches using grid-based algorithms, supporting periodic boundary conditions (PBC).
*   **Structure Alignment:** Calculating RMSD and optimal rotational matrices using the QCP (Quaternion-based Characteristic Polynomial) method.
*   **Selection Export:** Exporting `AtomGroup` selections to external formats (VMD, PyMOL, Gromacs, CHARMM, Jmol) for visualization or further analysis.

### 3. Important APIs and usage patterns
*   **`Universe`:** The primary object owning topology and trajectory data.
*   **`AtomGroup`:** A collection of atoms; methods operate on the current trajectory frame.
*   **`FastNS`:** A grid-based neighbor search class.
*   **`PeriodicKDTree`:** A wrapper around `scipy.spatial.cKDTree` for PBC-aware spatial queries.
*   **`SelectionWriter`:** Classes for exporting selections (e.g., `MDAnalysis.selections.vmd.SelectionWriter`).
*   **`ProgressBar`:** A decorator for iterables (e.g., `u.trajectory`) to provide visual feedback during analysis.
*   **`pickle_open` / `anyopen`:** Utilities for handling file I/O, including compressed formats and picklable file streams.

### 4. Inputs and file formats
MDAnalysis supports a wide range of formats, including:
*   **Topology:** PSF, PDB, GRO, CRD (CHARMM), DMS (Desmond), and FHI-AIMS.
*   **Trajectory:** DCD, XTC, TRR, and others.
*   **Streams:** `NamedStream` allows wrapping memory buffers (e.g., `io.StringIO`) to act as file-like inputs.

### 5. Outputs and generated artifacts
*   **Coordinate Arrays:** NumPy arrays (typically `float32`) representing positions, velocities, or forces.
*   **Selection Files:** `.vmd`, `.pml`, `.ndx`, `.str`, and `.spt` files for cross-package interoperability.
*   **Logs:** Standardized logging via `MDAnalysis.start_logging()`.

### 6. Configuration and environment assumptions
*   **Dependencies:** Requires NumPy and SciPy. Optional dependencies (e.g., for specific readers) are handled at runtime.
*   **Logging:** The library uses a top-level logger named `MDAnalysis`.
*   **Precision:** Calculations generally default to `float32` for coordinate arrays, though some mathematical functions use `float64`.

### 7. Commands and examples
**Neighbor Search with PBC:**
```python
from MDAnalysis.lib.nsgrid import FastNS
gridsearch = FastNS(cutoff, coords, box, pbc=True)
results = gridsearch.search(search_coords)
pairs = results.get_pairs()
```

**Trajectory Iteration with Progress Bar:**
```python
from MDAnalysis.lib.log import ProgressBar
for ts in ProgressBar(u.trajectory):
    # perform analysis
```

**Writing Selections:**
```python
with mda.selections.gromacs.SelectionWriter('leaflets.ndx', mode='w') as ndx:
    ndx.write(upper_saturated, name='upper_sat')
```

**Coordinate Augmentation (PBC):**
```python
images, mapping = augment_coordinates(coordinates, box, max_cutoff)
all_coords = numpy.concatenate([coordinates, images])
```

### 8. Constraints, preconditions, compatibility rules
*   **Universe Ownership:** A `Universe` owns the topology and trajectory state.
*   **PBC Handling:** `FastNS` and `PeriodicKDTree` require box dimensions in the format `[lx, ly, lz, alpha, beta, gamma]`.
*   **Coordinate Units:** Readers handle unit conversion; internal calculations typically use base units.
*   **In-place Operations:** Many `lib` functions (e.g., `make_whole`, `convert_pos_from_native`) modify arrays in-place by default for performance.
*   **Type Selection:** `FastNS` and `PeriodicKDTree` require `numpy.float32` for coordinate arrays.

### 9. Facts to preserve in the final README
*   MDAnalysis is object-oriented and designed for reproducibility.
*   The library supports both serial and OpenMP-parallelized distance calculations.
*   `NamedStream` enables in-memory analysis without writing intermediate files to disk.
*   The library provides robust tools for handling triclinic boxes and minimum image conventions.

### 10. Missing or weak documentation
*   The `transformations` library documentation notes that the API is not stable and is not optimized for speed.
*   Some low-level modules (e.g., `MDAnalysis.lib._distances`) lack comprehensive error checking and are marked for cautious use.
*   The `DCDFile` reader notes that DCD is not a well-defined format, and post-processing of unit cell information may be required depending on the originating software (CHARMM vs. NAMD).

===== Original documentation part 12/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library designed for the analysis of molecular dynamics (MD) trajectories and structural data. It provides a unified interface for reading various file formats, selecting atoms, performing geometric measurements, and applying on-the-fly coordinate transformations.

### 2. Main workflows
*   **Universe Initialization:** Loading topology and trajectory data into a `Universe` object.
*   **Topology Parsing:** Extracting structural information (atoms, residues, segments, bonds, etc.) from diverse file formats.
*   **Trajectory Analysis:** Iterating over frames to compute properties or apply transformations.
*   **Coordinate Transformations:** Modifying trajectory data on-the-fly (e.g., setting box dimensions) using the `transformations` framework.
*   **Unit Conversion:** Converting between native simulation units and MDAnalysis base units for positions, velocities, forces, and time.

### 3. Important APIs and usage patterns
*   **`MDAnalysis.Universe`**: The central object owning topology and trajectory state.
*   **`guess_TopologyAttrs()`**: The primary API for guessing missing topology attributes (e.g., masses, atom types).
*   **`TransformationBase`**: The base class for creating custom on-the-fly trajectory transformations.
*   **`add_transformations()`**: Method to register transformations to a trajectory.
*   **`convert_*_from_native` / `convert_*_to_native`**: Methods for unit conversion (positions, velocities, forces, time).
*   **`parse()`**: The standard method across all topology parsers to return a `Topology` object.

### 4. Inputs and file formats
MDAnalysis supports a wide range of formats:
*   **Topology/Structure:** PSF (CHARMM/NAMD/XPLOR), PDB, PDBQT (AutoDock), PQR, GRO (GROMACS), ITP/TOP (GROMACS/AMBER), GSD (HOOMD), HoomdXML, MOL2 (Tripos), MMTF, MMCIF/PDBx, TXYZ/ARC (Tinker), and XYZ.
*   **Trajectory:** Handled by specific readers associated with the formats above.
*   **Configuration:** Preprocessor variables for ITP/TOP files (e.g., `#define`, `#ifdef`) are handled via keyword arguments in the `Universe` constructor.

### 5. Outputs and generated artifacts
*   **`Topology` object**: The internal representation of the system structure.
*   **`Timestep` object**: Contains coordinate, velocity, force, and box information for a specific frame.
*   **Temporary/Output files**: Created only in the designated `output_dir`.

### 6. Configuration and environment assumptions
*   **Thread Management:** Transformations can limit thread usage via `max_threads` to avoid oversubscription with parallel engines like Dask.
*   **Optional Dependencies:** Some parsers (e.g., `MMCIFParser` using `gemmi`) require external libraries.
*   **Unit System:** MDAnalysis uses internal base units (Å for length, ps for time). Native units vary by format and are handled by the `convert_*` methods.

### 7. Commands and examples

**Loading a Universe:**
```python
import MDAnalysis as mda
u = mda.Universe("example.gsd")
```

**Defining a custom transformation:**
```python
class NewTransformation(TransformationBase):
    def __init__(self, ag, parameter, max_threads=1, parallelizable=True):
        super().__init__(max_threads=max_threads, parallelizable=parallelizable)
        self.ag = ag
        self._param = parameter

    def _transform(self, ts):
        ts.positions = some_function(ts, self.ag, self._param)
        return ts

new_transformation = NewTransformation(ag, param)
u.trajectory.add_transformations(new_transformation)
```

**Setting box dimensions:**
```python
# Set simulation box dimensions to [a, b, c, alpha, beta, gamma]
u.trajectory.add_transformations(mda.transformations.boxdimensions.set_dimensions(dimensions))
```

**Reading an ITP file with preprocessor variables:**
```python
import MDAnalysis as mda
from MDAnalysis.tests.datafiles import ITP_tip5p
u = mda.Universe(ITP_tip5p, EXTRA_ATOMS=True, HW1_CHARGE=3, HW2_CHARGE=3)
```

### 8. Constraints, preconditions, compatibility rules
*   **Universe Ownership:** A `Universe` owns the topology and trajectory state.
*   **In-place Operations:** `convert_*` methods default to `inplace=True` for performance.
*   **Atom Selection:** `AtomGroup` methods operate on selected atoms at the current trajectory frame.
*   **TPR Compatibility:** The `TPRParser` supports specific Gromacs versions (see `SUPPORTED_VERSIONS` in `MDAnalysis.topology.tpr.setting`).
*   **PDB Residue Limits:** Standard `PDBParser` handles up to 9,999 residues; use `ExtendedPDBParser` for up to 99,999.
*   **Mass/Type Guessing:** Removed from individual parsers; must be invoked via `universe.guess_TopologyAttrs()`.

### 9. Facts to preserve in the final README
*   MDAnalysis 2.11.0 is the current version.
*   The library is object-oriented and designed for scientific Python workflows.
*   Always use `universe.guess_TopologyAttrs()` for missing attributes.
*   Transformations are applied on-the-fly to the trajectory.

### 10. Missing or weak documentation
*   The exact behavior of `parallelizable` in `TransformationBase` is noted as not yet checked by the core library.
*   Some parsers (e.g., `MinimalParser`) have limited documentation regarding their specific requirements for `n_atoms`.
*   The `TPRParser` development notes indicate that support for new TPR versions requires manual updates to the parser logic.

===== Original documentation part 13/13 =====
### 1. Project purpose
MDAnalysis is an object-oriented Python library designed for the analysis of molecular dynamics (MD) simulations. It provides a unified interface for reading, manipulating, and analyzing structural and trajectory data from a wide range of simulation packages (e.g., GROMACS, Amber, NAMD, CHARMM, LAMMPS). It is built for scientific reproducibility and performance, utilizing NumPy for data handling and offering modular analysis algorithms.

### 2. Main workflows
*   **Universe Initialization:** Loading topology and trajectory files into a `Universe` object, which serves as the central container for simulation state.
*   **Atom Selection:** Filtering atoms using selection strings (e.g., `"name OH"`) to create `AtomGroup` objects.
*   **Trajectory Iteration:** Traversing trajectory frames to compute properties (e.g., center of mass, radius of gyration) or apply transformations.
*   **Coordinate Transformations:** Modifying trajectory coordinates in-place or via `add_transformations` (e.g., wrapping, unwrapping, fitting, rotating, translating).
*   **Analysis:** Running reusable analysis algorithms (e.g., RMSD, contact analysis, flow field generation).

### 3. Important APIs and usage patterns
*   **`MDAnalysis.Universe(topology, trajectory)`**: The primary entry point.
*   **`Universe.select_atoms(selection_string)`**: Returns an `AtomGroup`.
*   **`AtomGroup` methods**: Operate on the current frame (e.g., `.positions`, `.center_of_mass()`, `.velocities`, `.forces`).
*   **`Universe.trajectory.add_transformations(transform)`**: Registers a transformation to be applied during iteration.
*   **`MDAnalysis.units`**: Provides conversion factors and constants (e.g., `convert(x, u1, u2)`).
*   **Analysis Classes**: Generally follow a `Class(universe, ...).run()` pattern.

### 4. Inputs and file formats
MDAnalysis supports a wide variety of topology and trajectory formats.
*   **Topology:** PSF, PDB, GRO, TPR, etc.
*   **Trajectory:** DCD, XTC, TRR, etc.
*   **Units:** Base units are Å (length), ps (time), kJ/mol (energy), $e$ (charge), u (mass), kJ/(mol·Å) (force), and Å/ps (speed).

### 5. Outputs and generated artifacts
*   **Numpy Arrays:** Coordinate, velocity, and force data are exposed as NumPy arrays.
*   **Transformation Results:** Modified `Timestep` objects.
*   **Visualization Data:** Streamline generation returns displacement arrays (`dx`, `dy`, `dz`) and statistical metrics.

### 6. Configuration and environment assumptions
*   **Dependencies:** Requires NumPy. Optional dependencies may be required for specific readers or analysis modules.
*   **Parallelization:** Many transformations and analysis modules support `max_threads` and `parallelizable` flags.
*   **Thread Safety:** Some transformations (e.g., `rotateby`, `fit_rot_trans`) perform better with `max_threads=1`.

### 7. Commands and examples

**Basic Universe and Selection:**
```python
import MDAnalysis as mda
u = mda.Universe('topol.tpr','traj.trr')
ag = u.select_atoms('name OH')
for ts in u.trajectory:
    print(ag.center_of_mass())
```

**Trajectory Translation:**
```python
ts = MDAnalysis.transformations.translate([1,2,3])(ts)
```

**Trajectory Rotation:**
```python
from MDAnalysis import transformations
ts = u.trajectory.ts
angle = 90
d = [0,0,1]
rotated = transformations.rotate.rotateby(angle, direction=d, ag=u.atoms)(ts)
```

**Fitting (RMSD Superposition):**
```python
ag = u.select_atoms("protein")
ref = mda.Universe("reference.pdb")
transform = mda.transformations.fit_rot_trans(ag, ref, plane="xy", weights="mass")
u.trajectory.add_transformations(transform)
```

**NoJump Unwrapping:**
```python
transformation = NoJump()
u.trajectory.add_transformations(transformation)
for ts in u.trajectory:
    print(ts.positions)
```

**Position Averaging:**
```python
N=3
transformation = PositionAverager(N, check_reset=True)
u.trajectory.add_transformations(transformation)
for ts in u.trajectory:
    if transformation.current_avg == transformation.avg_frames:
        print(ts.positions)
```

### 8. Constraints, preconditions, compatibility rules
*   **Universe Ownership:** A `Universe` owns the topology and trajectory state.
*   **Transformation Order:** Transformations are applied to the `Timestep` object. Some transformations (e.g., `NoJump`) require periodic box dimensions to be set for every frame.
*   **In-place Modification:** `unwrap` modifies atom positions in-place.
*   **Unit Conversion:** Conversions are always performed via the base unit as an intermediate step.
*   **Parallelization:** `PositionAverager` defaults to `parallelizable=False`.

### 9. Facts to preserve in the final README
*   MDAnalysis uses NIST CODATA 2010 values for physical constants.
*   The library is licensed under LGPLv3+ (source) and LGPLv2.1+ (components).
*   Always cite the Gowers et al. (2016) and Michaud-Agrawal et al. (2011) papers when using the library.
*   The `MDAnalysis.analysis` module contains the core reusable algorithms.

### 10. Missing or weak documentation
*   The documentation for `PositionAverager` mentions `resetarrays()` but does not explicitly detail the internal state management for non-sequential iteration beyond the provided example.
*   Specific error handling for incompatible unit conversions is mentioned but not fully enumerated.
*   The distinction between `geometry` and `mass` centering in `center_in_box` is documented, but the behavior when an `AtomGroup` has zero mass is not explicitly defined.

Real usage from the project's existing test suite (these compile and pass — base
the Valid Call Patterns and realistic Common Failure Modes on them; may be empty):
```Python
(no existing test found for this API)
```

Verbatim code example(s) from the ORIGINAL project README that call `python:MDAnalysis.lib.distances.calc_bonds`
(the project's real, documented usage — may be empty):
```Python
===== Shared original document: pinned-root-readme:README.rst =====
================================
  MDAnalysis Repository README
================================

|numfocus| 

|build| |cron| |cirruscron| |linters| |cov|

|docs| |devdocs| |discussions|

|pypi| |anaconda| |asv|

MDAnalysis_ is a Python library for the analysis of computer simulations of many-body systems at the molecular scale, spanning use cases from interactions of drugs with proteins to novel materials. It is widely used in the scientific community and is written by scientists for scientists. 

It works with a wide range of popular simulation packages including GROMACS, Amber, NAMD, CHARMM, DL_POLY, HOOMD, LAMMPS and many others — see the lists of supported `trajectory formats`_ and `topology formats`_.
MDAnalysis also includes widely used analysis algorithms in the `MDAnalysis.analysis`_ module.

.. _numfocus-fiscal-sponsor-attribution:

The MDAnalysis project uses an `open governance model`_ and is fiscally sponsored by `NumFOCUS`_. Consider making 
a `tax-deductible donation`_ to help the project pay for developer time, professional services, travel, workshops, and a variety of other needs.

.. image:: https://www.mdanalysis.org/public/images/numfocus-sponsored-small.png
   :alt: NumFOCUS (Fiscally Sponsored Project)
   :target: https://numfocus.org/project/mdanalysis
   :align: center

This project is bound by a `Code of Conduct`_.

|powered_by_MDA|

If you use MDAnalysis_ in your project consider letting your users and the world know about it by displaying the MDAnalysis_ badge! `Embedding code`_ is available for different markups.

Example analysis script
=======================

.. code:: python

   import MDAnalysis as mda

   # Load simulation results with a single line
   u = mda.Universe('topol.tpr','traj.trr')

   # Select atoms
   ag = u.select_atoms('name OH')

   # Atom data made available as Numpy arrays
   ag.positions
   ag.velocities
   ag.forces

   # Iterate through trajectories
   for ts in u.trajectory:
       print(ag.center_of_mass())


Documentation
=============

**New users** should read the `Quickstart Guide`_ and might want to
look at our videos_, in which core developers explain various aspects
of MDAnalysis.

**All users** should read the `User Guide`_.

**Developers** may also want to refer to the `MDAnalysis API docs`_.

A growing number of `tutorials`_ are available that explain how to
conduct RMSD calculations, structural alignment, distance and contact
analysis, and many more.


Installation and availability
=============================

The latest release can be **installed via pip or conda** as
described in the `Installation Quick Start`_.

**Source code** is hosted in a git repository at
https://github.com/MDAnalysis/mdanalysis and is packaged under the
GNU Lesser General Public License, version 3 or any later version (LGPLv3+).
Individual source code components are provided under the
GNU Lesser General Public License, version 2.1 or any later version (LGPLv2.1+).
Please see the file LICENSE_ for more information.


Contributing
============

Please report **bugs** or **enhancement requests** through the `Issue
Tracker`_. Questions can also be asked on `GitHub Discussions`_.

If you are a **new developer** who would like to start contributing to
MDAnalysis get in touch on `GitHub Discussions`_. To set up a
development environment and run the test suite read the `developer
guide`_.


Citation
========

When using MDAnalysis in published work, please cite the following
two papers:

*   R\. J. Gowers, M. Linke, J. Barnoud, T. J. E. Reddy,
    M\. N. Melo, S. L. Seyler, D. L. Dotson, J. Domanski,
    S\. Buchoux, I. M. Kenney, and O. Beckstein. MDAnalysis:
    A Python package for the rapid analysis of molecular
    dynamics simulations. In S. Benthall and S. Rostrup,
    editors, Proceedings of the 15th Python in Science
    Conference, pages 102-109, Austin, TX, 2016. SciPy.
    doi: `10.25080/Majora-629e541a-00e`_    
*   N. Michaud-Agrawal, E. J. Denning, T. B. Woolf,
    and O. Beckstein. MDAnalysis: A Toolkit for the Analysis of Molecular
    Dynamics Simulations. *J. Comput. Chem.* **32** (2011), 2319--2327.
    doi: `10.1002/jcc.21787`_

For citations of included algorithms and sub-modules please see the references_.


.. _NumFOCUS: https://numfocus.org/
.. _open governance model: https://www.mdanalysis.org/pages/governance/
.. _tax-deductible donation: https://numfocus.org/donate-to-mdanalysis
.. _`Code of Conduct`: https://www.mdanalysis.org/conduct/
.. _trajectory formats: https://docs.mdanalysis.org/documentation_pages/coordinates/init.html#id1
.. _topology formats: https://docs.mdanalysis.org/documentation_pages/topology/init.html#supported-topology-formats
.. _MDAnalysis: https://www.mdanalysis.org
.. _LICENSE:
   https://github.com/MDAnalysis/mdanalysis/blob/develop/LICENSE
.. _`Installation Quick Start`:
   https://www.mdanalysis.org/pages/installation_quick_start/
.. _`MDAnalysis.analysis`: https://docs.mdanalysis.org/documentation_pages/analysis_modules.html
.. _`tutorials`: https://userguide.mdanalysis.org/examples/README.html
.. _`videos`: https://www.mdanalysis.org/pages/learning_MDAnalysis/#videos
.. _`Quickstart Guide`:
   https://userguide.mdanalysis.org/examples/quickstart.html
.. _`User Guide`: https://userguide.mdanalysis.org
.. _`MDAnalysis API docs`:
   https://docs.mdanalysis.org
.. _`Issue Tracker`: https://github.com/mdanalysis/mdanalysis/issues
.. _`GitHub Discussions`:
   https://github.com/MDAnalysis/mdanalysis/discussions
.. _`developer guide`:
   https://userguide.mdanalysis.org/contributing.html
.. _`10.1002/jcc.21787`: https://dx.doi.org/10.1002/jcc.21787
.. _`10.25080/Majora-629e541a-00e`: https://doi.org/10.25080/Majora-629e541a-00e
.. _references: https://docs.mdanalysis.org/documentation_pages/references.html
.. _Embedding code: https://www.mdanalysis.org/pages/citations/#powered-by-mdanalysis

.. |docs| image:: https://img.shields.io/badge/docs-latest-brightgreen.svg
   :alt: Documentation (latest release)
   :target: https://docs.mdanalysis.org

.. |devdocs| image:: https://img.shields.io/badge/docs-development-yellow.svg
   :alt: Documentation (development version)
   :target: https://docs.mdanalysis.org/dev

.. |numfocus| image:: https://img.shields.io/badge/powered%20by-NumFOCUS-orange.svg?style=flat&colorA=E1523D&colorB=007D8A
   :alt: Powered by NumFOCUS
   :target: https://www.numfocus.org/

.. |build| image:: https://github.com/MDAnalysis/mdanalysis/actions/workflows/gh-ci.yaml/badge.svg
   :alt: Github Actions Build Status
   :target: https://github.com/MDAnalysis/mdanalysis/actions/workflows/gh-ci.yaml

.. |cron| image:: https://github.com/MDAnalysis/mdanalysis/actions/workflows/gh-ci-cron.yaml/badge.svg
   :alt: Github Actions Cron Job Status
   :target: https://github.com/MDAnalysis/mdanalysis/actions/workflows/gh-ci-cron.yaml

.. |cirruscron| image:: https://img.shields.io/cirrus/github/MDAnalysis/mdanalysis/develop
   :alt: Cirrus CI - Cron job status
   :target: https://cirrus-ci.com/github/MDAnalysis/mdanalysis/develop

.. |linters| image:: https://github.com/MDAnalysis/mdanalysis/actions/workflows/linters.yaml/badge.svg
   :alt: Github Actions Linters Status
   :target: https://github.com/MDAnalysis/mdanalysis/actions/workflows/linters.yaml

.. |cov|   image:: https://codecov.io/gh/MDAnalysis/mdanalysis/branch/develop/graph/badge.svg
   :alt: Coverage Status
   :target: https://codecov.io/gh/MDAnalysis/mdanalysis

.. |pypi| image:: https://img.shields.io/pypi/v/MDAnalysis
   :alt: PyPI Version
   :target: https://pypi.org/project/MDAnalysis/

.. |anaconda| image:: https://anaconda.org/conda-forge/mdanalysis/badges/version.svg
   :alt: Anaconda
   :target: https://anaconda.org/conda-forge/mdanalysis
   
.. |asv| image:: https://img.shields.io/badge/benchmarked%20by-asv-blue.svg
   :alt: ASV Benchmarks
   :target:  https://www.mdanalysis.org/benchmarks/

.. |powered_by_MDA| image:: https://img.shields.io/badge/Powered%20by-MDAnalysis-orange.svg?logoWidth=15&logo=data:image/x-icon;base64,AAABAAEAEBAAAAEAIAAoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJD+XwCY/fEAkf3uAJf97wGT/a+HfHaoiIWE7n9/f+6Hh4fvgICAjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACT/yYAlP//AJ///wCg//8JjvOchXly1oaGhv+Ghob/j4+P/39/f3IAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJH8aQCY/8wAkv2kfY+elJ6al/yVlZX7iIiI8H9/f7h/f38UAAAAAAAAAAAAAAAAAAAAAAAAAAB/f38egYF/noqAebF8gYaagnx3oFpUUtZpaWr/WFhY8zo6OmT///8BAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgICAn46Ojv+Hh4b/jouJ/4iGhfcAAADnAAAA/wAAAP8AAADIAAAAAwCj/zIAnf2VAJD/PAAAAAAAAAAAAAAAAICAgNGHh4f/gICA/4SEhP+Xl5f/AwMD/wAAAP8AAAD/AAAA/wAAAB8Aov9/ALr//wCS/Z0AAAAAAAAAAAAAAACBgYGOjo6O/4mJif+Pj4//iYmJ/wAAAOAAAAD+AAAA/wAAAP8AAABhAP7+FgCi/38Axf4fAAAAAAAAAAAAAAAAiIiID4GBgYKCgoKogoB+fYSEgZhgYGDZXl5e/m9vb/9ISEjpEBAQxw8AAFQAAAAAAAAANQAAADcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAjo6Mb5iYmP+cnJz/jY2N95CQkO4pKSn/AAAA7gAAAP0AAAD7AAAAhgAAAAEAAAAAAAAAAACL/gsAkv2uAJX/QQAAAAB9fX3egoKC/4CAgP+NjY3/c3Nz+wAAAP8AAAD/AAAA/wAAAPUAAAAcAAAAAAAAAAAAnP4NAJL9rgCR/0YAAAAAfX19w4ODg/98fHz/i4uL/4qKivwAAAD/AAAA/wAAAP8AAAD1AAAAGwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALGxsVyqqqr/mpqa/6mpqf9KSUn/AAAA5QAAAPkAAAD5AAAAhQAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADkUFBSuZ2dn/3V1df8uLi7bAAAATgBGfyQAAAA2AAAAMwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB0AAADoAAAA/wAAAP8AAAD/AAAAWgC3/2AAnv3eAJ/+dgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA9AAAA/wAAAP8AAAD/AAAA/wAKDzEAnP3WAKn//wCS/OgAf/8MAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIQAAANwAAADtAAAA7QAAAMAAABUMAJn9gwCe/e0Aj/2LAP//AQAAAAAAAAAA
   :alt: Powered by MDAnalysis
   :target: https://www.mdanalysis.org

.. |discussions| image:: https://img.shields.io/github/discussions/MDAnalysis/MDAnalysis
   :alt: GitHub Discussions
   :target: https://github.com/MDAnalysis/mdanalysis/discussions


===== https://docs.mdanalysis.org/2.11.0/documentation_pages/lib/distances.html#MDAnalysis.lib.distances.calc_bonds =====
MDAnalysis.lib.distances.calc_bonds(coords1: ndarray[tuple[Any, ...], dtype[_ScalarT]] | AtomGroup, coords2: ndarray[tuple[Any, ...], dtype[_ScalarT]] | AtomGroup, box: ndarray[tuple[Any, ...], dtype[_ScalarT]] | None = None, result: ndarray[tuple[Any, ...], dtype[_ScalarT]] | None = None, backend: str = 'serial') → ndarray[tuple[Any, ...], dtype[_ScalarT]][source]

Calculates the bond lengths between pairs of atom positions from the two coordinate arrays coords1 and coords2, which must contain the same number of coordinates. coords1[i] and coords2[i] represent the positions of atoms connected by the i-th bond. If single coordinates are supplied, a single distance will be returned.

In comparison to distance_array() and self_distance_array(), which calculate distances between all possible combinations of coordinates, calc_bonds() only calculates distances between pairs of coordinates, similar to:

numpy.linalg.norm(a - b) for a, b in zip(coords1, coords2)

If the optional argument box is supplied, the minimum image convention is applied when calculating distances. Either orthogonal or triclinic boxes are supported.

If a numpy array of dtype numpy.float64 with shape (n,) (for n coordinate pairs) is provided in result, then this preallocated array is filled. This can speed up calculations.

Parameters:

coords1 (numpy.ndarray or AtomGroup) – Coordinate array of shape (3,) or (n, 3) for one half of a single or n bonds, respectively (dtype is arbitrary, will be converted to numpy.float32 internally). Also accepts an AtomGroup.

coords2 (numpy.ndarray or AtomGroup) – Coordinate array of shape (3,) or (n, 3) for the other half of a single or n bonds, respectively (dtype is arbitrary, will be converted to numpy.float32 internally). Also accepts an AtomGroup.

box (numpy.ndarray, optional) – The unitcell dimensions of the system, which can be orthogonal or triclinic and must be provided in the same format as returned by MDAnalysis.coordinates.timestep.Timestep.dimensions: [lx, ly, lz, alpha, beta, gamma].

result (numpy.ndarray, optional) – Preallocated result array of dtype numpy.float64 and shape (n,) (for n coordinate pairs). Avoids recreating the array in repeated function calls.

backend ({'serial', 'OpenMP', 'distopia'}, optional) – Keyword selecting the type of acceleration. Defaults to ‘serial’.

Returns:

bondlengths – numpy.float64 Array containing the bond lengths between each pair of coordinates. If two single coordinates were supplied, their distance is returned as a single number instead of an array.

Return type:

numpy.ndarray (dtype=numpy.float64, shape=(n,)) or

Added in version 0.8.

Changed in version 0.13.0: Added backend keyword.

Changed in version 0.19.0: Internal dtype conversion of input coordinates to numpy.float32. Now also accepts single coordinates as input.

Changed in version 2.3.0: Can now accept an AtomGroup as an argument in any position and checks inputs using type hinting.

Changed in version 2.5.0: Can now optionally use the fast distance functions from distopia

```

GROUND THE CALL FORM by combining the sources above, in this priority order — and
NEVER invent a call shape that appears in none of them:
1. If a test-suite example is shown, its call form is authoritative (it compiles
   and passes) — reproduce that exact receiver and argument order.
2. Otherwise use the original-README example's call form.
3. If BOTH are shown, reproduce a real form verbatim (either compiles); when they
   differ, the instance/implicit form `value.python:MDAnalysis.lib.distances.calc_bonds(...)` is the most portable.
4. If NEITHER is shown, derive the call from the Signature/API facts and say in the
   entry that the example is inferred from the signature (not verified).
Preserve the receiver/qualifier EXACTLY as written — if it is
`value.python:MDAnalysis.lib.distances.calc_bonds(...)` or `Object.python:MDAnalysis.lib.distances.calc_bonds(...)`, keep it; do NOT collapse it to
a bare `python:MDAnalysis.lib.distances.calc_bonds(...)`, which usually will not compile.

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
TODO: one sentence describing what `python:MDAnalysis.lib.distances.calc_bonds` does, in the project's domain terms.

### Parameters
- `coords1` (`Union[npt.NDArray, 'AtomGroup']`): TODO — what this argument means / expected values.
- `coords2` (`Union[npt.NDArray, 'AtomGroup']`): TODO — what this argument means / expected values.
- `box` (`Optional[npt.NDArray]`), default `None`: TODO — what this argument means / expected values.
- `result` (`Optional[npt.NDArray]`), default `None`: TODO — what this argument means / expected values.
- `backend` (`str`), default `'serial'`: TODO — what this argument means / expected values.

### Input
TODO: the data, file formats, and preconditions the caller must provide.

### Output
Returns `npt.NDArray` — TODO: what the value represents and its format.

### Valid Call Patterns
```python
TODO
```

### LLM Instruction Prompt
- TODO: rules an LLM must follow when calling `python:MDAnalysis.lib.distances.calc_bonds`.

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

