"""Run the staged receiver change against the unchanged evaluator release."""
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
release = Path("/tmp/aideal-launch-2026-11-17/recovery-release")
overlay = Path(__file__).resolve().parent
sys.path.insert(0, str(release / "tests"))
sys.path.insert(0, str(release / "vendor/aideal_engine/src"))
import aideal
aideal.__path__.insert(0, str(overlay / "vendor/aideal_engine/src/aideal"))
suite = unittest.TestSuite()
for path in [overlay / "tests/test_constructor_receiver_hints.py",
             release / "tests/test_doc_check_owner_overrides.py",
             release / "tests/test_canonical_prompt_targets.py"]:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
