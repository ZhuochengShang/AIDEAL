"""Explicit local execution of prepared development probes, with raw receipts.

No providers, held-out task banks or reference solutions are accepted. JVMs run
with normal host permissions; this helper is not an operating-system sandbox.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from urllib.parse import unquote, urlparse

from alias_probe_evidence import bind, core_ref, git, load, save, verified, verify_runtime

HARNESS = '''public class Harness {
  public static void main(String[] args) {
    AliasDevelopmentProbe$.MODULE$.main(args);
  }
}
'''


def command(args, directory, stem, timeout=120):
    """Retain stdout/stderr/process status even on launch errors and timeouts."""
    directory = Path(directory); start = time.monotonic()
    record = {'command':args, 'cwd':str(directory), 'timeout_seconds':timeout, 'returncode':None}
    env = {key:os.environ[key] for key in ('HOME','TMPDIR','LANG','LC_ALL') if key in os.environ}
    env['PATH'] = os.defpath
    with (directory/(stem+'.stdout')).open('xb') as out, (directory/(stem+'.stderr')).open('xb') as err:
        try:
            child = subprocess.Popen(args, cwd=directory, env=env, stdout=out, stderr=err, start_new_session=True)
            try: record['returncode'] = child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL); child.wait()
                record.update(returncode=child.returncode, timed_out=True)
        except OSError as error:
            record['launch_error'] = type(error).__name__ + ': ' + str(error)
    record['elapsed_seconds'] = round(time.monotonic()-start, 6)
    record['stdout'] = bind(directory/(stem+'.stdout')); record['stderr'] = bind(directory/(stem+'.stderr'))
    ref = save(directory/(stem+'.process.json'), record)
    if record['returncode'] != 0: raise ValueError('Development process failed; retain evidence: '+ref['path'])
    return ref


def observations(path, expected_mode, expected_count=None):
    records = [line.split('=',1)[1] for line in Path(path).read_text().splitlines()
               if line.startswith('AIDEAL_DEVELOPMENT_PROBE=')]
    if len(records) != 1: raise ValueError('Expected exactly one development observation record')
    value = json.loads(records[0]); rows = value.get('observations')
    if (set(value) != {'mode','observations'} or value['mode'] != expected_mode
            or not isinstance(rows,list) or not rows or any(not isinstance(r,str) for r in rows)
            or (expected_count is not None and len(rows) != expected_count)):
        raise ValueError('Malformed or incomplete development observations')
    # Matching exceptions alone are insufficient evidence of useful forwarding.
    if not any(row.startswith('ok:') for row in rows):
        raise ValueError('All examples failed; requires review despite matching exceptions')
    return rows


def loaded_from(path, owner, overlay):
    found = []
    for line in Path(path).read_text().splitlines():
        if '] ' in line and ' source: ' in line:
            name, source = line.split('] ')[-1].split(' source: ',1)
            if name == owner:
                location = urlparse(source)
                found.append(location.scheme == 'file' and Path(unquote(location.path)).resolve() == Path(overlay).resolve())
    return bool(found) and all(found)


def compare(canonical, alias, entry, overlay):
    left = observations(verified(canonical['stdout']), 'canonical', entry['example_count'])
    right = observations(verified(alias['stdout']), 'alias', entry['example_count'])
    for run in (canonical, alias):
        if load(verified(run['process']))['returncode'] != 0: raise ValueError('JVM failed')
        for field in ('stderr','trace','classload'): verified(run[field])
    if left != right: raise ValueError('Canonical/alias development observations differ')
    canonical_event, alias_event = entry['canonical_event'], entry['alias_event']
    ct = verified(canonical['trace']).read_text().splitlines()
    at = verified(alias['trace']).read_text().splitlines()
    if canonical_event not in ct or canonical_event not in at or alias_event not in at or alias_event in ct:
        raise ValueError('Separate traces do not establish the alias-phase canonical route')
    target_owner = canonical_event.split('(',1)[0].rsplit('.',1)[0]
    alias_owner = alias_event.split('(',1)[0].rsplit('.',1)[0]
    for run, owner in ((canonical,target_owner),(alias,target_owner),(alias,alias_owner)):
        if not loaded_from(verified(run['classload']),owner,overlay):
            raise ValueError('Observed class was not loaded from the bound source overlay')
    return {'canonical_run':canonical, 'alias_run':alias, 'canonical_observations':left,
            'alias_observations':right, 'observations_equal':True,
            'limits':'Finite paired development examples; traces aggregate examples in each separate JVM, not per-example or causal proof.'}


def verify_plan(plan_path, expected=None, full=True):
    from alias_probe import HERE, MODULES
    plan_ref = bind(plan_path)
    if expected is not None and plan_ref != expected: raise ValueError('Plan changed during execution')
    plan = load(plan_path)
    if (plan.get('status') != 'prepared_not_executed'
            or plan.get('held_out_bank_used_for_development') is not False
            or plan.get('protocol') != 'independent_development_alias_probe_v1'):
        raise ValueError('Wrong development plan protocol')
    for key in ('proposal','targets','backends','backend_receipts','trace_runner'): verified(plan[key])
    for ref in plan['controllers'] + plan['canonical_sources']: verified(ref)
    if any(bind(HERE/name) not in plan['controllers'] for name in MODULES):
        raise ValueError('Executing probe controller differs from the prepared controller')
    for ref in plan['aliases']: verified(core_ref(ref))
    if git(plan['baseline_root'],'rev-parse','HEAD') != plan['baseline_revision']:
        raise ValueError('Baseline checkout changed')
    for entry in plan['entries']:
        for key in ('certificate','program','trace_policy'): verified(entry[key])
    backends, receipts = load(plan['backends']['path']), load(plan['backend_receipts']['path'])
    runtimes, builds = {}, {}
    for arm in ('alias_only','combined'):
        verified(plan['runtimes'][arm])
        if full:
            runtime, build = verify_runtime(backends[arm],receipts[arm],plan['aliases'],plan['trace_runner']['path'])
        else:
            runtime = load(plan['runtimes'][arm]['path']); build = load(verified(runtime['build_identity']))
            for ref in [*build['inputs']['source'],build['overlay'],build['helper']]: verified(ref)
            if git(build['worktree'],'rev-parse','HEAD') != build['revision']: raise ValueError('Arm source HEAD changed')
        runtimes[arm], builds[arm] = runtime, build
    return plan, receipts, runtimes, builds


def execute_pair(directory, entry, runtime, trace_runner):
    directory.mkdir(); classes = directory/'classes'; classes.mkdir()
    program = verified(entry['program']); policy = verified(entry['trace_policy'])
    (directory/'Harness.java').write_text(HARNESS)
    compiler_cp = os.pathsep.join(runtime['compiler_jars'])
    library_cp = os.pathsep.join([runtime['overlay'],runtime['helper'],*runtime['runtime_jars']])
    command([runtime['java'],'-cp',compiler_cp,'scala.tools.nsc.Main','-classpath',library_cp,
             '-d',str(classes),str(program)], directory, 'scala_compile')
    run_cp = os.pathsep.join([runtime['overlay'],runtime['helper'],str(classes),*runtime['runtime_jars']])
    command([runtime['javac'],'-cp',run_cp,'-d',str(classes),str(directory/'Harness.java'),
             str(trace_runner)], directory,'java_compile')
    runs = []
    for mode in ('canonical','alias'):
        where = directory/mode; where.mkdir()
        process = command([runtime['java'],'-cp',str(classes),'TraceRunner',run_cp,mode,str(policy)], where,'debugger')
        runs.append({'process':process, 'stdout':bind(where/'program.stdout'),
                     'stderr':bind(where/'program.stderr'), 'trace':bind(where/'trace.txt'),
                     'classload':bind(where/'classload.log')})
    comparison = compare(*runs,entry,runtime['overlay'])
    return save(directory/'comparison.json',comparison)


def run(plan_path, output):
    from alias_probe import new_output
    plan_ref = bind(plan_path)
    plan, receipts, runtimes, builds = verify_plan(plan_path,plan_ref)
    out = new_output(output,[plan['baseline_root'],*(r['worktree'] for r in receipts.values())])
    rows = []
    try:
        for arm in ('alias_only','combined'):
            for index, entry in enumerate(plan['entries'],1):
                verify_plan(plan_path,plan_ref,full=False)
                unit = out/(arm+'_%04d' % index)
                request = {'protocol':plan['protocol'], 'backend':receipts[arm], 'target_apis':[entry['api']],
                           'program':entry['program'], 'certificate':entry['certificate'],
                           'trace_policy':entry['trace_policy'], 'plan':plan_ref}
                # Request is persisted before launching either compiler or JVM.
                request_ref = save(out/(arm+'_%04d.request.json' % index), request)
                comparison_ref = execute_pair(unit,entry,runtimes[arm],verified(plan['trace_runner']))
                verify_plan(plan_path,plan_ref,full=False)
                raw = [bind(p) for p in sorted(unit.rglob('*')) if p.is_file()]
                payload = {'backend_sha256':receipts[arm]['sha256'], 'build_sha256':builds[arm]['sha256'],
                    'execution_pass':True,'paired_observations_pass':True,
                    'canonical_target_reached':True,'alias_target_reached':True,
                    'observed_alias_events':[entry['alias_event']],
                    'adjudication_artifacts':[request_ref,*raw,entry['program'],entry['certificate'],entry['trace_policy']]}
                process_ref = save(unit/'process.json',{'status':'ok','payload':payload})
                rows.append({**{k:entry[k] for k in ('api','alias_name','canonical_event','alias_event')},
                             'arm':arm,'request':request_ref,'process':process_ref,'comparison':comparison_ref})
        verify_plan(plan_path,plan_ref,full=True)
        value = {'status':'verified_alias_behavior','proposal':plan['proposal'],'backends':plan['backends'],
            'backend_receipts':plan['backend_receipts'],'plan':plan_ref,
            'held_out_bank_used_for_development':False,'probes':rows,
            'alias_target_coverage':plan['alias_target_coverage'],'untreated_targets':plan['untreated_targets'],
            'limits':plan['limits']}
        save(out/'receipt.json',value); return value
    except Exception as error:
        save(out/'failure.json',{'status':'requires_review','plan':plan_ref,'completed_probes':rows,
             'error_type':type(error).__name__,'reason':str(error),
             'held_out_bank_used_for_development':False})
        raise
