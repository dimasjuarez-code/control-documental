from pathlib import Path
from documental.search import tokens
from documental.precision import code_patterns, remaining_query


def normalized_words(text):
    return {word[:-1] if len(word) > 4 and word.endswith('s') else word for word in tokens(text)}


def filter_documents(documents, query='', folder='Todas', file_format='Todos'):
    codes = code_patterns(query)
    terms = normalized_words(remaining_query(query))
    matches = []
    for identity, document in documents.items():
        name = document['name']
        if folder != 'Todas' and Path(name).parent.as_posix() != folder:
            continue
        if file_format != 'Todos' and Path(name).suffix.lower().lstrip('.').upper() != file_format:
            continue
        document_text = name + '\n' + '\n'.join(fragment.text for fragment in document['fragments'])
        if not all(pattern.search(document_text) for pattern in codes):
            continue
        title_words = normalized_words(name)
        fragment_words = [(fragment, normalized_words(fragment.text)) for fragment in document['fragments']]
        words = title_words | {word for _, group in fragment_words for word in group}
        # Todas las palabras deben coincidir; ampliar la consulta reduce resultados.
        if not all(any(word.startswith(term) for word in words) for term in terms):
            continue
        previews = sorted(fragment_words, key=lambda pair: sum(any(word.startswith(term) for word in pair[1]) for term in terms), reverse=True)
        matches.append((identity, document, [fragment for fragment, _ in previews]))
    def relevance(match):
        name_words = normalized_words(Path(match[1]['name']).stem)
        title_hits = sum(any(word.startswith(term) for word in name_words) for term in terms)
        body_hits = sum(any(word.startswith(term) for word in normalized_words(fragment.text)) for fragment in match[2][:3] for term in terms)
        return (-title_hits, -body_hits, match[1]['name'].lower())
    return sorted(matches, key=relevance)
