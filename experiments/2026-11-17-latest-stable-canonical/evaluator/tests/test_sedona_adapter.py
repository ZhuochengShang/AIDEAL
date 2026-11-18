import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/sedonadb'))
from unittest.mock import patch

from aideal.api_registry import registered_sql_details
from run_snippet import validate_snippet
from sedona_runtime import TrackedContext, calls_function, initialize_sedona, _database_identity


class FakeFrame:
    def to_arrow_table(self):
        return object()

    def execute(self):
        return None


class FakeContext:
    def sql(self, query, **kwargs):
        return FakeFrame()


class AdapterTests(unittest.TestCase):
    def test_native_configuration_must_precede_package_import(self):
        with patch.dict("sys.modules", {"sedonadb": object()}):
            with self.assertRaisesRegex(RuntimeError, "before importing"):
                initialize_sedona()

    def test_projection_database_identity_records_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "proj.db"
            with sqlite3.connect(path) as database:
                database.execute("CREATE TABLE metadata (key TEXT, value TEXT)")
                database.execute("INSERT INTO metadata VALUES ('DATABASE.LAYOUT.VERSION.MINOR','6')")
            identity = _database_identity(path)
            self.assertEqual(identity["layout"]["DATABASE.LAYOUT.VERSION.MINOR"], "6")
            self.assertEqual(identity["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_sql_function_detection(self):
        self.assertTrue(calls_function("SELECT st_area /* comment */ (x)", "ST_Area"))
        self.assertTrue(calls_function('SELECT "st_area"(x)', "ST_Area"))
        self.assertFalse(calls_function("SELECT 'ST_Area(x)'", "ST_Area"))
        self.assertFalse(calls_function("SELECT 1 -- ST_Area(x)", "ST_Area"))
        self.assertFalse(calls_function("SELECT other_st_area(x)", "ST_Area"))

    def test_actual_materialization_required(self):
        ctx = TrackedContext("ST_Area", FakeContext())
        frame = ctx.sql("SELECT ST_Area(x)")
        with self.assertRaises(AssertionError):
            ctx.verify()
        frame.to_arrow_table()
        ctx.verify()

    def test_non_target_execution_rejected(self):
        ctx = TrackedContext("ST_Area", FakeContext())
        ctx.sql("SELECT ST_Length(x)").execute()
        with self.assertRaises(AssertionError):
            ctx.verify()

    def test_assertion_required(self):
        validate_snippet("# TODO API_TEST_START\nassert value == 6\n# TODO API_TEST_END")
        with self.assertRaises(ValueError):
            validate_snippet("# TODO API_TEST_START\nprint('__CHECK__ ST_Area 6')\n# TODO API_TEST_END")

    def test_source_and_inventory_are_hash_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "st_area.qmd"
            source.write_text("title: ST_Area\n")
            definition = {"name": "ST_Area", "file": "st_area.qmd", "line": 1,
                          "file_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                          "signature": "ST_Area(geometry) -> double", "params": [],
                          "returns": "double", "description": "Area"}
            inventory = root / "inventory.json"
            inventory.write_text(json.dumps({"schema": 1, "kind": "registered_sql",
                                            "registered_names": ["st_area"], "definitions": [definition]}))
            cfg = SimpleNamespace(root=root, surface_filter="all", exclude_names=[], raw={"codebase": {
                "api_inventory": "inventory.json", "api_inventory_sha256": hashlib.sha256(inventory.read_bytes()).hexdigest()}})
            self.assertEqual(registered_sql_details(cfg)[0]["definition_kind"], "registered_sql")
            source.write_text("changed")
            with self.assertRaises(ValueError):
                registered_sql_details(cfg)
            source.write_text("title: ST_Area\n")
            inventory.write_text(inventory.read_text() + "\n")
            with self.assertRaises(ValueError):
                registered_sql_details(cfg)


if __name__ == "__main__":
    unittest.main()
