"""Recuperación local BM25, independiente de la interfaz y de modelos de IA."""
from collections import Counter
from dataclasses import dataclass
from math import log
import re
import unicodedata

STOPWORDS = set('a al de del el la las los un una unos unas y o en con por para que como cual cuales es se su sus me mi sobre'.split())


def tokens(text: str) -> list[str]:
    normalized = ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')
    return [word for word in re.findall(r'\w+', normalized) if word not in STOPWORDS]


@dataclass(frozen=True)
class Fragment:
    document_id: str
    filename: str
    location: str
    text: str


@dataclass(frozen=True)
class SearchResult:
    fragment: Fragment
    score: float


def split_text(document_id: str, filename: str, location: str, text: str) -> list[Fragment]:
    words = text.split()
    fragments = []
    for start in range(0, len(words), 180):
        fragments.append(Fragment(document_id, filename, location, ' '.join(words[start:start + 220])))
        if start + 220 >= len(words):
            break
    return fragments


class SearchIndex:
    """Un futuro agente puede invocar search y citar los fragmentos devueltos."""

    def __init__(self, fragments: list[Fragment]):
        self.fragments = fragments
        self.counts = [Counter(tokens(f.text)) for f in fragments]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.average = sum(self.lengths) / max(len(fragments), 1) or 1
        self.frequencies = Counter(term for counts in self.counts for term in counts)

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        terms = set(tokens(query))
        results = []
        size = len(self.fragments)
        for fragment, counts, length in zip(self.fragments, self.counts, self.lengths):
            score = 0.0
            for term in terms:
                frequency = counts[term]
                if frequency:
                    idf = log(1 + (size - self.frequencies[term] + 0.5) / (self.frequencies[term] + 0.5))
                    score += idf * frequency * 2.5 / (frequency + 1.5 * (0.25 + 0.75 * length / self.average))
            if score > 0:
                results.append(SearchResult(fragment, score))
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]
