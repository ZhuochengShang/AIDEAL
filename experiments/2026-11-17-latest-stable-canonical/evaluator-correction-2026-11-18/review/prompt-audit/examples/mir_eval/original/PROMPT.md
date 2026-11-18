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
