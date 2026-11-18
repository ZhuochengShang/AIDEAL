"""Transparent SQL execution tracking for an audience-written Python snippet.

This is a target-use/materialization gate, not an independent correctness oracle.
The snippet's own assertions provide the native R0 correctness check.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import sys


_RUNTIME_IDENTITY = None


def _database_identity(path):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
        layout = dict(database.execute("SELECT key, value FROM metadata WHERE key LIKE 'DATABASE.LAYOUT.VERSION.%'"))
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "layout": layout}


def initialize_sedona():
    """Select the measured wheels' native libraries/data before initialization.

    Rasterio's GDAL uses its own bundled PROJ database; Sedona's standalone
    PROJ engine uses pyproj's matching database and library explicitly.
    Inherited Conda PROJ/GDAL paths must never select a different database.
    """
    global _RUNTIME_IDENTITY
    if _RUNTIME_IDENTITY is not None:
        import sedonadb
        return sedonadb
    if any(name in sys.modules for name in ("sedonadb", "rasterio", "pyproj")):
        raise RuntimeError("Initialize the Sedona adapter before importing sedonadb, rasterio, or pyproj")
    package_dirs = {}
    for name in ("pyproj", "rasterio"):
        spec = importlib.util.find_spec(name)
        if spec is None or not spec.origin:
            raise RuntimeError(f"Required runtime package is missing: {name}")
        directory = Path(spec.origin).resolve().parent
        if not directory.is_relative_to(Path(sys.prefix).resolve()):
            raise RuntimeError(f"{name} was resolved outside the measured Python environment: {directory}")
        package_dirs[name] = directory
    pyproj_data = package_dirs["pyproj"] / "proj_dir/share/proj"
    rasterio_proj_data = package_dirs["rasterio"] / "proj_data"
    rasterio_gdal_data = package_dirs["rasterio"] / "gdal_data"
    for path in (pyproj_data / "proj.db", rasterio_proj_data / "proj.db"):
        if not path.is_file():
            raise RuntimeError(f"Expected wheel-bundled PROJ database is missing: {path}")
    if not rasterio_gdal_data.is_dir():
        raise RuntimeError(f"Expected wheel-bundled GDAL data is missing: {rasterio_gdal_data}")
    overridden = [key for key in ("PROJ_DATA", "PROJ_LIB", "PROJ_AUX_DB", "GDAL_DATA", "GDAL_DRIVER_PATH") if key in os.environ]
    for key in ("PROJ_DATA", "PROJ_LIB", "PROJ_AUX_DB", "GDAL_DATA", "GDAL_DRIVER_PATH"):
        os.environ.pop(key, None)
    os.environ["PROJ_DATA"] = str(rasterio_proj_data)
    os.environ["PROJ_LIB"] = str(rasterio_proj_data)
    os.environ["GDAL_DATA"] = str(rasterio_gdal_data)
    os.environ["PROJ_NETWORK"] = "OFF"
    import pyproj
    pyproj.datadir.set_data_dir(str(pyproj_data))
    import rasterio
    from rasterio._env import set_gdal_config, set_proj_data_search_path, get_proj_data_search_paths
    set_proj_data_search_path(str(rasterio_proj_data))
    set_gdal_config("GDAL_DATA", str(rasterio_gdal_data))
    assert Path(pyproj.datadir.get_data_dir()).resolve() == pyproj_data
    assert str(rasterio_proj_data) in get_proj_data_search_paths()
    import sedonadb
    sedonadb.configure_proj("pyproj")
    sedonadb.configure_gdal("rasterio")
    _RUNTIME_IDENTITY = {
        "package_directories": {name: str(path) for name, path in package_dirs.items()},
        "pyproj_database": _database_identity(pyproj_data / "proj.db"),
        "rasterio_database": _database_identity(rasterio_proj_data / "proj.db"),
        "rasterio_gdal_data": str(rasterio_gdal_data),
        "overridden_inherited_variable_names": overridden,
        "projection_network": "OFF",
    }
    return sedonadb


def native_runtime_identity():
    initialize_sedona()
    return dict(_RUNTIME_IDENTITY)


def calls_function(sql, target):
    # Remove SQL string literals and comments before matching a function token.
    token = re.compile(r"'(?:''|[^'])*'|--[^\n]*|/\*[\s\S]*?\*/|\"(?:\"\"|[^\"])*\"|[A-Za-z_][A-Za-z_0-9]*|[^\s]", re.M)
    tokens = []
    for match in token.finditer(sql):
        value = match.group()
        if value.startswith(("--", "/*")):
            continue
        if value.startswith("'"):
            tokens.append("<literal>")
        elif value.startswith('"'):
            tokens.append(value[1:-1].replace('""', '"').lower())
        else:
            tokens.append(value.lower())
    return any(name == target.lower() and nxt == "(" for name, nxt in zip(tokens, tokens[1:]))


class TrackedFrame:
    def __init__(self, frame, owner, uses_target):
        self._frame = frame
        self._owner = owner
        self._uses_target = uses_target

    def to_arrow_table(self, *args, **kwargs):
        result = self._frame.to_arrow_table(*args, **kwargs)
        self._owner.materialized_target |= self._uses_target
        return result

    def execute(self):
        result = self._frame.execute()
        self._owner.materialized_target |= self._uses_target
        return result


def requested_sql_target(program):
    """Resolve the evaluator's exact identity, independently of its folder slug."""
    directory = Path(program).resolve().parent
    record = directory / 'requested_target.json'
    if record.is_file():
        value = json.loads(record.read_text())
        api_id = value.get('api_id')
        name = value.get('display_name')
        if (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', name)
                or api_id != 'sql:' + name):
            raise ValueError('Invalid qualified SQL target receipt')
        return api_id, name
    # Historical runs used a simple SQL function name as the directory suffix.
    name = directory.name.removeprefix('run_')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', name):
        raise ValueError('Missing target receipt for qualified SQL output')
    return name, name


class TrackedContext:
    def __init__(self, target, context=None):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", target):
            raise ValueError("Invalid SQL target name")
        if context is None:
            sedonadb = initialize_sedona()
            context = sedonadb.connect()
        self._context = context
        self.target = target
        self.materialized_target = False

    def sql(self, query, **kwargs):
        if not isinstance(query, str):
            raise TypeError("sd.sql requires a SQL string")
        return TrackedFrame(self._context.sql(query, **kwargs), self,
                            calls_function(query, self.target))

    def verify(self):
        if not self.materialized_target:
            raise AssertionError(f"Target SQL function {self.target} was not called and materialized through sd.sql")

