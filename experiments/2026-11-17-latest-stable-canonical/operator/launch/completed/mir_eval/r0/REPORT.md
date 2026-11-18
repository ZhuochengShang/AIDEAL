# Fix-loop report — result

_Generated 2026-11-17 17:15 by `aideal fix-report`._

- kind: **comprehension**  ·  run_id: `20261118-010233Z`  ·  models: audience=google:gemini-3.1-flash-lite, fixer=google:gemini-3.1-flash-lite
- pass **128/178** raw (71.9%)  ·  scored **128/178** (71.9%) after excluding 0 infra
- wall 0.22 h  ·  tokens in 400,170 / out 31,869 ·  llm calls 178  ·  max_fix_rounds 0
- pass-by-round: r0:128  ·  **0 rescued by the fix loop** (pass@0 = 128)

## Failure clusters (one issue, many APIs)

_Current failures grouped by normalized error signature (identifiers masked). Fixing the top cluster's root cause pays across all its APIs._

- **9x** [runtime] AssertionError:
  - `python:mir_eval.alignment.evaluate`, `python:mir_eval.chord.evaluate`, `python:mir_eval.chord.join`, `python:mir_eval.chord.merge_chord_intervals`, `python:mir_eval.chord.reduce_extended_quality`, `python:mir_eval.display.events`, `python:mir_eval.display.piano_roll`, `python:mir_eval.segment.evaluate`, `python:mir_eval.separation.evaluate`
- **4x** [runtime] FileNotFoundError: [Errno 2] No such file or directory: <name>
  - `python:mir_eval.io.load_patterns`, `python:mir_eval.pattern.first_n_three_layer_P`, `python:mir_eval.pattern.occurrence_FPR`, `python:mir_eval.pattern.standard_FPR`
- **4x** [runtime] TypeError: object of type <name> has no len()
  - `python:mir_eval.multipitch.compute_num_freqs`, `python:mir_eval.pattern.establishment_FPR`, `python:mir_eval.pattern.evaluate`, `python:mir_eval.pattern.validate`
- **4x** [runtime] ValueError: Reference intervals and pitches have different lengths.
  - `python:mir_eval.transcription.evaluate`, `python:mir_eval.transcription.precision_recall_f1_overlap`, `python:mir_eval.transcription.validate`, `python:mir_eval.transcription_velocity.precision_recall_f1_overlap`
- **3x** [runtime] ValueError: Expected 2 columns, got 1 at /home/zshan011/apps/aideal/studies/<num>-11-17-latest-stable-canonical/sources/mir_eval/tests/data/
  - `python:mir_eval.io.load_delimited`, `python:mir_eval.io.load_labeled_events`, `python:mir_eval.io.load_time_series`
- **3x** [runtime] ValueError: <name> is not in the form <name> or <name>
  - `python:mir_eval.key.evaluate`, `python:mir_eval.key.validate`, `python:mir_eval.key.weighted_score`
- **2x** [runtime] ValueError: Reference times and frequencies have unequal lengths.
  - `python:mir_eval.multipitch.evaluate`, `python:mir_eval.multipitch.validate`
- **2x** [runtime] ValueError: A frequency of 0.0 was found which is less than the minimum allowable value <name> min_freq = 20.0 (did you supply frequency val
  - `python:mir_eval.multipitch.metrics`, `python:mir_eval.util.validate_frequencies`
- **2x** [runtime] TypeError: <name> not supported between instances of <name> and <name>
  - `python:mir_eval.multipitch.midi_to_chroma`, `python:mir_eval.util.adjust_events`
- **2x** [runtime] ValueError: operands could not be broadcast together with shapes (4,4) (5,5)
  - `python:mir_eval.transcription.match_notes`, `python:mir_eval.transcription_velocity.match_notes`
- **1x** [runtime] AssertionError: Expected C:maj, got G:maj
  - `python:mir_eval.display.IntervalFormatter`
- **1x** [runtime] TypeError: IntervalFormatter.__init__() missing 1 required positional argument: <name>
  - `python:mir_eval.display.IntervalFormatter.__call__`

## Why each API fails (50 failing)

### `python:mir_eval.alignment.evaluate` — runtime

- canonical source: `source/mir_eval/alignment.py:312`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.chord.evaluate` — runtime

- canonical source: `source/mir_eval/chord.py:1524`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.chord.join` — runtime

- canonical source: `source/mir_eval/chord.py:435`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.chord.merge_chord_intervals` — runtime

- canonical source: `source/mir_eval/chord.py:1489`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.chord.reduce_extended_quality` — runtime

- canonical source: `source/mir_eval/chord.py:318`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.display.IntervalFormatter` — runtime

- canonical source: `source/mir_eval/display.py:364`
- last error: AssertionError: Expected C:maj, got G:maj
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected C:maj, got G:maj

### `python:mir_eval.display.IntervalFormatter.__call__` — runtime

- canonical source: `source/mir_eval/display.py:379`
- last error: TypeError: IntervalFormatter.__init__() missing 1 required positional argument: 'ticks'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: IntervalFormatter.__init__() missing 1 required positional argument: 'ticks'

### `python:mir_eval.display.events` — runtime

- canonical source: `source/mir_eval/display.py:429`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.display.multipitch` — runtime

- canonical source: `source/mir_eval/display.py:648`
- last error: IndexError: tuple index out of range
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IndexError: tuple index out of range

### `python:mir_eval.display.piano_roll` — runtime

- canonical source: `source/mir_eval/display.py:759`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.io.load_delimited` — runtime

- canonical source: `source/mir_eval/io.py:32` · reached: `source/mir_eval/io.py:98`
- last error: ValueError: Expected 2 columns, got 1 at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/ref00.txt:1:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Expected 2 columns, got 1 at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/ref00.

### `python:mir_eval.io.load_intervals` — runtime

- canonical source: `source/mir_eval/io.py:206` · reached: `source/mir_eval/io.py:106`, `source/mir_eval/io.py:234`, `source/mir_eval/io.py:108`
- last error: ValueError: Couldn't convert value 0.7353 N using float found at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/chord/ref00.lab:1:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Couldn't convert value 0.7353 N using float found at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eva

### `python:mir_eval.io.load_key` — runtime

- canonical source: `source/mir_eval/io.py:497` · reached: `source/mir_eval/io.py:529`
- last error: ValueError: Key file should contain only one line.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Key file should contain only one line.

### `python:mir_eval.io.load_labeled_events` — runtime

- canonical source: `source/mir_eval/io.py:162` · reached: `source/mir_eval/io.py:193`, `source/mir_eval/io.py:98`
- last error: ValueError: Expected 2 columns, got 1 at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/ref00.txt:1:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Expected 2 columns, got 1 at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/ref00.

### `python:mir_eval.io.load_patterns` — runtime

- canonical source: `source/mir_eval/io.py:331` · reached: `source/mir_eval/io.py:380`, `source/mir_eval/io.py:26`
- last error: FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/patterns/example.txt'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/patterns/example.txt'

### `python:mir_eval.io.load_tempo` — runtime

- canonical source: `source/mir_eval/io.py:542` · reached: `source/mir_eval/io.py:572`, `source/mir_eval/io.py:98`
- last error: ValueError: Expected 3 columns, got 1 at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/ref00.txt:1:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Expected 3 columns, got 1 at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/ref00.

### `python:mir_eval.io.load_time_series` — runtime

- canonical source: `source/mir_eval/io.py:293` · reached: `source/mir_eval/io.py:322`, `source/mir_eval/io.py:98`
- last error: ValueError: Expected 2 columns, got 1 at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/ref00.txt:1:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Expected 2 columns, got 1 at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/ref00.

### `python:mir_eval.io.load_valued_intervals` — runtime

- canonical source: `source/mir_eval/io.py:448` · reached: `source/mir_eval/io.py:106`, `source/mir_eval/io.py:480`, `source/mir_eval/io.py:108`
- last error: ValueError: Couldn't convert value N using float found at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/chord/ref00.lab:1:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Couldn't convert value N using float found at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests

### `python:mir_eval.io.load_wav` — runtime

- canonical source: `source/mir_eval/io.py:409` · reached: `source/mir_eval/__init__.py:247`, `source/mir_eval/util.py:960`, `source/mir_eval/io.py:432`
- last error: ValueError: File format b'5.98' not understood. Only 'RIFF', 'RIFX', and 'RF64' supported.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: File format b'5.98' not understood. Only 'RIFF', 'RIFX', and 'RF64' supported.

### `python:mir_eval.key.evaluate` — runtime

- canonical source: `source/mir_eval/key.py:184` · reached: `source/mir_eval/key.py:212`, `source/mir_eval/util.py:889`, `source/mir_eval/key.py:152`
- last error: ValueError: 'C:maj' is not in the form '(key) (mode)' or 'X'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: 'C:maj' is not in the form '(key) (mode)' or 'X'

### `python:mir_eval.key.validate` — runtime

- canonical source: `source/mir_eval/key.py:77` · reached: `source/mir_eval/key.py:89`, `source/mir_eval/key.py:57`
- last error: ValueError: 'C:maj' is not in the form '(key) (mode)' or 'X'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: 'C:maj' is not in the form '(key) (mode)' or 'X'

### `python:mir_eval.key.weighted_score` — runtime

- canonical source: `source/mir_eval/key.py:116` · reached: `source/mir_eval/key.py:152`, `source/mir_eval/key.py:89`, `source/mir_eval/key.py:57`
- last error: ValueError: 'C:maj' is not in the form '(key) (mode)' or 'X'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: 'C:maj' is not in the form '(key) (mode)' or 'X'

### `python:mir_eval.melody.raw_chroma_accuracy` — runtime

- canonical source: `source/mir_eval/melody.py:622`
- last error: TypeError: to_cent_voicing() missing 2 required positional arguments: 'est_time' and 'est_freq'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: to_cent_voicing() missing 2 required positional arguments: 'est_time' and 'est_freq'

### `python:mir_eval.multipitch.compute_num_freqs` — runtime

- canonical source: `source/mir_eval/multipitch.py:191`
- last error: TypeError: object of type 'numpy.float64' has no len()
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: object of type 'numpy.float64' has no len()

### `python:mir_eval.multipitch.compute_num_true_positives` — runtime

- canonical source: `source/mir_eval/multipitch.py:207` · reached: `source/mir_eval/multipitch.py:242`, `source/mir_eval/util.py:679`, `source/mir_eval/util.py:724`
- last error: IndexError: too many indices for array: array is 0-dimensional, but 1 were indexed
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IndexError: too many indices for array: array is 0-dimensional, but 1 were indexed

### `python:mir_eval.multipitch.evaluate` — runtime

- canonical source: `source/mir_eval/multipitch.py:479` · reached: `source/mir_eval/multipitch.py:529`, `source/mir_eval/util.py:878`, `source/mir_eval/multipitch.py:409`
- last error: ValueError: Reference times and frequencies have unequal lengths.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Reference times and frequencies have unequal lengths.

### `python:mir_eval.multipitch.metrics` — runtime

- canonical source: `source/mir_eval/multipitch.py:349` · reached: `source/mir_eval/multipitch.py:409`, `source/mir_eval/multipitch.py:92`, `source/mir_eval/util.py:824`
- last error: ValueError: A frequency of 0.0 was found which is less than the minimum allowable value of min_freq = 20.0 (did you supply frequency values in Hz?)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: A frequency of 0.0 was found which is less than the minimum allowable value of min_freq = 20.0 (did you supply frequency values in Hz?)

### `python:mir_eval.multipitch.midi_to_chroma` — runtime

- canonical source: `source/mir_eval/multipitch.py:174`
- last error: TypeError: '>=' not supported between instances of 'list' and 'int'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: '>=' not supported between instances of 'list' and 'int'

### `python:mir_eval.multipitch.resample_multipitch` — runtime

- canonical source: `source/mir_eval/multipitch.py:102` · reached: `source/mir_eval/multipitch.py:137`
- last error: ValueError: x and y arrays must be equal in length along interpolation axis.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: x and y arrays must be equal in length along interpolation axis.

### `python:mir_eval.multipitch.validate` — runtime

- canonical source: `source/mir_eval/multipitch.py:57` · reached: `source/mir_eval/multipitch.py:87`
- last error: ValueError: Reference times and frequencies have unequal lengths.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Reference times and frequencies have unequal lengths.

### `python:mir_eval.pattern.establishment_FPR` — runtime

- canonical source: `source/mir_eval/pattern.py:238` · reached: `source/mir_eval/pattern.py:278`, `source/mir_eval/pattern.py:106`
- last error: TypeError: object of type 'float' has no len()
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: object of type 'float' has no len()

### `python:mir_eval.pattern.evaluate` — runtime

- canonical source: `source/mir_eval/pattern.py:597` · reached: `source/mir_eval/pattern.py:627`, `source/mir_eval/util.py:889`, `source/mir_eval/pattern.py:208`
- last error: TypeError: object of type 'float' has no len()
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: object of type 'float' has no len()

### `python:mir_eval.pattern.first_n_target_proportion_R` — runtime

- canonical source: `source/mir_eval/pattern.py:554` · reached: `source/mir_eval/io.py:396`
- last error: IndexError: list index out of range
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] IndexError: list index out of range

### `python:mir_eval.pattern.first_n_three_layer_P` — runtime

- canonical source: `source/mir_eval/pattern.py:509` · reached: `source/mir_eval/io.py:380`, `source/mir_eval/io.py:26`
- last error: FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/pattern/ref_pattern.txt'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/pattern/ref_pattern.txt'

### `python:mir_eval.pattern.occurrence_FPR` — runtime

- canonical source: `source/mir_eval/pattern.py:299` · reached: `source/mir_eval/io.py:380`, `source/mir_eval/io.py:26`
- last error: FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/pattern/ref_pattern.txt'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/pattern/ref_pattern.txt'

### `python:mir_eval.pattern.standard_FPR` — runtime

- canonical source: `source/mir_eval/pattern.py:171` · reached: `source/mir_eval/io.py:380`, `source/mir_eval/io.py:26`
- last error: FileNotFoundError: [Errno 2] No such file or directory: 'ref_pattern.txt'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundError: [Errno 2] No such file or directory: 'ref_pattern.txt'

### `python:mir_eval.pattern.three_layer_FPR` — runtime

- canonical source: `source/mir_eval/pattern.py:382` · reached: `source/mir_eval/pattern.py:410`, `source/mir_eval/pattern.py:94`, `source/mir_eval/pattern.py:78`
- last error: TypeError: 'numpy.float64' object is not iterable
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: 'numpy.float64' object is not iterable

### `python:mir_eval.pattern.validate` — runtime

- canonical source: `source/mir_eval/pattern.py:81` · reached: `source/mir_eval/pattern.py:106`
- last error: TypeError: object of type 'float' has no len()
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: object of type 'float' has no len()

### `python:mir_eval.segment.evaluate` — runtime

- canonical source: `source/mir_eval/segment.py:1181`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.separation.evaluate` — runtime

- canonical source: `source/mir_eval/separation.py:854`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.tempo.validate` — runtime

- canonical source: `source/mir_eval/tempo.py:52`
- last error: AssertionError: Validation failed for valid tempo inputs
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Validation failed for valid tempo inputs

### `python:mir_eval.transcription.evaluate` — runtime

- canonical source: `source/mir_eval/transcription.py:785` · reached: `source/mir_eval/transcription.py:829`, `source/mir_eval/util.py:889`, `source/mir_eval/transcription.py:566`
- last error: ValueError: Reference intervals and pitches have different lengths.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Reference intervals and pitches have different lengths.

### `python:mir_eval.transcription.match_notes` — runtime

- canonical source: `source/mir_eval/transcription.py:336` · reached: `source/mir_eval/transcription.py:458`
- last error: ValueError: operands could not be broadcast together with shapes (4,4) (5,5)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: operands could not be broadcast together with shapes (4,4) (5,5)

### `python:mir_eval.transcription.precision_recall_f1_overlap` — runtime

- canonical source: `source/mir_eval/transcription.py:477` · reached: `source/mir_eval/transcription.py:566`, `source/mir_eval/transcription.py:137`
- last error: ValueError: Reference intervals and pitches have different lengths.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Reference intervals and pitches have different lengths.

### `python:mir_eval.transcription.validate` — runtime

- canonical source: `source/mir_eval/transcription.py:117` · reached: `source/mir_eval/transcription.py:137`
- last error: ValueError: Reference intervals and pitches have different lengths.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Reference intervals and pitches have different lengths.

### `python:mir_eval.transcription_velocity.evaluate` — runtime

- canonical source: `source/mir_eval/transcription_velocity.py:359`
- last error: AssertionError: Missing keys in scores: odict_keys(['Precision', 'Recall', 'F-measure', 'Average_Overlap_Ratio', 'Precision_no_offset', 'Recall_no_offset', 'F-measure_no_offset', 'Average_Overlap_Ratio_no_offset'])
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Missing keys in scores: odict_keys(['Precision', 'Recall', 'F-measure', 'Average_Overlap_Ratio', 'Precision_no_offset', 'Recall_no_off

### `python:mir_eval.transcription_velocity.match_notes` — runtime

- canonical source: `source/mir_eval/transcription_velocity.py:107` · reached: `source/mir_eval/transcription_velocity.py:182`, `source/mir_eval/transcription.py:458`
- last error: ValueError: operands could not be broadcast together with shapes (4,4) (5,5)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: operands could not be broadcast together with shapes (4,4) (5,5)

### `python:mir_eval.transcription_velocity.precision_recall_f1_overlap` — runtime

- canonical source: `source/mir_eval/transcription_velocity.py:230` · reached: `source/mir_eval/transcription_velocity.py:321`, `source/mir_eval/transcription_velocity.py:88`, `source/mir_eval/transcription.py:137`
- last error: ValueError: Reference intervals and pitches have different lengths.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Reference intervals and pitches have different lengths.

### `python:mir_eval.util.adjust_events` — runtime

- canonical source: `source/mir_eval/util.py:359`
- last error: TypeError: '>=' not supported between instances of 'tuple' and 'float'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: '>=' not supported between instances of 'tuple' and 'float'

### `python:mir_eval.util.validate_frequencies` — runtime

- canonical source: `source/mir_eval/util.py:794` · reached: `source/mir_eval/util.py:824`
- last error: ValueError: A frequency of 0.0 was found which is less than the minimum allowable value of min_freq = 20.0 (did you supply frequency values in Hz?)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: A frequency of 0.0 was found which is less than the minimum allowable value of min_freq = 20.0 (did you supply frequency values in Hz?)
