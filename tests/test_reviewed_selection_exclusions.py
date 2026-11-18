"""Source-bound scope exclusions precede overload election; no subject or API runs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
from aideal.api_canonical_selection import (
    QUALIFIED_POLICY_VERSION, reviewed_selection_exclusion_ids, select_canonical_implementations)
from aideal.api_origin import audit_api_origins
from aideal.api_public_inventory import digest, qualified_inventory_details
from aideal.api_registry import relocated_inventory_binding


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class ReviewedSelectionExclusionsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'source/pkg').mkdir(parents=True)
        self.cfg = SimpleNamespace(root=self.root, language='Java', raw={'codebase': {
            'api_origin': {'source_roots': ['source/pkg'], 'library_namespaces': ['pkg'],
                           'external_namespaces': ['java', 'scala']}}})
        self.rows, files = [], []
        declarations = [
            ('Java', 'A', 'core', 'public int run(int x) { return x + 1; }', 1),
            ('Java', 'A', 'wrapper', 'public int run(int x, int unused) { return run(x); }', 2),
            ('Java', 'B', 'other-owner', 'public int run(int x) { return x * 2; }', 1),
            ('Scala', 'Foreign', 'other-language', 'def run(x: Int): Int = x + 3', 1)]
        for language, owner, site, declaration, arity in declarations:
            path = 'pkg/' + site + ('.java' if language == 'Java' else '.scala')
            text = '// source contains a unicode character: 🙂\n' + declaration + '\n'
            raw = text.encode(); (self.root / 'source' / path).write_bytes(raw)
            files.append({'path': path, 'sha256': sha(raw), 'bytes': len(raw), 'encoding': 'utf-8'})
            prefix = text[:text.index(declaration)]
            start = len(prefix.encode('utf-16-le')) // 2
            self.rows.append({'site_id': site, 'language': language, 'name': 'run',
                'owner': 'pkg.' + owner, 'defining_owner': 'pkg.' + owner,
                'defining_owner_kind': 'class', 'qualified_name': 'pkg.' + owner + '.run',
                'api_id': language.lower() + ':pkg.' + owner + '.run',
                'kind': 'method', 'definition_kind': 'method', 'path': path,
                'file': 'source/' + path, 'defining_file': 'source/' + path, 'line': 2,
                'start': start, 'end': start + len(declaration.encode('utf-16-le')) // 2,
                'offset_unit': 'UTF-16 code units in decoded UTF-8 source',
                'source_sha256': sha(raw), 'source_span_sha256': sha(declaration.encode()),
                'parameter_count': arity, 'parameter_count_status': 'compiler_declared',
                'params': [{'name': 'x' + str(i)} for i in range(arity)], 'signature': declaration,
                'scope': 'production', 'callable': True, 'synthetic': False, 'is_abstract': False,
                'body_presence': 'present', 'declared_visibility': 'public', 'public_owner_chain': True,
                'inventory_status': 'candidate', 'body_classification': {'category': 'implementation'},
                'preferred_public_path': 'pkg.' + owner + '.run',
                'exposure_ids': [language.lower() + ':pkg.' + owner + '.run']})
        for row, origin in zip(self.rows, audit_api_origins(self.cfg, self.rows)['decisions']):
            row['api_origin'] = origin
        self.ledger = {'schema': 2, 'kind': 'qualified_source_api_inventory', 'records': self.rows,
            'source_snapshot': {'commit': 'commit', 'tree': 'tree'}, 'source_version': 'fixture',
            'origin_policy': {'source_roots': ['pkg'], 'library_namespaces': ['pkg'],
                              'external_namespaces': ['java', 'scala']},
            'source_files': files, 'source_file_binding_sha256': digest(files)}
        self.write('ledger.json', self.ledger)
        self.data = {'schema': 2, 'kind': 'qualified_source_api_inventory', 'source_root': 'source',
            'source_inventory': 'ledger.json', 'source_inventory_sha256': sha((self.root/'ledger.json').read_bytes()),
            'source_commit': 'commit', 'source_tree': 'tree', 'source_version': 'fixture',
            'declaration_ids': [r['site_id'] for r in self.rows if r['language'] == 'Java'],
            'canonical_selection': 'selection.json', 'canonical_selection_policy_version': QUALIFIED_POLICY_VERSION}
        self.review = {'schema': 'source_bound_selection_exclusions/v1', 'review_version': 'fixture-review-v1',
            'source_inventory_sha256': self.data['source_inventory_sha256'], 'records': []}
        self.freeze()
        git = patch('aideal.api_public_inventory.subprocess.run', side_effect=lambda args, **kw:
                    SimpleNamespace(stdout='commit' if args[-1] == 'HEAD' else 'tree' if args[-1] == 'HEAD^{tree}' else ''))
        git.start(); self.addCleanup(git.stop)

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value, sort_keys=True) + '\n')
        return sha((self.root / name).read_bytes())

    def exclusion(self, site, reason='wrapper'):
        row = next(r for r in self.rows if r['site_id'] == site)
        return {key: row[key] for key in ('site_id', 'source_sha256', 'source_span_sha256')} | {
            'reason': reason, 'evidence': 'Reviewed complete declaration; this is an explicit study-scope exclusion.'}

    def freeze(self, exclusions=None):
        if exclusions is not None:
            self.review['records'] = exclusions
            self.data.update(selection_exclusions='review.json', selection_exclusions_sha256=self.write('review.json', self.review))
        excluded = {r['site_id'] for r in self.review['records']} if 'selection_exclusions' in self.data else set()
        selection = select_canonical_implementations([r for r in self.rows if r['site_id'] not in excluded], policy_version=QUALIFIED_POLICY_VERSION)
        if 'selection_exclusions' in self.data:
            selection['selection_exclusions_sha256'] = self.data['selection_exclusions_sha256']
        self.data.update(canonical_selection_sha256=self.write('selection.json', selection),
                         canonical_declaration_ids=[r['site_id'] for r in selection['winners'] if r['language'] == self.cfg.language])
        self.cfg.raw['codebase'].update(api_inventory='inventory.json', api_inventory_sha256=self.write('inventory.json', self.data))

    def read(self):
        return qualified_inventory_details(self.cfg, self.data)

    def test_absence_preserves_original_selection(self):
        self.assertEqual({'wrapper', 'other-owner'}, {r['site_id'] for r in self.read()})
        self.assertNotIn('selection_exclusions', self.data)

    def test_review_precedes_max_arity_preserving_api_identity_and_distinct_owners(self):
        before = deepcopy(self.ledger)
        self.freeze([self.exclusion('wrapper')])
        rows = self.read()
        self.assertEqual({'core', 'other-owner'}, {r['site_id'] for r in rows})
        self.assertEqual({'java:pkg.A.run', 'java:pkg.B.run'}, {r['api_id'] for r in rows})
        self.assertEqual(['core', 'wrapper', 'other-owner'], self.data['declaration_ids'])
        self.assertEqual(before, self.ledger)

    def test_equal_arity_wrapper_yields_core_without_merging_other_owners(self):
        wrapper = next(r for r in self.rows if r['site_id'] == 'wrapper')
        wrapper['parameter_count'] = 1
        self.ledger['records'] = self.rows
        self.data['source_inventory_sha256'] = self.write('ledger.json', self.ledger)
        self.review['source_inventory_sha256'] = self.data['source_inventory_sha256']
        self.freeze([self.exclusion('wrapper')])
        self.assertEqual({'core', 'other-owner'}, {r['site_id'] for r in self.read()})

    def test_other_language_reviews_are_checked_before_language_filter(self):
        self.freeze([self.exclusion('wrapper'), self.exclusion('other-language')])
        self.assertEqual({'core', 'other-owner'}, {r['site_id'] for r in self.read()})
        self.review['records'][1]['source_span_sha256'] = '0' * 64
        self.freeze(self.review['records'])
        with self.assertRaisesRegex(ValueError, 'source hash differs'):
            self.read()

    def test_changed_source_of_excluded_other_language_still_fails(self):
        self.freeze([self.exclusion('wrapper'), self.exclusion('other-language')])
        (self.root/'source/pkg/other-language.scala').write_text('changed source')
        with self.assertRaisesRegex(ValueError, 'Bound source file changed'):
            self.read()

    def test_forged_span_of_excluded_other_language_still_fails(self):
        foreign = next(r for r in self.rows if r['site_id'] == 'other-language')
        foreign['source_span_sha256'] = '0' * 64
        self.data['source_inventory_sha256'] = self.write('ledger.json', self.ledger)
        self.review['source_inventory_sha256'] = self.data['source_inventory_sha256']
        self.freeze([self.exclusion('wrapper'), self.exclusion('other-language')])
        with self.assertRaisesRegex(ValueError, 'Definition span changed'):
            self.read()

    def test_forged_file_hash_of_excluded_other_language_still_fails(self):
        foreign = next(r for r in self.rows if r['site_id'] == 'other-language')
        foreign['source_sha256'] = '0' * 64
        self.data['source_inventory_sha256'] = self.write('ledger.json', self.ledger)
        self.review['source_inventory_sha256'] = self.data['source_inventory_sha256']
        self.freeze([self.exclusion('wrapper'), self.exclusion('other-language')])
        with self.assertRaisesRegex(ValueError, 'source file hash differs'):
            self.read()

    def test_review_schema_and_each_required_field_fail_closed(self):
        valid = self.exclusion('wrapper')
        mutations = [lambda d: d.update(schema='future'), lambda d: d.update(review_version=''),
            lambda d: d.update(source_inventory_sha256='0'*64), lambda d: d.update(records={}),
            lambda d: d.update(records=[None]), lambda d: d['records'].append(dict(valid)),
            lambda d: d['records'][0].update(site_id='unknown'), lambda d: d['records'][0].update(site_id=[]),
            lambda d: d['records'][0].update(reason='inferred_from_name'), lambda d: d['records'][0].update(evidence=''),
            lambda d: d['records'][0].update(evidence={}), lambda d: d['records'][0].pop('source_sha256'),
            lambda d: d['records'][0].pop('source_span_sha256'), lambda d: d['records'][0].update(source_sha256='0'*64)]
        for i, mutate in enumerate(mutations):
            review = deepcopy(self.review); review['records'] = [dict(valid)]; mutate(review)
            with self.subTest(case=i), self.assertRaises(ValueError):
                reviewed_selection_exclusion_ids(review, self.rows, self.data['source_inventory_sha256'])

    def test_all_explicit_reasons_are_source_bound(self):
        for reason in ('wrapper', 'unimplemented', 'duplicate', 'abstract_type'):
            self.freeze([self.exclusion('wrapper', reason)])
            with self.subTest(reason=reason):
                self.assertEqual({'core', 'other-owner'}, {r['site_id'] for r in self.read()})

    def test_review_bytes_and_selection_receipt_binding_cannot_drift(self):
        self.freeze([self.exclusion('wrapper')])
        (self.root/'review.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'checksum changed'):
            self.read()
        self.freeze([self.exclusion('wrapper')])
        receipt = json.loads((self.root/'selection.json').read_text())
        receipt.pop('selection_exclusions_sha256')
        self.data['canonical_selection_sha256'] = self.write('selection.json', receipt)
        with self.assertRaisesRegex(ValueError, 'receipt binding differs'):
            self.read()

    def test_missing_review_path_or_checksum_is_rejected(self):
        for field in ('selection_exclusions', 'selection_exclusions_sha256'):
            self.freeze([self.exclusion('wrapper')]); self.data.pop(field)
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.read()

    def test_relative_exclusion_binding_relocates_without_changing_review_bytes(self):
        self.freeze([self.exclusion('wrapper')])
        before = (self.root/'review.json').read_bytes()
        content, checksum = relocated_inventory_binding(self.cfg)
        relocated = json.loads(content)
        self.assertEqual(str((self.root/'review.json').resolve()), relocated['selection_exclusions'])
        self.assertEqual(sha(content), checksum)
        self.assertEqual(before, (self.root/'review.json').read_bytes())
        self.assertEqual({'core', 'other-owner'}, {r['site_id'] for r in qualified_inventory_details(self.cfg, relocated)})


if __name__ == '__main__':
    unittest.main()
