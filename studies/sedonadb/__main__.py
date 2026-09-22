"""Optional SedonaDB SQL example commands, separate from the AIDEAL core."""
import argparse
import json
from pathlib import Path

from .fixtures import relocated_catalog
from .runner import run
from .trace import trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('trace', help='Preview a prompt without calling an LLM')
    p.add_argument('--api', required=True)
    p = sub.add_parser('run', help='Execute SQL examples through an existing Rust binary')
    for name in ('binary', 'output', 'gdal', 'proj', 'proj-db'):
        p.add_argument('--' + name, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.command == 'trace':
        result = trace(root, args.api)
    else:
        output = Path(args.output).resolve()
        catalog = relocated_catalog(root, output / 'fixture_catalog.json')
        result = run(catalog, args.binary, output, environment={
            'AIDEAL_GDAL_LIBRARY': str(Path(args.gdal).resolve()),
            'AIDEAL_PROJ_LIBRARY': str(Path(args.proj).resolve()),
            'AIDEAL_PROJ_DATABASE': str(Path(args.proj_db).resolve()),
        }, supporting_files=[
            root / 'studies/sedonadb/evidence/cea.tif', root / 'studies/sedonadb/evidence/test4.tiff',
            root / 'studies/sedonadb/harnesses/configured/Cargo.lock', root / 'studies/sedonadb/harnesses/configured/src/main.rs',
            Path(__file__), root / 'studies/sedonadb/fixtures.py', root / 'workflow/ablation.py',
            args.gdal, args.proj, args.proj_db,
        ])
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
