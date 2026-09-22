"""CLI routes for development proposals, versioning and source refactor reports."""
import json
from pathlib import Path


def add_development_commands(sub):
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
    p = sub.add_parser('preview-improvements', help='Save bounded source/API/development-error inputs; no model call')
    p.add_argument('--study', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--alias-path', help='New source-module path relative to the library checkout')
    p.add_argument('--api', action='append', dest='apis', help='API name, qualified name or exact file:line:name ID; repeatable')
    p.add_argument('--development-errors', help='Explicit development error JSONL; never held-out evaluation failures')
    p.add_argument('--max-apis', type=int, default=12)
    p.add_argument('--max-context-characters', type=int, default=60000)
    p.set_defaults(development_handler=True)
    p = sub.add_parser('propose-improvements', help='Call the configured development model once; save alias/hint proposals')
    p.add_argument('--preview', required=True)
    p.add_argument('--model-config', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--readme', help='Already generated README to include in the complete treatment bundle')
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
    p = sub.add_parser('show-fix-hints', help='Retrieve saved hints for one function and a matching error; no model call')
    p.add_argument('--hints', required=True)
    p.add_argument('--function', required=True)
    p.add_argument('--error-file', required=True)
    p.set_defaults(development_handler=True)


def run_development_command(args):
    from .ablation import load
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
        return bundle_proposals(args.proposals, args.output, readme=args.readme)
    if args.command in ('install-refactor', 'versions'):
        from .source_refactors import install_refactor, study_versions
        return (install_refactor(args.study, args.proposal) if args.command == 'install-refactor'
                else study_versions(args.study))
    if args.command == 'preview-improvements':
        from .improvement_context import preview_improvements
        return preview_improvements(args.study, args.output, alias_path=args.alias_path,
            apis=args.apis, development_errors=args.development_errors, max_apis=args.max_apis,
            max_context_characters=args.max_context_characters)
    if args.command == 'propose-improvements':
        from .improvement_suggestions import propose_improvements
        return propose_improvements(args.preview, args.model_config, args.output, readme=args.readme)
    if args.command == 'install-treatments':
        from .treatment_versions import apply_treatments
        return apply_treatments(args.study, args.proposal)
    if args.command == 'show-fix-hints':
        from .improvement_suggestions import matching_fix_hints
        return {'status': 'unverified', 'hints': matching_fix_hints(
            load(args.hints), args.function, Path(args.error_file).read_text())}
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
