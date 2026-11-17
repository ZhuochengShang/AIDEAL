"""Offline source-origin contracts; fixture text is parsed, never imported."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/aideal_engine/src"))
import aideal
STAGED_PACKAGE = str(ROOT / "vendor/aideal_engine/src/aideal")
if STAGED_PACKAGE not in aideal.__path__:
    aideal.__path__.insert(0, STAGED_PACKAGE)
from aideal.api_origin import audit_api_origins, filter_api_origins
from aideal.api_discovery import api_origin_audit, public_api_details, public_api_surface, render_api_surface


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OriginTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "source"; self.source.mkdir()
        self.file = self.source / "Tools.java"
        self.file.write_text("package ownlib; class Tools { public int map(int x) { return spark.map(x); } }")
        self.cfg = SimpleNamespace(root=self.root, language="Java", project_name="fixture",
            surface_filter="all", exclude_names=[], visibility={}, source_globs=["source/*.java"],
            test_globs=[], public_def_regex=r"\b(?:def|class)\s+(\w+)",
            raw={"codebase": {"api_origin": {
                "source_roots": ["source"], "library_namespaces": ["ownlib"],
                "external_namespaces": ["java", "org.apache.spark", "math", "builtins", "foreign"]}}})

    def row(self, **changes):
        result={"name":"map", "qualified_name":"ownlib.Tools.map", "owner":"ownlib.Tools",
                "module":"Java:class", "definition_kind":"compiler_declared_method",
                "file":"source/Tools.java", "line":1, "file_sha256":sha(self.file),
                "signature":"public int map(int x)", "params":[], "returns":"int",
                "description":"", "visibility":"public", "site_id":"custom-map"}
        return {**result, **changes}

    def test_disabled_is_exact_backward_compatibility(self):
        self.cfg.raw={"codebase":{}}
        rows=[self.row(),self.row(qualified_name="java.lang.Object.toString")]
        self.assertIs(rows,filter_api_origins(self.cfg,rows))
        with patch("aideal.api_discovery.configured_api_details",return_value=rows):
            self.assertIs(rows,public_api_details(self.cfg))
            self.assertEqual({"map"},public_api_surface(self.cfg))
        self.assertNotIn("api_origin",rows[0])

    def test_source_caller_not_called_dependency_and_custom_override_kept(self):
        rows=[self.row(name="mapPixels",qualified_name="ownlib.Tools.mapPixels"),
              self.row(name="toString",qualified_name="ownlib.Tools.toString",is_override=True)]
        result=audit_api_origins(self.cfg,rows)
        self.assertEqual({"library_defined":2},result["counts"])
        self.assertEqual({"mapPixels","toString"},{r["name"]for r in result["included"]})

    def test_external_defining_owner_beats_local_exposure_and_same_bare_name(self):
        rows=[self.row(),self.row(qualified_name="ownlib.Tools.map",inherited=True,
                                defining_owner="org.apache.spark.rdd.RDD",site_id="spark-map"),
              self.row(name="toString",qualified_name="ownlib.Tools.toString",
                       defining_owner="java.lang.Object",inherited=True)]
        result=audit_api_origins(self.cfg,rows)
        self.assertEqual({"library_defined":1,"external_defined":2},result["counts"])
        self.assertEqual(["custom-map"],[r["site_id"]for r in result["included"]])

    def test_python_import_only_math_and_inherited_without_binding(self):
        rows=[self.row(name="sqrt",qualified_name="ownlib.sqrt",defining_owner="math",import_only=True),
              self.row(inherited=True),self.row(import_only=True)]
        audit=audit_api_origins(self.cfg,rows)
        self.assertEqual([],audit["included"])
        self.assertEqual({"external_defined":1,"unresolved":2},audit["counts"])
        self.assertEqual("exposure_without_defining_source",audit["decisions"][1]["reason"])

    def test_owned_public_reexport_uses_actual_defining_file(self):
        exposure=self.source/"__init__.py";exposure.write_text("from ownlib.tools import map\n")
        row=self.row(file="source/__init__.py",file_sha256=sha(exposure),import_only=True,
                     defining_file="source/Tools.java",defining_file_sha256=sha(self.file),
                     defining_owner="ownlib.Tools")
        result=audit_api_origins(self.cfg,[row])
        self.assertEqual("library_defined",result["decisions"][0]["status"])
        row["defining_file_sha256"]="0"*64
        self.assertEqual("defining_file_hash_mismatch",audit_api_origins(self.cfg,[row])["decisions"][0]["reason"])

    def test_unknown_namespace_and_namespace_prefix_collision_remain_visible(self):
        rows=[self.row(qualified_name="unknown.Tools.map"),self.row(qualified_name="ownlibrary.Tools.map")]
        audit=audit_api_origins(self.cfg,rows)
        self.assertEqual({"unresolved":2},audit["counts"])
        self.assertFalse(audit["included"])

    def test_contradictory_defining_owners_are_unresolved(self):
        row=self.row(defining_owner="ownlib.Tools",declaring_owner="java.lang.Object")
        self.assertEqual("conflicting_defining_owner_evidence",audit_api_origins(self.cfg,[row])["decisions"][0]["reason"])

    def test_relative_python_defining_owner_uses_matching_module_identity(self):
        row=self.row(qualified_name="ownlib.tools.Tools.map",module="ownlib.tools",owner="Tools",defining_owner="Tools")
        self.assertEqual("library_defined",audit_api_origins(self.cfg,[row])["decisions"][0]["status"])

    def test_nested_relative_owner_and_constructor_identity_are_supported(self):
        for qualified in ["ownlib.tools.Outer.Inner.map","ownlib.tools.Outer.Inner"]:
            row=self.row(qualified_name=qualified,module="ownlib.tools",owner="Outer.Inner",defining_owner="Outer.Inner")
            with self.subTest(qualified=qualified):
                self.assertEqual("library_defined",audit_api_origins(self.cfg,[row])["decisions"][0]["status"])

    def test_symlink_loop_during_owner_normalization_remains_unresolved(self):
        loop=self.source/"loop.java";loop.symlink_to(loop.name)
        row=self.row(defining_file="source/loop.java",defining_owner="ownlib.Tools",module="ownlib")
        decision=audit_api_origins(self.cfg,[row])["decisions"][0]
        self.assertEqual("unresolved",decision["status"])
        self.assertEqual("unreadable_defining_source",decision["reason"])

    def test_defining_file_does_not_bypass_same_file_hash_claims(self):
        row=self.row(defining_file="source/Tools.java",file_sha256="0"*64)
        self.assertEqual("defining_file_hash_mismatch",audit_api_origins(self.cfg,[row])["decisions"][0]["reason"])
        row["defining_file_sha256"]=sha(self.file)
        self.assertEqual("defining_file_hash_mismatch",audit_api_origins(self.cfg,[row])["decisions"][0]["reason"])

    def test_file_symlink_escape_and_missing_file_rejected(self):
        outside=self.root/"outside.java";outside.write_text("class Outside {}")
        escape=self.source/"escape.java";escape.symlink_to(outside)
        rows=[self.row(file="source/escape.java",file_sha256=sha(outside)),self.row(file="source/missing.java")]
        result=audit_api_origins(self.cfg,rows)
        self.assertFalse(result["included"])
        self.assertTrue(result["decisions"][0]["symlink_escape"])
        self.assertEqual("unreadable_defining_source",result["decisions"][1]["reason"])

    def test_explicit_source_root_symlink_is_supported(self):
        link=self.root/"declared-root";link.symlink_to(self.source,target_is_directory=True)
        self.cfg.raw["codebase"]["api_origin"]["source_roots"]=["declared-root"]
        self.assertEqual(1,len(filter_api_origins(self.cfg,[self.row(file="declared-root/Tools.java")])))

    def test_hash_ownership_and_policy_changes_bind_decisions(self):
        row=self.row();first=audit_api_origins(self.cfg,[row]);again=audit_api_origins(self.cfg,[row])
        self.assertEqual(first,again)
        changed=audit_api_origins(self.cfg,[{**row,"signature":"different overload"}])
        self.assertNotEqual(first["decisions"][0]["ownership_sha256"],changed["decisions"][0]["ownership_sha256"])
        self.file.write_text(self.file.read_text()+"\n// source changed")
        changed=audit_api_origins(self.cfg,[row])
        self.assertEqual("defining_file_hash_mismatch",changed["decisions"][0]["reason"])
        self.cfg.raw["codebase"]["api_origin"]["external_namespaces"].append("another")
        self.assertNotEqual(first["policy_sha256"],audit_api_origins(self.cfg,[row])["policy_sha256"])

    def test_unpinned_source_hash_is_observed_not_claimed_prebound(self):
        row=self.row();del row["file_sha256"]
        decision=audit_api_origins(self.cfg,[row])["decisions"][0]
        self.assertEqual(sha(self.file),decision["file_sha256"])
        self.assertIsNone(decision["declared_file_sha256"])

    def test_invalid_and_conflicting_policy_is_not_silently_disabled(self):
        self.cfg.raw["codebase"]["api_origin"]=None
        with self.assertRaises(ValueError):audit_api_origins(self.cfg,[self.row()])
        self.cfg.raw["codebase"]["api_origin"]={"source_roots":["source"],"library_namespaces":["ownlib"],"external_namespaces":["ownlib"]}
        self.assertEqual("conflicting_namespace_rules",audit_api_origins(self.cfg,[self.row()])["decisions"][0]["reason"])

    def test_sql_docs_cannot_stand_in_for_registration_defining_source(self):
        self.cfg.raw["codebase"]["api_origin"]["library_namespaces"]=["SQL"]
        row=self.row(name="ST_Area",qualified_name="ST_Area",module="SQL",owner="",definition_kind="registered_sql")
        decision=audit_api_origins(self.cfg,[row])["decisions"][0]
        self.assertEqual("registered_sql_requires_defining_source_binding",decision["reason"])
        self.cfg.raw={"codebase":{}}
        self.assertEqual([row],filter_api_origins(self.cfg,[row]))

    def test_registered_details_surface_and_dump_use_same_site_policy(self):
        rows=[self.row(),self.row(qualified_name="java.util.Map.map",owner="java.util.Map"),
              self.row(name="unknown",qualified_name="mystery.unknown")]
        with patch("aideal.api_discovery.configured_api_details",return_value=rows):
            self.assertEqual(["ownlib.Tools.map"],[r["qualified_name"]for r in public_api_details(self.cfg)])
            self.assertEqual({"map"},public_api_surface(self.cfg))
            audit=api_origin_audit(self.cfg)
            dump=render_api_surface(self.cfg)
        self.assertEqual({"library_defined":1,"external_defined":1,"unresolved":1},audit["counts"])
        self.assertIn("external_defined: java.util.Map.map",dump)
        self.assertIn("unresolved: mystery.unknown",dump)

    def python_config(self):
        own=self.source/"ownlib";own.mkdir();(own/"__init__.py").write_text("")
        foreign=self.source/"foreign";foreign.mkdir();(foreign/"__init__.py").write_text("")
        self.cfg.language="Python";self.cfg.source_globs=["source/**/*.py"]
        self.cfg.public_def_regex=r"^\s*(?:def|class)\s+([A-Za-z_]\w*)"
        return own,foreign

    def test_real_python_discovery_does_not_import_dependencies_or_inherited_members(self):
        own,_=self.python_config()
        (own/"tools.py").write_text("from math import sqrt\nfrom pyspark import RDD\ndef mapPixels(x):\n    return sqrt(x)\nclass LocalRDD(RDD):\n    def map(self, f):\n        return super().map(f)\n")
        names=public_api_surface(self.cfg)
        self.assertEqual({"LocalRDD","map","mapPixels"},names)
        self.assertNotIn("sqrt",names);self.assertNotIn("collect",names)
        self.assertNotIn("pyspark",sys.modules)

    def test_same_name_external_site_cannot_supply_documentation_to_custom_site(self):
        own,foreign=self.python_config()
        (own/"tools.py").write_text('def map(x):\n    return x\ndef selected(x):\n    """Owned documentation."""\n    return x\n')
        (foreign/"tools.py").write_text('def map(x):\n    """External documentation must not select the custom map."""\n    return x\n')
        self.cfg.surface_filter="documented"
        self.assertEqual({"selected"},public_api_surface(self.cfg))
        self.assertEqual({"map","selected"},public_api_surface(self.cfg,"all"))


if __name__=="__main__":unittest.main()
