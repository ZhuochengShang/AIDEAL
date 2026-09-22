"""Relocate pinned fixture paths without changing the archived run catalog."""
from pathlib import Path

from workflow.ablation import bind, file_hash, load, save


def relocated_catalog(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    catalog = load(root / 'studies/sedonadb/evidence/sql_reference_local_paths.json')
    for entry in catalog:
        examples = {}
        for binding in entry.get('fixture_bindings', []):
            fixture = root / 'studies/sedonadb/evidence' / Path(binding['local_fixture']['path']).name
            if file_hash(fixture) != binding['local_fixture']['sha256']:
                raise ValueError('Pinned fixture changed: ' + str(fixture))
            # Quotes in directory names must remain a single SQL string literal.
            quoted = str(fixture).replace("'", "''")
            index = binding['example_index'] - 1
            # Several fixtures can belong to one SQL block. Start from the
            # original SQL once, then retain every replacement in that block.
            sql = examples.get(index, binding['original_sql'])
            examples[index] = sql.replace(binding['original_locator'], quoted)
            binding['local_fixture'] = bind(fixture)
        for index, sql in examples.items():
            entry['examples'][index] = sql
    if destination.exists():
        if load(destination) != catalog:
            raise ValueError('Existing relocated catalog differs; use a new output directory')
    else:
        save(destination, catalog)
    return destination
