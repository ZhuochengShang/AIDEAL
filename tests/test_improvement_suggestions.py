"""Source previews and synthetic model suggestions must preserve development boundaries."""
from copy import deepcopy
from pathlib import Path
import json
import shlex
import subprocess
import sys
import tempfile
import unittest

from workflow.ablation import load
from workflow.improvement_context import preview_improvements
from workflow.improvement_suggestions import propose_improvements, validate_suggestions, matching_fix_hints
from workflow.worktrees import attach
from workflow.treatment_versions import apply_treatments


class ImprovementTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repo = self.root / 'library'
        (self.repo / 'src').mkdir(parents=True)
        (self.repo / 'src/ops.py').write_text('raise RuntimeError("TARGET MUST NEVER BE IMPORTED")\n\n'
            'def scaled(x, factor=2):\n    """Scale a value."""\n    return x * factor\n\n'
            'def offset(x, delta=1):\n    return x + delta\n')
        (self.repo / 'README.md').write_text('Original documentation')
        (self.repo / '.gitattributes').write_text('*.py filter=tripwire\n')
        (self.repo / 'private_answers.txt').write_text('HIDDEN_ORACLE_SENTINEL')
        config = self.repo / 'configs/aideal.yaml'
        config.parent.mkdir()
        config.write_text('extends: [python]\nproject: {name: TestLibrary, language: Python}\n'
            'codebase: {source_globs: [src/**/*.py]}\nfiles: {original_readme: README.md}\n')
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True, stderr=subprocess.DEVNULL).strip()
        git('init', '-q')
        git('config', 'user.name', 'Test')
        git('config', 'user.email', 'test@example.invalid')
        git('add', '.')
        git('commit', '-qm', 'Baseline')
        self.study = self.root / 'study'
        attach(self.repo, config, self.study)
        self.log = self.root / 'development.jsonl'
        self.log.write_text(json.dumps({'function': 'scaled', 'status': 'fail', 'split': 'development',
            'error': 'TypeError: factor must be numeric', 'root_cause': 'string factor passed',
            'code': 'scaled(2, "bad")'}) + '\n')
        self.model = self.root / 'model.py'
        self.model.write_text('''import json,sys
request=json.load(sys.stdin)
context=json.loads(request['prompt'])
api=next(a for a in context['apis'] if a['name']=='scaled')
errors=context['development_errors']
result={'aliases':[{'name':'scale_value','target_function':api['id'],'rationale':'Clearer action name'}],
 'alias_code':'from .ops import scaled\\n\\ndef scale_value(x, factor=2):\\n    return scaled(x, factor)\\n',
 'alias_interface':'scale_value(x, factor=2) delegates to scaled, preserving defaults and results.',
 'hints':[{'function_id':api['id'],'evidence_ids':[errors[0]['id']],
 'error_contains':'factor must be numeric','likely_cause':'A non-numeric factor may have been supplied.',
 'fix_steps':['Check the factor type and pass the intended numeric value.'],
 'suggested_fix_code':'scaled(2, 3)','validation':'Check numeric behavior and invalid-input behavior.'}] if errors else [],
 'notes':'Synthetic proposal; no compilation or runtime validation.'}
if len(sys.argv)>1:
 result['aliases']=[];result['alias_code']='';result['alias_interface']='';result['hints']=[]
print(json.dumps({'code':json.dumps(result),'model_version':'synthetic','usage':{'input_tokens':0,'output_tokens':0}}))
''')
        self.model_config = self.root / 'model.json'
        self.settings = {'model': {'name': 'synthetic', 'command': [sys.executable, str(self.model)],
            'temperature': 0, 'max_output_tokens': 4000, 'timeout_s': 5}}
        self.model_config.write_text(json.dumps(self.settings))

    def preview(self, **kwargs):
        result = preview_improvements(self.study, self.root / 'preview', alias_path='src/aliases.py',
            apis=['scaled'], development_errors=self.log, **kwargs)
        return Path(result['preview'])

    def test_preview_is_bounded_and_never_reads_private_answers_or_imports_source(self):
        preview = load(self.preview())
        self.assertEqual(0, preview['llm_calls'])
        self.assertEqual(['scaled'], [a['name'] for a in preview['context']['apis']])
        self.assertNotIn('HIDDEN_ORACLE_SENTINEL', json.dumps(preview))
        self.assertIn('TARGET MUST NEVER BE IMPORTED', json.dumps(preview))
        self.assertEqual('error-1', preview['context']['development_errors'][0]['id'])
        with self.assertRaisesRegex(ValueError, 'outside source'):
            preview_improvements(self.study, self.repo / 'new-preview', apis=['scaled'])
        self.assertFalse((self.repo / 'new-preview').exists())

    def test_preview_does_not_run_git_filters(self):
        marker = self.root / 'FILTER_EXECUTED'
        script = self.root / 'git_filter.py'
        script.write_text('from pathlib import Path\nimport sys\n'
            f'Path({str(marker)!r}).write_text("executed")\n'
            'sys.stdout.write(sys.stdin.read())\n')
        subprocess.run(['git', '-C', str(self.study / 'Original/source'), 'config',
            'filter.tripwire.clean', shlex.join([sys.executable, str(script)])], check=True)
        self.preview()
        self.assertFalse(marker.exists())

    def test_recorded_request_and_generated_alias_hints_are_consistent(self):
        preview = self.preview()
        readme = self.root / 'generated.md'
        readme.write_text('SUPPLIED_README_NOT_MODEL_INPUT')
        result = propose_improvements(preview, self.model_config, self.root / 'proposal', readme=readme)
        proposal = load(result['proposal'])
        self.assertEqual('proposed_unvalidated', result['status'])
        self.assertEqual({'readme', 'alias', 'alias_interface', 'error_hints'}, set(proposal['artifacts']))
        request = load(self.root / 'proposal/model_attempt/request.json')
        self.assertNotIn('SUPPLIED_README_NOT_MODEL_INPUT', request['prompt'])
        self.assertEqual(load(preview)['context'], json.loads(request['prompt']))
        self.assertIn('thin wrappers', request['system'])
        hints = load(proposal['artifacts']['error_hints']['path'])
        fn = load(preview)['context']['apis'][0]['id']
        selected = matching_fix_hints(hints, fn, 'TypeError: factor must be numeric')
        self.assertEqual(1, len(selected))
        self.assertEqual('unverified', selected[0]['status'])
        self.assertEqual([], matching_fix_hints(hints, 'another-function', 'factor must be numeric'))
        self.assertEqual([], matching_fix_hints(hints, fn, 'unrelated error'))
        self.assertTrue((self.root / 'proposal/function_fix_hints.jsonl').is_file())
        self.assertFalse((self.study / 'Alias only/source/src/aliases.py').exists())

    def test_study_hold_blocks_model_calls_but_allows_read_only_preview(self):
        (self.study / 'REVIEW_HOLD.json').write_text('{}')
        preview = self.preview()
        with self.assertRaisesRegex(ValueError, 'paused'):
            propose_improvements(preview, self.model_config, self.root / 'proposal')
        self.assertFalse((self.root / 'proposal').exists())

    def test_proposal_installs_identical_treatments_with_branch_commits(self):
        preview = self.preview()
        readme = self.root / 'generated.md'
        readme.write_text('Generated API documentation')
        result = propose_improvements(preview, self.model_config, self.root / 'proposal', readme=readme)
        application = apply_treatments(self.study, result['proposal'])
        self.assertEqual('applied_unvalidated', application['status'])
        self.assertFalse(application['evaluated'])
        attachment = load(self.study / 'attachment.json')
        self.assertEqual(attachment['revision'], application['arms']['original']['commit_revision'])
        for arm, item in application['arms'].items():
            if arm != 'original':
                self.assertNotEqual(item['parent_revision'], item['commit_revision'])
            source = Path(item['path'])
            self.assertEqual(arm in ('alias_only', 'combined'), (source / 'src/aliases.py').exists())
            self.assertEqual(arm in ('readme_only', 'combined'), (source / '.aideal/treatments/README.md').exists())
            self.assertEqual(arm in ('error_hints_only', 'combined'), (source / '.aideal/treatments/error_hints.json').exists())
        combined = Path(application['arms']['combined']['path'])
        for arm, names in {'readme_only': ['.aideal/treatments/README.md'],
                           'alias_only': ['src/aliases.py', '.aideal/treatments/ALIASES.md'],
                           'error_hints_only': ['.aideal/treatments/error_hints.json']}.items():
            for name in names:
                self.assertEqual((Path(application['arms'][arm]['path']) / name).read_bytes(),
                                 (combined / name).read_bytes())
        self.assertEqual(application, apply_treatments(self.study, result['proposal']))
        self.assertFalse((self.repo / 'src/aliases.py').exists())

    def test_source_change_after_preview_is_rejected_before_model_call(self):
        preview = self.preview()
        (self.study / 'Original/source/src/ops.py').write_text('def changed(): pass\n')
        with self.assertRaises(ValueError):
            propose_improvements(preview, self.model_config, self.root / 'proposal')
        self.assertFalse((self.root / 'proposal').exists())

    def test_known_held_out_failures_are_rejected(self):
        self.log.write_text(json.dumps({'function':'scaled','status':'fail','split':'held_out','error':'private'})+'\n')
        with self.assertRaisesRegex(ValueError, 'Held-out'):
            self.preview()
        self.assertFalse((self.root / 'preview').exists())

    def test_forged_evidence_unknown_api_and_unmatched_predicate_are_rejected(self):
        preview = self.preview()
        result = propose_improvements(preview, self.model_config, self.root / 'proposal')
        suggestions = load(self.root / 'proposal/suggestions.json')
        context = load(preview)['context']
        for location, field, value in [('aliases','target_function','unknown'),
            ('hints','evidence_ids',['invented']), ('hints','error_contains','string factor passed'),
            ('hints','fix_steps',[]), ('hints','function_id',{'invalid':'mapping'})]:
            with self.subTest(field=field):
                changed=deepcopy(suggestions);changed[location][0][field]=value
                with self.assertRaises(ValueError):validate_suggestions(changed, context)
        changed=deepcopy(suggestions);changed['hints'][0]['status']='verified'
        with self.assertRaises(ValueError):validate_suggestions(changed, context)

    def test_empty_model_suggestions_preserve_evidence_without_claiming_a_treatment(self):
        preview = self.preview()
        self.settings['model']['command'].append('empty')
        self.model_config.write_text(json.dumps(self.settings))
        result = propose_improvements(preview, self.model_config, self.root / 'proposal')
        self.assertEqual('no_supported_suggestions', result['status'])
        self.assertFalse((self.root / 'proposal/proposal.json').exists())
        self.assertTrue((self.root / 'proposal/model_attempt/process.json').is_file())


if __name__ == '__main__':
    unittest.main()
