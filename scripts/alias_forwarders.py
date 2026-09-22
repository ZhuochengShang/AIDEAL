"""Conservative Scala 2 forwarding recognizer. Unsupported syntax is review-only.

This is deliberately not a Scala compiler or a general effect/type checker.
Only a small whole-module grammar is accepted; discarded text can never hide
an initializer, additional definition, literal, operator or second expression.
"""
from dataclasses import dataclass
import re


class ReviewRequired(ValueError):
    pass


@dataclass(frozen=True)
class Token:
    value: str
    line: int


def tokens(text):
    result, pos, line = [], 0, 1
    while pos < len(text):
        if text[pos].isspace():
            line += text[pos] == '\n'; pos += 1
        elif text.startswith('//', pos):
            end = text.find('\n', pos); pos = len(text) if end < 0 else end
        elif text.startswith('/*', pos):
            depth = 1; pos += 2
            while depth and pos < len(text):
                if text.startswith('/*', pos): depth += 1; pos += 2
                elif text.startswith('*/', pos): depth -= 1; pos += 2
                else: line += text[pos] == '\n'; pos += 1
            if depth: raise ReviewRequired('Unclosed comment')
        elif text[pos] in '\"\'`':
            # No string, character, quoted identifier or interpolation is part
            # of the supported wrapper grammar. Reject, never erase literals.
            raise ReviewRequired('Literals/quoted identifiers need manual review')
        else:
            match = re.match(r'[A-Za-z_][A-Za-z_0-9]*|[0-9]+|[^\s]', text[pos:])
            result.append(Token(match[0], line)); pos += len(match[0])
    return result


GEOLITE = 'edu.ucr.cs.bdlab.beast.geolite'
NAMES = {
    'java.io.ObjectInput': 'Ljava/io/ObjectInput;',
    'java.io.ObjectOutput': 'Ljava/io/ObjectOutput;',
    'java.awt.geom.Point2D.Double': 'Ljava/awt/geom/Point2D$Double;',
    'org.apache.spark.sql.types.DataType': 'Lorg/apache/spark/sql/types/DataType;',
    'org.apache.spark.sql.types.StructType': 'Lorg/apache/spark/sql/types/StructType;',
    'org.apache.spark.sql.Row': 'Lorg/apache/spark/sql/Row;',
    'org.locationtech.jts.geom.Envelope': 'Lorg/locationtech/jts/geom/Envelope;',
    **{GEOLITE + '.' + name: 'L' + GEOLITE.replace('.', '/') + '/' + name + ';'
       for name in ('IFeature', 'RasterMetadata')},
}
TERMS = {GEOLITE + '.' + name for name in ('Feature', 'RasterSchemaHelper')}
IMPORTABLE = set(NAMES) | TERMS | {'java.awt.geom.Point2D'}
BUILTINS = {'Any': 'Ljava/lang/Object;', 'String': 'Ljava/lang/String;',
            'Int': 'I', 'Long': 'J', 'Double': 'D', 'Float': 'F', 'Boolean': 'Z',
            'Byte': 'B', 'Short': 'S', 'Char': 'C', 'Unit': 'V'}
RESERVED = {'def', 'val', 'var', 'object', 'class', 'trait', 'new', 'return',
            'this', 'super', 'implicit', 'null', 'true', 'false', 'if', 'match'}


class Parser:
    def __init__(self, text): self.ts, self.i = tokens(text), 0
    def peek(self): return self.ts[self.i].value if self.i < len(self.ts) else None
    def take(self, expected=None):
        if self.i >= len(self.ts): raise ReviewRequired('Unexpected end of source')
        value = self.ts[self.i].value; self.i += 1
        if expected is not None and value != expected:
            raise ReviewRequired('Expected ' + expected + ', found ' + value)
        return value
    def ident(self):
        value = self.take()
        if not re.fullmatch('[A-Za-z_][A-Za-z_0-9]*', value) or value in RESERVED:
            raise ReviewRequired('Unsupported identifier: ' + value)
        return value
    def dotted(self):
        parts = [self.ident()]
        while self.peek() == '.':
            self.take('.'); parts.append(self.ident())
        return '.'.join(parts)
    def type_text(self):
        value = self.dotted()
        if self.peek() == '[':
            self.take('['); inner = self.type_text(); self.take(']')
            if value not in ('Array', 'scala.Array'):
                raise ReviewRequired('Only Array type parameters are supported')
            value = 'Array[' + inner + ']'
        return value
    def params(self):
        rows = []; self.take('(')
        while self.peek() != ')':
            name = self.ident(); self.take(':'); typ = self.type_text(); default = None
            if self.peek() == '=':
                self.take('='); default = self.take('null')
            rows.append({'name': name, 'type': typ, 'default': default})
            if self.peek() != ',': break
            self.take(',')
        self.take(')')
        if len({r['name'] for r in rows}) != len(rows): raise ReviewRequired('Duplicate parameters')
        return rows


def parse_module(source):
    p = Parser(source); p.take('package'); package = p.dotted()
    if p.peek() == ';': p.take(';')
    imports = set()
    while p.peek() == 'import':
        p.take(); start_line = p.ts[p.i].line; values = []; depth = 0
        while p.peek() is not None:
            token = p.ts[p.i]
            if values and depth == 0 and (token.line > start_line or token.value in (';', 'object', 'import')): break
            value = p.take(); depth += (value == '{') - (value == '}'); values.append(value)
        value = ''.join(values)
        if '.{' in value and value.endswith('}'):
            prefix, names = value.split('.{', 1)
            expanded = {prefix + '.' + n for n in names[:-1].split(',')}
        elif value.endswith('._'):
            prefix = value[:-2]
            if prefix not in ('java.io', 'org.apache.spark.sql.types', GEOLITE):
                raise ReviewRequired('Unsupported wildcard import')
            expanded = {n for n in IMPORTABLE if n.rsplit('.', 1)[0] == prefix}
        else: expanded = {value}
        if not expanded or not expanded <= IMPORTABLE:
            raise ReviewRequired('Unsupported or renamed import')
        if any(n.rsplit('.', 1)[-1] in BUILTINS for n in expanded):
            raise ReviewRequired('Import shadows an implicitly available Scala type')
        imports.update(expanded)
        if p.peek() == ';': p.take(';')
    p.take('object'); owner = p.ident()
    if owner in {n.rsplit('.', 1)[-1] for n in IMPORTABLE} | set(BUILTINS):
        raise ReviewRequired('Wrapper object shadows a trusted type/receiver')
    p.take('{'); methods = []
    while p.peek() != '}':
        p.take('def'); name = p.ident(); parameters = p.params()
        if name in {n.rsplit('.',1)[-1] for n in IMPORTABLE} | set(BUILTINS):
            raise ReviewRequired('Wrapper method shadows a trusted type/receiver')
        p.take(':'); returns = p.type_text(); p.take('=')
        block = p.peek() == '{'
        if block: p.take('{')
        call = p.dotted(); actual = []
        parentheses = p.peek() == '('
        if parentheses:
            p.take('(')
            while p.peek() != ')':
                actual.append(p.ident())
                if p.peek() != ',': break
                p.take(',')
            p.take(')')
        if block: p.take('}')
        if p.peek() == ';': p.take(';')
        if p.peek() not in ('def', '}'):
            raise ReviewRequired('Body must contain one direct forwarding expression')
        methods.append({'name': name, 'parameters': parameters, 'returns': returns,
                        'call': call, 'arguments': actual, 'call_parentheses': parentheses})
    p.take('}')
    if p.peek() is not None: raise ReviewRequired('Additional top-level source is unsupported')
    if not methods or len({m['name'] for m in methods}) != len(methods):
        raise ReviewRequired('Missing or overloaded wrapper definitions')
    return {'package': package, 'owner': owner, 'imports': sorted(imports), 'methods': methods}


def resolve(name, module):
    if name.startswith('_root_.'): name = name[7:]
    available = set(module['imports']) | {n for n in IMPORTABLE if n.rsplit('.', 1)[0] == module['package']}
    if name in IMPORTABLE: return name
    choices = {n for n in available if n.rsplit('.', 1)[-1] == name}
    if name == 'Point2D.Double' and 'java.awt.geom.Point2D' in available:
        choices.add('java.awt.geom.Point2D.Double')
    if len(choices) != 1: raise ReviewRequired('Unresolved or ambiguous name: ' + name)
    return next(iter(choices))


def type_descriptor(name, module):
    if name.startswith('Array[') and name.endswith(']'):
        inner = type_descriptor(name[6:-1], module)
        if inner == 'V': raise ReviewRequired('Array[Unit] is not supported')
        return '[' + inner
    if name.startswith('scala.') and name[6:] in BUILTINS: name = name[6:]
    if name in BUILTINS: return BUILTINS[name]
    full = resolve(name, module)
    if full not in NAMES: raise ReviewRequired('Unsupported parameter/return type')
    return NAMES[full]


def split_descriptor(value):
    found = re.fullmatch(r'\((.*)\)(.+)', value)
    if not found: raise ReviewRequired('Malformed JVM descriptor')
    params, result, offset = [], found[2], 0
    while offset < len(found[1]):
        match = re.match(r'\[*(?:[BCDFIJSZ]|L[^;]+;)', found[1][offset:])
        if not match: raise ReviewRequired('Unsupported JVM argument descriptor')
        params.append(match[0]); offset += len(match[0])
    return params, result


def canonical_signature(source, line, name):
    """Read only a pinned declaration header, including null defaults/property form."""
    text = '\n'.join(source.splitlines()[line - 1:line + 19]).lstrip()
    if not re.match(r'def\s+' + re.escape(name) + r'\b', text):
        raise ReviewRequired('Target line is not the exact public def header')
    depth = 0; end = None
    for index, char in enumerate(text):
        if char in '([': depth += 1
        elif char in ')]': depth -= 1
        elif char == '=' and depth == 0: end = index; break
    if end is None: raise ReviewRequired('Unsupported canonical declaration header')
    p = Parser(text[:end]); p.take('def')
    if p.ident() != name: raise ReviewRequired('Canonical name differs')
    parentheses = p.peek() == '('
    parameters = p.params() if parentheses else []
    returns = None
    if p.peek() == ':':
        p.take(':'); returns = p.type_text()
    if p.peek() is not None: raise ReviewRequired('Unsupported canonical signature')
    return {'parameters': parameters, 'parentheses': parentheses, 'returns': returns}


def certify(module, method, target, canonical_parameters, canonical_parentheses=True):
    """Certify an exact target and one-to-one unchanged argument forwarding."""
    formals = method['parameters']; names = [r['name'] for r in formals]
    arguments = method['arguments']; base, dot, called = method['call'].rpartition('.')
    if not dot or called != target['method']: raise ReviewRequired('Canonical method differs')
    canonical_types, result_type = split_descriptor(target['descriptor'])
    if len(canonical_types) != len(canonical_parameters): raise ReviewRequired('Source/descriptor arity differs')
    instance = not target['jvm_owner'].endswith('$')
    receiver_index = None
    if instance:
        if base not in names: raise ReviewRequired('Instance receiver must be a wrapper parameter')
        receiver_index = names.index(base)
        expected_receiver = 'L' + target['jvm_owner'].replace('.', '/') + ';'
        if type_descriptor(formals[receiver_index]['type'], module) != expected_receiver:
            raise ReviewRequired('Receiver parameter type differs from canonical owner')
    else:
        if base in names or resolve(base, module) != target['api'].rsplit('.', 1)[0]:
            raise ReviewRequired('Object receiver differs from canonical owner')
    used = arguments + ([base] if instance else [])
    if len(arguments) != len(canonical_types) or sorted(used) != sorted(names) or len(set(used)) != len(used):
        raise ReviewRequired('Arguments must forward every formal exactly once')
    for index, (name, expected) in enumerate(zip(arguments, canonical_types)):
        formal = formals[names.index(name)]
        if type_descriptor(formal['type'], module) != expected:
            raise ReviewRequired('Parameter type differs from canonical argument')
        if formal['default'] != canonical_parameters[index]['default']:
            raise ReviewRequired('Default argument differs from canonical source')
    if receiver_index is not None and formals[receiver_index]['default'] is not None:
        raise ReviewRequired('Receiver defaults are unsupported')
    if type_descriptor(method['returns'], module) != result_type:
        raise ReviewRequired('Return type differs from canonical descriptor')
    if method['call_parentheses'] != canonical_parentheses:
        raise ReviewRequired('Canonical property/argument-list syntax differs')
    # Nullary/property syntax comes from the pinned source declaration.
    full_owner = module['package'] + '.' + module['owner']
    descriptor = '(' + ''.join(type_descriptor(p['type'], module) for p in formals) + ')' + result_type
    return {'alias_name': method['name'], 'alias_owner': full_owner,
            'alias_event': full_owner + '$.' + method['name'] + descriptor,
            'canonical_api': target['api'],
            'canonical_event': target['jvm_owner'] + '.' + target['method'] + target['descriptor'],
            'parameters': formals, 'canonical_arguments': arguments, 'receiver_parameter': base if instance else None,
            'canonical_parameters': canonical_parameters,
            'claim': 'Supported syntax has one direct canonical call with unchanged one-to-one parameter forwarding; not an all-input behavior proof.'}


def alias_call(certificate, canonical_arguments, receiver=None):
    if len(canonical_arguments) != len(certificate['canonical_arguments']):
        raise ReviewRequired('Development case arity differs from wrapper')
    mapping = dict(zip(certificate['canonical_arguments'], canonical_arguments))
    if certificate['receiver_parameter']:
        if receiver is None: raise ReviewRequired('Missing development receiver')
        mapping[certificate['receiver_parameter']] = receiver
    return certificate['alias_owner'] + '.' + certificate['alias_name'] + '(' + ', '.join(
        mapping[p['name']] for p in certificate['parameters']) + ')'
