# Fix-loop report — result

_Generated 2026-11-18 09:33 by `aideal fix-report`._

- kind: **comprehension**  ·  run_id: `20261118-172101Z`  ·  models: audience=google:gemini-3.1-flash-lite, fixer=google:gemini-3.1-flash-lite
- pass **119/178** raw (66.9%)  ·  scored **119/178** (66.9%) after excluding 0 infra
- wall 0.21 h  ·  tokens in 436,815 / out 39,441 ·  llm calls 178  ·  max_fix_rounds 0
- pass-by-round: r0:119  ·  **0 rescued by the fix loop** (pass@0 = 119)

## Failure clusters (one issue, many APIs)

_Current failures grouped by normalized error signature (identifiers masked). Fixing the top cluster's root cause pays across all its APIs._

- **19x** [runtime] UnboundLocalError: cannot access local variable <name> where it is not associated with a value
  - `python:mir_eval.alignment.evaluate`, `python:mir_eval.chord.directional_hamming_distance`, `python:mir_eval.segment.detection`, `python:mir_eval.segment.deviation`, `python:mir_eval.segment.mutual_information`, `python:mir_eval.segment.pairwise`, `python:mir_eval.segment.rand_index`, `python:mir_eval.segment.validate_structure`, `python:mir_eval.segment.vmeasure`, `python:mir_eval.transcription.evaluate`, `python:mir_eval.transcription.match_note_offsets`, `python:mir_eval.transcription.match_note_onsets`, `python:mir_eval.transcription.offset_precision_recall_f1`, `python:mir_eval.transcription.onset_precision_recall_f1` …
- **6x** [runtime] AssertionError:
  - `python:mir_eval.chord.evaluate`, `python:mir_eval.chord.reduce_extended_quality`, `python:mir_eval.separation.bss_eval_images`, `python:mir_eval.separation.bss_eval_images_framewise`, `python:mir_eval.separation.evaluate`, `python:mir_eval.util.deprecated`
- **4x** [runtime] ValueError: <name> is not in the form <name> or <name>
  - `python:mir_eval.key.evaluate`, `python:mir_eval.key.validate`, `python:mir_eval.key.validate_key`, `python:mir_eval.key.weighted_score`
- **4x** [runtime] TypeError: object of type <name> has no len()
  - `python:mir_eval.pattern.first_n_target_proportion_R`, `python:mir_eval.pattern.occurrence_FPR`, `python:mir_eval.pattern.three_layer_FPR`, `python:mir_eval.pattern.validate`
- **3x** [runtime] ValueError: A frequency of 0.0 was found which is less than the minimum allowable value <name> min_freq = 20.0 (did you supply frequency val
  - `python:mir_eval.multipitch.evaluate`, `python:mir_eval.multipitch.metrics`, `python:mir_eval.util.validate_frequencies`
- **3x** [runtime] FileNotFoundError: [Errno 2] No such file or directory: <name>
  - `python:mir_eval.pattern.establishment_FPR`, `python:mir_eval.pattern.evaluate`, `python:mir_eval.pattern.first_n_three_layer_P`
- **2x** [runtime] AttributeError: <name> object has no attribute <name>
  - `python:mir_eval.chord.seg`, `python:mir_eval.display.IntervalFormatter`
- **2x** [runtime] ValueError: Expected 2 columns, got 1 at /home/zshan011/apps/aideal/studies/<num>-11-17-latest-stable-canonical/sources/mir_eval/tests/data/
  - `python:mir_eval.io.load_delimited`, `python:mir_eval.io.load_labeled_events`
- **1x** [runtime] AssertionError: Expected <name>, got C:maj(7)/5
  - `python:mir_eval.chord.join`
- **1x** [runtime] TypeError: only length-1 arrays can be converted to Python scalars
  - `python:mir_eval.display.IntervalFormatter.__call__`
- **1x** [runtime] AttributeError: module <name> has no attribute <name>
  - `python:mir_eval.display.events`
- **1x** [runtime] AssertionError: Ticker did not set y-axis to MIDI note integer values
  - `python:mir_eval.display.ticker_pitch`

## Why each API fails (59 failing)

### `python:mir_eval.alignment.evaluate` — runtime

- canonical source: `source/mir_eval/alignment.py:312`
- last error: UnboundLocalError: cannot access local variable 'ref_events' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_events' where it is not associated with a value

### `python:mir_eval.chord.directional_hamming_distance` — runtime

- canonical source: `source/mir_eval/chord.py:1358`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.chord.evaluate` — runtime

- canonical source: `source/mir_eval/chord.py:1524`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.chord.join` — runtime

- canonical source: `source/mir_eval/chord.py:435`
- last error: AssertionError: Expected 'C:maj7/5', got C:maj(7)/5
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected 'C:maj7/5', got C:maj(7)/5

### `python:mir_eval.chord.reduce_extended_quality` — runtime

- canonical source: `source/mir_eval/chord.py:318`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.chord.seg` — runtime

- canonical source: `source/mir_eval/chord.py:1460` · reached: `source/mir_eval/chord.py:1484`, `source/mir_eval/chord.py:1457`, `source/mir_eval/chord.py:1389`
- last error: AttributeError: 'tuple' object has no attribute 'ndim'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'tuple' object has no attribute 'ndim'

### `python:mir_eval.display.IntervalFormatter` — runtime

- canonical source: `source/mir_eval/display.py:364`
- last error: AttributeError: 'IntervalFormatter' object has no attribute 'base'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: 'IntervalFormatter' object has no attribute 'base'

### `python:mir_eval.display.IntervalFormatter.__call__` — runtime

- canonical source: `source/mir_eval/display.py:379` · reached: `source/mir_eval/display.py:377`
- last error: TypeError: only length-1 arrays can be converted to Python scalars
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: only length-1 arrays can be converted to Python scalars

### `python:mir_eval.display.events` — runtime

- canonical source: `source/mir_eval/display.py:429`
- last error: AttributeError: module 'matplotlib.pyplot' has no attribute 'LineCollection'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AttributeError: module 'matplotlib.pyplot' has no attribute 'LineCollection'

### `python:mir_eval.display.ticker_pitch` — runtime

- canonical source: `source/mir_eval/display.py:981`
- last error: AssertionError: Ticker did not set y-axis to MIDI note integer values
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Ticker did not set y-axis to MIDI note integer values

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

- canonical source: `source/mir_eval/io.py:497`
- last error: AssertionError: Test fixture tests/data/key/test_key.txt not found.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Test fixture tests/data/key/test_key.txt not found.

### `python:mir_eval.io.load_labeled_events` — runtime

- canonical source: `source/mir_eval/io.py:162` · reached: `source/mir_eval/io.py:193`, `source/mir_eval/io.py:98`
- last error: ValueError: Expected 2 columns, got 1 at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/ref00.txt:1:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Expected 2 columns, got 1 at /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/mir_eval/tests/data/beat/ref00.

### `python:mir_eval.io.load_patterns` — runtime

- canonical source: `source/mir_eval/io.py:331`
- last error: AssertionError: Test fixture tests/data/patterns/example.txt not found, cannot verify load_patterns.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Test fixture tests/data/patterns/example.txt not found, cannot verify load_patterns.

### `python:mir_eval.io.load_tempo` — runtime

- canonical source: `source/mir_eval/io.py:542`
- last error: FileNotFoundError: Test fixture tests/data/tempo/mirex_tempo.txt not found.
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundError: Test fixture tests/data/tempo/mirex_tempo.txt not found.

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

### `python:mir_eval.key.validate_key` — runtime

- canonical source: `source/mir_eval/key.py:46` · reached: `source/mir_eval/key.py:57`
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

### `python:mir_eval.multipitch.evaluate` — runtime

- canonical source: `source/mir_eval/multipitch.py:479` · reached: `source/mir_eval/multipitch.py:529`, `source/mir_eval/util.py:878`, `source/mir_eval/multipitch.py:409`
- last error: ValueError: A frequency of 0.0 was found which is less than the minimum allowable value of min_freq = 20.0 (did you supply frequency values in Hz?)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: A frequency of 0.0 was found which is less than the minimum allowable value of min_freq = 20.0 (did you supply frequency values in Hz?)

### `python:mir_eval.multipitch.metrics` — runtime

- canonical source: `source/mir_eval/multipitch.py:349` · reached: `source/mir_eval/multipitch.py:409`, `source/mir_eval/multipitch.py:92`, `source/mir_eval/util.py:824`
- last error: ValueError: A frequency of 0.0 was found which is less than the minimum allowable value of min_freq = 20.0 (did you supply frequency values in Hz?)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: A frequency of 0.0 was found which is less than the minimum allowable value of min_freq = 20.0 (did you supply frequency values in Hz?)

### `python:mir_eval.pattern.establishment_FPR` — runtime

- canonical source: `source/mir_eval/pattern.py:238` · reached: `source/mir_eval/io.py:380`, `source/mir_eval/io.py:26`
- last error: FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/pattern/ref_pattern.txt'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/pattern/ref_pattern.txt'

### `python:mir_eval.pattern.evaluate` — runtime

- canonical source: `source/mir_eval/pattern.py:597` · reached: `source/mir_eval/io.py:380`, `source/mir_eval/io.py:26`
- last error: FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/pattern/ref.txt'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/pattern/ref.txt'

### `python:mir_eval.pattern.first_n_target_proportion_R` — runtime

- canonical source: `source/mir_eval/pattern.py:554` · reached: `source/mir_eval/pattern.py:585`, `source/mir_eval/pattern.py:106`
- last error: TypeError: object of type 'float' has no len()
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: object of type 'float' has no len()

### `python:mir_eval.pattern.first_n_three_layer_P` — runtime

- canonical source: `source/mir_eval/pattern.py:509` · reached: `source/mir_eval/io.py:380`, `source/mir_eval/io.py:26`
- last error: FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/pattern/ref_pattern.txt'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] FileNotFoundError: [Errno 2] No such file or directory: 'tests/data/pattern/ref_pattern.txt'

### `python:mir_eval.pattern.occurrence_FPR` — runtime

- canonical source: `source/mir_eval/pattern.py:299` · reached: `source/mir_eval/pattern.py:346`, `source/mir_eval/pattern.py:106`
- last error: TypeError: object of type 'float' has no len()
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: object of type 'float' has no len()

### `python:mir_eval.pattern.standard_FPR` — runtime

- canonical source: `source/mir_eval/pattern.py:171`
- last error: NameError: name 'pattern_reference_file' is not defined
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] NameError: name 'pattern_reference_file' is not defined

### `python:mir_eval.pattern.three_layer_FPR` — runtime

- canonical source: `source/mir_eval/pattern.py:382` · reached: `source/mir_eval/pattern.py:410`, `source/mir_eval/pattern.py:106`
- last error: TypeError: object of type 'float' has no len()
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: object of type 'float' has no len()

### `python:mir_eval.pattern.validate` — runtime

- canonical source: `source/mir_eval/pattern.py:81` · reached: `source/mir_eval/pattern.py:106`
- last error: TypeError: object of type 'float' has no len()
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: object of type 'float' has no len()

### `python:mir_eval.segment.detection` — runtime

- canonical source: `source/mir_eval/segment.py:168`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.segment.deviation` — runtime

- canonical source: `source/mir_eval/segment.py:252`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.segment.evaluate` — runtime

- canonical source: `source/mir_eval/segment.py:1181` · reached: `source/mir_eval/util.py:319`
- last error: ValueError: operands could not be broadcast together with shapes (4,) (4,2)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: operands could not be broadcast together with shapes (4,) (4,2)

### `python:mir_eval.segment.mutual_information` — runtime

- canonical source: `source/mir_eval/segment.py:869`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.segment.pairwise` — runtime

- canonical source: `source/mir_eval/segment.py:310`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.segment.rand_index` — runtime

- canonical source: `source/mir_eval/segment.py:413`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.segment.validate_structure` — runtime

- canonical source: `source/mir_eval/segment.py:121`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.segment.vmeasure` — runtime

- canonical source: `source/mir_eval/segment.py:1100`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.separation.bss_eval_images` — runtime

- canonical source: `source/mir_eval/separation.py:373`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.separation.bss_eval_images_framewise` — runtime

- canonical source: `source/mir_eval/separation.py:508`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.separation.bss_eval_sources_framewise` — runtime

- canonical source: `source/mir_eval/separation.py:261`
- last error: AssertionError: Expected shape (2, -1), got (2, 1)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError: Expected shape (2, -1), got (2, 1)

### `python:mir_eval.separation.evaluate` — runtime

- canonical source: `source/mir_eval/separation.py:854`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.transcription.average_overlap_ratio` — runtime

- canonical source: `source/mir_eval/transcription.py:592`
- last error: TypeError: validate_intervals() missing 1 required positional argument: 'est_intervals'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: validate_intervals() missing 1 required positional argument: 'est_intervals'

### `python:mir_eval.transcription.evaluate` — runtime

- canonical source: `source/mir_eval/transcription.py:785`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.transcription.match_note_offsets` — runtime

- canonical source: `source/mir_eval/transcription.py:170`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.transcription.match_note_onsets` — runtime

- canonical source: `source/mir_eval/transcription.py:263`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.transcription.offset_precision_recall_f1` — runtime

- canonical source: `source/mir_eval/transcription.py:706`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.transcription.onset_precision_recall_f1` — runtime

- canonical source: `source/mir_eval/transcription.py:644`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.transcription.precision_recall_f1_overlap` — runtime

- canonical source: `source/mir_eval/transcription.py:477` · reached: `source/mir_eval/transcription.py:566`, `source/mir_eval/transcription.py:143`
- last error: ValueError: Reference contains at least one non-positive pitch value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: Reference contains at least one non-positive pitch value

### `python:mir_eval.transcription.validate` — runtime

- canonical source: `source/mir_eval/transcription.py:117`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.transcription.validate_intervals` — runtime

- canonical source: `source/mir_eval/transcription.py:148`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.transcription_velocity.evaluate` — runtime

- canonical source: `source/mir_eval/transcription_velocity.py:359`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.transcription_velocity.match_notes` — runtime

- canonical source: `source/mir_eval/transcription_velocity.py:107`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.transcription_velocity.precision_recall_f1_overlap` — runtime

- canonical source: `source/mir_eval/transcription_velocity.py:230`
- last error: UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] UnboundLocalError: cannot access local variable 'ref_intervals' where it is not associated with a value

### `python:mir_eval.util.adjust_events` — runtime

- canonical source: `source/mir_eval/util.py:359`
- last error: TypeError: '>=' not supported between instances of 'tuple' and 'float'
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] TypeError: '>=' not supported between instances of 'tuple' and 'float'

### `python:mir_eval.util.deprecated` — runtime

- canonical source: `source/mir_eval/util.py:946`
- last error: AssertionError:
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] AssertionError:

### `python:mir_eval.util.validate_frequencies` — runtime

- canonical source: `source/mir_eval/util.py:794` · reached: `source/mir_eval/util.py:824`
- last error: ValueError: A frequency of 0.0 was found which is less than the minimum allowable value of min_freq = 20.0 (did you supply frequency values in Hz?)
- loop trajectory: **PROGRESSING (error changed every round, 1 rounds)**
- rounds:
  - r0 [runtime] ValueError: A frequency of 0.0 was found which is less than the minimum allowable value of min_freq = 20.0 (did you supply frequency values in Hz?)
