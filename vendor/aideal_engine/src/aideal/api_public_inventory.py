"""Static, defining-owner API inventory and a hash-bound opt-in reader.

No subject import, decorator evaluation, source execution, or model call occurs.
Python is parsed with ast; .pyx uses Cython's parser (optional tooling dependency).
Exposure aliases and inherited access paths point to definitions, not new targets.
"""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
from functools import lru_cache
import io
import json
from pathlib import Path
import subprocess
import tokenize

INVENTORY_VERSION = 'defining_api_and_public_exposures_v1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _public(name):
    return not name.startswith('_') or (name.startswith('__') and name.endswith('__') and name not in {'__init__', '__new__', '__cinit__', '__dealloc__'})


def _expr(node):
    return ast.unparse(node) if node is not None else ''


def _params(node, method=False):
    positional = [*node.args.posonlyargs, *node.args.args]
    defaults = [None] * (len(positional) - len(node.args.defaults)) + list(node.args.defaults)
    params = []
    for i, (arg, default) in enumerate(zip(positional, defaults)):
        params.append({'name': arg.arg, 'type': _expr(arg.annotation), 'default': _expr(default) if default is not None else None,
                       'required': default is None, 'kind': 'positional_only' if i < len(node.args.posonlyargs) else 'positional_or_keyword'})
    if node.args.vararg:
        params.append({'name': node.args.vararg.arg, 'type': _expr(node.args.vararg.annotation), 'default': None, 'required': False, 'kind': 'var_positional'})
    for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        params.append({'name': arg.arg, 'type': _expr(arg.annotation), 'default': _expr(default) if default is not None else None,
                       'required': default is None, 'kind': 'keyword_only'})
    if node.args.kwarg:
        params.append({'name': node.args.kwarg.arg, 'type': _expr(node.args.kwarg.annotation), 'default': None, 'required': False, 'kind': 'var_keyword'})
    receiver = params.pop(0) if method and positional else None
    return {'params': params, 'parameter_count': len(params), 'parameter_count_status': 'declared', 'implicit_receiver': receiver}


def _module(path, package_root, package_name):
    rel = path.relative_to(package_root)
    parts = list(rel.with_suffix('').parts)
    if parts[-1] == '__init__':
        parts.pop()
    return '.'.join([package_name, *parts])


def _offsets(text):
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    return lines, offsets


def _python_span(node, lines, starts):
    start = starts[node.lineno - 1] + len(lines[node.lineno-1].encode()[:node.col_offset].decode())
    end = starts[node.end_lineno - 1] + len(lines[node.end_lineno-1].encode()[:node.end_col_offset].decode())
    return start, end


def _body(node, span_sha):
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body.pop(0)
    decorators = [_expr(d) for d in getattr(node, 'decorator_list', [])]
    abstract = any(d.rsplit('.',1)[-1] == 'abstractmethod' for d in decorators)
    empty = not body or all(isinstance(n, ast.Pass) or isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and n.value.value is Ellipsis for n in body)
    category = 'abstract' if abstract else 'no_body' if empty else 'implementation'
    return {'category': category, 'reviewed': True, 'evidence': {'method': 'Python AST declaration/body presence; no inference of forwarding or semantic equivalence', 'source_span_sha256': span_sha, 'decorators': decorators}}


def _literal_names(node):
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)) and all(isinstance(v, ast.Constant) and isinstance(v.value, str) for v in node.elts):
        return [v.value for v in node.elts]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal_names(node.left), _literal_names(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _python_file(path, root, module, library, source):
    tree = ast.parse(source, filename=str(path), type_comments=True)
    lines, starts = _offsets(source)
    relative = path.relative_to(root).as_posix()
    file_sha = _sha(path.read_bytes())
    rows, aliases, classes, issues = [], [], {}, []
    factories, generated, data_names = {}, [], []
    exports = None
    all_known = True
    package = module if path.stem == '__init__' else module.rsplit('.', 1)[0]

    def alias(name, target, node, condition=(), relation='import'):
        aliases.append({'exposed_name': module+'.'+name, 'target': target, 'path': relative, 'line': node.lineno,
                        'conditional_context': list(condition), 'relation': relation})

    def visit(body, owners=(), condition=(), local=False):
        nonlocal exports, all_known
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                isclass = isinstance(node, ast.ClassDef)
                start,end = _python_span(node,lines,starts)
                qualified = '.'.join((module,*owners,node.name))
                decorators = [_expr(x) for x in node.decorator_list]
                prop = not isclass and any(d.rsplit('.',1)[-1] in {'property','cached_property','setter','deleter','getter'} for d in decorators)
                kind = 'class_constructor' if isclass else 'property' if prop else 'method' if owners else 'function'
                row = {'site_id':f'Python:{library}:{relative}:{start}:{kind}:{node.name}', 'library':library,'language':'Python','source_language':'Python',
                       'name':node.name,'module':module,'owner':'.'.join(owners),'qualified_name':qualified,'api_id':'python:'+qualified,
                       'defining_owner':'.'.join((module,*owners)),'defining_owner_kind':'class' if owners or isclass else 'module',
                       'defining_file':relative,'file':relative,'path':relative,'line':node.lineno,'end_line':node.end_lineno,'start':start,'end':end,
                       'offset_unit':'Unicode code points in decoded source','source_sha256':file_sha,'source_span_sha256':_sha(source[start:end].encode()),
                       'kind':kind,'definition_kind':kind,'callable':not prop,'declared_visibility':'public' if _public(node.name) else 'non-public',
                       'public_owner_chain':all(_public(x) for x in owners),'scope':'production','synthetic':False,'decorators':decorators,
                       'conditional_context':list(condition),'local_definition':local,'description':ast.get_docstring(node) or ''}
                if isclass:
                    bases = [_expr(x) for x in node.bases]
                    ctors = [x for x in node.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name in {'__init__','__new__'}]
                    chosen = next((x for x in ctors if x.name=='__init__'), next(iter(ctors),None))
                    row.update(_params(chosen,True) if chosen else {'params':[],'parameter_count':None,'parameter_count_status':'unknown_inherited_or_generated','implicit_receiver':None})
                    row.update(signature='class '+node.name+('('+', '.join(bases)+')' if bases else ''), returns=qualified,
                               class_bases=bases, class_keywords=[_expr(x) for x in node.keywords], constructor_signature='def '+chosen.name+'('+_expr(chosen.args)+')' if chosen else '',
                               body_classification={'category':'implementation','reviewed':True,'evidence':{'method':'Declared class API; constructor arity recorded separately; class body is not a wrapper classification','source_span_sha256':row['source_span_sha256']}})
                    classes[qualified]={'row':row,'bases':bases,'module':module,'owners':owners,'node':node}
                else:
                    row.update(_params(node,bool(owners) and 'staticmethod' not in decorators))
                    row.update(signature=('async def ' if isinstance(node,ast.AsyncFunctionDef) else 'def ')+node.name+'('+_expr(node.args)+')',returns=_expr(node.returns),body_classification=_body(node,row['source_span_sha256']))
                    row['is_abstract']=row['body_classification']['category']=='abstract'
                    row['body_presence']='absent' if row['body_classification']['category']=='no_body' else 'present'
                    nested={n.name:n for n in node.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
                    returns=[]
                    def collect_returns(statements):
                        for item in statements:
                            if isinstance(item,ast.Return):returns.append(item.value)
                            elif not isinstance(item,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                                for field in ('body','orelse','finalbody'):
                                    values=getattr(item,field,None)
                                    if isinstance(values,list):collect_returns(values)
                    collect_returns(node.body)
                    returned={n.id for n in returns if isinstance(n,ast.Name)}
                    if returns and len(returned)==1 and all(isinstance(n,ast.Name) and n.id in nested for n in returns):
                        inner=nested[next(iter(returned))]
                        factories[qualified]={'params':_params(inner),'line':inner.lineno,'signature':'def '+inner.name+'('+_expr(inner.args)+')','factory_site_id':row['site_id'],'factory_source_sha256':file_sha,'factory_span_sha256':row['source_span_sha256']}
                rows.append(row)
                if isclass:
                    visit(node.body,owners+(node.name,),condition,local)
                else:
                    # Local definitions remain explicit ledger exclusions, not public targets.
                    for inner in ast.walk(node):
                        if inner is not node and isinstance(inner,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                            issues.append({'path':relative,'line':inner.lineno,'name':inner.name,'status':'excluded','reason':'function_local_definition'})
            elif isinstance(node,ast.ImportFrom) and not owners and not local:
                if node.level:
                    parts=package.split('.')
                    base='.'.join(parts[:len(parts)-node.level+1])
                    target='.'.join(x for x in [base,node.module] if x)
                else:
                    target=node.module or ''
                for value in node.names:
                    alias(value.asname or value.name,target+'.'+value.name,node,condition,'star_import' if value.name=='*' else 'import')
            elif isinstance(node,ast.Import) and not owners and not local:
                for value in node.names:
                    alias(value.asname or value.name.split('.')[0],value.name if value.asname else value.name.split('.')[0],node,condition)
            elif isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign)) and not local:
                targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                value=node.value
                for target in targets:
                    if not isinstance(target,ast.Name):continue
                    if target.id=='__all__' and not owners:
                        names=_literal_names(value)
                        if names is None:all_known=False
                        elif isinstance(node,ast.AugAssign):exports=(exports or [])+names
                        else:exports=names
                    elif not owners and isinstance(value,(ast.Name,ast.Attribute)):
                        alias(target.id,_expr(value),node,condition,'assignment')
                    elif not owners and isinstance(value,ast.Call):
                        start,end=_python_span(node,lines,starts)
                        generated.append({'name':target.id,'callee':_expr(value.func),'path':relative,'line':node.lineno,'end_line':node.end_lineno,'start':start,'end':end,'source_sha256':file_sha,'source_span_sha256':_sha(source[start:end].encode()),'signature':source[start:end],'module':module,'conditional_context':list(condition)})
                    elif not owners and isinstance(value,(ast.Constant,ast.Dict,ast.List,ast.Tuple,ast.Set)):
                        data_names.append(module+'.'+target.id)
            elif not local:
                # Conditional source declarations are retained with their controlling site.
                for field in ('body','orelse','finalbody'):
                    value=getattr(node,field,None)
                    clause={'kind':'if','line':node.lineno,'expression':_expr(node.test),'expected':field=='body'} if isinstance(node,ast.If) else {'kind':type(node).__name__,'line':getattr(node,'lineno',0),'branch':field}
                    if isinstance(value,list):visit(value,owners,condition+(clause,))
                for arm in [*getattr(node,'handlers',[]),*getattr(node,'cases',[])]:
                    visit(arm.body,owners,condition+(f'{type(node).__name__}@{getattr(node,"lineno",0)}',))
    visit(tree.body)
    if not all_known:issues.append({'path':relative,'status':'unresolved','reason':'dynamic___all__','module':module})
    return rows,aliases,classes,issues,{'names':exports,'fully_resolved':all_known,'factories':factories,'generated':generated,'data_names':data_names}


def _cy_name(node):
    for attr in ('name','class_name'):
        name=getattr(node,attr,None)
        if isinstance(name,str):return name
    base=getattr(node,'declarator',None) or getattr(node,'base',None)
    return _cy_name(base) if base is not None else ''


def _cy_expr(node):
    if node is None:return ''
    name=type(node).__name__
    if name=='NameNode':return node.name
    if name=='AttributeNode':return _cy_expr(node.obj)+'.'+node.attribute
    if hasattr(node,'value'):return repr(node.value)
    return ''


def _cython_file(path,root,module,library,source):
    try:
        import Cython
        from Cython.Compiler.TreeFragment import parse_from_strings
    except ImportError as exc:
        raise ValueError('Cython parser is required for .pyx inventory; refusing an incomplete Python-only scan') from exc
    tree=parse_from_strings(str(path),source)
    lines,starts=_offsets(source);relative=path.relative_to(root).as_posix();file_sha=_sha(path.read_bytes())
    rows,classes,issues=[],{},[]
    def children(node):
        for field in node.child_attrs:
            value=getattr(node,field,None)
            for child in value if isinstance(value,list) else [value]:
                if hasattr(child,'child_attrs'):yield child
    def visit(node,owners=()):
        kind=type(node).__name__
        isclass=kind in {'CClassDefNode','PyClassDefNode'}
        isfunction=kind in {'DefNode','CFuncDefNode'}
        if isclass or isfunction:
            name=_cy_name(node);line=node.pos[1];end_line=min(len(lines),node.end_pos()[1]);start=starts[line-1];end=starts[end_line]
            qualified='.'.join((module,*owners,name));decorators=[_cy_expr(getattr(d,'decorator',None)) for d in getattr(node,'decorators',None) or []]
            prop=any(d.rsplit('.',1)[-1] in {'property','cached_property','setter','getter','deleter'} for d in decorators)
            exposed=isclass or kind=='DefNode' or bool(getattr(node,'overridable',False))
            rowkind='class_constructor' if isclass else 'property' if prop else 'method' if owners else 'function'
            row={'site_id':f'Python:{library}:{relative}:{start}:{rowkind}:{name}','library':library,'language':'Python','source_language':'Cython',
                 'name':name,'module':module,'owner':'.'.join(owners),'qualified_name':qualified,'api_id':'python:'+qualified,
                 'defining_owner':'.'.join((module,*owners)),'defining_owner_kind':'class' if owners or isclass else 'module',
                 'defining_file':relative,'file':relative,'path':relative,'line':line,'end_line':end_line,'start':start,'end':end,
                 'offset_unit':'Unicode code points in decoded source','source_sha256':file_sha,'source_span_sha256':_sha(source[start:end].encode()),
                 'kind':rowkind,'definition_kind':rowkind,'callable':exposed and not prop,'python_exposed':exposed,
                 'declared_visibility':'public' if _public(name) and exposed else 'non-public','public_owner_chain':all(_public(x) for x in owners),
                 'scope':'production','synthetic':False,'decorators':decorators,'description':str(getattr(node,'doc','') or ''),
                 'signature':lines[line-1].strip(),'returns':'','cython_node_kind':kind,'parser_version':Cython.__version__,
                 'body_classification':{'category':'implementation','reviewed':True,'evidence':{'method':'Cython parser declaration/body; no wrapper/equivalence inference','parser_version':Cython.__version__,'node_kind':kind,'source_span_sha256':_sha(source[start:end].encode())}}}
            if isclass:
                bases=[_cy_expr(x) for x in getattr(getattr(node,'bases',None),'args',[])];row.update(class_bases=bases,params=[],parameter_count=None,parameter_count_status='unknown_inherited_or_generated')
                classes[qualified]={'row':row,'bases':bases,'module':module,'owners':owners}
            else:
                declarator=getattr(node,'declarator',node)
                args=list(getattr(declarator,'args',[]));params=[]
                for arg in args:
                    params.append({'name':_cy_name(arg),'type':_cy_expr(getattr(arg,'base_type',None)),'default':_cy_expr(getattr(arg,'default',None)) if getattr(arg,'default',None) is not None else None,
                                   'required':getattr(arg,'default',None) is None,'kind':'keyword_only' if getattr(arg,'kw_only',False) else 'positional_or_keyword'})
                receiver=params.pop(0) if owners and params and 'staticmethod' not in decorators else None
                for attr,label in [('star_arg','var_positional'),('starstar_arg','var_keyword')]:
                    arg=getattr(node,attr,None)
                    if arg is not None:params.append({'name':_cy_name(arg),'type':'','default':None,'required':False,'kind':label})
                row.update(params=params,parameter_count=len(params),parameter_count_status='declared',implicit_receiver=receiver)
            rows.append(row)
            if isfunction:return
            owners=owners+(name,)
        for child in children(node):visit(child,owners)
    visit(tree)
    for qualified,info in classes.items():
        ctor=next((r for r in rows if r['qualified_name']==qualified+'.__init__'),next((r for r in rows if r['qualified_name']==qualified+'.__cinit__'),None))
        if ctor:
            info['row'].update({k:deepcopy(ctor[k]) for k in ('params','parameter_count','parameter_count_status','implicit_receiver')})
            info['row']['constructor_signature']=ctor['signature']
    return rows,[],classes,issues,{'names':None,'fully_resolved':True,'factories':{},'generated':[],'data_names':[]}


def scan_python_surface(root, package_roots, library, source_snapshot=None, binding_environment=None):
    """Enumerate .py/.pyx declarations, reexports and C3-resolved owned inheritance.

    package_roots maps relative package directories to import names. Every file,
    excluded declaration, unresolved binding and ownership edge remains visible.
    The snapshot is an attestation from the caller; file hashes are verified here.
    """
    root=Path(root).resolve();rows=[];aliases=[];classes={};issues=[];modules={};files=[]
    binding_environment=binding_environment or {'facts':{}}
    for relative,package in sorted(package_roots.items()):
        package_root=(root/relative).resolve(strict=True)
        if not package_root.is_relative_to(root):raise ValueError('Package root escapes source checkout')
        for path in sorted({*package_root.rglob('*.py'),*package_root.rglob('*.pyx')}):
            if not path.resolve().is_relative_to(root):raise ValueError('Source symlink escapes pinned root')
            if any(part in {'tests','test','__pycache__'} for part in path.relative_to(package_root).parts[:-1]):
                issues.append({'path':path.relative_to(root).as_posix(),'status':'excluded','reason':'test_source_path'});continue
            raw=path.read_bytes();encoding=tokenize.detect_encoding(io.BytesIO(raw).readline)[0];source=raw.decode(encoding)
            module=_module(path,package_root,package)
            if module in modules:raise ValueError('Two source implementations occupy one Python module: '+module)
            parsed=(_cython_file if path.suffix=='.pyx' else _python_file)(path,root,module,library,source)
            local_rows,local_aliases,local_classes,local_issues,exports=parsed
            rows+=local_rows;aliases+=local_aliases;classes.update(local_classes);issues+=local_issues
            modules[module]={'path':path.relative_to(root).as_posix(),'exports':exports}
            files.append({'path':path.relative_to(root).as_posix(),'sha256':_sha(raw),'bytes':len(raw),'encoding':encoding})
    by_qn=defaultdict(list)
    for row in rows:by_qn[row['qualified_name']].append(row)
    alias_map=defaultdict(list)
    for edge in aliases:
        if edge['relation']!='star_import':alias_map[edge['exposed_name']].append(edge)
    def resolve(value,module,seen=(),absolute=False):
        if len(seen)>64:return set()
        choices=[value] if absolute or value.startswith(tuple(package_roots.values())) else [module+'.'+value,value]
        for candidate in choices:
            if candidate in by_qn:return {candidate}
            if candidate in seen:continue
            parts=candidate.split('.')
            for cut in range(len(parts),0,-1):
                prefix='.'.join(parts[:cut]);suffix='.'.join(parts[cut:])
                if prefix in alias_map:
                    found=set()
                    for edge in alias_map[prefix]:
                        target=edge['target']+('.'+suffix if suffix else '')
                        found.update(resolve(target,prefix.rsplit('.',1)[0],seen+(candidate,),absolute=edge['relation']!='assignment'))
                    if found:return found
            if candidate in modules:return {candidate}
        return set()
    factories={q:v for module in modules.values() for q,v in module['exports']['factories'].items()}
    data_names={q for module in modules.values() for q in module['exports']['data_names']}
    for info in modules.values():
        for assignment in info['exports']['generated']:
            targets=resolve(assignment['callee'],assignment['module']) & set(factories)
            if len(targets)!=1:
                issues.append({**assignment,'status':'unresolved','reason':'runtime_generated_symbol_type_not_established'})
                continue
            factory=next(iter(targets));proof=factories[factory];qualified=assignment['module']+'.'+assignment['name']
            row={**assignment,'site_id':f"Python:{library}:{assignment['path']}:{assignment['start']}:function:{assignment['name']}",
                 'library':library,'language':'Python','source_language':'Python','qualified_name':qualified,'api_id':'python:'+qualified,
                 'owner':'','defining_owner':assignment['module'],'defining_owner_kind':'module','defining_file':assignment['path'],'file':assignment['path'],
                 'offset_unit':'Unicode code points in decoded source','kind':'function','definition_kind':'function','callable':True,
                 'declared_visibility':'public' if _public(assignment['name']) else 'non-public','public_owner_chain':True,'scope':'production','synthetic':False,
                 'description':'','returns':'','generated_callable':{'factory':factory,**proof},**deepcopy(proof['params']),
                 'body_classification':{'category':'implementation','reviewed':True,'evidence':{'method':'Owned factory returns one locally declared callable; assignment binds that generated callable','factory':factory,'source_span_sha256':assignment['source_span_sha256'],'factory_span_sha256':proof['factory_span_sha256']}}}
            rows.append(row);by_qn[qualified].append(row)
    # Expand statically known star imports, never evaluate dynamic __all__.
    for edge in [x for x in aliases if x['relation']=='star_import']:
        target=edge['target'][:-2]
        if target not in modules:
            issues.append({**edge,'status':'unresolved','reason':'star_import_target_not_owned_or_dynamic'});continue
        exports=modules[target]['exports']
        names=exports['names']
        if names is None:
            names=sorted({q[len(target)+1:].split('.')[0] for q in [*by_qn,*alias_map] if q.startswith(target+'.') and _public(q[len(target)+1:].split('.')[0])})
        for name in names:
            new={**edge,'exposed_name':edge['exposed_name'][:-1]+name,'target':target+'.'+name,'relation':'resolved_star_import'}
            alias_map[new['exposed_name']].append(new);aliases.append(new)
    exposures=[]
    def expose(public_name,definition,relation,evidence):
        if not _public(public_name.rsplit('.',1)[-1]):return
        exposures.append({'exposure_id':'python:'+public_name,'qualified_name':public_name,'defining_api_id':'python:'+definition,
                          'defining_qualified_name':definition,'relation':relation,'evidence':evidence,'status':'resolved'})
    for row in rows:
        if row['declared_visibility']=='public' and row['public_owner_chain']:
            expose(row['qualified_name'],row['qualified_name'],'declared',{'path':row['path'],'line':row['line'],'source_sha256':row['source_sha256']})
    for name,edges in sorted(alias_map.items()):
        if not _public(name.rsplit('.',1)[-1]):continue
        targets=set()
        for edge in edges:targets.update(resolve(edge['target'],name.rsplit('.',1)[0],absolute=edge['relation']!='assignment'))
        target_defs=targets & set(by_qn)
        if len(target_defs)==1:
            expose(name,next(iter(target_defs)),'reexport',{'edges':edges})
        elif target_defs or not targets:
            data_only=all(e['target'] in data_names for e in edges)
            exposures.append({'exposure_id':'python:'+name,'qualified_name':name,'defining_api_id':None,'relation':'import_or_alias',
                              'status':'noncallable' if data_only else 'unresolved' if target_defs or any(e['target'].startswith(tuple(package_roots.values())) for e in edges) else 'external',
                              'reason':'explicit_data_binding' if data_only else 'ambiguous_or_unresolved_source_binding' if target_defs else 'not_an_owned_definition','candidates':sorted(target_defs),'evidence':edges})
    mro_cache={}
    def mro(qn,stack=()):
        if qn in mro_cache:return mro_cache[qn]
        if qn in stack:return None
        info=classes[qn];bases=[];external=[]
        for base in info['bases']:
            resolved=resolve(base,info['module'])
            # ``from other import A; class A(A):`` binds the base before the
            # new class assignment. Its import binding must beat the new name.
            if resolved=={qn} and qn in alias_map:
                resolved=set()
                for edge in alias_map[qn]:
                    resolved.update(resolve(edge['target'],info['module'],absolute=edge['relation']!='assignment'))
            owned=resolved & set(classes)
            if len(owned)==1:bases.append(next(iter(owned)))
            elif base in {'object','builtins.object'}:continue
            else:external.append(base)
        info['row']['inheritance_external_or_unresolved']=external
        if external:
            issues.append({'qualified_name':qn,'status':'unresolved','reason':'external_or_dynamic_base_members_not_enumerated','bases':external})
        linear=[]
        for base in bases:
            value=mro(base,stack+(qn,))
            if value is None:return None
            linear.append(list(value))
        linear.append(list(bases));result=[qn]
        while any(linear):
            linear=[x for x in linear if x]
            head=next((x[0] for x in linear if all(x[0] not in y[1:] for y in linear)),None)
            if head is None:return None
            result.append(head)
            for seq in linear:
                if seq and seq[0]==head:seq.pop(0)
        mro_cache[qn]=result;return result
    for qn,info in classes.items():
        order=mro(qn)
        if order is None:
            issues.append({'qualified_name':qn,'status':'unresolved','reason':'inconsistent_or_cyclic_static_mro'});continue
        info['row']['static_mro']=order
        # Class construction inherits one exact __init__/__new__ contract when known.
        if info['row']['parameter_count'] is None and not info['row'].get('decorators') and not info['row'].get('class_keywords'):
            for base in order[1:]:
                parent=classes[base]['row']
                if parent['parameter_count'] is not None:
                    info['row'].update(params=deepcopy(parent['params']),parameter_count=parent['parameter_count'],parameter_count_status='inherited_static_constructor',constructor_defining_api_id=parent['api_id']);break
            if info['row']['parameter_count'] is None and not info['bases']:
                info['row'].update(parameter_count=0,parameter_count_status='implicit_object_constructor')
        class_paths=[x['qualified_name'] for x in exposures if x.get('defining_qualified_name')==qn]
        seen=set()
        for ancestor in order:
            for name,definitions in by_qn.items():
                if not name.startswith(ancestor+'.') or '.' in name[len(ancestor)+1:]:continue
                member=name[len(ancestor)+1:]
                if member in seen:continue
                seen.add(member)
                if not _public(member):continue
                for public_class in class_paths:
                    expose(public_class+'.'+member,name,'inherited' if ancestor!=qn else 'class_reexport_member',{'class':qn,'declaring_class':ancestor,'static_mro':order,'external_or_dynamic_bases':info['row']['inheritance_external_or_unresolved']})
    # Exact duplicate exposure edges are consolidated without collapsing definitions.
    exposures=list({digest(x):x for x in exposures}.values())
    exposed=defaultdict(list)
    for e in exposures:
        if e.get('defining_api_id'):exposed[e['defining_api_id']].append(e['exposure_id'])
    for row in rows:
        row['exposure_ids']=sorted(set(exposed[row['api_id']]))
        row['public_exposure_established']=bool(row['exposure_ids'])
        row['public_access_paths']=[x.split(':',1)[1] for x in row['exposure_ids']]
        row['preferred_public_path']=min((x.split(':',1)[1] for x in row['exposure_ids']),key=lambda x:(len(x.split('.')),len(x),x),default=None)
        reason=None
        if row.get('python_exposed') is False:reason='c_only_cython_declaration'
        elif row['name'] in {'__init__','__new__','__cinit__','__dealloc__'}:reason='constructor_or_lifecycle_part_of_class'
        elif not row['exposure_ids']:reason='no_public_owned_exposure'
        elif not row['callable']:reason='noncallable_property'
        resolutions=[]
        for clause in row.get('conditional_context',[]):
            if not isinstance(clause,dict) or clause.get('kind')!='if':continue
            try:
                value=_condition_value(ast.parse(clause['expression'],mode='eval').body,row['module'],binding_environment['facts'])
            except (KeyError,ValueError):value=None
            resolutions.append({**clause,'value':value,'active':None if value is None else bool(value)==clause['expected']})
        row['conditional_binding_resolution']=resolutions
        if any(x['active'] is False for x in resolutions):reason='inactive_recorded_runtime_variant'
        row['inventory_status']='excluded' if reason else 'candidate'
        row['inventory_reason']=reason or 'public_source_defined_callable'
    return {'schema':2,'kind':'qualified_source_api_inventory','inventory_version':INVENTORY_VERSION,'library':library,
            'source_snapshot':source_snapshot or {},'package_roots':package_roots,'binding_environment':binding_environment,'records':rows,'exposures':exposures,'issues':issues,
            'source_files':files,'source_file_binding_sha256':digest(files),'counts':{'definitions':len(rows),'candidate_sites':sum(r['inventory_status']=='candidate' for r in rows),
            'source_files':len(files),'cython_files':sum(f['path'].endswith('.pyx') for f in files),'exposures':len(exposures),'exposure_status':dict(Counter(e['status'] for e in exposures)),
            'issue_reasons':dict(Counter(e['reason'] for e in issues))}}


def qualified_inventory_details(cfg,data):
    """Validate an opt-in frozen defining-API ledger, then apply qualified selection.

    This reader uses bound source bytes and source spans; it never imports the
    subject. Python/Cython identity is independently parsed with pinned tooling,
    cached only after current source hashes and scanner/tool versions match.
    Source ownership is recalculated after path relocation using the effective
    source-root/namespace policy.
    """
    from .api_registry import _bound_json
    from .api_origin import audit_api_origins, origin_enabled
    from .api_canonical_selection import QUALIFIED_POLICY_VERSION, select_canonical_implementations
    if data.get('schema')!=2 or data.get('kind')!='qualified_source_api_inventory':raise ValueError('Unsupported qualified inventory')
    if not origin_enabled(cfg):raise ValueError('Qualified inventory requires explicit source-origin policy')
    ledger=_bound_json(cfg,data,'source_inventory')
    if ledger.get('schema')!=2 or ledger.get('kind')!='qualified_source_api_inventory':raise ValueError('Unsupported qualified source ledger')
    relative=Path(data['source_root'])
    if relative.is_absolute() or '..' in relative.parts:raise ValueError('Source root must be relative and contained')
    root=(Path(cfg.root)/relative).resolve(strict=True)
    configured_policy=cfg.raw['codebase']['api_origin']
    for key in ('library_namespaces','external_namespaces'):
        if set(configured_policy.get(key,[]))!=set(ledger['origin_policy'].get(key,[])):
            raise ValueError('Source namespace policy differs from frozen inventory')
    configured_roots={(Path(cfg.root)/value).resolve(strict=True) for value in configured_policy.get('source_roots',[])}
    frozen_roots={(root/value).resolve(strict=True) for value in ledger['origin_policy']['source_roots']}
    if configured_roots!=frozen_roots:raise ValueError('Source root policy differs from frozen inventory')
    snapshot=ledger['source_snapshot']
    if data.get('source_commit')!=snapshot['commit'] or data.get('source_tree')!=snapshot['tree'] or data.get('source_version')!=ledger.get('source_version'):
        raise ValueError('Source identity differs between manifest and ledger')
    def git(*args):
        r=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,timeout=30,check=True)
        return r.stdout.strip()
    if (git('rev-parse','HEAD')!=snapshot['commit'] or git('rev-parse','HEAD^{tree}')!=snapshot['tree'] or git('status','--porcelain','--untracked-files=no')):
        raise ValueError('Pinned source identity changed')
    files=ledger['source_files']
    if digest(files)!=ledger['source_file_binding_sha256']:raise ValueError('Source binding digest changed')
    text_by_path={}
    for binding in files:
        path=root/binding['path']
        if not path.resolve(strict=True).is_relative_to(root):raise ValueError('Source evidence escapes root')
        raw=path.read_bytes()
        if _sha(raw)!=binding['sha256'] or len(raw)!=binding['bytes']:raise ValueError('Bound source file changed: '+binding['path'])
        text_by_path[binding['path']]=raw.decode(binding.get('encoding','utf-8'))
    rows=deepcopy(ledger['records'])
    if len({r['site_id'] for r in rows})!=len(rows):raise ValueError('Duplicate definition site')
    requested=data.get('declaration_ids')
    expected=[r['site_id'] for r in rows if r['language'].lower()==cfg.language.lower() and r.get('inventory_status')=='candidate']
    if not isinstance(requested,list) or len(requested)!=len(set(requested)) or set(requested)!=set(expected):raise ValueError('Manifest must bind every candidate definition for its language')
    candidates=[]
    # Verify Python identity facts independently of a self-consistent rewritten
    # JSON ledger. Cython remains a parser-only optional operator dependency.
    actual_python=None
    if ledger.get('package_roots'):
        import importlib.metadata
        parser_version=importlib.metadata.version('Cython') if any(f['path'].endswith('.pyx') for f in files) else 'not_required'
        if parser_version not in {'not_required','3.3.1'}:raise ValueError('Cython inventory verification requires pinned parser 3.3.1')
        environment=ledger.get('binding_environment',{'facts':{}})
        for fact in environment['facts'].values():
            path=Path(cfg.root)/fact['evidence_path'];raw=path.read_bytes()
            if _sha(raw)!=fact['evidence_sha256']:raise ValueError('Conditional runtime evidence changed')
            value=json.loads(raw)
            for key in fact['evidence_json_path']:value=value[key]
            expected=('available_module' if value else None) if fact.get('transform')=='module_or_none' else value
            if expected!=fact['value']:raise ValueError('Conditional runtime fact differs from receipt')
        actual=_cached_python_parse(str(root),json.dumps(ledger['package_roots'],sort_keys=True),ledger['library'],json.dumps(snapshot,sort_keys=True),
                                    ledger['source_file_binding_sha256'],_sha(Path(__file__).read_bytes()),parser_version,json.dumps(environment,sort_keys=True))
        actual_python={row['site_id']:row for row in actual['records']}
        if set(actual_python)!={row['site_id'] for row in rows}:
            raise ValueError('Python/Cython ledger omits or adds source definitions')
    for row in rows:
        if row['site_id'] not in requested:continue
        text=text_by_path[row['path']];start,end=row['start'],row['end']
        span=text.encode('utf-16-le')[2*start:2*end].decode('utf-16-le') if row.get('offset_unit','').startswith('UTF-16') else text[start:end]
        if _sha(span.encode())!=row['source_span_sha256']:raise ValueError('Definition span changed')
        if actual_python is not None:
            actual=actual_python.get(row['site_id'])
            fields=('name','module','owner','defining_owner','defining_owner_kind','signature','returns','implicit_receiver','public_access_paths','preferred_public_path','conditional_context','qualified_name','kind','path','line','start','end','parameter_count','parameter_count_status','params','exposure_ids','source_sha256','source_span_sha256',
                    'scope','callable','public_owner_chain','declared_visibility','public_exposure_established','synthetic','body_presence','is_abstract','inventory_status','inventory_reason','forwarding')
            if actual is None or any(actual.get(k)!=row.get(k) for k in fields):
                raise ValueError('Python/Cython defining facts differ from a fresh static parse')
        row.update(file=str(relative/row['path']),defining_file=str(relative/row['path']),definition_kind=row['kind'],visibility='public')
        candidates.append(row)
    origins=audit_api_origins(cfg,candidates)
    for row,decision in zip(candidates,origins['decisions']):row['api_origin']=decision
    selected=select_canonical_implementations(candidates,policy_version=QUALIFIED_POLICY_VERSION)
    if selected['counts'].get('unresolved_sites'):
        raise ValueError('Qualified inventory contains unresolved selection families; review the selection receipt')
    receipt=_bound_json(cfg,data,'canonical_selection')
    if data.get('canonical_selection_policy_version')!=QUALIFIED_POLICY_VERSION or receipt.get('policy_version')!=QUALIFIED_POLICY_VERSION:
        raise ValueError('Qualified selection policy differs')
    expected_ids=[r['site_id'] for r in receipt['winners'] if r['language'].lower()==cfg.language.lower()]
    if set(selected['winner_site_ids'])!=set(expected_ids) or set(data.get('canonical_declaration_ids',[]))!=set(expected_ids):
        raise ValueError('Qualified selected definition identities changed')
    # Compiler ledgers can omit source comments entirely. After verifying the
    # frozen selection, expose the common consumer schema without rewriting its
    # provenance or inventing documentation. Python/Cython comments stay exact.
    for row in selected['winners']:
        description = row.get('description')
        if description is None:
            row['description'] = ''
        elif not isinstance(description, str):
            raise ValueError('Qualified API source description must be text or absent')
    return selected['winners']


@lru_cache(maxsize=8)
def _cached_python_parse(root,packages,library,snapshot,verified_source_digest,scanner_sha256,parser_version,environment):
    # All key components are independently reverified by the caller first.
    return scan_python_surface(root,json.loads(packages),library,json.loads(snapshot),json.loads(environment))


def _condition_value(node,module,facts):
    if isinstance(node,ast.Name):return facts[module+'.'+node.id]['value']
    if isinstance(node,ast.Constant):return node.value
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not):return not _condition_value(node.operand,module,facts)
    if isinstance(node,ast.Compare) and len(node.ops)==1:
        left,right=_condition_value(node.left,module,facts),_condition_value(node.comparators[0],module,facts)
        if isinstance(node.ops[0],(ast.Is,ast.Eq)):return left==right
        if isinstance(node.ops[0],(ast.IsNot,ast.NotEq)):return left!=right
    raise ValueError('Condition cannot be resolved without execution')


def reconcile_documentation(ledger, documents):
    """Exact typed document identities only; no simple-name/string-hit credit.

    ``documents`` are reviewed records with qualified_name, object_type, URL,
    anchor and text hash. Class aliases/inherited exposures are resolved by the
    source graph before this join. Noncallable fields remain separately mapped.
    """
    by_name=defaultdict(list)
    for doc in documents:by_name[doc['qualified_name']].append(doc)
    by_api=defaultdict(set)
    defining_names=defaultdict(set)
    for row in ledger['records']:
        by_api[row['api_id']].add(row['qualified_name'])
        defining_names[row['api_id']].add(row['qualified_name'])
    for exposure in ledger.get('exposures',[]):
        if exposure.get('status')=='resolved' and exposure.get('defining_api_id'):
            by_api[exposure['defining_api_id']].add(exposure['qualified_name'])
    mapped={}
    for api_id,names in sorted(by_api.items()):
        hits=[]
        for name in sorted(names):
            for doc in by_name.get(name,[]):
                hits.append({**doc,'matched_qualified_name':name,'match_type':'exact_defining_identity' if name in defining_names[api_id] else 'resolved_public_exposure'})
        hits=list({digest(x):x for x in hits}.values())
        mapped[api_id]={'status':'documented' if hits else 'undocumented','evidence':hits,
                        'reason':'Exact defining/exposure identity found in reviewed original documentation' if hits else 'No exact defining or statically resolved public exposure identity in the reviewed original document index; bare-name mentions are not coverage'}
    return mapped


def normalize_compiler_inventory(root, library, declarations, source_snapshot, prior_body_rows=()):
    """Reconcile existing parser-only JVM declarations, retaining every decision.

    The upstream compiler evidence is separately bound; no subject is compiled
    or executed here. Constructors are class-call families, fields/types remain
    visible as noncallables, and structural 'wrapper' labels do not remove rows.
    """
    from .api_registry import _parameters
    root=Path(root).resolve();rows=[];files={};issues=[]
    prior={r['site_id']:r for r in prior_body_rows}
    for original in declarations:
        row=deepcopy(original);relative=row['path'];path=root/relative
        if not path.resolve(strict=True).is_relative_to(root):raise ValueError('Compiler source escapes root')
        raw=path.read_bytes();sha=_sha(raw)
        if row['source_sha256']!=sha:raise ValueError('Compiler source hash differs: '+relative)
        files[relative]={'path':relative,'sha256':sha,'bytes':len(raw),'encoding':'utf-8'}
        source=raw.decode();start,end=row['start'],row['end']
        segment=source.encode('utf-16-le')[2*start:2*end].decode('utf-16-le')
        row.update(library=library,file=relative,defining_file=relative,offset_unit='UTF-16 code units in decoded UTF-8 source',source_span_sha256=_sha(segment.encode()),
                   original_kind=row['kind'],defining_owner_kind=row.get('owner_kind','class'),defining_owner=row.get('owner') or row['qualified_name'].rsplit('.',1)[0],
                   module=row['path'].split('/')[0] if library=='rdpro' else 'thumbnailator',source_language=row['language'])
        callable_kind=row['kind'] in {'method','constructor','class_constructor'}
        if row['kind']=='constructor':
            row['qualified_name']=row['owner'];row['name']=row['owner'].rsplit('.',1)[-1];row['kind']='class_constructor'
        row.update(api_id=row['language'].lower()+':'+row['qualified_name'],definition_kind=row['kind'],callable=callable_kind)
        old=prior.get(row['site_id'],{})
        row['body_classification']=old.get('body_classification',row.get('body_classification',{'category':'unresolved','reviewed':True,'evidence':{'method':'Compiler declaration retained; no wrapper or equivalence inference','source_span_sha256':row['source_span_sha256']}}))
        if callable_kind:
            try:
                params,returns=_parameters(row['signature'],row['language'])
                row.update(params=params,parameter_count=len(params),parameter_count_status='compiler_declared',returns=returns)
            except ValueError as exc:
                row.update(params=[],parameter_count=None,parameter_count_status='unknown_compiler_signature',returns='')
                issues.append({'site_id':row['site_id'],'reason':'unparsed_compiler_signature','error':str(exc)})
            # Parser classification is explicit only for body absence/abstract.
            category=row['body_classification'].get('category')
            row['is_abstract']=category=='abstract'
            row['body_presence']='absent' if category in {'no_body','abstract_or_empty'} else 'present'
        else:row.update(params=[],parameter_count=None,parameter_count_status='not_callable',returns='')
        reason='noncallable_declaration' if not callable_kind else 'not_public_owner_chain' if row.get('declared_visibility')!='public' or row.get('public_owner_chain') is not True else 'synthetic_declaration' if row.get('synthetic') is not False else 'test_support_scope' if row.get('scope')!='production' else None
        row.update(inventory_status='excluded' if reason else 'candidate',inventory_reason=reason or 'public_source_defined_callable',exposure_ids=[row['api_id']] if reason is None else [],preferred_public_path=row['qualified_name'])
        rows.append(row)
    bindings=[files[k] for k in sorted(files)]
    return {'schema':2,'kind':'qualified_source_api_inventory','inventory_version':INVENTORY_VERSION,'library':library,'source_snapshot':source_snapshot,
            'records':rows,'exposures':[],'issues':issues,'source_files':bindings,'source_file_binding_sha256':digest(bindings),
            'counts':{'definitions':len(rows),'candidate_sites':sum(x['inventory_status']=='candidate' for x in rows),'source_files':len(bindings),'by_module':dict(Counter(x['module'] for x in rows if x['inventory_status']=='candidate'))}}
