import unittest
from unittest.mock import patch, Mock
import pymupdf
from cloud_highlight import highlight
from cloud_store import CloudStore


class CloudTests(unittest.TestCase):
    def test_public_catalog_pagination(self):
        responses = []
        for data in [[{'id': 'a'}], []]:
            response = Mock()
            response.json.return_value = data
            responses.append(response)
        with patch('cloud_store.requests.get', side_effect=responses) as request:
            self.assertEqual(CloudStore('https://example.supabase.co', 'sb_publishable_test').rows(), [{'id': 'a'}])
            self.assertEqual(request.call_args.kwargs['params']['offset'], 1)

    def test_download_path_is_encoded(self):
        store = CloudStore('https://example.supabase.co', 'key')
        self.assertIn('manual%20uno.pdf', store.asset_url('vistas/manual uno.pdf'))
        with self.assertRaises(ValueError):
            store.asset_url('../secret')

    def test_highlight_does_not_modify_original(self):
        with pymupdf.open() as document:
            document.new_page().insert_text((50, 50), 'MF-100A')
            original = document.tobytes()
        marked, pages = highlight(original, 'MF100A')
        self.assertEqual(pages, [1])
        with pymupdf.open(stream=original, filetype='pdf') as document:
            self.assertEqual(list(document[0].annots() or []), [])
        with pymupdf.open(stream=marked, filetype='pdf') as document:
            self.assertEqual(len(list(document[0].annots())), 1)
