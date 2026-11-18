"""Owner-qualified selection contracts using source-bound, offline fixtures."""
from copy import deepcopy
import hashlib
from itertools import permutations
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
from aideal.api_canonical_selection import (
    POLICY_VERSION, QUALIFIED_POLICY_VERSION, select_canonical_implementations,
)
from aideal.api_origin import audit_api_origins


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class QualifiedSelectionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        source = self.root / 'source'
        source.mkdir()
        # Fixture text is parsed/hashed only, never imported or compiled.
        self.file = source / 'Library.scala'
        self.file.write_text('package ownlib\nobject Raster { def reproject(x: Int) = spark.map(x) }\n')
        self.cfg = SimpleNamespace(root=self.root, raw={'codebase': {'api_origin': {
            'source_roots': ['source'], 'library_namespaces': ['ownlib'],
            'external_namespaces': ['org.apache.spark', 'java', 'builtins'],
        }}})

    def row(self, site, name='reproject', owner='ownlib.Raster', count=1, **changes):
        row = {'site_id': site, 'language': 'Scala', 'name': name, 'owner': owner,
               'qualified_name': owner + '.' + name, 'path': 'source/Library.scala',
               'file': 'source/Library.scala', 'line': 2, 'source_sha256': sha(self.file.read_bytes()),
               'source_span_sha256': sha(('bound-source-span:' + site).encode()),
               'parameter_count': count, 'params': [{'name': f'p{i}', 'required': True} for i in range(count or 0)],
               'scope': 'production', 'declared_visibility': 'public', 'public_owner_chain': True,
               'synthetic': False, 'callable': True, 'definition_kind': 'method',
               'defining_owner_kind': 'object', 'body_classification': {'category': 'implementation'}}
        row.update(changes)
        row['api_origin'] = audit_api_origins(self.cfg, [row])['decisions'][0]
        return row

    def select(self, rows):
        return select_canonical_implementations(rows, policy_version=QUALIFIED_POLICY_VERSION)

    def proof(self, wrapper, target, mapping=None):
        wrapper['forwarding'] = {'relation': 'direct_forwarder', 'target_site_id': target['site_id'],
            'semantics_preserved': True, 'source_span_sha256': wrapper['source_span_sha256'],
            'target_source_span_sha256': target['source_span_sha256'],
            'argument_map': mapping if mapping is not None else [
                {'source_parameter': p['name'], 'target_parameter': p['name']} for p in wrapper['params']],
            'evidence': {'method': 'fixture exact direct-call AST', 'side_effects': False}}
        return wrapper

    def test_distinct_owners_with_same_name_remain(self):
        rows = [self.row('raster'), self.row('vector', owner='ownlib.Vector', count=4)]
        result = self.select(rows)
        self.assertEqual({'scala:ownlib.Raster.reproject', 'scala:ownlib.Vector.reproject'}, set(result['winner_api_ids']))
        self.assertEqual(2, result['counts']['winner_api_ids'])
        self.assertEqual(1, result['counts']['winner_names'])

    def test_distinct_languages_remain(self):
        result = self.select([self.row('scala'), self.row('java', language='Java')])
        self.assertEqual(2, result['counts']['winner_sites'])

    def test_only_overloads_within_same_api_reduce_by_explicit_arity(self):
        result = self.select([self.row('short', count=1), self.row('long', count=4), self.row('other-owner', owner='ownlib.Vector')])
        self.assertEqual({'long', 'other-owner'}, set(result['winner_site_ids']))
        omitted = result['rejected_sites'][0]
        self.assertEqual('overload_selection_policy_only', omitted['relationship'])
        self.assertEqual('long', omitted['canonical_site_id'])

    def test_unknown_body_and_legacy_wrapper_label_are_not_duplicate_proof(self):
        rows = [self.row('spark-map', name='map', body_classification={'category': 'wrapper', 'evidence': 'calls spark.map'}),
                self.row('unknown', name='unknown', body_classification=None)]
        result = self.select(rows)
        self.assertEqual({'spark-map', 'unknown'}, set(result['winner_site_ids']))
        self.assertEqual(2, result['counts']['review_note_sites'])

    def test_singleton_unknown_arity_is_retained_without_inventing_zero(self):
        row = self.row('class', name='Raster', qualified_name='ownlib.Raster', count=None,
                       definition_kind='class_constructor', parameter_count_status='unknown_inherited')
        winner = self.select([row])['winners'][0]
        self.assertIsNone(winner['parameter_count'])
        self.assertEqual('sole_qualified_callable_arity_unknown', winner['reason'])

    def test_reported_zero_with_unknown_status_is_not_treated_as_known(self):
        row = self.row('unknown', count=0, parameter_count_status='unknown_from_old_parser')
        winner = self.select([row])['winners'][0]
        self.assertIsNone(winner['parameter_count'])
        self.assertEqual(0, winner['reported_parameter_count'])

    def test_unknown_competing_overloads_stay_unresolved(self):
        result = self.select([self.row('unknown', count=None), self.row('known', count=3)])
        self.assertEqual([], result['winner_site_ids'])
        self.assertEqual(2, result['counts']['unresolved_sites'])
        self.assertFalse(result['selection_resolved'])

    def test_class_and_companion_object_collision_requires_review(self):
        result = self.select([self.row('object'), self.row('class', defining_owner_kind='class')])
        self.assertEqual(2, result['counts']['unresolved_sites'])

    def test_constructor_operation_collision_requires_review(self):
        result = self.select([self.row('method'), self.row('ctor', definition_kind='class_constructor')])
        self.assertEqual(2, result['counts']['unresolved_sites'])

    def test_compiler_proven_companions_keep_distinct_kind_qualified_ids(self):
        rows = [self.row('object'), self.row('class', defining_owner_kind='class')]
        for row in rows:
            row['identity_owner_kind'] = row['defining_owner_kind']
            row['identity_disambiguation'] = {'method':'compiler_owner_kind_collision',
                'owner_kinds':['class','object'], 'source_span_sha256':row['source_span_sha256']}
        result = self.select(rows)
        self.assertEqual({'scala:class:ownlib.Raster.reproject','scala:object:ownlib.Raster.reproject'}, set(result['winner_api_ids']))
        self.assertEqual(result,self.select(result['site_decisions']))

    def test_owner_kind_label_without_real_companion_family_is_rejected(self):
        row = self.row('object', identity_owner_kind='object')
        with self.assertRaisesRegex(ValueError,'discriminator'): self.select([row])
        row['identity_disambiguation'] = {'method':'compiler_owner_kind_collision',
            'owner_kinds':['class','object'], 'source_span_sha256':row['source_span_sha256']}
        with self.assertRaisesRegex(ValueError,'family'): self.select([row])

    def test_conditional_variants_are_not_silently_selected_by_arity(self):
        rows = [self.row('torch',count=5,conditional_context=['If@10:body']),
                self.row('fallback',count=0,conditional_context=['If@10:orelse'])]
        result = self.select(rows)
        self.assertEqual(2,result['counts']['unresolved_sites'])
        self.assertEqual({'conditional_definition_variant_unresolved'},{r['reason'] for r in result['rejected_sites']})

    def test_same_condition_overloads_still_use_maximum_arity(self):
        rows = [self.row('short',count=1,conditional_context=['If@10:body']),
                self.row('long',count=3,conditional_context=['If@10:body'])]
        self.assertEqual(['long'],self.select(rows)['winner_site_ids'])

    def test_direct_wrapper_requires_argument_map_and_exact_retained_target(self):
        target = self.row('target', name='original')
        wrapper = self.proof(self.row('wrapper', name='clearName'), target)
        result = self.select([wrapper, target])
        self.assertEqual(['target'], result['winner_site_ids'])
        self.assertEqual('target', result['rejected_sites'][0]['canonical_site_id'])
        self.assertEqual('proven_direct_forwarder', result['rejected_sites'][0]['reason'])

    def test_optional_unforwarded_target_argument_can_keep_its_default(self):
        target = self.row('target', name='original', count=2)
        target['params'][1].update(required=False, default='None')
        wrapper = self.proof(self.row('wrapper', name='clearName'), target)
        self.assertEqual(['target'], self.select([wrapper, target])['winner_site_ids'])

    def test_required_unforwarded_target_argument_does_not_reduce(self):
        target = self.row('target', name='original', count=2)
        wrapper = self.proof(self.row('wrapper', name='clearName'), target)
        self.assertEqual(2, self.select([wrapper, target])['counts']['winner_sites'])

    def test_wrong_span_missing_target_or_transformed_argument_does_not_reduce(self):
        target = self.row('target', name='original')
        base = self.proof(self.row('wrapper', name='clearName'), target)
        cases = [{'source_span_sha256': 'changed'}, {'target_site_id': 'missing'},
                 {'argument_map': [{'source_parameter': 'p0.toArray', 'target_parameter': 'p0'}]},
                 {'argument_map': [{'source_parameter': 'p0', 'target_parameter': 'p0', 'conversion': 'float'}]}]
        for mutation in cases:
            wrapper = deepcopy(base); wrapper['forwarding'].update(mutation)
            with self.subTest(mutation=mutation):
                self.assertEqual(2, self.select([wrapper, target])['counts']['winner_sites'])

    def test_target_losing_its_overload_election_cannot_discard_wrapper(self):
        target = self.row('short', name='original')
        larger = self.row('long', name='original', count=3)
        wrapper = self.proof(self.row('wrapper', name='clearName'), target)
        result = self.select([target, larger, wrapper])
        self.assertEqual({'long', 'wrapper'}, set(result['winner_site_ids']))

    def test_wrapper_cycles_do_not_eliminate_every_candidate(self):
        first, second = self.row('first', name='first'), self.row('second', name='second')
        self.proof(first, second); self.proof(second, first)
        self.assertEqual(2, self.select([first, second])['counts']['winner_sites'])

    def test_external_defining_origin_is_excluded_even_with_library_style_name(self):
        row = self.row('dependency', owner='org.apache.spark.RDD', name='map')
        result = self.select([row])
        self.assertEqual('dependency_defined_api', result['rejected_sites'][0]['reason'])

    def test_missing_origin_or_forged_origin_or_changed_source_is_unresolved(self):
        for change in ('missing', 'digest', 'source', 'identity'):
            row = self.row('raster')
            if change == 'missing': row.pop('api_origin')
            if change == 'digest': row['api_origin']['reason'] = 'tampered'
            if change == 'source': row['source_sha256'] = 'different'
            if change == 'identity': row['qualified_name'] = 'ownlib.Other.reproject'
            with self.subTest(change=change):
                result = self.select([row])
                self.assertEqual(1, result['counts']['unresolved_sites'])
                self.assertEqual([], result['winner_site_ids'])

    def test_explicit_noncallable_private_abstract_and_synthetic_are_excluded(self):
        rows = [self.row('property', callable=False), self.row('private', declared_visibility='non-public'),
                self.row('abstract', is_abstract=True), self.row('bodyless', body_presence='absent'),
                self.row('generated', synthetic=True), self.row('test', scope='test')]
        self.assertEqual(6, self.select(rows)['counts']['excluded_sites'])

    def test_verified_public_reexport_keeps_private_defining_identity(self):
        row = self.row('private-export', name='_implementation', declared_visibility='non-public',
                       public_owner_chain=False, public_exposure_established=True,
                       exposure_ids=['scala:ownlib.api.public_name'])
        winner = self.select([row])['winners'][0]
        self.assertEqual('scala:ownlib.Raster._implementation', winner['api_id'])
        self.assertEqual('non-public', winner['declared_visibility'])

    def test_all_rows_have_dispositions_and_inputs_remain_unchanged(self):
        rows = [self.row('x'), self.row('larger', count=2), self.row('private', declared_visibility='non-public')]
        before = deepcopy(rows); result = self.select(rows)
        self.assertEqual(before, rows)
        self.assertEqual(len(rows), len(result['site_decisions']))
        self.assertEqual(len(rows), sum(result['counts'][key] for key in ('winner_sites','omitted_sites','excluded_sites','unresolved_sites')))
        json.dumps(result, allow_nan=False)

    def test_input_order_and_receipt_replay_are_deterministic(self):
        rows = [self.row('z'), self.row('a'), self.row('unknown', name='other', count=None)]
        expected = self.select(rows)
        for ordered in permutations(rows): self.assertEqual(expected, self.select(ordered))
        self.assertEqual(expected, self.select(expected['site_decisions']))

    def test_invalid_parameters_id_and_duplicate_site_raise(self):
        for changes in ({'params': ['x']}, {'params':[{'name': ''}]}, {'parameter_count':True},
                        {'api_id':'scala:ownlib.Wrong.reproject'}, {'parameter_count':-1}):
            row = self.row('bad'); row.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError): self.select([row])
        with self.assertRaisesRegex(ValueError, 'duplicate site_id'):
            self.select([self.row('same'), self.row('same')])

    def test_empty_inventory_has_complete_accounting(self):
        result = self.select([])
        self.assertTrue(result['selection_resolved'])
        self.assertEqual({}, result['by_language'])
        self.assertEqual(0, result['counts']['winner_sites'])

    def test_explicit_legacy_policy_remains_default(self):
        rows = [{'site_id':'a','language':'Scala','name':'run','owner':'A','path':'A.scala','line':1,
                 'parameter_count':2,'body_classification':{'category':'implementation','reviewed':True,'evidence':'AST'}},
                {'site_id':'b','language':'Scala','name':'run','owner':'B','path':'B.scala','line':1,
                 'parameter_count':1,'body_classification':{'category':'implementation','reviewed':True,'evidence':'AST'}}]
        self.assertEqual(select_canonical_implementations(rows), select_canonical_implementations(rows, policy_version=POLICY_VERSION))
        self.assertEqual(['a'], select_canonical_implementations(rows)['winner_site_ids'])
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            select_canonical_implementations(rows, policy_version='future')


if __name__ == '__main__':
    unittest.main()
