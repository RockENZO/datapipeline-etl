"""Freeze observable query/status/projection behavior before handler refactoring."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import es_search_api as api


class SearchContractTests(unittest.TestCase):
    def test_reviewed_http_and_backend_contract(self):
        contract=json.loads((Path(__file__).parent/'fixtures/search_contract.json').read_text())
        self.assertEqual(contract['baseline_sha'],'9f7848be262c89b1538997a56409db3ac50482d9')
        self.assertEqual(len(contract['cases']),102)
        for case in contract['cases']:
            with self.subTest(path=case['path'],query=case['query']), \
                 patch.object(api.es,'search',return_value={'hits':{'hits':[contract['backend_hit']]}}) as backend:
                response=api.app.test_client().get(case['path'],query_string=case['query'])
                self.assertEqual(response.status_code,case['status'])
                self.assertEqual(response.get_json(),case['body'])
                calls=[{'args':list(c.args),'kwargs':c.kwargs} for c in backend.call_args_list]
                self.assertEqual(calls,case['backend_calls'])
                self.assertEqual(api.app.url_map.bind('localhost').match(case['path'])[0],case['endpoint'])

    def test_unknown_dataset_stays_not_found(self):
        with patch.object(api.es,'search') as backend:
            self.assertEqual(api.app.test_client().get('/es_search/not_registered?query=x').status_code,404)
            backend.assert_not_called()
