"""Load the one validated condition source before MDAnalysis imports.

The pinned wheel supplies compiled extensions. Only MDAnalysis.lib.util comes
from the selected condition checkout. This never edits or installs into the wheel.
"""
import argparse
import hashlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import runpy
import sys

MODULE = 'MDAnalysis.lib.util'
BASELINE_SHA = '4d37165adcc10536b8f51308924285fa02858e0ec84165082498308c135b46da'
CANDIDATE_SHA = 'fcc026d39549ae3e9b0a8dedfb069e82d90b98b8bff26f3626d34dfd138778d9'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ConditionSource(importlib.abc.MetaPathFinder):
    def __init__(self, source):
        self.source = source

    def find_spec(self, fullname, path=None, target=None):
        if fullname == MODULE:
            return importlib.util.spec_from_file_location(fullname, self.source)
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('program', type=Path)
    args = parser.parse_args()
    if any(name == 'MDAnalysis' or name.startswith('MDAnalysis.') for name in sys.modules):
        raise RuntimeError('Select condition source before the first MDAnalysis import')
    package = importlib.util.find_spec('MDAnalysis')
    roots = list(package.submodule_search_locations) if package else []
    if len(roots) != 1:
        raise RuntimeError('Expected one pinned installed MDAnalysis package')
    installed = Path(roots[0]) / 'lib/util.py'
    source = (args.source_root / 'package/MDAnalysis/lib/util.py').resolve(strict=True)
    if digest(installed) != BASELINE_SHA or digest(source) != CANDIDATE_SHA:
        raise RuntimeError('Installed baseline or condition source differs from validation')
    sys.dont_write_bytecode = True
    sys.meta_path.insert(0, ConditionSource(source))
    module = importlib.import_module(MODULE)
    distances = importlib.import_module('MDAnalysis.lib.distances')
    if (Path(module.__file__).resolve() != source
            or distances.check_box is not module.check_box
            or module.check_box.__code__.co_firstlineno != 2607):
        raise RuntimeError('Dependent modules did not bind the selected check_box')
    receipt = {'source': str(source), 'source_sha256': digest(source),
               'installed_baseline': str(installed), 'baseline_sha256': digest(installed),
               'selected_before_first_library_import': True,
               'distances_check_box_is_selected_function': True}
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    try:
        sys.argv = [str(args.program)]
        runpy.run_path(str(args.program), run_name='__main__')
    finally:
        if digest(installed) != BASELINE_SHA or digest(source) != CANDIDATE_SHA:
            raise RuntimeError('Library source changed during execution')


if __name__ == '__main__':
    main()
