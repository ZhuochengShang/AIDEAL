"""Current development routes: batched aliases and native exception guidance."""
import json
from pathlib import Path

from .compatibility_cli import (COMPATIBILITY_COMMANDS, add_compatibility_commands,
                                run_compatibility_command)


def add_development_commands(sub):
    # Define the arguments for each current development command and mark it for the
    # development dispatcher.
    for command, help_text, options in (
        ('preview-native-hints', 'Collect pinned Original R0 development failures for native exception guidance',
         ('manifest', 'output')),
        ('propose-native-hints', 'Propose native runtime guidance from an Original R0 preview',
         ('preview', 'model-config', 'output')),
        ('validate-native-hints', 'Execute four paired controls against baseline and native-message sources',
         ('proposal', 'validation-plan', 'output')),
        ('install-native-hints', 'Apply validated native messages to an explicit separate clean checkout',
         ('validation', 'target')),
        ('prepare-native-hints', 'Prepare existing exception-message edits; no model call or source installation',
         ('source-root', 'spec', 'output')),
    ):
        p = sub.add_parser(command, help=help_text)
        for option in options:
            p.add_argument('--' + option, required=True)
        p.set_defaults(development_handler=True)
    p = sub.add_parser('preview-library', help='Save bounded batches covering the configured public API inventory')
    p.add_argument('--study', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--alias-path-template', help='New source path containing {batch}, e.g. src/aideal_aliases_{batch}.py')
    p.add_argument('--api', action='append', dest='apis')
    p.add_argument('--development-errors')
    p.add_argument('--batch-size', type=int, default=12)
    p.add_argument('--max-context-characters', type=int, default=60000)
    p.add_argument('--max-catalog-characters', type=int, default=6000)
    p.add_argument('--max-error-characters', type=int, default=12000)
    p.add_argument('--max-batches', type=int, default=1000)
    p.set_defaults(development_handler=True)
    p = sub.add_parser('propose-library', help='Generate/resume independent bounded model batches; preserve exact requests')
    p.add_argument('--preview', required=True, help='Library preview manifest')
    p.add_argument('--model-config', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--max-batches', type=int)
    p.set_defaults(development_handler=True)
    p = sub.add_parser('bundle-proposals', help='Combine all selected batches into a complete multi-file treatment version')
    p.add_argument('--proposal', required=True, action='append', dest='proposals')
    p.add_argument('--include-legacy-hints', action='store_true',
                   help='Explicitly include JSON hints for schema 1 compatibility; native studies omit them')
    p.add_argument('--readme')
    p.add_argument('--output', required=True)
    p.set_defaults(development_handler=True)
    p = sub.add_parser('install-refactor', help='Version explicit source replacements in a separate baseline-derived worktree')
    p.add_argument('--study', required=True)
    p.add_argument('--proposal', required=True)
    p.set_defaults(development_handler=True)
    p = sub.add_parser('versions', help='Show source branches, treatment versions and navigation paths for one study')
    p.add_argument('--study', required=True)
    p.set_defaults(development_handler=True)
    p = sub.add_parser('install-treatments', help='Commit a complete proposal bundle into the isolated treatment branches')
    p.add_argument('--study', required=True)
    p.add_argument('--proposal', required=True)
    p.set_defaults(development_handler=True)
    p = sub.add_parser('scan-duplicates', help='Suggest attached-library refactors without executing or modifying source')
    p.add_argument('--repo', required=True)
    p.add_argument('--source-glob', action='append', dest='source_globs')
    p.add_argument('--output', required=True)
    p.set_defaults(development_handler=True)
    p = sub.add_parser('compare-duplicates', help='Compare compatible before/after duplicate-candidate reports')
    p.add_argument('--before', required=True)
    p.add_argument('--after', required=True)
    p.add_argument('--output', required=True)
    p.set_defaults(development_handler=True)
    # Earlier commands retain their original arguments and artifact semantics.
    add_compatibility_commands(sub)


def run_development_command(args):
    # Pass parsed arguments to the matching workflow and return its report. Duplicate
    # scans and comparisons save their report here.
    from .ablation import load
    # The old and current preview names share one evidence intake.
    if args.command in ('preview-native-hints', 'preview-source-hints'):
        from .source_hint_development import build_development_preview
        return build_development_preview(args.manifest, args.output)
    if args.command in COMPATIBILITY_COMMANDS:
        return run_compatibility_command(args)
    if args.command in ('prepare-native-hints', 'propose-native-hints', 'validate-native-hints', 'install-native-hints'):
        from .native_hints import (prepare_native_hints, propose_native_hints,
                                   validate_native_hints, install_native_hints)
        if args.command == 'prepare-native-hints':
            return prepare_native_hints(args.source_root, args.spec, args.output)
        if args.command == 'propose-native-hints':
            return propose_native_hints(args.preview, args.model_config, args.output)
        if args.command == 'validate-native-hints':
            return validate_native_hints(args.proposal, args.validation_plan, args.output)
        return install_native_hints(args.validation, args.target)
    if args.command == 'preview-library':
        from .improvement_batches import preview_library_improvements
        return preview_library_improvements(args.study, args.output,
            alias_path_template=args.alias_path_template, apis=args.apis,
            development_errors=args.development_errors, batch_size=args.batch_size,
            max_context_characters=args.max_context_characters, max_batches=args.max_batches,
            max_catalog_characters=args.max_catalog_characters, max_error_characters=args.max_error_characters)
    if args.command == 'propose-library':
        from .improvement_batches import propose_library_improvements
        return propose_library_improvements(args.preview, args.model_config, args.output,
                                            max_batches=args.max_batches)
    if args.command == 'bundle-proposals':
        from .treatment_bundles import bundle_proposals
        return bundle_proposals(args.proposals, args.output, readme=args.readme,
                                include_legacy_hints=args.include_legacy_hints)
    if args.command in ('install-refactor', 'versions'):
        from .source_refactors import install_refactor, study_versions
        return (install_refactor(args.study, args.proposal) if args.command == 'install-refactor'
                else study_versions(args.study))
    if args.command == 'install-treatments':
        from .treatment_versions import apply_treatments
        return apply_treatments(args.study, args.proposal)
    from .source_duplicates import scan_duplicates, compare_duplicate_reports
    if args.command == 'scan-duplicates':
        result = scan_duplicates(args.repo, source_globs=args.source_globs)
    else:
        result = compare_duplicate_reports(load(args.before), load(args.after))
    path = Path(args.output).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
    return result
