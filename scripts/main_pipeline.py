"""Recorded main-only RDPro pipeline. No paid work occurs without an explicit stage."""
import argparse
import copy
import fcntl
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import time
from contextlib import contextmanager

from pipeline_gates import (bind, load, verified, write_once, refresh_manifest, inspect_bundle,
                            hint_delivery, require_review, require_alias_probes)


class Pipeline:
    def __init__(self, engine, study, seed_config_dir, python=sys.executable):
        self.engine = Path(engine).resolve(strict=True)
        self.study = Path(study).resolve(strict=True)
        self.seed = Path(seed_config_dir).resolve(strict=True)
        self.python = str(Path(python).resolve(strict=True))
        self.root = self.study / 'development/recorded_five_condition_run'
        self.inputs = self.study / 'development/authoring_inputs'
        self.root.mkdir(parents=True, exist_ok=True)
        sys.path.insert(0, str(self.engine))
        from workflow.preparation import _engine_config_module
        self.yaml = _engine_config_module().yaml
        self.plan = load(self.study / 'development/study_plan.json')

    def event(self, stage, status, **fields):
        row = {'time_unix': time.time(), 'stage': stage, 'status': status, **fields}
        encoded = (json.dumps(row, ensure_ascii=False) + '\n').encode()
        fd = os.open(self.root / 'events.jsonl', os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.write(fd, encoded); os.fsync(fd)
        finally:
            os.close(fd)
        return row

    @contextmanager
    def lock(self, name):
        with (self.root / (name + '.lock')).open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    def json(self, relative, value):
        return write_once(self.root / relative, value)

    def telemetry(self, stage):
        from workflow.task_telemetry import collect_telemetry
        stamp=str(time.time_ns())
        scopes={'development':self.root,'audience':self.study/'runs/recorded_five_conditions'}
        paths=[]
        for name,root in scopes.items():
            if root.exists():
                report=collect_telemetry(root)
                path=self.json('telemetry/'+stamp+'-'+stage+'-'+name+'.json',report)
                paths.append(bind(path))
        return paths

    def command(self, stage, args, result_paths, *, resume=False):
        """Only controller commands are executed; model-generated shell text never is."""
        folder = self.root / 'stages' / stage
        folder.mkdir(parents=True, exist_ok=True)
        with self.lock(stage):
            complete = folder / 'complete.json'
            if complete.exists():
                receipt = load(complete)
                if receipt['command'] != args:
                    raise ValueError('Stage command changed')
                for ref in receipt['outputs']:
                    verified(ref)
                return receipt
            attempts = sorted(folder.glob('attempt-*'))
            if attempts and not resume:
                raise ValueError('Prior incomplete stage needs explicit reconciliation: ' + stage)
            attempt = folder / ('attempt-%03d' % (len(attempts) + 1))
            attempt.mkdir()
            write_once(attempt / 'command.json', {'args': args})
            self.event(stage, 'started', attempt=str(attempt))
            env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(self.engine)}
            started = time.monotonic()
            caught = None
            try:
                with (attempt / 'stdout.log').open('w') as out, (attempt / 'stderr.log').open('w') as err:
                    result = subprocess.run(args, cwd=self.engine, env=env, stdout=out, stderr=err,
                                            timeout=180 if stage=='publish' else None)
            except BaseException as exc:
                caught = exc
                result = type('InterruptedProcess', (), {'returncode': None})()
            record = {'command': args, 'returncode': result.returncode, 'seconds': time.monotonic()-started,
                      'stdout': bind(attempt/'stdout.log'), 'stderr': bind(attempt/'stderr.log')}
            write_once(attempt/'process.json', record)
            self.telemetry(stage)
            if caught is not None:
                self.event(stage,'interrupted',error_type=type(caught).__name__)
                raise caught
            if result.returncode or any(not Path(p).is_file() for p in result_paths):
                self.event(stage, 'failed', process=str(attempt/'process.json'))
                raise ValueError('Stage failed or did not publish its expected receipts: ' + stage)
            if stage == 'propose' and load(result_paths[0]).get('status') != 'complete_unvalidated':
                self.event(stage, 'incomplete_requires_review')
                raise ValueError('Proposal collection incomplete or conflicting; review saved evidence')
            if stage == 'audience' and load(result_paths[0]).get('all_complete') is not True:
                self.event(stage, 'unresolved_units')
                raise ValueError('Audience report has unresolved units; no completion claimed')
            receipt = {**record, 'outputs': [bind(p) for p in result_paths]}
            write_once(complete, receipt)
            self.event(stage, 'complete', receipt=str(complete))
            return receipt

    def verify_prepared(self):
        value = load(self.root/'prepared.json')
        for ref in value['bindings']:
            verified(ref)
        from workflow.native_provider_bridge import active_controller_hashes
        if active_controller_hashes() != value['controller_sha256']:
            raise ValueError('Provider/controller changed after run preparation')
        return value

    def prepare(self):
        from workflow.native_provider_bridge import active_controller_hashes
        from workflow.readme_authoring import prepare_readme_session
        with self.lock('prepare'):
            if (self.root/'prepared.json').exists():
                return self.verify_prepared()
            attachment = load(self.study/'attachment.json')
            if attachment['revision'] != self.plan['source_revision']:
                raise ValueError('Attached baseline differs from reviewed study plan')
            cfg = self.yaml.safe_load((self.seed/'baseline.yaml').read_text())
            pins = active_controller_hashes()
            if self.plan['tasks'] != {'micro':16,'puzzle':16,'fixtures_per_task':3} or self.plan['readme_scope']['families'] != 280:
                raise ValueError('This runner requires the reviewed 16-API/32-task/280-family scope')
            for role in ('author', 'reviewer', 'fixer'):
                entry = cfg['models']['registry'][cfg['models']['roles'][role]]
                if entry['provider'] != 'aideal-codex-audited' or entry['model'] != 'gpt-5.3-codex':
                    raise ValueError('Unexpected authoring provider')
                bridge = entry['bridge']
                if bridge['policy'] != 'study-v2' or float(bridge['max_cost_usd']) != 100:
                    raise ValueError('Expected approved existing study-v2 $100 policy')
                if (bridge['study_id'] != self.plan['study_id']
                        or bridge['budget_ledger'] != str(self.study/'development/shared_budget.json')
                        or bridge['max_output_tokens'] != (8192 if role=='reviewer' else 4096)):
                    raise ValueError('Native role policy differs from the reviewed main-only limits')
                bridge.update(controller_sha256=pins, evidence_dir=str(self.root/'provider_evidence'/role))
            cfg['files']['project_profile'] = str((self.seed/'project_profile.yaml').resolve(strict=True))
            cfg['files']['prompts_dir'] = str(self.engine/'prompts')
            cfg['study_preparation'] = {'status': 'authorized_main_only', 'audience_units': 480}
            config = self.root/'configs/baseline.yaml'; config.parent.mkdir(exist_ok=True)
            text = self.yaml.safe_dump(cfg, sort_keys=False)
            if config.exists() and config.read_text() != text:
                raise ValueError('Copied model configuration changed')
            config.write_text(text)
            model = self.yaml.safe_load((self.seed/'improvement-model.yaml').read_text())
            expected_flags = {'--budget-policy=study-v2', '--study-id='+self.plan['study_id'], '--max-cost-usd=100',
                              '--budget-ledger='+str(self.study/'development/shared_budget.json')}
            if not expected_flags <= set(model['model']['command']) or model['model']['max_output_tokens'] != 8192:
                raise ValueError('Proposal adapter must share the exact reviewed ledger and limits')
            model['model']['command'][0] = self.python
            model['model']['command'][1] = str(self.engine/'workflow/openai_codex_adapter.py')
            model['status'] = 'authorized_main_only'
            proposal_config = self.root/'configs/improvement-model.yaml'
            content = self.yaml.safe_dump(model, sort_keys=False)
            if proposal_config.exists() and proposal_config.read_text() != content:
                raise ValueError('Copied proposal configuration changed')
            proposal_config.write_text(content)
            session = self.root/'authoring'
            if not session.exists():
                prepare_readme_session(config, self.inputs/'full.manifest.json', self.inputs/'base.skeleton.md',
                                       self.inputs/'shared_public_context.md', session)
            original = self.root/'original_documentation.md'
            docs = cfg['files']['original_readme']
            if not isinstance(docs, list) or not all(Path(p).is_absolute() for p in docs):
                raise ValueError('Seed original documentation must be explicit absolute files')
            data = '\n\n'.join(Path(p).read_text() for p in docs).encode()
            if original.exists() and original.read_bytes() != data:
                raise ValueError('Original documentation changed')
            original.write_bytes(data)
            paths = [config, proposal_config, original, session/'session.json', self.study/'development/study_plan.json',
                     self.study/'development/library_improvement_preview/manifest.json', Path(__file__), Path(__file__).with_name('pipeline_gates.py')]
            paths += sorted((self.engine/'workflow').glob('*.py'))
            paths += sorted((self.engine/'vendor/aideal_engine/src/aideal').glob('*.py'))
            paths += sorted((self.engine/'prompts').rglob('*.md'))
            paths += [p for p in (self.study/'evaluation_assets').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
            runtime_seed = load(self.study/'evaluation_assets/runtime.json')
            paths += [Path(p) for p in [runtime_seed['java'], runtime_seed['javac'], *runtime_seed['jars']]]
            paths += list(Path(__file__).parent.glob('alias_*.py'))
            if not Path(__file__).with_name('alias_probe.py').is_file():
                raise ValueError('Install the independent alias probe helper before preparation')
            if not (self.engine/'workflow/task_telemetry.py').is_file():
                raise ValueError('Install reviewed task telemetry before final preparation')
            paths = sorted(set(paths))
            versions=json.loads(subprocess.check_output([self.python,'-c',
                'import sys,importlib.metadata,json;print(json.dumps({"python":sys.version,"openai":importlib.metadata.version("openai")}))'],text=True))
            environment={'python_executable':self.python,'python_version':versions['python'],
                         'os':platform.system(),'os_release':platform.release(),'architecture':platform.machine(),
                         'openai_sdk_version':versions['openai'],
                         'engine_git_head':subprocess.check_output(['git','-C',str(self.engine),'rev-parse','HEAD'],text=True).strip(),
                         'engine_git_branch':subprocess.check_output(['git','-C',str(self.engine),'symbolic-ref','--short','HEAD'],text=True).strip(),
                         'source_revision':attachment['revision'],'secrets_or_environment_dumped':False}
            paths.append(self.json('environment.json',environment))
            result = {'status': 'prepared_main_only', 'main_units': 480, 'controls_required': 480,
                      'controller_sha256': pins, 'bindings': [bind(p) for p in paths], 'provider_calls': 0}
            self.json('prepared.json', result); self.event('prepare', 'complete'); self.telemetry('prepare')
            return result

    def propose(self):
        self.verify_prepared()
        return self.command('propose', [self.python, '-m', 'workflow', 'propose-library',
            '--preview', str(self.study/'development/library_improvement_preview/manifest.json'),
            '--model-config', str(self.root/'configs/improvement-model.yaml'), '--output', str(self.root/'proposals')],
            [self.root/'proposals/collection.json'])

    def author(self):
        self.verify_prepared()
        from workflow.readme_session import load_verified
        load_verified(self.root/'authoring')
        return self.command('author', [self.python, '-m', 'workflow.readme_session', '--session', str(self.root/'authoring')],
                            [self.root/'authoring/completion.json', self.root/'authoring/README.md'])

    def refresh(self):
        self.verify_prepared(); self.author()
        from workflow.readme_spans import inspect_sections
        from workflow.readme_authoring import prepare_readme_session
        with self.lock('prepare-refresh'):
            manifest = refresh_manifest(load(self.inputs/'full.manifest.json'), (self.root/'authoring/README.md').read_bytes(),
                                       self.plan['readme_scope']['refresh_selected_ids'], inspect_sections)
            path = self.json('refresh.manifest.json', manifest)
            if not (self.root/'refresh').exists():
                prepare_readme_session(self.root/'configs/baseline.yaml', path, self.root/'authoring/README.md',
                                       self.inputs/'shared_public_context.md', self.root/'refresh',
                                       self.inputs/'development_diagnostics.jsonl')
        from workflow.readme_session import load_verified
        load_verified(self.root/'refresh')
        return self.command('refresh', [self.python, '-m', 'workflow.readme_session', '--session', str(self.root/'refresh')],
                            [self.root/'refresh/completion.json', self.root/'refresh/README.md'])

    def artifacts(self):
        self.propose(); self.refresh()
        collection = load(self.root/'proposals/collection.json')
        if collection.get('completed_batches') != 4 or collection.get('status') != 'complete_unvalidated':
            raise ValueError('Four complete proposal batches required')
        proposals = [verified(row['proposal']) for row in collection['batches'] if row.get('proposal')]
        if not proposals:raise ValueError('No supported treatments; requires review')
        args = [self.python, '-m', 'workflow', 'bundle-proposals']
        for path in proposals:
            args += ['--proposal', str(path)]
        args += ['--readme', str(self.root/'refresh/README.md'), '--output', str(self.root/'bundle')]
        self.command('bundle', args, [self.root/'bundle/proposal.json'])
        check = inspect_bundle(self.root/'bundle/proposal.json', self.plan['api_function_ids'])
        self.json('artifact_manifest.json', check)
        self.event('artifacts', 'artifacts_ready_requires_review', manifest=str(self.root/'artifact_manifest.json'))
        return check

    def install_build(self, review):
        self.verify_prepared()
        require_review(review, self.root/'artifact_manifest.json', self.root/'bundle/proposal.json')
        self.json('installation_review_binding.json', bind(review))
        self.command('install', [self.python, '-m', 'workflow', 'install-treatments', '--study', str(self.study),
                                '--proposal', str(self.root/'bundle/proposal.json')], [self.study/'treatments/current.json'])
        return self.command('build', [self.python, str(self.study/'evaluation_assets/build_backends.py'),
                                     '--study', str(self.study), '--output', str(self.root/'runtime')],
                            [self.root/'runtime/backends.json'])

    def proposal_paths(self):
        collection=load(self.root/'proposals/collection.json')
        if collection.get('completed_batches')!=4 or collection.get('status')!='complete_unvalidated':
            raise ValueError('Four completed proposal batches are required')
        return [verified(row['proposal']) for row in collection['batches'] if row.get('proposal')]

    def source_review(self):
        self.propose()
        args=[self.python,str(Path(__file__).with_name('alias_probe.py')),'source-review']
        for path in self.proposal_paths():args += ['--proposal',str(path)]
        args += ['--targets',str(self.study/'evaluation_assets/targets.json'),
                 '--source-root',load(self.study/'attachment.json')['worktrees']['original']['path'],
                 '--owner-helper',str(self.engine/'workflow/scala_owners.py'),'--output',str(self.root/'source_review')]
        return self.command('source-review',args,[self.root/'source_review/review.json'])

    def alias_probe(self):
        from workflow.condition_setup import read_condition_config
        self.configure()
        payload=read_condition_config(self.root/'conditions.yaml')
        receipts=self.json('backend_receipts.json',payload['backends'])
        helper=str(Path(__file__).with_name('alias_probe.py'))
        self.command('prepare-alias-probes',[self.python,helper,'prepare','--proposal',str(self.root/'bundle/proposal.json'),
            '--targets',str(self.study/'evaluation_assets/targets.json'),
            '--source-root',load(self.study/'attachment.json')['worktrees']['original']['path'],
            '--owner-helper',str(self.engine/'workflow/scala_owners.py'),'--backends',str(self.root/'runtime/backends.json'),
            '--backend-receipts',str(receipts),'--trace-runner',str(self.study/'evaluation_assets/TraceRunner.java'),
            '--output',str(self.root/'alias_probe_plan')],[self.root/'alias_probe_plan/plan.json'])
        return self.command('alias-probes',[self.python,helper,'run','--plan',str(self.root/'alias_probe_plan/plan.json'),
            '--output',str(self.root/'alias_probes')],[self.root/'alias_probes/receipt.json'])

    def configure(self):
        self.verify_prepared()
        from workflow.condition_setup import read_condition_config
        from workflow.condition_inputs import FIVE_ARMS
        backends = load(self.root/'runtime/backends.json')
        attachment = load(self.study/'attachment.json')
        model = self.yaml.safe_load((self.root/'configs/improvement-model.yaml').read_text())['model']
        model = {'name': model['name'], 'command': model['command'], 'artifacts': [str(self.engine/'workflow'/p) for p in
                        ('openai_codex_adapter.py', 'provider_budget.py', 'response_status.py')]}
        conditions = {}
        for arm in FIVE_ARMS:
            row = backends[arm]; source = Path(row['worktree'])
            branch = subprocess.check_output(['git', '-C', str(source), 'symbolic-ref', '--short', 'HEAD'], text=True).strip()
            if str(source) != attachment['worktrees'][arm]['path']:
                raise ValueError('Backend does not belong to attached arm')
            treatment = source/'.aideal/treatments'
            condition = {'documents': [str(treatment/'README.md') if arm in ('readme_only','combined') else str(self.root/'original_documentation.md')],
                         'source': {'worktree':str(source),'revision':row['revision'],'branch':branch,'artifacts':row['source_artifacts']},
                         'adapter': {'command':[self.python,str(self.study/'evaluation_assets/execute.py'),row['runtime']],
                                     'artifacts':row['source_artifacts']}}
            if arm in ('alias_only','combined'):condition['alias_interface']=str(treatment/'ALIASES.md')
            if arm in ('error_hints_only','combined'):condition['error_hints']=str(treatment/'error_hints.json')
            conditions[arm]=condition
        policy = self.plan['public_context_policy']
        cfg = {'schema_version':1,'design':'five_arm','bank':str(self.study/'bank/bank.json'), 'model':model,
               'api_function_ids':self.plan['api_function_ids'],'development_case_ids':[],
               'holdout_review':'Assistant-authored independent Python expected-value algorithms and trusted Scala controls. Fresh bank held out from author/proposal payloads; only separate development diagnostics used. Three fixtures per case, target-trace union is not causal attribution.',
               'common':{'temperature':0,'max_output_tokens':2048,'max_snippet_fixes':1,'provider_attempt_limit':1,
                         'execution_timeout_s':150,'provider_timeout_s':150,'trial_ids':['trial_01','trial_02','trial_03'],
                         'ordering_seed':42,'documentation_max_characters':8000,'documentation_selection':policy['documentation_selection'],
                         'alias_max_characters':12000,'hint_max_characters':1500,'source_access':False}, 'conditions':conditions}
        path=self.root/'conditions.yaml'; data=self.yaml.safe_dump({'condition_evaluation':cfg},sort_keys=False)
        if path.exists() and path.read_text()!=data:raise ValueError('Condition config changed')
        path.write_text(data)
        read_condition_config(path)  # Read-only source/artifact/schema checks, no controls.
        self.event('configure','complete',configuration=str(path))
        return {'configuration':bind(path)}

    def preflight(self, alias_probes):
        from workflow.condition_setup import read_condition_config
        from workflow.condition_context import public_context
        self.configure()
        payload=read_condition_config(self.root/'conditions.yaml')
        check=inspect_bundle(self.root/'bundle/proposal.json',self.plan['api_function_ids'])
        hints=hint_delivery(check,self.study/'development/independent_compiler_diagnostics_v1/development_diagnostics.jsonl',
                            self.plan['api_function_ids'],[str(self.root/'original_documentation.md')],
                            self.plan['public_context_policy']['documentation_selection'],public_context)
        self.json('hint_delivery.json',hints)
        hint_count = len(load(check['artifacts']['error_hints']['path'])['hints'])
        matched = {h['index'] for row in hints['rows'] for h in row['matched']}
        if not hint_count or len(matched) != hint_count or any(r['truncated'] for r in hints['rows']):
            raise ValueError('Some development hints missing/clipped; requires explicit review before freeze')
        aliases=require_alias_probes(alias_probes,check,self.root/'runtime/backends.json',payload['backends'],self.target_events())
        result={'status':'preflight_passed','configuration':bind(self.root/'conditions.yaml'),
                'alias_behavior':aliases,'hint_delivery':bind(self.root/'hint_delivery.json'), 'artifacts':check}
        self.json('preflight.json',result);self.event('preflight','complete');return result

    def target_events(self):
        return {r['api']:r['jvm_owner']+'.'+r['method']+r['descriptor']
                for r in load(self.study/'evaluation_assets/targets.json')['targets']}

    def freeze(self):
        self.verify_prepared()
        gate=load(self.root/'preflight.json')
        if gate['status']!='preflight_passed' or gate['configuration']!=bind(self.root/'conditions.yaml'):
            raise ValueError('Matching completed preflight required')
        verified(gate['alias_behavior']['receipt']);verified(gate['hint_delivery'])
        review = verified(load(self.root/'installation_review_binding.json'))
        require_review(review, self.root/'artifact_manifest.json', self.root/'bundle/proposal.json')
        from workflow.condition_setup import read_condition_config
        payload = read_condition_config(self.root/'conditions.yaml')
        require_alias_probes(gate['alias_behavior']['receipt']['path'],
                            inspect_bundle(self.root/'bundle/proposal.json', self.plan['api_function_ids']),
                            self.root/'runtime/backends.json', payload['backends'], self.target_events())
        result=self.command('freeze',[self.python,'-m','workflow','freeze-conditions','--config',str(self.root/'conditions.yaml'),
                          '--output',str(self.root/'frozen')],[self.root/'frozen/frozen.json'],resume=True)
        return result

    def publish(self):
        self.verify_prepared()
        from workflow.condition_inputs import FIVE_ARMS
        attachment=load(self.study/'attachment.json');baseline=attachment['revision']
        root=attachment['worktrees']['original']['path']
        def git(*args):return subprocess.check_output(['git','-C',root,*args],text=True,timeout=180).strip()
        if len(git('rev-list','--parents','-n','1',baseline).split())!=1:
            raise ValueError('Only the clean root snapshot ancestry may be published')
        prefix='study/2026-09-22-gpt-5.3-codex-32tasks'
        remote='https://github.com/ZhuochengShang/AIDEAL-RDPro.git'
        auth=['git','-c','credential.helper=','-c','credential.helper=!gh auth git-credential',
              '-c','http.lowSpeedLimit=1','-c','http.lowSpeedTime=60','-C',root]
        backends=load(self.root/'runtime/backends.json');refs={}
        for arm in FIVE_ARMS:
            revision=backends[arm]['revision'];git('merge-base','--is-ancestor',baseline,revision)
            name=prefix+'/'+arm.replace('_','-')
            existing=subprocess.check_output(auth+['ls-remote',remote,'refs/heads/'+name],text=True,timeout=180).strip()
            if existing and existing.split()[0]!=revision:raise ValueError('Remote study branch already has another commit')
            refs[name]=revision
        output=self.root/'published_source_branches.json'
        receipt=self.root/'stages/publish/complete.json'
        if not receipt.exists():
            self.command('publish',auth+['push','--atomic',remote,*[sha+':refs/heads/'+name for name,sha in refs.items()]],[])
        for name,sha in refs.items():
            actual=subprocess.check_output(auth+['ls-remote',remote,'refs/heads/'+name],text=True,timeout=180).strip()
            if not actual or actual.split()[0]!=sha:raise ValueError('Published study reference verification failed')
        return self.json('published_source_branches.json',{'status':'verified_remote_refs','remote':remote,'branches':refs})

    def run(self):
        self.publish(); self.freeze()
        return self.command('audience',[self.python,'-m','workflow','run-conditions','--study',str(self.root/'frozen/frozen.json'),
                            '--output',str(self.study/'runs/recorded_five_conditions')],
                            [self.study/'runs/recorded_five_conditions/report.json'],resume=True)

    def status(self):
        return {'root':str(self.root),'stages':{p.parent.name:load(p) for p in sorted((self.root/'stages').glob('*/complete.json'))},
                'artifact_review_needed':(self.root/'artifact_manifest.json').exists() and not (self.root/'runtime/backends.json').exists(),
                'results':str(self.study/'runs/recorded_five_conditions/report.json')}

    def await_gate(self, path, stage, wait):
        if path and wait:
            self.event(stage, 'waiting_for_external_review', expected=str(path))
            while True:
                try:
                    load(path);break
                except (FileNotFoundError,json.JSONDecodeError):
                    time.sleep(15)
        return bool(path and Path(path).is_file())

    def advance(self, review=None, alias_probes=None, wait=False):
        with self.lock('advance'):
            self.prepare();self.propose()
            if not review:
                self.source_review();review=self.root/'source_review/review.json'
            self.artifacts()
            if not self.await_gate(review, 'installation-review', wait):
                return {'status':'artifacts_ready_requires_review','manifest':str(self.root/'artifact_manifest.json')}
            self.install_build(review);self.configure()
            if not alias_probes:
                self.alias_probe();alias_probes=self.root/'alias_probes/receipt.json'
            if not self.await_gate(alias_probes, 'alias-probes', wait):
                return {'status':'runtime_ready_requires_alias_behavior_probes','backends':str(self.root/'runtime/backends.json')}
            self.preflight(alias_probes);self.publish();self.freeze();return self.run()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','propose','author','refresh','artifacts','install-build','source-review','alias-probe','configure','preflight','publish','freeze','run','advance','status'])
    for name in ('engine','study','seed-config-dir'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--python',default=sys.executable);parser.add_argument('--review');parser.add_argument('--alias-probes')
    parser.add_argument('--wait-for-review', action='store_true', help='Advance waits for explicit review/probe files; never invents approval')
    args=parser.parse_args();pipeline=Pipeline(args.engine,args.study,args.seed_config_dir,args.python)
    try:
        if args.stage=='advance':result=pipeline.advance(args.review,args.alias_probes,args.wait_for_review)
        elif args.stage=='install-build':
            if not args.review:parser.error('--review required')
            result=pipeline.install_build(args.review)
        elif args.stage=='preflight':
            if not args.alias_probes:parser.error('--alias-probes required')
            result=pipeline.preflight(args.alias_probes)
        else:result=getattr(pipeline,args.stage.replace('-','_'))()
    except BaseException as exc:
        pipeline.event(args.stage,'stopped',error_type=type(exc).__name__)
        try:
            pipeline.telemetry('stopped-'+args.stage)
        except Exception as telemetry_error:
            pipeline.event('telemetry','failed',error_type=type(telemetry_error).__name__)
        raise
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
