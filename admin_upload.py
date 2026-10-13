"""Proceso administrativo. Ejecutar en un servidor, nunca desde la web pública."""
import argparse
from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import quote

import requests
import pymupdf
import numpy as np

from cloud_store import CloudStore, BUCKET
from documental.search import split_text


def word_to_pdf(source, workspace):
    executable = shutil.which('libreoffice') or shutil.which('soffice')
    if not executable:
        raise RuntimeError('La administración necesita LibreOffice instalado en el servidor.')
    profile = (workspace / 'profile').as_uri()
    subprocess.run([executable, f'-env:UserInstallation={profile}', '--headless', '--convert-to', 'pdf', '--outdir', str(workspace), str(source.resolve())], check=True, timeout=120, capture_output=True)
    output = workspace / (source.stem + '.pdf')
    if not output.is_file():
        raise RuntimeError('No se pudo convertir el Word.')
    return output.read_bytes()


def prepare(source):
    original = source.read_bytes()
    with tempfile.TemporaryDirectory() as directory:
        if source.suffix.lower() == '.pdf':
            pdf_bytes = original
        elif source.suffix.lower() == '.docx':
            pdf_bytes = word_to_pdf(source, Path(directory))
        else:
            content = original.decode('utf-8-sig', errors='replace')
            with pymupdf.open() as document:
                for start in range(0, len(content.splitlines()) or 1, 45):
                    document.new_page().insert_textbox(pymupdf.Rect(45, 45, 550, 790), '\n'.join(content.splitlines()[start:start + 45]), fontsize=9)
                pdf_bytes = document.tobytes()
    fragments = []
    engine = None
    identity = sha256(original).hexdigest()
    with pymupdf.open(stream=pdf_bytes, filetype='pdf') as document:
        for number, page in enumerate(document, 1):
            text = page.get_text()
            if len(''.join(text.split())) < 200 or any(pymupdf.Rect(info['bbox']).get_area() > page.rect.get_area() * 0.5 for info in page.get_image_info()):
                if engine is None:
                    from rapidocr_onnxruntime import RapidOCR
                    engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)
                pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
                array = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, pixmap.n)
                lines, _ = engine(array, use_cls=False)
                for points, recognized, confidence, *_ in lines or []:
                    if confidence < 0.45:
                        continue
                    text += '\n' + recognized
                    rect = pymupdf.Rect(min(p[0] for p in points) / 2, min(p[1] for p in points) / 2, max(p[0] for p in points) / 2, max(p[1] for p in points) / 2)
                    for factor in [0.7, 0.5, 0.35, 0.2]:
                        # Capa invisible para buscar y resaltar; el original se almacena aparte.
                        if page.insert_textbox(rect, recognized, fontsize=max(rect.height * factor, 2), render_mode=3) >= 0:
                            break
            fragments.extend({'location': f'Página {number}', 'text': fragment.text} for fragment in split_text(identity, source.name, f'Página {number}', text))
        return identity, original, document.tobytes(), fragments


def main():
    parser = argparse.ArgumentParser(description='Publicar documentos en Supabase desde administración')
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    key = os.environ['SUPABASE_ADMIN_KEY']
    store = CloudStore(os.environ['SUPABASE_URL'], key)
    for source in sorted(args.folder.rglob('*')):
        if not source.is_file() or source.suffix.lower() not in {'.pdf', '.docx', '.txt'}:
            continue
        identity, original, preview, fragments = prepare(source)
        original_path = f'originales/{identity}{source.suffix.lower()}'
        preview_path = f'vistas/{identity}.pdf'
        for path, data, mime in [(original_path, original, 'application/octet-stream'), (preview_path, preview, 'application/pdf')]:
            response = requests.post(store.url + '/storage/v1/object/' + BUCKET + '/' + quote(path, safe='/'), headers={**store.headers, 'Content-Type': mime, 'x-upsert': 'true'}, data=data, timeout=120)
            response.raise_for_status()
        response = requests.post(store.url + '/rest/v1/documental_documents', headers={**store.headers, 'Prefer': 'resolution=merge-duplicates'}, json={'id': identity, 'name': source.relative_to(args.folder).as_posix(), 'original_path': original_path, 'preview_path': preview_path, 'fragments': fragments, 'published': True}, timeout=60)
        response.raise_for_status()
        print('Publicado:', source.name)


if __name__ == '__main__':
    main()
