"""Attach libraries, version treatments, and evaluate matched study conditions."""
import argparse
import json
from pathlib import Path

from .ablation import ARMS
from .evaluation_report import verify
from .evaluation_setup import CONDITIONS

ROOT = Path(__file__).resolve().parents[1]


def main():
    # Entry point for scripts/aideal: read the command and its arguments.
    # Dispatch to preparation, development, evaluation or inspection, then
    # print that operation's result. Only the selected command is run.
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog='Earlier treatment commands remain callable by name. See docs/TREATMENT_WORKFLOW.md for migration.')
    sub = parser.add_subparsers(dest='command', required=True, metavar='COMMAND')
    from .development_cli import add_development_commands
    add_development_commands(sub)
    p = sub.add_parser('attach', help='Create an isolated clone and five real Git branches')
    p.add_argument('--repo', required=True)
    p.add_argument('--config', required=True, help='AIDEAL YAML configuration')
    p.add_argument('--output', required=True)
    p = sub.add_parser('prepare-study', help='Prepare YAML-bound condition records without cloning')
    p.add_argument('--config', required=True)
    p.add_argument('--output', required=True)
    p = sub.add_parser('status', help='Inspect a supplied study or show toolkit scope')
    p.add_argument('--study')
    sub.add_parser('serve', help='Expose the portable controller as an MCP tool server')
    sub.add_parser('verify', help='Check toolkit artifact integrity, not evaluation scores')
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
    p.add_argument('--condition', choices=CONDITIONS)
    p.add_argument('--max-units', type=int, help='Bound work this invocation without changing the denominator')
    p.add_argument('--retry-provider', action='store_true', help='Explicitly allow another bounded batch of transport attempts; preserve all prior calls')
    args = parser.parse_args()

    # Development subcommands register a handler with the parser.
    # The study commands below dispatch by their command name.
    if getattr(args, 'development_handler', False):
        from .development_cli import run_development_command
        print(json.dumps(run_development_command(args), indent=2, ensure_ascii=False))
        return

    if args.command == 'serve':
        from .mcp_server import main as serve
        serve()
        return
    if args.command == 'freeze-conditions':
        from .evaluation_freeze import freeze_conditions
        result = freeze_conditions(args.config, args.output)
    elif args.command == 'run-conditions':
        from .evaluation_conditions import run_conditions
        result = run_conditions(args.study, args.output, args.condition, args.max_units, args.retry_provider)
    elif args.command == 'freeze-evaluation':
        from .evaluation_readme import freeze_evaluation
        result = freeze_evaluation(args.config, args.output)
    elif args.command == 'run-evaluation':
        from .evaluation_readme import run_evaluation
        result = run_evaluation(args.study, args.output, args.condition, args.max_units, args.retry_provider)
    elif args.command == 'attach':
        from .worktrees import attach
        result = attach(args.repo, args.config, args.output)
    elif args.command == 'prepare-study':
        from .preparation import prepare_study
        result = prepare_study(args.config, args.output)
    elif args.command == 'status':
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
                'native_hint_development': 'preview-native-hints, propose-native-hints, validate-native-hints, install-native-hints',
                'compatibility_commands': 'Earlier treatment commands remain callable; see docs/TREATMENT_WORKFLOW.md',
                'source_refactors': 'scan-duplicates, install-refactor, compare-duplicates; independent validation required',
                'condition_evaluation': 'freeze-conditions and run-conditions; explicit adapters, bank and source versions',
                'version_navigation': 'versions --study PATH',
                'automatic_library_validation': 'Library adapters, build artifacts and regression checks remain explicit',
            }
    elif args.command == 'verify':
        result = verify(ROOT)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.command == 'verify' and not result['verified']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
