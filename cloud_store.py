from urllib.parse import quote, urlparse
import requests

BUCKET = 'documental-public'


class CloudStore:
    def __init__(self, url, key):
        parsed = urlparse(url)
        if parsed.scheme != 'https' or not parsed.hostname:
            raise ValueError('SUPABASE_URL debe ser una dirección HTTPS válida.')
        self.url = url.rstrip('/')
        self.headers = {'apikey': key}
        if key.startswith('eyJ'):
            self.headers['Authorization'] = f'Bearer {key}'

    def rows(self):
        result = []
        offset = 0
        while True:
            response = requests.get(self.url + '/rest/v1/documental_documents', headers=self.headers,
                params={'select': '*', 'published': 'eq.true', 'order': 'name.asc,id.asc', 'offset': offset, 'limit': 100}, timeout=30)
            response.raise_for_status()
            page = response.json()
            result.extend(page)
            if not page:
                return result
            offset += len(page)

    def asset_url(self, path):
        if not path or path.startswith('/') or '..' in path.split('/'):
            raise ValueError('Ruta de documento inválida.')
        return self.url + '/storage/v1/object/public/' + BUCKET + '/' + quote(path, safe='/')

    def read(self, path):
        response = requests.get(self.asset_url(path), timeout=60)
        response.raise_for_status()
        return response.content
