#!/usr/bin/env python3
"""Render the audited reading route as an offline HTML guide and editable SVG.

Function locations come from the existing static code map. This diagram is a
dependency/reading guide, not proof that every stage is automatically invoked.
"""
from __future__ import annotations

import argparse
import ast
from html import escape
import json
from pathlib import Path
from urllib.parse import quote

from build_code_map import build_map


STAGES = [
    ('setup', '1. Choose the project and runtime',
     'Start with the correct interpreter, library source, README, fixtures, task bank and model settings.',
     ['workflow.__main__:main', 'workflow.evaluation_setup:read_config', 'workflow.preparation:prepare_study'],
     'configs/*.example.yaml; project profile; public task contracts; private checker data',
     'No model call. Native engine and portable evaluator have separate configuration/CLI paths.',
     'Validated configuration or an actionable setup error.',
     'scripts/aideal --help; scripts/aideal status; scripts/check_project.py --tests --output <fresh-directory>',
     'The tested environment is geo_llm_spark. Plain system python3 is 3.9 and does not have the required packages.'),
    ('versions', '2. Attach isolated library versions',
     'Prepare five source worktrees or inspect an existing attached study. Editing toolkit code is separate from switching a library treatment.',
     ['workflow.worktrees:attach', 'workflow.preparation:prepare_study', 'workflow.source_refactors:study_versions'],
     'Library repository, YAML configuration, and a new study directory.',
     'No model call. Git/source identity checks and explicit worktree preparation.',
     '<study>/attachment.json; Original/source; README only/source; Alias only/source; Error hints only/source; Combined/source.',
     'scripts/aideal attach --repo <library> --config <yaml> --output <new-study>; scripts/aideal versions --study <study>',
     'Baseline branches alone do not contain generated treatments. Run and review development/installation steps first.'),
    ('catalog', '3. Inspect the API inventory and inputs',
     'Review exactly which APIs and definitions are selected, including signatures, source locations and available examples.',
     ['aideal.api_discovery:public_api_details', 'aideal.api_examples:api_test_examples',
      'workflow.improvement_batches:preview_library_improvements', 'workflow.improvement_context:preview_improvements'],
     'Configured source/test globs, public API rules, profile and optional development failures.',
     'Deterministic discovery and bounded preview; no proposal model call at this stage.',
     'API details; bounded batch preview.json files and a library preview manifest.',
     'python -m aideal.cli --config <yaml> api-surface --json; scripts/aideal preview-library --study <study> --output <preview>',
     'The native README catalog groups bare names; definition counts and distinct API-name counts are different denominators.'),
    ('readme', '4. Generate, test and revise README entries',
     'Generate entries, let an audience model write programs, execute them, and optionally diagnose failures to revise selected entries. Fresh checks measure the revised document.',
     ['aideal.readme_generation:find_or_create', 'aideal.doc_check_execution:_comprehension_execute',
      'aideal.doc_repair:run', 'aideal.deepdive:deep_dive_run', 'aideal.prompts:load'],
     'API signatures, source comments, selected examples and distilled original documentation. Diagnosis additionally receives relevant source and failed-use evidence.',
     'Author: aideal/readme_entry and readme_distill. Audience: comprehension_write_exec. Diagnosis/revision: deep_dive, docfix_diagnose, docfix_rewrite. The configured compiler/runner executes programs.',
     'Configured LLM README; .aideal_exec/readme_generation_state.json; development execution records; revised API entries.',
     'python -m aideal.cli --config <yaml> readme --generate --limit 0; python -m aideal.cli --config <yaml> comprehension --execute --max-fix-rounds 0; python -m aideal.cli --config <yaml> fix-docs --help',
     'This uses the vendored engine. The portable three-README evaluator consumes supplied documents; it does not generate them.'),
    ('aliases', '5. Propose callable aliases',
     'Review model proposals for clearer names/calling patterns. A wrapper forwards to the original operation; a proposal is not a proven improvement.',
     ['workflow.improvement_batches:propose_library_improvements', 'workflow.improvement_suggestions:propose_improvements',
      'workflow.treatment_bundles:bundle_proposals'],
     'Saved bounded API/source preview, profile, optional permitted development failures and model configuration.',
     'prompts/improvement_suggestions.md. Development model requests/responses are saved. Library-specific build and behavior checks remain explicit.',
     'suggestions.json; proposal.json; alias source files and interface descriptions; batch collection.json.',
     'scripts/aideal propose-library --preview <manifest> --model-config <yaml> --output <proposals>; scripts/aideal bundle-proposals --proposal <proposal> --output <bundle>',
     'The model can propose no aliases. Structural checks do not prove semantic equivalence. Bundling excludes legacy JSON hints unless --include-legacy-hints is explicitly selected.'),
    ('hints', '6. Develop native embedded fix hints',
     'Use permitted Original development failures to propose guidance. Modify an existing exception message and compare baseline/candidate behavior on four paired controls.',
     ['workflow.source_hint_development:build_development_preview', 'workflow.native_hints:propose_native_hints',
      'workflow.native_hints:prepare_native_hints', 'workflow.native_hints:validate_native_hints',
      'workflow.native_hints:install_native_hints'],
     'Pinned development failure/code/diagnostic; function source; requirement evidence; independent control programs and checker plan.',
     'prompts/native_hint_development.md. Author proposes; deterministic source edits and trusted execution adapters validate.',
     'preview.json; proposal.json; source candidates; validation.json; installed source edits awaiting review and commit.',
     'scripts/aideal preview-native-hints --help; scripts/aideal propose-native-hints --help; scripts/aideal validate-native-hints --help; scripts/aideal install-native-hints --help',
     'The current native path uses schema 3 exception messages. Older JSON and source-comment treatments remain isolated in evaluation_legacy_hints.py for explicit compatibility. Native edits support limited literal-message syntax, not every failure.'),
    ('install', '7. Install the chosen resources',
     'Install complete reviewed resource versions into the appropriate isolated library branches and keep their exact source/artifact identities.',
     ['workflow.treatment_versions:apply_treatments', 'workflow.native_hints:install_native_hints',
      'workflow.source_refactors:install_refactor'],
     'Generated README, alias bundle or validated native-hint receipt, and explicit target worktrees.',
     'No proposal model call. Treatment bundles are committed by their installer. Native-hint installation leaves explicit target edits for review and commit. Adapters must build/import the installed version.',
     'Treatment records and commits; versions output; optional independent refactor branch.',
     'scripts/aideal install-treatments --study <study> --proposal <bundle>; scripts/aideal versions --study <study>',
     'Native hints require an explicit commit/build after installation and before freezing. There is no automatic synchronization among toolkit copies and frozen studies.'),
    ('freeze', '8. Validate the checker and freeze a study',
     'Run correct, wrong-output and no-target controls against each configured backend, then bind documents, code, prompts, fixtures and runtime artifacts.',
     ['workflow.evaluation_freeze:freeze_conditions', 'workflow.evaluation_freeze:validate_conditions',
      'workflow.evaluation_freeze:verify_inputs', 'workflow.evaluation_setup:freeze_evaluation'],
     'Condition YAML, independent micro/puzzle bank, library backend commits/builds, model adapter and oracle artifacts.',
     'No audience model call. Trusted checker adapters run control programs. Private answers stay in checker inputs.',
     'validation/ records and frozen.json with study/controller/backend fingerprints.',
     'scripts/aideal freeze-conditions --config <yaml> --output <new-study>; alternative: freeze-evaluation for three supplied READMEs',
     'Changed code/resources require a new validated freeze. Do not rewrite historical identities or remove review holds to force reuse.'),
    ('audience', '9. Generate an audience program',
     'Select matched public context and generate R0. On permitted repair rounds, supply the failed program and public diagnostic.',
     ['workflow.evaluation_runner:run_study', 'workflow.evaluation_runner:run_unit',
      'workflow.evaluation_conditions:run_conditions', 'workflow.evaluation_readme:run_evaluation',
      'workflow.evaluation_context:public_context', 'workflow.evaluation_program_generation:_request_solution'],
     'Frozen public task, README, alias interface if enabled, common settings, and previous public feedback for repairs.',
     'Inline SYSTEM and audience_prompt/public_context, not automatically the development prompt files. Configured provider command; SDK adapters are optional.',
     '<run>/<condition>/<case>--<trial>/round_XX/provider_XXX/{request.json,process.json,stdout.txt,stderr.txt}; generation.json and exposure receipts.',
     'scripts/aideal run-conditions --study <frozen.json> --output <new-or-matching-run> --max-units 1',
     'This command can spend API credits. Incomplete/refused/empty generations stay unresolved and are not executed as complete programs.'),
    ('execute', '10. Build, run and check the program',
     'The trusted library adapter compiles or imports the candidate, checks output correctness and confirms target API use.',
     ['workflow.execution:invoke', 'workflow.evaluation_freeze:execute_condition',
      'workflow.evaluation_freeze:checked_outcome', 'workflow.evaluation_setup:_checked_execution'],
     'Candidate code plus private checker inputs, fixtures and the pinned library backend. Private checker data is not sent to the audience.',
     'No LLM inside the generic execution function. Language/build details and generated-code isolation belong to the explicit adapter.',
     'round_XX/execution_XXX/{request.json,process.json,stdout.txt,stderr.txt}; adapter outputs and evidence bindings.',
     'Inspect the condition adapter.command and its validation controls before running a real library.',
     'Exit code zero alone is not a pass. Execution, independent oracle and target-use checks must agree.'),
    ('repair', '11. Retry or stop without mixing histories',
     'Repair the program up to the configured limit. Keep transport retries, program repairs and README revision as separate operations.',
     ['workflow.evaluation_readme:previous_result', 'workflow.repair_context:compact_previous',
      'workflow.evaluation_program_generation:mark_generation', 'workflow.evaluation_runner:verify_row', 'workflow.evaluation_runner:replay'],
     'Failed code, public diagnostic and permitted treatment guidance. Schema 3 hints are already in the native diagnostic.',
     'Same audience model for program repair; optional deterministic context compaction. No automatic author/README update inside a frozen evaluation.',
     'Next round evidence or unresolved/failed/passed result.json. Completed calls are reused only after evidence checks.',
     'Repeat run-conditions with the same frozen study/output to resume; --retry-provider explicitly extends transport attempts.',
     'Shared development memory is not automatically injected into every matched-condition trial. Optional memory paths belong to development.'),
    ('results', '12. Read scores and inspect exact evidence',
     'Report microtasks and puzzles separately, first-attempt and within-repair-limit success, paired changes, tokens, provider time and execution time.',
     ['workflow.evaluation_report:report_conditions', 'workflow.evaluation_report:write_condition_report',
      'workflow.evaluation_report:report', 'workflow.ablation:score'],
     'Verified per-unit checkpoints and complete provider/checker evidence, with the frozen denominator.',
     'No model call. Deterministic aggregation of recorded outcomes.',
     '<run>/report.json and REPORT.md; per-unit result.json; exact requests, generated programs, logs and usage in round directories.',
     'Open REPORT.md, then result.json, then the corresponding provider and execution folders.',
     'Unresolved units remain in the denominator. The audit uses synthetic fixtures; it is not a new six-library result.'),
]


def svg(prefix=''):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1440 2110" role="img" aria-labelledby="title desc">',
             '<title id="title">AIDEAL code reading and execution workflow</title>',
             '<desc id="desc">Twelve linked checkpoints. Original development failures feed hint authoring. Reviewed task banks and private checker controls feed freezing. Frozen evaluation repairs programs with fixed resources; development memory is separate.</desc>',
             '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#49627d"/></marker></defs>',
             '<style>text{font-family:Arial,sans-serif;fill:#182c43}.title{font-size:30px;font-weight:700}.sub{font-size:18px;fill:#52657a}.node{font-size:23px;font-weight:700}.body{font-size:19px}.source{font-size:16px;fill:#52657a}.lane{font-size:19px;font-weight:700;letter-spacing:1px}.edge{fill:none;stroke:#49627d;stroke-width:2.6;marker-end:url(#arrow)}.optional{stroke-dasharray:7 5}</style>',
             '<rect width="1440" height="2110" fill="#fff"/>',
             '<text class="title" x="40" y="45">AIDEAL · from configuration to inspectable results</text>',
             '<text class="sub" x="40" y="78">Click a numbered checkpoint for functions, source lines, prompts and commands.</text>',
             '<text class="sub" x="40" y="104">Arrows show dependencies and the frozen repair loop; development commands remain explicit.</text>']

    def text(x, y, lines, cls='body', gap=27):
        for i, line in enumerate(lines):
            parts.append(f'<text class="{cls}" x="{x}" y="{y+i*gap}">{escape(line)}</text>')

    def box(key, x, y, w, h, title, lines, source=(), color='#f0f6fc'):
        parts.append(f'<a xlink:href="{escape(prefix)}#stage-{key}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{color}" stroke="#b8c9d9" stroke-width="1.6"/>')
        text(x+18, y+34, [title], 'node')
        text(x+18, y+66, lines)
        text(x+18, y+h-18-(len(source)-1)*22, source, 'source', 22)
        parts.append('</a>')

    def sidecar(x, y, w, h, title, lines, color):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{color}" stroke="#c5cbd3"/>')
        text(x+18, y+28, [title], 'lane')
        text(x+18, y+54, lines, 'sub', 24)

    def edge(path, label=None, x=0, y=0, optional=False):
        parts.append(f'<path class="edge{" optional" if optional else ""}" d="{path}"/>')
        if label:
            text(x, y, [label], 'sub')

    box('setup', 40, 130, 400, 130, '1  Configuration + runtime',
        ['Source · README · data · settings'], ['workflow/__main__.py'])
    box('versions', 520, 130, 400, 130, '2  Prepare source versions',
        ['Separate worktrees · pinned commits'], ['workflow/worktrees.py'])
    box('catalog', 1000, 130, 400, 130, '3  Review API inventory',
        ['Definitions · signatures · examples'], ['aideal/api_discovery.py'])
    edge('M440 195H514'); edge('M920 195H994')

    parts.append('<rect x="24" y="290" width="1392" height="385" rx="16" fill="#fbf8f2" stroke="#e5d8c6"/>')
    text(44, 321, ['RESOURCE DEVELOPMENT · review each proposed change'], 'lane')
    sidecar(1000, 345, 400, 94, 'Pinned Original development R0',
            ['Failed program + runtime diagnostic', 'Source identity · held-out cases excluded'], '#fff2d8')
    edge('M1040 260V335H960V450H240V459')
    edge('M720 450V459')
    edge('M1200 439V459')
    box('readme', 40, 465, 400, 190, '4  README development',
        ['Generate → audience development test', 'Diagnose failure → revise → recheck'],
        ['aideal/readme_generation.py', 'aideal/doc_repair.py'], '#fff8eb')
    box('aliases', 520, 465, 400, 190, '5  Alias development',
        ['Bounded source → model proposal', 'Forwarding wrappers → explicit checks'],
        ['workflow/improvement_batches.py', 'workflow/improvement_suggestions.py'], '#fff8eb')
    box('hints', 1000, 465, 400, 190, '6  Native fix hints',
        ['Evidence → model → exception message', 'Four paired execution controls'],
        ['workflow/source_hint_development.py', 'workflow/native_hints.py'], '#fff8eb')
    text(44, 369, ['API facts and source previews support authors.',
                   'Permitted development failures can also inform',
                   'README diagnosis and alias proposals.'], 'sub', 25)

    # All three reviewed development outputs join the explicit installation step.
    edge('M240 655V688H700V920H686')
    edge('M720 655V688H700')
    edge('M1200 655V688H700')
    sidecar(40, 715, 640, 100, 'Development memory · optional reuse',
            ['Errors + repair outcomes → deterministic compact notes.',
             'Record / reuse in native development, outside held-out trials.'], '#f2edfa')
    parts.append('<path class="edge optional" d="M100 661V709" marker-start="url(#arrow)"/>')
    sidecar(760, 715, 640, 100, 'Reviewed task bank + trusted checker controls',
            ['Public micro / puzzle contracts → audience context.',
             'Private reference answers and checks → execution adapter only.'], '#eef7f2')
    edge('M1080 815V844')
    box('install', 40, 850, 640, 140, '7  Install, review, commit and build',
        ['Original · README · Alias · Native hints · Combined'],
        ['workflow/treatment_versions.py · native_hints.py'], '#edf6ef')
    box('freeze', 760, 850, 640, 140, '8  Validate controls + freeze identities',
        ['Correct / wrong-output / no-target controls → frozen.json'],
        ['workflow/evaluation_freeze.py'], '#edf6ef')
    edge('M680 950H754')

    text(40, 1039, ['FROZEN EVALUATION · same tasks, fixed resources, separate trial histories'], 'lane')
    edge('M1080 990V1065H240V1099')
    box('audience', 40, 1105, 400, 160, '9  Audience generation',
        ['Public task + permitted resources', 'R0 or revised complete program'],
        ['workflow/evaluation_context.py', 'workflow/evaluation_runner.py'], '#edf5ff')
    box('execute', 520, 1105, 400, 160, '10  Build · run · check',
        ['Execution + oracle + target API use', 'Private checker data stays here'],
        ['workflow/evaluation_freeze.py', 'workflow/execution.py'], '#edf5ff')
    box('results', 1000, 1105, 400, 160, '12  Results + evidence',
        ['Micro / puzzle · R0 / final', 'Tokens · model time · execution time'],
        ['workflow/evaluation_report.py'], '#edf6ef')
    edge('M440 1185H514')
    edge('M920 1185H994'); text(929, 1156, ['Stop'], 'sub')
    box('repair', 520, 1330, 560, 145, '11  Feedback + bounded program repair',
        ['Verified failure → current code + public diagnostic', 'Native hints arrive in the library exception message'],
        ['workflow/evaluation_runner.py · repair_context.py'], '#edf5ff')
    edge('M720 1265V1324', 'Failure + repair remains', 735, 1304)
    edge('M520 1400H240V1271', 'Same audience', 265, 1375)
    edge('M100 1265V1510H1200V1271', optional=True)
    text(40, 1544, ['Incomplete/refused generation: save without execution. Exhausted transport retries or unverified checks stop the invocation.'], 'sub')
    text(40, 1576, ['All attempts retain exact model inputs, programs, execution outputs and usage. No paid calls are part of this code audit.'], 'sub')
    parts.append('<rect x="24" y="1606" width="1392" height="480" rx="16" fill="#f6f8fc" stroke="#c9d6e5"/>')
    text(44, 1641, ['PORTABLE STUDY RUNNER · two policies share one program-repair loop'], 'lane')
    box('audience', 40, 1665, 640, 110, 'Treatment comparison adapter',
        ['README · aliases · native hints · combined'],
        ['workflow/evaluation_conditions.py'], '#edf5ff')
    box('audience', 760, 1665, 640, 110, 'Three-README comparison adapter',
        ['Original · Generated · Repaired README'],
        ['workflow/evaluation_readme.py'], '#edf5ff')
    edge('M360 1775V1800H560V1814')
    edge('M1080 1775V1800H880V1814')
    box('audience', 400, 1820, 640, 145, 'Shared schedule, repair and evidence checks',
        ['run_study → run_unit → verify_row / replay',
         'Request → generation check → execute → repair / stop'],
        ['workflow/evaluation_runner.py'], '#edf6ef')
    edge('M720 1965V1989')
    box('results', 400, 1995, 640, 75, 'Saved evidence → one reporting module', [],
        ['workflow/evaluation_report.py · both report contracts'], '#edf6ef')
    parts.append('</svg>')
    return '\n'.join(parts)


def build(root, audit, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    data = build_map(root)
    navigation_date = audit.get('navigation_date', audit['date'])
    by_id = {f['id']: f for f in data['functions']}
    stem = audit.get('stem', 'CODE_AUDIT_' + audit['date'])
    if Path(stem).name != stem or not stem or stem in ('.', '..'):
        raise ValueError('Audit stem must be a plain artifact basename')
    svg_path, html_path = output / (stem + '.svg'), output / (stem + '.html')
    svg_path.write_text(svg(html_path.name), encoding='utf-8')
    links = []
    for row in STAGES:
        key,title,description,functions,inputs,model,outputs,command,limit = row
        command = command.replace('python -m aideal.cli', '"$AIDEAL_PY" -m aideal.cli').replace('scripts/aideal', '"$AIDEAL_PY" scripts/aideal').replace('scripts/check_project.py', '"$AIDEAL_PY" scripts/check_project.py')
        function_links = []
        for name in functions:
            item = by_id.get(data['aliases'].get(name,name))
            if item:
                function_links.append(f'<li><a href="CODE_MAP.html#{quote(item["id"],safe="")}">{escape(name)}</a><small>{escape(item["path"])}:{item["line"]}</small></li>')
            else:
                function_links.append(f'<li>{escape(name)} <small>Check module entry; dynamic/renamed symbol.</small></li>')
        links.append(f'''<section id="stage-{key}" class="stage"><h2>{escape(title)}</h2>
<p>{escape(description)}</p><div class="detail-grid"><div><details><summary>Functions and current source lines</summary><ol>{''.join(function_links)}</ol></details></div>
<div><h3>Inputs</h3><p>{escape(inputs)}</p><h3>Model, prompt and execution</h3><p>{escape(model)}</p></div>
<div><h3>Inspect the outputs</h3><p>{escape(outputs)}</p><h3>Command route</h3><code>{escape(command)}</code></div></div>
<p class="boundary">{escape(limit)}</p><a class="back" href="#flow">Back to overview ↑</a></section>''')
    findings = ''.join(f'<tr><td>{escape(f["id"])} · {escape(f["severity"])}</td><td><strong>{escape(f["title"])}</strong><br>{escape(f["detail"])}</td><td>{escape(f["status"])}</td></tr>' for f in audit['findings'])
    funcs = ''.join(f'<li data-name="{escape((f["id"]+" "+f["path"]).lower(),quote=True)}"><a href="CODE_MAP.html#{quote(f["id"],safe="")}">{escape(f["id"])}</a><small>{escape(f["path"])}:{f["line"]}</small></li>' for f in data['functions'])
    def review_link(name, label):
        item = by_id.get(data['aliases'].get(name, name))
        if not item:
            return escape(label)
        return (f'<a href="CODE_MAP.html#{quote(item["id"], safe="")}">{escape(label)}</a>'
                f'<small>{escape(item["path"])}:{item["line"]}</small>')
    def source_start(relative, name):
        path = root / relative
        node = next(n for n in ast.walk(ast.parse(path.read_text()))
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
        label = f'{relative}:{node.lineno} — {name}'
        href = 'vscode://file' + quote(str(path), safe='/') + ':' + str(node.lineno)
        return f'<a href="{href}">{escape(label)}</a>'

    review_paths = f'''<section id="first-task" class="card"><h2>Start with the RDPro run you just inspected</h2>
<p>Use this reading order instead of reading the Explorer list alphabetically. Each pass below has a different entry point.</p>
<div class="versions"><div><h3>A. Follow one RDPro microbenchmark</h3>
<p>{source_start('scripts/trace_original_micro.py', 'main')}</p>
<p>{review_link('aideal.doc_check_comprehension:comprehension_check', 'Select the API and original documentation')}</p>
<p>{review_link('aideal.doc_check_execution:_comprehension_execute', 'Follow R0, feedback, R1 and optional R2')}</p>
<p><a href="../.local/rdpro-trace-review/INDEX.html">Recorded Gemini prompts, code and errors</a><br><a href="RDPRO_SINGLE_API_TRACE.md">VS Code pause/debug instructions</a></p>
</div><div><h3>B. Read the five-condition study runner</h3>
<p>{review_link('workflow.__main__:main', 'Command dispatcher')}</p>
<p>{review_link('workflow.evaluation_conditions:run_conditions', 'Open the frozen study and select its policy')}</p>
<p>{review_link('workflow.evaluation_runner:run_study', 'Schedule condition × case × trial')}{review_link('workflow.evaluation_runner:run_unit', 'Run and repair one task')}</p>
<p>This portable path uses independent checker outcomes. The RDPro microbenchmark trace above uses the native engine and audience-written assertions.</p>
</div><div><h3>C. Review resource development separately</h3>
<p><a href="#stage-readme">4. README generation and deep dive</a><br><a href="#stage-aliases">5. Alias proposals</a><br><a href="#stage-hints">6. Native exception hints</a><br><a href="#stage-install">7. Install and rebuild</a></p>
<p>None of these development stages ran inside the recent Original Gemini trace. Alias validation and RDPro native-hint controls/rebuild still require explicit preparation.</p></div></div>
<p class="boundary">In the screenshot, condition_evaluation.py, condition_inputs.py and condition_setup.py are compatibility imports. Read evaluation_conditions.py, evaluation_inputs.py and evaluation_freeze.py instead. evaluation_program_generation.py writes a task program; readme_generation.py writes README entries. __pycache__ contains generated bytecode, not source to review.</p>
<p>For every function record its caller, inputs, return value, written files, model/process calls, and stop/error conditions. The <a href="EVALUATION_CODE_GUIDE.md">numbered workbook</a> gives source lines and review questions. The <a href="CODE_MAP.html">function map</a> expands remaining helpers.</p></section>'''
    tests = audit.get('verification',{})
    verification_path = audit.get('verification_path', 'code_audit_2026-10-28/verification/checks.json')
    audit_path = audit.get('audit_path', 'code_audit_2026-10-28/audit.json')
    nav = ''.join(f'<a href="#stage-{s[0]}">{escape(s[1])}</a>' for s in STAGES)
    contents = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AIDEAL code audit and reading guide</title><style>
:root{{color-scheme:light;--ink:#1b2e44;--muted:#53687c;--border:#d7e0e8;--blue:#165da1}}*{{box-sizing:border-box}}body{{margin:0;background:#f3f6f9;color:var(--ink);font:16px/1.55 system-ui,sans-serif}}a{{color:var(--blue)}}header,main{{max-width:1460px;margin:auto;padding:28px}}header{{padding-bottom:12px}}h1{{font-size:36px;letter-spacing:-.6px;margin:4px 0 12px}}h2{{font-size:24px;margin:0 0 12px}}h3{{font-size:16px;margin:14px 0 4px}}p{{margin:6px 0 14px}}.eyebrow{{font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted)}}.card,.stage{{background:white;border:1px solid var(--border);border-radius:14px;padding:24px;margin-bottom:22px}}.stage{{scroll-margin-top:14px}}.stats,.detail-grid,.versions{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}}.stat{{background:#eaf2f8;border-radius:10px;padding:16px}}.stat b{{display:block;font-size:25px}}nav{{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}}nav a{{font-size:13px;text-decoration:none;background:#fff;border:1px solid var(--border);padding:7px 10px;border-radius:8px}}.diagram{{overflow:auto;background:white;border:1px solid var(--border);border-radius:14px;margin-bottom:22px}}svg{{display:block;width:100%;min-width:800px}}.boundary{{background:#fff6e5;border-left:4px solid #bd8d33;padding:11px 15px;font-size:14px}}.back{{font-size:13px}}small{{display:block;color:var(--muted);font-size:12px;overflow-wrap:anywhere}}li{{margin-bottom:10px}}code{{display:block;font:12px/1.7 ui-monospace,monospace;white-space:normal;overflow-wrap:anywhere;background:#f1f5f8;padding:12px;border-radius:8px}}table{{width:100%;border-collapse:collapse;font-size:14px}}td,th{{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--border)}}th{{background:#eef3f7}}.function-list{{columns:2;padding-left:22px}}.function-list li{{break-inside:avoid;font-size:13px}}input{{width:100%;padding:12px;border:1px solid var(--border);border-radius:8px;font:inherit;margin:12px 0}}[hidden]{{display:none!important}}@media(max-width:800px){{header,main{{padding:14px}}h1{{font-size:28px}}.stats,.detail-grid,.versions{{grid-template-columns:1fr}}.function-list{{columns:1}}}}@media print{{body{{background:white}}nav,.back,input{{display:none}}.card,.stage{{break-inside:avoid}}svg{{min-width:0}}.function-list{{columns:2}}}}
</style><header><div class="eyebrow">Navigation {escape(navigation_date)} · test receipt {escape(audit['date'])}</div><h1>AIDEAL code review, from start to finish</h1>
<p>{escape(audit['verdict'])}</p><small>Primary checkout: {escape(str(root))}</small><nav><a href="#first-task">Step-by-step starting point</a><a href="#start">Portable study runner</a><a href="#flow">Workflow diagram</a><a href="#audit">Findings &amp; checks</a><a href="#locations">Which version?</a><a href="#function-index">All functions</a><a href="{stem}.svg">Editable SVG</a><a href="{stem}.md">Full report and commands</a></nav></header>
<main>{review_paths}<div class="stats"><div class="stat"><b>{escape(str(tests.get('python_tests','Pending')))}</b>Python tests in the linked historical receipt</div><div class="stat"><b>{escape(str(tests.get('node_tests','Pending')))}</b>Navigator tests</div><div class="stat"><b>{len(data['functions'])}</b>definitions indexed across {len(data['modules'])} modules</div></div>
<p class="boundary">Passing tests do not establish bug-free operation for every library. This review does not launch paid providers or modify recorded experiments. Dynamic call edges and external adapters still need runtime validation.</p>
<section class="card"><h2>Use the tested environment</h2><p>Set these once in your terminal before using the command routes below. Angle-bracket values are placeholders for a reviewed configuration and fresh output directory. Development model calls and run commands can spend credits; help and the offline checker do not.</p><code>cd {escape(str(root))}<br>export AIDEAL_PY=/Users/clockorangezoe/miniconda3/envs/geo_llm_spark/bin/python<br>export PYTHONPATH="$PWD/vendor/aideal_engine/src"</code></section>
<section id="start" class="card"><h2>Portable study runner: three main files</h2><div class="versions">
<div><h3>1. Shared portable runner</h3><p>{review_link('workflow.evaluation_runner:run_study', 'run_study — schedule and resume')}{review_link('workflow.evaluation_runner:run_unit', 'run_unit — generation, checking and repair')}{review_link('workflow.evaluation_runner:verify_row', 'verify_row — validate saved evidence')}</p></div>
<div><h3>2. Treatment policy</h3><p>{review_link('workflow.evaluation_conditions:_ConditionPolicy', 'evaluation_conditions.py')}</p><p>Supplies treatment context, native diagnostic behavior, backend checks and exposure receipts.</p></div>
<div><h3>3. README policy</h3><p>{review_link('workflow.evaluation_readme:_ReadmePolicy', 'evaluation_readme.py')}</p><p>Supplies three-document selection and its checker contract. Both policies use the same execution and replay loop.</p></div></div>
<details><summary>Supporting files, grouped by responsibility</summary><p>Context: evaluation_context.py and repair_context.py. Freeze and inputs: evaluation_freeze.py, evaluation_inputs.py and evaluation_setup.py. Task programs: evaluation_program_generation.py. Execution: execution.py. Reports: evaluation_report.py. Legacy hint delivery: evaluation_legacy_hints.py, reached only by explicit older protocols.</p></details>
<p><a href="TREATMENT_WORKFLOW.md">README, alias and native-hint development commands</a> · <a href="EVALUATION_CODE_GUIDE.md">Concise reading guide and output locations</a></p></section>
<div id="flow" class="diagram">{svg()}</div><nav>{nav}</nav>
<section class="card"><h2>Actual calls in a frozen comparison</h2>
<p>Start at <a href="#start">evaluation_runner.run_study</a>. Both public entry points select a small policy and delegate to it. The shared runner verifies saved evidence, schedules matched units and invokes the same run_unit loop.</p>
<code>run_conditions / run_evaluation → run_study → run_unit<br>→ policy.request → _request_solution → invoke(provider adapter)<br>→ mark_generation → policy.execute → invoke(checker adapter) → policy.outcome<br>→ previous_result → policy.request for the next permitted repair<br>→ verify_row → replay → evaluation_report.py</code>
<p>The generation check prevents incomplete, refused or explicitly failed responses from executing; these outcomes end the unit and allow the schedule to continue. A pass or repair-limit failure ends the unit. Exhausted provider transport attempts or unverifiable checker outcomes stop the invocation with an unresolved record. Native guidance reaches the next request through the library's diagnostic; schema 3 does not retrieve a separate hint file.</p></section>
<section class="card"><h2>Two repair paths, with different memory rules</h2><div class="versions">
<div><h3>Frozen five-condition evaluation</h3><p><a href="#stage-audience">evaluation_runner.run_unit</a> uses the same configured audience model for R0 and repairs. It supplies the current failed program and public diagnostic. It does not automatically inject shared development memory or revise library resources.</p></div>
<div><h3>Native README development checks</h3><p><a href="#stage-readme">doc_check_execution._comprehension_execute</a> uses the audience role at R0 and the fixer role on retries. Retries can consult recorded failures for the same API. <a href="#stage-readme">deep_dive_run</a> diagnoses source and history; <a href="#stage-readme">doc_repair.run</a> rewrites and rechecks entries.</p></div>
<div><h3>Optional puzzle development memory</h3><p>The native puzzle wrapper can pass error summaries and compact notes through PUZZLE_HINTS to its configured runner and consolidate notes after a failed round. The runner must consume that input. This is separate from the frozen comparison.</p></div></div>
<p class="boundary">The diagram does not imply one automatic end-to-end command. The developer supplies reviewed task banks, trusted checker adapters and treatment validation; then freezes the resources before running the matched comparison.</p></section>
<section id="audit" class="card"><h2>Reproduced issues and verification</h2><table><thead><tr><th>ID</th><th>Finding</th><th>State</th></tr></thead><tbody>{findings}</tbody></table><p>{escape(tests.get('summary',''))}</p>
<p><a href="{escape(verification_path, quote=True)}">Machine-readable verification and source hashes</a> · <a href="{escape(audit_path, quote=True)}">Scope and findings</a></p></section>
<section id="locations" class="card"><h2>Three code locations, three distinct roles</h2><div class="versions"><div><h3>Named development checkout</h3><p>The main diagram maps this directory and its actual uncommitted code. Existing edits are preserved.</p><small>{escape(str(root))}</small></div><div><h3>Newer native-hint controller</h3><p>A separate September 30 clone adds complete failure inventory and audited README sessions. Its functions are not silently substituted into this map.</p><small>.local/native_fix_hints_controller · feature/2026-09-30-native-fix-hints</small></div><div><h3>Older operational runtime</h3><p>The workspace Runtime_engine link targets GRAIL_robust_core_v4. Its A1/A2/B2 supervisors and passive observers are a separate execution path.</p><small>AIDEAL_WORKSPACE/01_Runtime/Runtime_engine</small></div></div>
<p class="boundary">This guide maps the current named checkout. Use the updated start page to navigate, then inspect each run's frozen identity and saved evidence for its actual status. Separate controller copies and archived results do not establish that the current implementation completed a new comparison.</p></section>
{''.join(links)}
<section id="function-index" class="card"><details><summary>Complete static function reference · helpers included</summary><p>Search the indexed name or module, then open its source, callers and callees in the code map. This includes helper functions and classes. An unresolved dynamic call is not evidence that a function is unused.</p><input id="search" aria-label="Search functions" placeholder="Try native_hints, readme_generation, repair, score…"><p id="count">{len(data['functions'])} definitions</p><ul class="function-list">{funcs}</ul></details></section></main>
<script>const search=document.getElementById('search');const rows=[...document.querySelectorAll('[data-name]')];search.addEventListener('input',()=>{{const term=search.value.toLowerCase().trim();let count=0;for(const row of rows){{row.hidden=!row.dataset.name.includes(term);if(!row.hidden)count++}}document.getElementById('count').textContent=count+' definitions'}});</script></html>'''
    html_path.write_text(contents, encoding='utf-8')
    return {'html':str(html_path),'svg':str(svg_path),'definitions':len(data['functions']),'modules':len(data['modules'])}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    print(json.dumps(build(args.root,json.loads(args.audit.read_text()),args.output or args.root/'docs'),indent=2))


if __name__=='__main__':
    main()
