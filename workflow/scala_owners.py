"""Conservative lexical ownership for brace-bodied Scala source (not Scala 3 indentation).

This disambiguates discovered definition sites; it does not infer API visibility,
type correctness, overload equivalence or dynamic dispatch. Ambiguous headers
and unbalanced source fail closed instead of silently choosing a receiver.
"""
from dataclasses import dataclass
from functools import lru_cache
import re


@dataclass(frozen=True)
class Token:
    value: str
    line: int


def _tokens(source):
    tokens = []
    i, line, n = 0, 1, len(source)
    while i < n:
        if source[i].isspace():
            line += source[i] == '\n'
            i += 1
        elif source.startswith('//', i):
            end = source.find('\n', i)
            i = n if end < 0 else end
        elif source.startswith('/*', i):
            level = 1
            i += 2
            while i < n and level:
                if source.startswith('/*', i):
                    level += 1
                    i += 2
                elif source.startswith('*/', i):
                    level -= 1
                    i += 2
                else:
                    line += source[i] == '\n'
                    i += 1
            if level:
                raise ValueError('Unterminated Scala comment')
        elif source.startswith('"""', i):
            end = source.find('"""', i + 3)
            if end < 0:
                raise ValueError('Unterminated Scala triple-quoted string')
            end += 3
            # Scala permits quote characters immediately before the final
            # three delimiters, e.g. four trailing quotes for a quoted label.
            while end < n and source[end] == '"':
                end += 1
            line += source[i:end].count('\n')
            i = end
        elif source[i] == '"' or (source[i] == "'" and re.match(r"'(?:\\.|[^'\\\n])'", source[i:])):
            quote = source[i]
            i += 1
            while i < n and source[i] != quote:
                if source[i] == '\\':
                    i += 2
                else:
                    line += source[i] == '\n'
                    i += 1
            if i >= n:
                raise ValueError('Unterminated Scala literal')
            i += 1
        elif source[i] == '`':
            end = source.find('`', i + 1)
            if end < 0 or '\n' in source[i:end]:
                raise ValueError('Invalid Scala quoted identifier')
            tokens.append(Token(source[i + 1:end], line))
            i = end + 1
        else:
            match = re.match(r'[A-Za-z_$][\w$]*|[^\s]', source[i:])
            value = match.group()
            tokens.append(Token(value, line))
            i += len(value)
    return tokens


def _body_start(tokens, start):
    """First declaration body outside constructor/type parameters, or no body."""
    depths = {'(': 0, '[': 0}
    for index in range(start, len(tokens)):
        value = tokens[index].value
        # A bodyless declaration ends before an unrelated expression on the
        # next line. Do not steal that expression's lambda/initializer brace.
        if (not any(depths.values()) and index and tokens[index].line > tokens[index - 1].line
                and value not in ('{', 'extends', 'with', '(', '[', 'private', 'protected')
                and tokens[index - 1].value not in ('extends', 'with', '.', ',')):
            return None
        if value in depths:
            depths[value] += 1
        elif value == ')':
            depths['('] -= 1
        elif value == ']':
            depths['['] -= 1
        elif not any(depths.values()):
            if value == '{':
                return index
            if value in ('}', ';', 'class', 'object', 'trait', 'def', 'val', 'var', 'package'):
                return None
        if any(v < 0 for v in depths.values()):
            return None
    return None


@lru_cache(maxsize=128)
def definitions_with_owners(source):
    """Return direct named-owner member sites; local/anonymous scopes map to None."""
    tokens = _tokens(source)
    bodies = {}
    for index, token in enumerate(tokens[:-1]):
        if token.value not in ('class', 'object', 'trait'):
            continue
        if index and tokens[index - 1].value in ('.', 'classOf'):
            continue
        name = tokens[index + 1].value
        if not re.fullmatch(r'[A-Za-z_$][\w$]*', name):
            continue
        body = _body_start(tokens, index + 2)
        if body is not None:
            if body in bodies:
                raise ValueError('Ambiguous Scala owner header')
            bodies[body] = {'receiver': name, 'owner_kind': token.value, 'declaration_line': token.line}
    stack, result = [], {}
    for index, token in enumerate(tokens):
        if token.value == '{':
            owner = bodies.get(index)
            # A named class inside a method/anonymous block is local as well;
            # its methods are not members of the enclosing receiver's API.
            if owner and any(item is None for item in stack):
                owner = None
            if owner:
                parents = [item['receiver'] for item in stack if item]
                owner = {**owner, 'owner_path': '.'.join(parents + [owner['receiver']])}
            stack.append(owner)
        elif token.value == '}':
            if not stack:
                raise ValueError('Unbalanced Scala source braces')
            stack.pop()
        elif token.value == 'def' and index + 1 < len(tokens):
            owner = stack[-1] if stack else None
            key = (token.line, tokens[index + 1].value)
            if key in result:
                raise ValueError('Multiple same-line definition sites require explicit resolution')
            result[key] = dict(owner) if owner else None
    if stack:
        raise ValueError('Unbalanced Scala source braces')
    return result


def owner_at_line(source: str, line: int, name: str | None = None) -> dict:
    """Require one definition at a one-based source line and return its lexical owner."""
    if type(line) is not int or line < 1:
        raise ValueError('Source line must be a positive integer')
    rows = [value for (where, method), value in definitions_with_owners(source).items()
            if where == line and (name is None or method == name)]
    if len(rows) != 1 or rows[0] is None:
        raise ValueError('Definition has no unique brace-bodied Scala receiver')
    return dict(rows[0])
