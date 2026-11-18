"""Earlier treatment command names, retained for existing scripts and artifacts.

These commands are deliberately absent from the main help listing. Omitting
the argparse ``help`` argument keeps a command callable without advertising it;
its own ``--help`` explains the supported migration. No saved format is changed.
"""
from pathlib import Path


COMPATIBILITY_COMMANDS = (
    'preview-source-hints', 'propose-source-hints', 'validate-source-hints',
    'install-source-hints', 'preview-improvements', 'propose-improvements',
    'show-fix-hints',
)


def add_compatibility_commands(sub):
    # Register older command names and arguments with descriptions on their own help
    # pages.
    for command, description, options in (
        ('preview-source-hints', 'Collect Original R0 failures. Use preview-native-hints for new native-message studies.',
         ('manifest', 'output')),
        ('propose-source-hints', 'Propose source-comment guidance for schema 2 studies. Use propose-native-hints for new native-message studies.',
         ('preview', 'model-config', 'output')),
        ('validate-source-hints', 'Validate source-comment guidance. New native-message proposals require validate-native-hints instead.',
         ('proposal', 'validation-plan', 'output')),
        ('install-source-hints', 'Install validated source comments for schema 2 studies. New native-message validations use install-native-hints.',
         ('validation', 'targets', 'output')),
    ):
        p = sub.add_parser(command, description='Compatibility command. ' + description)
        for option in options:
            p.add_argument('--' + option, required=True)
        p.set_defaults(development_handler=True)
    p = sub.add_parser('preview-improvements', description=(
        'Compatibility command for a single preview. Use preview-library for new proposals; '
        'select a small API scope with --api to produce one batch.'))
    p.add_argument('--study', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--alias-path', help='New source-module path relative to the library checkout')
    p.add_argument('--api', action='append', dest='apis', help='API name, qualified name or exact file:line:name ID; repeatable')
    p.add_argument('--development-errors', help='Explicit development error JSONL; never held-out evaluation failures')
    p.add_argument('--max-apis', type=int, default=12)
    p.add_argument('--max-context-characters', type=int, default=60000)
    p.set_defaults(development_handler=True)
    p = sub.add_parser('propose-improvements', description=(
        'Compatibility command for saved single-preview artifacts. Use propose-library '
        'for new library preview manifests, then bundle-proposals.'))
    p.add_argument('--preview', required=True)
    p.add_argument('--model-config', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--readme', help='Already generated README to include in the complete treatment bundle')
    p.set_defaults(development_handler=True)
    p = sub.add_parser('show-fix-hints', description=(
        'Compatibility diagnostic for legacy JSON hints. Native exception guidance reaches '
        'repair through execution feedback and is not retrieved with this command.'))
    p.add_argument('--hints', required=True)
    p.add_argument('--function', required=True)
    p.add_argument('--error-file', required=True)
    p.set_defaults(development_handler=True)


def run_compatibility_command(args):
    # Route earlier command names to their existing handlers. The shared preview
    # command is handled by the main development dispatcher.
    if args.command == 'propose-source-hints':
        from .source_hint_development import propose_source_hints
        return propose_source_hints(args.preview, args.model_config, args.output)
    if args.command == 'validate-source-hints':
        from .source_hint_development import validate_source_hint_development
        return validate_source_hint_development(args.proposal, args.validation_plan, args.output)
    if args.command == 'install-source-hints':
        from .source_hint_installation import install_source_hints
        return install_source_hints(args.validation, args.targets, args.output)
    if args.command == 'preview-improvements':
        from .improvement_context import preview_improvements
        return preview_improvements(args.study, args.output, alias_path=args.alias_path,
            apis=args.apis, development_errors=args.development_errors, max_apis=args.max_apis,
            max_context_characters=args.max_context_characters)
    if args.command == 'propose-improvements':
        from .improvement_suggestions import propose_improvements
        return propose_improvements(args.preview, args.model_config, args.output, readme=args.readme)
    if args.command == 'show-fix-hints':
        from .ablation import load
        from .improvement_suggestions import matching_fix_hints
        return {'status': 'unverified', 'hints': matching_fix_hints(
            load(args.hints), args.function, Path(args.error_file).read_text())}
    raise ValueError('Unknown compatibility command: ' + args.command)
