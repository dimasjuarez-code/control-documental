import re
import pymupdf
from documental.precision import canonical, code_patterns, remaining_query
from documental.search import tokens


def highlight(data, query):
    patterns = code_patterns(query)
    patterns += [re.compile(r'(?<!\w)' + re.escape(canonical(word[:-1] if len(word) > 4 and word.endswith('s') else word)) + r'\w*', re.I) for word in tokens(remaining_query(query))]
    hits = []
    with pymupdf.open(stream=data, filetype='pdf') as document:
        for number, page in enumerate(document, 1):
            text = ''
            ranges = []
            for word in page.get_text('words', sort=True):
                start = len(text)
                text += canonical(word[4]) + ' '
                ranges.append((start, len(text) - 1, word[:4]))
            boxes = set()
            for pattern in patterns:
                for match in pattern.finditer(text):
                    for start, end, rect in ranges:
                        if start < match.end() and end > match.start():
                            boxes.add(tuple(rect))
            if boxes:
                mark = page.add_highlight_annot([pymupdf.Rect(box) for box in sorted(boxes)])
                mark.set_colors(stroke=(1, 0.85, 0))
                mark.update()
                hits.append(number)
        return document.tobytes(), hits
