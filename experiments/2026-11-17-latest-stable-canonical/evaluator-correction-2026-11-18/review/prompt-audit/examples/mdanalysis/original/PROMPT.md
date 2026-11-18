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
