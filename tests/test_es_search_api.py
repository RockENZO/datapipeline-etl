"""Public search contract; backend details must stay off the HTTP boundary."""
import runpy
import unittest
from unittest.mock import patch
from flask import Flask
import es_search_api as search


class SearchApiTests(unittest.TestCase):
    def urls(self):
        for rule in search.app.url_map.iter_rules():
            if rule.rule.startswith('/es_search/'):
                yield rule.rule

    def test_all_backend_failures_are_redacted(self):
        secret = 'http://private-user:example-token@internal-es:9200/customer-record'
        client = search.app.test_client()
        for url in self.urls():
            with self.subTest(url=url), patch.object(search.es, 'search', side_effect=RuntimeError(secret)):
                response = client.get(url, query_string={'query': 'test', 'field': 'Name'})
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.json, {'error': 'Search service unavailable'})
                self.assertNotIn(secret, response.get_data(as_text=True))

    def test_hit_and_geometry_response_shapes_are_preserved(self):
        hit = {'_id': 'fixture', '_source': {'geometry': {'type': 'Point', 'coordinates': [151, -33]}}}
        for url in self.urls():
            with self.subTest(url=url), patch.object(search.es, 'search', return_value={'hits': {'hits': [hit]}}):
                response = search.app.test_client().get(url, query_string={'query': 'test', 'field': 'Name'})
                self.assertEqual(response.status_code, 200)
                expected = [hit['_source']['geometry']] if url in ('/es_search/lga_ndd_total', '/es_search/dzn') else [hit]
                self.assertEqual(response.json, expected)

    def test_invalid_requests_do_not_reach_backend(self):
        optional = {'/es_search/ucl', '/es_search/ticket_parking_rates', '/es_search/lga_ndd_total', '/es_search/dzn'}
        for url in self.urls():
            if url in optional:
                continue
            with self.subTest(url=url), patch.object(search.es, 'search') as backend:
                self.assertEqual(search.app.test_client().get(url).status_code, 400)
                backend.assert_not_called()

    def test_direct_entry_point_never_enables_debugger(self):
        # Execute the real module entry point without opening a network socket.
        with patch.object(Flask, 'run') as run:
            runpy.run_module('es_search_api', run_name='__main__')
        self.assertFalse(run.call_args.kwargs.get('debug', False))
        self.assertEqual(run.call_args.kwargs['port'], 5003)


if __name__ == '__main__':
    unittest.main()
