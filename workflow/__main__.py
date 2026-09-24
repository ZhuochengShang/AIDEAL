"""Attach libraries, version treatments, and evaluate matched study conditions."""
import argparse
import json
from pathlib import Path

from .ablation import ARMS, load
from .reporting import verify

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    from .development_cli import add_development_commands
    add_development_commands(sub)
    p = sub.add_parser('attach', help='Create an isolated clone and five real Git branches')
    p.add_argument('--repo', required=True)
    p.add_argument('--config', required=True, help='AIDEAL YAML configuration')
    p.add_argument('--output', required=True)
    p = sub.add_parser('prepare-study', help='Prepare YAML-bound condition records without cloning')
    p.add_argument('--config', required=True)
    p.add_argument('--output', required=True)
    p = sub.add_parser('status', aliases=['study-status'], help='Inspect a supplied study or show toolkit scope')
    p.add_argument('--study')
    sub.add_parser('serve', help='Expose the portable controller as an MCP tool server')
    sub.add_parser('verify', help='Check toolkit artifact integrity, not evaluation scores')
    sub.add_parser('walkthrough', help='Show the repository-independent operating sequence')
    p = sub.add_parser('run-arm', help='Report the remaining evaluation integration requirements')
    p.add_argument('--arm', choices=list(ARMS))
    p = sub.add_parser('freeze-conditions', help='Validate each backend and freeze a five-arm, six-arm or refactor comparison')
    p.add_argument('--config', required=True)
    p.add_argument('--output', required=True)
    p = sub.add_parser('run-conditions', help='Execute/resume a frozen treatment comparison')
    p.add_argument('--study', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--condition', choices=[*ARMS, 'refactor_only'])
    p.add_argument('--max-units', type=int)
    p.add_argument('--retry-provider', action='store_true')
    p = sub.add_parser('freeze-evaluation', help='Validate real oracle controls and freeze three README conditions')
    p.add_argument('--config', required=True)
    p.add_argument('--output', required=True)
    p = sub.add_parser('run-evaluation', help='Execute/resume a frozen three-README experiment')
    p.add_argument('--study', required=True, help='Path to frozen.json')
    p.add_argument('--output', required=True, help='Separate run directory; reuse it to resume')
    p.add_argument('--condition', help='Exact condition label from the frozen README design')
    p.add_argument('--max-units', type=int, help='Bound work this invocation without changing the denominator')
    p.add_argument('--retry-provider', action='store_true', help='Explicitly allow another bounded batch of transport attempts; preserve all prior calls')
    args = parser.parse_args()

    if getattr(args, 'development_handler', False):
        from .development_cli import run_development_command
        print(json.dumps(run_development_command(args), indent=2, ensure_ascii=False))
        return

    if args.command == 'serve':
        from .mcp_server import main as serve
        serve()
        return
    if args.command == 'freeze-conditions':
        from .condition_setup import freeze_conditions
        result = freeze_conditions(args.config, args.output)
    elif args.command == 'run-conditions':
        from .condition_evaluation import run_conditions
        result = run_conditions(args.study, args.output, args.condition, args.max_units, args.retry_provider)
    elif args.command == 'freeze-evaluation':
        from .evaluation import freeze_evaluation
        result = freeze_evaluation(args.config, args.output)
    elif args.command == 'run-evaluation':
        from .evaluation import run_evaluation
        result = run_evaluation(args.study, args.output, args.condition, args.max_units, args.retry_provider)
    elif args.command == 'attach':
        from .worktrees import attach
        result = attach(args.repo, args.config, args.output)
    elif args.command == 'prepare-study':
        from .preparation import prepare_study
        result = prepare_study(args.config, args.output)
    elif args.command in ('status', 'study-status'):
        if args.study:
            from .preparation import prepared_study_status
            result = prepared_study_status(args.study)
        else:
            result = {
                'tool': 'AIDEAL', 'default_repository': None, 'conditions': list(ARMS),
                'entrypoint': 'attach --repo PATH --config YAML --output PATH',
                'evaluation_tasks': ['microtests', 'puzzles'],
                'readme_evaluation': 'freeze-evaluation then run-evaluation; requires configured oracle/model adapters',
                'treatment_development': 'preview-library, propose-library, bundle-proposals, install-treatments',
                'source_refactors': 'scan-duplicates, install-refactor, compare-duplicates; independent validation required',
                'condition_evaluation': 'freeze-conditions and run-conditions; explicit adapters, bank and source versions',
                'version_navigation': 'versions --study PATH',
                'automatic_library_validation': 'Library adapters, build artifacts and regression checks remain explicit',
            }
    elif args.command == 'verify':
        result = verify(ROOT)
    elif args.command == 'walkthrough':
        result = load(ROOT / 'docs/stages.json')
    else:
        result = {
            'launched': False, 'requested_arm': args.arm,
            'missing': ['Use an explicit frozen condition study; no study selected by legacy branch flag'],
            'next': 'freeze-conditions --config YAML --output PATH, then run-conditions --study frozen.json --output PATH',
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.command == 'run-arm' or (args.command == 'verify' and not result['verified']):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
