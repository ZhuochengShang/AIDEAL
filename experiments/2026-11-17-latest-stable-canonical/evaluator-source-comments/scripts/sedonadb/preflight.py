#!/usr/bin/env python3
"""Record library identity and smoke-test the SQL materialization adapter.

No model calls. Run in the same Python environment as measured snippets.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import sys


def digest(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def inspect_runtime(fixtures=None):
    from sedona_runtime import TrackedContext, initialize_sedona, native_runtime_identity
    sedonadb = initialize_sedona()
    import sedonadb._lib
    sd = sedonadb.connect()
    scalar = sorted(n for n in set(sd._impl.list_scalar_udfs())
                    if n.startswith(("st_", "rs_", "s2_", "sd_")))
    aggregate = sorted(n for n in sd._impl.list_aggregate_udfs()
                       if n.startswith(("st_", "rs_", "s2_", "sd_")))
    checks = {}
    for target, sql, expected in [
        ("ST_Area", "SELECT ST_Area(ST_GeomFromWKT('POLYGON ((0 0, 2 0, 2 3, 0 3, 0 0))')) AS value", 6.0),
        ("ST_Collect_Agg", "SELECT ST_NPoints(ST_Collect_Agg(ST_Point(x, x))) AS value FROM (VALUES (1), (2)) AS t(x)", 2),
        ("RS_Example", "SELECT RS_Width(RS_Example()) AS value", 64),
        ("RS_AsGeoTiff", "SELECT RS_Width(RS_FromGDALRaster(RS_AsGeoTiff(RS_Example()))) AS value", 64),
        ("ST_Transform", "SELECT ST_X(ST_Transform(ST_Point(0, 0), 'EPSG:4326', 'EPSG:3857')) AS value", 0.0),
    ]:
        ctx = TrackedContext(target, sd)
        actual = ctx.sql(sql).to_arrow_table().column("value")[0].as_py()
        assert actual == expected, (target, actual, expected)
        ctx.verify()
        rejected = False
        try:
            assert actual == expected + 1
        except AssertionError:
            rejected = True
        assert rejected
        checks[target] = {"positive": True, "wrong_expected_value_rejected": rejected, "value": actual}
    s2 = TrackedContext("S2_CellIdFromPoint", sd)
    cell = s2.sql("SELECT S2_CellIdFromPoint(ST_GeogPoint(-64, 45)) AS cell").to_arrow_table().column("cell")[0].as_py()
    s2.verify()
    checks["S2_CellIdFromPoint"] = {"materialized": True, "value": cell,
                                     "semantic_oracle": "not asserted; optional backend initialization only"}
    fixture_identity = []
    if fixtures:
        import rasterio
        for filename in ("cea.tif", "test4.tiff"):
            path = (fixtures / filename).resolve()
            with rasterio.open(path) as raster:
                expected = raster.width
            ctx = TrackedContext("RS_FromPath", sd)
            escaped = str(path).replace("'", "''")
            actual = ctx.sql(f"SELECT RS_Width(RS_FromPath('{escaped}')) AS value").to_arrow_table().column("value")[0].as_py()
            assert actual == expected
            ctx.verify()
            fixture_identity.append({**digest(path), "expected_width": expected, "observed_width": actual})
    unused = TrackedContext("ST_Area", sd)
    unused.sql("SELECT 'ST_Area(ignored)' AS text").to_arrow_table()
    try:
        unused.verify()
    except AssertionError:
        checks["string_literal_not_target_use"] = True
    else:
        raise AssertionError("Literal target text incorrectly qualified as function use")
    lazy = TrackedContext("ST_Area", sd)
    lazy.sql("SELECT ST_Area(ST_GeomFromWKT('POLYGON ((0 0, 1 0, 1 1, 0 0))'))")
    try:
        lazy.verify()
    except AssertionError:
        checks["unmaterialized_target_rejected"] = True
    else:
        raise AssertionError("Lazy target incorrectly qualified as materialized")
    packages = {}
    for name in ("sedonadb", "pyarrow", "rasterio", "pyproj"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {"package_versions": packages, "python": sys.version,
            "executable": str(Path(sys.executable).resolve()),
            "extension": digest(sedonadb._lib.__file__),
            "native_dependencies": native_runtime_identity(),
            "features": sedonadb.__features__, "scalar_names": scalar,
            "aggregate_names": aggregate, "operator_smokes": checks,
            "fixtures": fixture_identity,
            "operator_smokes_are_not_audience_scores": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-registry", type=Path)
    parser.add_argument("--fixtures", type=Path)
    args = parser.parse_args()
    report = inspect_runtime(args.fixtures)
    ok = report["package_versions"]["sedonadb"] == "0.5.0"
    if args.expected_registry:
        expected = json.loads(args.expected_registry.read_text())
        old = set(expected["sedona_scalar_functions"]) | {
            n for n in expected["all_aggregate_functions_including_datafusion"]
            if n.startswith(("st_", "rs_", "s2_", "sd_"))}
        new = set(report["scalar_names"]) | set(report["aggregate_names"])
        report["expected_registry"] = digest(args.expected_registry)
        report["missing_from_runtime"] = sorted(old - new)
        report["extra_in_runtime"] = sorted(new - old)
        report["historical_registry_matches"] = old == new
    report["ready"] = bool(ok)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"ready": ok, "scalar_names": len(report["scalar_names"]),
                      "aggregate_names": len(report["aggregate_names"]), "output": str(args.output)}))
    raise SystemExit(0 if ok else 1)
