"""Read a documented MySQL dump subset without executing any SQL.

Lexical boundaries respect quotes, escapes, doubled quotes and comments. Data
statements outside the selected tables are deliberately not decoded. Unknown
statements affecting a selected table fail closed. Versioned dump SET comments
are metadata, never executed. No eval/exec and no database connection.
"""
from dataclasses import dataclass, field
import gzip
import hashlib
from pathlib import Path
import re


class DumpError(ValueError):
    pass


TOKEN = re.compile(r"'(?:\\.|''|[^'\\])*'|\"(?:\\.|\"\"|[^\"\\])*\"|`(?:``|[^`])*`|/\*.*?\*/|--(?=\s)[^\n]*|\#[^\n]*|;|['\"`]|/\*", re.S)
VALUE = re.compile(r"\s*(?:('(?:\\.|''|[^'\\])*'|\"(?:\\.|\"\"|[^\"\\])*\")|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|(NULL)\b|([(),;]))", re.S|re.I)


def statements(stream):
    pending, pieces = '', []
    while True:
        chunk = stream.read(1024*1024)
        final = not chunk
        pending += chunk
        consumed = 0
        incomplete = False
        for match in TOKEN.finditer(pending):
            token = match.group()
            if not final and match.end() > len(pending)-2:
                pieces.append(pending[consumed:match.start()])
                pending = pending[match.start():]
                incomplete = True
                break
            if token in ("'",'"','`','/*'):
                if final:
                    raise DumpError('Unterminated quoted value, identifier or comment')
                pieces.append(pending[consumed:match.start()])
                pending = pending[match.start():]
                incomplete = True
                break
            if token == ';':
                pieces.append(pending[consumed:match.end()])
                yield ''.join(pieces)
                pieces = []
                consumed = match.end()
        if not incomplete:
            end = len(pending) if final else max(consumed,len(pending)-2)
            pieces.append(pending[consumed:end])
            pending = pending[end:]
        if final:
            rest = strip_comments(''.join(pieces)).strip()
            if rest:
                raise DumpError('Statement without terminating semicolon')
            return


def strip_comments(text):
    return TOKEN.sub(lambda m: ' ' if m.group().startswith(('/*','--','#')) else m.group(),text)


def literal(token):
    if token.upper() == 'NULL':
        return None
    if token[0] not in ("'",'"'):
        return token  # Numeric values remain exact SQL decimal strings.
    quote = token[0]
    text, out, i = token[1:-1], [], 0
    escape = {'0':'\0','b':'\b','n':'\n','r':'\r','t':'\t','Z':'\x1a'}
    while i < len(text):
        if text[i] == '\\':
            i += 1
            char = text[i]
            out.append('\\'+char if char in '%_' else escape.get(char,char))
        elif text[i:i+2] == quote*2:
            out.append(quote); i += 1
        else:
            out.append(text[i])
        i += 1
    return ''.join(out)


def value_tokens(text):
    pos = 0
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():pos += 1
        if pos == len(text):
            return
        match = VALUE.match(text,pos)
        if not match:
            raise DumpError('Unsupported value/expression near '+repr(text[pos:pos+80]))
        pos = match.end()
        token = next(group for group in match.groups() if group is not None)
        yield token


def value_rows(text):
    tokens = iter(value_tokens(text))
    next_token = next(tokens,None)
    while next_token is not None:
        if next_token != '(':
            raise DumpError('Expected VALUES row, got '+repr(next_token))
        row, want_value = [], True
        for token in tokens:
            if want_value:
                if token in ('(',')',',',';'):
                    raise DumpError('Expected literal value')
                row.append(literal(token)); want_value=False
            elif token == ',':
                want_value=True
            elif token == ')':
                break
            else:
                raise DumpError('Expected comma or row end')
        else:
            raise DumpError('Unterminated VALUES row')
        yield row
        next_token = next(tokens,None)
        if next_token == ';':
            if next(tokens,None) is not None:
                raise DumpError('Trailing INSERT syntax')
            return
        if next_token != ',':
            raise DumpError('Expected comma between rows')
        next_token = next(tokens,None)
    raise DumpError('Missing INSERT terminator')


@dataclass
class Table:
    columns: list
    primary: list
    definition: str
    rows: dict = field(default_factory=dict)
    duplicates: set = field(default_factory=set)
    limits: dict = field(default_factory=dict)
    defaults: dict = field(default_factory=dict)


def schema(statement):
    name=re.match(r'CREATE TABLE(?: IF NOT EXISTS)?\s+`([^`]+)`\s*\(',statement,re.I)
    if not name:
        raise DumpError('Unsupported CREATE TABLE header')
    body=statement[name.end():]
    cols=re.findall(r'(?:^|\n)\s*`([^`]+)`\s+([^\n]+)',body)
    if not cols:
        raise DumpError('CREATE columns must be on separate lines')
    pk=re.search(r'PRIMARY KEY\s*\(([^)]+)\)',body,re.I)
    primary=re.findall(r'`([^`]+)`',pk[1]) if pk else []
    if not primary:
        raise DumpError('Missing primary key for '+name[1])
    limits={};defaults={}
    for column,spec in cols:
        default=re.search(r"\bDEFAULT\s+('(?:\\.|''|[^'\\])*'|NULL|-?\d+)",spec,re.I)
        if default:defaults[column]=literal(default[1])
        elif 'NOT NULL' not in spec.upper():defaults[column]=None
        size=re.match(r'(?:var)?char\((\d+)\)',spec,re.I)
        if size:limits[column]=('characters',int(size[1]))
        else:
            kind=re.match(r'[A-Za-z]+',spec)[0].lower()
            if kind in {'tinytext','text','mediumtext','longtext'}:
                limits[column]=('bytes',{'tinytext':255,'text':65535,'mediumtext':16777215,'longtext':4294967295}[kind])
    return name[1],Table([c for c,_ in cols],primary,statement,limits=limits,defaults=defaults)


def read_dump(path, selected, expected_sha=None, projection=None):
    path=Path(path)
    with path.open('rb') as raw:
        sha=hashlib.file_digest(raw,'sha256').hexdigest()
    if expected_sha and sha != expected_sha:
        raise DumpError(f'{path.name}: SHA256 mismatch ({sha})')
    tables={}
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rt',encoding='utf8',errors='strict',newline='') as stream:
        for number,raw in enumerate(statements(stream),1):
            text=strip_comments(raw).strip()
            if not text:continue
            reset=re.fullmatch(r'DELETE FROM `([^`]+)`;',text,re.I)
            if reset and reset[1] in selected:
                if reset[1] not in tables or tables[reset[1]].rows:
                    raise DumpError('Only an empty-table dump preamble DELETE is supported')
                continue  # HeidiSQL data preamble, not executed on any database.
            match=re.match(r'(?:CREATE TABLE(?: IF NOT EXISTS)?|INSERT(?: IGNORE)? INTO|REPLACE(?: INTO)?|DROP TABLE(?: IF EXISTS)?|LOCK TABLES|ALTER TABLE)\s+`([^`]+)`',text,re.I)
            table=match[1] if match else None
            if table not in selected and re.match(r'(?:INSERT|REPLACE|ALTER|CREATE)\b',text,re.I):
                # Qualified/unquoted headers must not silently disappear as an
                # unselected table. Inspect only the header, not literal content
                # or column names of an unrelated table.
                header=re.split(r'\bVALUES\b|\(',text,maxsplit=1,flags=re.I)[0]
                if any(re.search(r'(?<![A-Za-z0-9_])'+re.escape(t)+r'(?![A-Za-z0-9_])',header) for t in selected):
                    raise DumpError(f'Statement {number}: unsupported selected-table header')
            if table not in selected:
                # These are analysis inputs, not executable imports. No statement
                # outside the selected allowlist can contribute data or a patch.
                if re.match(r'(?:UPDATE|DELETE)\b',text,re.I) and any(re.search(r'\b'+re.escape(t)+r'\b',text) for t in selected):
                    raise DumpError(f'Statement {number}: UPDATE/DELETE in selected dump table')
                continue
            try:
                if text.upper().startswith('CREATE TABLE'):
                    name,definition=schema(text)
                    if name in tables:raise DumpError('Duplicate CREATE TABLE')
                    tables[name]=definition
                elif re.match(r'(?:INSERT|REPLACE)\b',text,re.I):
                    if table not in tables:raise DumpError('INSERT before schema')
                    header=re.match(r'(?:INSERT(?: IGNORE)? INTO|REPLACE(?: INTO)?)\s+`[^`]+`\s*(\([^)]*\))?\s+VALUES\s*',text,re.I)
                    if not header:raise DumpError('Only literal VALUES imports are supported')
                    definition=tables[table]
                    columns=re.findall(r'`([^`]+)`',header[1]) if header[1] else definition.columns
                    if len(set(columns))!=len(columns) or not set(columns)<=set(definition.columns):raise DumpError('Invalid INSERT column list')
                    if not set(definition.primary)<=set(columns):raise DumpError('Missing key columns')
                    for values in value_rows(text[header.end():]):
                        if len(values)!=len(columns):raise DumpError('Column/value count mismatch')
                        row=dict(zip(columns,values))
                        locale=next((row[k] for k in ('locale','Locale') if k in row),None)
                        if locale is not None and locale != 'ruRU' and any(k.lower()=='locale' for k in definition.primary):continue
                        key=tuple(row[c] for c in definition.primary)
                        if any(k is None for k in key):raise DumpError('NULL primary key')
                        if key in definition.rows:definition.duplicates.add(key)
                        if projection and table in projection:
                            row={k:v for k,v in row.items() if k in projection[table] or k in definition.primary}
                        definition.rows[key]=row
                elif re.match(r'(?:DROP TABLE|LOCK TABLES)\b',text,re.I):
                    continue  # Standard dump preamble; deliberately not executed.
                elif re.fullmatch(r'ALTER TABLE `[^`]+` (?:DISABLE|ENABLE) KEYS;',text,re.I):
                    continue
                else:
                    raise DumpError('Unsupported selected-table statement')
            except DumpError as error:
                raise DumpError(f'{path.name}, statement {number}, table {table}: {error}') from error
    return tables,sha
