import re
import unicodedata

CODE = re.compile(r'\b([A-Za-z]{1,12})\s*[-‐‑‒–—−]?\s*(\d+[A-Za-z]?)\b')


def canonical(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')


def code_patterns(query):
    return [re.compile(r'(?<!\w)' + re.escape(match[1]) + r'\s*[-‐‑‒–—−]?\s*' + re.escape(match[2]) + r'(?!\w)', re.IGNORECASE) for match in CODE.finditer(query)]


def remaining_query(query):
    return CODE.sub(' ', query)
