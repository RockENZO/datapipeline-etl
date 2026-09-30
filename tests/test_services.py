import unittest
from unittest.mock import Mock, patch
import GNAF_search_api as gnaf
import web_map.app as web
import es_index_multi_docker as indexer
from celery.exceptions import TimeoutError

class ServiceTests(unittest.TestCase):
    def test_search_validation(self):
        client = gnaf.app.test_client()
        for url in ('/search', '/search?address=street&state=invalid'):
            with patch.object(gnaf.search_task, 'apply_async') as submit:
                self.assertEqual(client.get(url).status_code, 400)
                submit.assert_not_called()

    def test_sync_and_async_search(self):
        task = Mock(id='abc')
        task.get.return_value = [{'latitude': -33.8}]
        with patch.object(gnaf.search_task, 'apply_async', return_value=task) as submit:
            client = gnaf.app.test_client()
            self.assertEqual(client.get('/search?address=95%20Balo%20Street&state=nsw').json, task.get.return_value)
            submit.assert_called_with(args=['95 Balo Street', 'NSW'])
            response = client.get('/search?address=street&async=true')
            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.headers['Location'], '/results/abc')

    def test_timeout_and_broker_failure(self):
        task = Mock()
        task.get.side_effect = TimeoutError()
        client = gnaf.app.test_client()
        with patch.object(gnaf.search_task, 'apply_async', return_value=task):
            self.assertEqual(client.get('/search?address=street').status_code, 504)
        with patch.object(gnaf.search_task, 'apply_async', side_effect=RuntimeError('secret')):
            response = client.get('/search?address=street')
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('secret', response.get_data(as_text=True))

    def test_result_backend_failure(self):
        with patch.object(gnaf.search_task, 'AsyncResult', side_effect=RuntimeError()):
            self.assertEqual(gnaf.app.test_client().get('/results/abc').status_code, 503)

    def test_health_dependency(self):
        with patch.object(web.es, 'ping', return_value=False):
            self.assertEqual(web.app.test_client().get('/health').status_code, 503)
        with patch.object(web.es, 'ping', return_value=True):
            self.assertEqual(web.app.test_client().get('/health').status_code, 200)

    def test_map_input_and_geojson(self):
        client = web.app.test_client()
        for query in ('size=no', 'size=0', 'size=1001', 'bbox=nan,0,1,2', 'bbox=2,0,1,2'):
            self.assertEqual(client.get('/api/search/stairs?' + query).status_code, 400)
        result = {'hits': {'total': {'value': 1}, 'hits': [{'_source': {'geometry': {'lat': -33, 'lon': 151}, 'properties': {'Name': 'Steps'}}}]}}
        with patch.object(web.es, 'search', return_value=result):
            response = client.get('/api/search/stairs').json
            self.assertEqual(response['data']['features'][0]['geometry']['coordinates'], [151, -33])

    def test_indexing_failure_is_fatal(self):
        with patch.object(indexer, 'es', Mock()):
            with self.assertRaises(FileNotFoundError):
                indexer.index_dataset('stairs', '/nonexistent/file')
        with self.assertRaises(FileNotFoundError):
            indexer.index_all_datasets()

if __name__ == '__main__':
    unittest.main()

class DemoTests(unittest.TestCase):
    def test_demo_generation_refuses_overwrite(self):
        import tempfile
        from pathlib import Path
        from make_demo_data import generate, FILES
        with tempfile.TemporaryDirectory() as temporary:
            generate(Path(temporary))
            self.assertEqual(len(list(Path(temporary).iterdir())), len(FILES))
            with self.assertRaises(FileExistsError):
                generate(Path(temporary))
