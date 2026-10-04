"""Conservative field-aware checks. Ambiguous rewrites enter manual review."""
from collections import Counter
import re

CYRILLIC=re.compile(r'[А-Яа-яЁё]')
GENDER=re.compile(r'\$[gG]([^;]*):([^;]*);')
GAME=re.compile(r'\$[nNrRcCbB]|\$\d+[A-Za-z]*|\$[A-Za-z]+')
LINK=re.compile(r'\|H([^|]+)\|h')
PRINTF=re.compile(r'%(?:(\d+)\$)?[-+ #0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:hh|ll|[hljztL])?([diouxXfFeEgGaAcspn%])')


def game_signature(text, female=False):
    # Added grammatical gender branches are allowed only if EACH branch keeps
    # the same substitutions. Nested/unterminated branches are rejected.
    expanded=GENDER.sub(lambda m:m[2] if female else m[1],text)
    if re.search(r'\$[gG]',expanded):raise ValueError('unsupported gender structure')
    tokens=GAME.findall(expanded)
    allowed=re.compile(r'\$[nNrRcCbB]|\$\d+[A-Za-z]*')
    if any(not allowed.fullmatch(t) for t in tokens):raise ValueError('unknown game substitution')
    return Counter('$b' if t in ('$b','$B') else t for t in tokens)


def quality(source, translation, limit=None, mode='game'):
    if not isinstance(translation,str) or not translation.strip():return 'empty donor text'
    if not isinstance(source,str) or not source.strip():return 'empty English source'
    if translation==source:return 'donor is English copy'
    if not CYRILLIC.search(translation):return 'Russian text not confirmed'
    if '\ufffd' in translation or any(0xD800<=ord(c)<=0xDFFF for c in translation):return 'damaged Unicode'
    if any(ord(c)<32 and c not in '\n\r\t' for c in translation):return 'forbidden control character'
    if any(ord(c)>0xFFFF for c in translation):return 'non-BMP text unsupported by utf8mb3 target'
    if re.search(r'(?:TODO|FIXME|UNTRANSLATED|не переведено|нет перевода|\[placeholder\])',translation,re.I):return 'placeholder text'
    if re.search(r'\\[nr]|&(?:quot|apos|lt|gt);',translation):return 'possible double escaping'
    if source.rstrip().endswith(('.', '!', '?', ';')) and not translation.rstrip().endswith(('.', '!', '?', ';')):return 'possible truncated sentence'
    if limit:
        unit,size=limit
        length=len(translation) if unit=='characters' else len(translation.encode('utf8'))
        if length>size:return 'field length exceeded'
    try:
        if mode=='game':
            for female in (False,True):
                if game_signature(source,female)!=game_signature(translation,female):return 'game substitutions differ in gender branch'
        elif mode=='printf':
            if [m.group() for m in PRINTF.finditer(source)]!=[m.group() for m in PRINTF.finditer(translation)] or any(m[2]=='n' for m in PRINTF.finditer(translation)):return 'printf arguments differ'
        elif mode=='fmt':
            if Counter(re.findall(r'(?<!\{)\{[^{}]*\}(?!\})',source))!=Counter(re.findall(r'(?<!\{)\{[^{}]*\}(?!\})',translation)):return 'fmt arguments differ'
        else:return 'unknown text subsystem'
    except ValueError as error:return str(error)
    # Link destinations and colors cannot be changed by translation.
    for pattern in (LINK,re.compile(r'\|T([^|]+)\|t'),re.compile(r'\|c([0-9a-fA-F]{8})')):
        if Counter(pattern.findall(source))!=Counter(pattern.findall(translation)):return 'client link, texture or color identity differs'
    for text in (source,translation):
        if text.count('|H')!=len(LINK.findall(text)) or text.count('|h')!=2*len(LINK.findall(text)):return 'unbalanced client hyperlink'
        if text.count('|r')!=len(re.findall(r'\|c[0-9a-fA-F]{8}',text)):return 'unbalanced color marker'
        if text.count('|T')!=len(re.findall(r'\|T[^|]+\|t',text)) or text.count('|t')!=text.count('|T'):return 'unbalanced texture marker'
    return None


def csv_cell(value):
    text='' if value is None else str(value)
    if text.lstrip('\ufeff \t\r\n').startswith(('=','+','-','@')) or text.startswith(('\t','\r','\n')):
        return "'"+text
    return text
