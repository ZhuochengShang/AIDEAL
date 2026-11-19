"""Future inventory excludes only source-proven empty import-error placeholders."""
import importlib.util
from pathlib import Path
import pytest

MODULE = Path(__file__).parents[1] / 'vendor/aideal_engine/src/aideal/api_public_inventory.py'
spec = importlib.util.spec_from_file_location('conditional_inventory_test', MODULE)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


def scan(tmp_path, text):
    package = tmp_path / 'pkg'
    package.mkdir()
    (package / '__init__.py').write_text(text)
    return {row['qualified_name']: row for row in inventory.scan_python_surface(
        tmp_path, {'pkg': 'pkg'}, 'fixture')['records']}


@pytest.mark.parametrize('exception', ['ImportError', 'ModuleNotFoundError',
                                    '(ImportError, ModuleNotFoundError)'])
def test_empty_import_error_placeholder_is_excluded_with_source_provenance(tmp_path, exception):
    rows = scan(tmp_path, f'try:\n import optional_dependency\nexcept {exception}:\n class Placeholder:\n  """Documentation-only placeholder."""\n  pass\n')
    row = rows['pkg.Placeholder']
    assert row['inventory_reason'] == 'empty_import_failure_placeholder'
    assert row['inventory_status'] == 'excluded'
    assert row['body_presence'] == 'absent'
    assert row['body_classification']['evidence']['source_span_sha256'] == row['source_span_sha256']
    clause = row['conditional_context'][0]
    assert clause['kind'] == 'except'
    assert clause['exception_type'] == exception
    assert clause['line'] == 3 and clause['try_line'] == 1
    assert clause['try_imports'] == ['import optional_dependency']


def test_real_fallback_and_ordinary_empty_class_remain_candidates(tmp_path):
    rows = scan(tmp_path, 'class Marker:\n pass\ntry:\n import optional_dependency\nexcept ImportError:\n class Fallback:\n  def run(self): return 1\n def fallback_function(): return 1\n')
    for name in ('Marker', 'Fallback', 'Fallback.run', 'fallback_function'):
        assert rows['pkg.' + name]['inventory_status'] == 'candidate'
    assert rows['pkg.Fallback']['conditional_context'][0]['exception_type'] == 'ImportError'


@pytest.mark.parametrize('declaration', ['class Fallback(External):',
                                       '@decorate\n class Fallback:',
                                       'class Fallback(metaclass=Meta):'])
def test_inherited_or_transformed_empty_fallback_is_not_assumed_stub(tmp_path, declaration):
    row = scan(tmp_path, 'try:\n import optional_dependency\nexcept ImportError:\n ' + declaration + '\n  pass\n')['pkg.Fallback']
    assert row['inventory_status'] == 'candidate'
    assert not row.get('import_failure_stub')


@pytest.mark.parametrize('exception', ['Exception', '(ImportError, ValueError)', ''])
def test_general_exception_handler_is_not_assumed_import_failure(tmp_path, exception):
    row = scan(tmp_path, f'try:\n import optional_dependency\nexcept {exception}:\n class Marker:\n  pass\n')['pkg.Marker']
    assert row['inventory_status'] == 'candidate'


def test_importerror_without_a_source_import_is_not_assumed_placeholder(tmp_path):
    row = scan(tmp_path, 'try:\n operation()\nexcept ImportError:\n class Marker:\n  pass\n')['pkg.Marker']
    assert row['inventory_status'] == 'candidate'


def test_nested_if_in_handler_retains_both_guards(tmp_path):
    row = scan(tmp_path, 'try:\n from optional_dependency import Reader\nexcept ImportError:\n if documentation:\n  class Placeholder:\n   ...\n')['pkg.Placeholder']
    assert row['inventory_status'] == 'excluded'
    assert [c['kind'] for c in row['conditional_context']] == ['except', 'if']


def test_success_and_finally_empty_classes_are_not_handler_stubs(tmp_path):
    rows = scan(tmp_path, 'try:\n import optional_dependency\n class Available:\n  pass\nexcept ImportError:\n pass\nfinally:\n class Final:\n  pass\n')
    assert rows['pkg.Available']['inventory_status'] == 'candidate'
    assert rows['pkg.Final']['inventory_status'] == 'candidate'


def test_shadowed_exception_name_is_not_assumed_builtin(tmp_path):
    row = scan(tmp_path, 'ImportError = SomeOtherError\ntry:\n import optional_dependency\nexcept ImportError:\n class Marker:\n  pass\n')['pkg.Marker']
    assert row['inventory_status'] == 'candidate'
