"""A truncated live feed must never become a successful refresh."""
import unittest
from unittest.mock import Mock, patch

import live_bus_indexer as buses


def response(data):
    result = Mock()
    result.json.return_value = data
    return result


def batch(*ids):
    return {'spatialReference': {'wkid': 4326}, 'features': [
        {'attributes': {'hashId': i}, 'geometry': {'x': 151, 'y': -33}}
        for i in ids]}


class CompleteBusFetchTests(unittest.TestCase):
    def test_fetches_all_ids_beyond_the_old_1000_limit(self):
        ids = list(range(1001))
        pages = [batch(*ids[i:i+250]) for i in range(0, len(ids), 250)]
        with patch.object(buses.requests, 'get', side_effect=[response({'objectIdFieldName': 'hashId', 'objectIds': ids})] + [response(p) for p in pages]) as get:
            data = buses.fetch_bus_data()
        self.assertEqual(len(data['features']), 1001)
        self.assertEqual(data['spatialReference'], {'wkid': 4326})
        self.assertEqual(get.call_count, 6)
        self.assertTrue(get.call_args_list[0].kwargs['params']['returnIdsOnly'])
        requested = [int(i) for c in get.call_args_list[1:] for i in c.kwargs['params']['where'].removeprefix('hashId IN (').removesuffix(')').split(',')]
        self.assertEqual(requested, ids)
        self.assertTrue(all(c.kwargs['params']['outSR'] == 4326 for c in get.call_args_list[1:]))

    def test_rejects_incomplete_or_untrustworthy_batches(self):
        for bad in [batch(1), batch(1, 1), batch(1, 3),
                    dict(batch(1, 2), exceededTransferLimit=True),
                    {'error': {'message': 'API error'}}, {'features': 'invalid'},
                    {'features': [None]}, dict(batch(1, 2), spatialReference={'wkid': 3857})]:
            with self.subTest(bad=bad), patch.object(buses.requests, 'get', side_effect=[response({'objectIdFieldName': 'hashId', 'objectIds': [1, 2]}), response(bad)]):
                self.assertIsNone(buses.fetch_bus_data())

    def test_second_batch_failure_does_not_write_or_delete(self):
        ids = list(range(251))
        replies = [response({'objectIdFieldName': 'hashId', 'objectIds': ids}),
                   response(batch(*ids[:250])), buses.requests.Timeout('late batch')]
        with patch.object(buses.requests, 'get', side_effect=replies), patch.object(buses.helpers, 'bulk') as bulk, patch.object(buses, 'es') as client:
            buses.index_bus_data()
        bulk.assert_not_called()
        client.delete_by_query.assert_not_called()

    def test_rejects_malformed_or_oversized_id_enumeration(self):
        for ids in [None, '1,2', [True], [1, 1], ['1'], list(range(10001))]:
            with self.subTest(ids=str(ids)[:50]), patch.object(buses.requests, 'get', return_value=response({'objectIdFieldName': 'hashId', 'objectIds': ids})) as get:
                self.assertIsNone(buses.fetch_bus_data())
                self.assertEqual(get.call_count, 1)

    def test_empty_feed_is_valid_but_never_deletes_existing_data(self):
        with patch.object(buses.requests, 'get', return_value=response({'objectIdFieldName': 'hashId', 'objectIds': []})), patch.object(buses.helpers, 'bulk') as bulk, patch.object(buses, 'es') as client:
            buses.index_bus_data()
        bulk.assert_not_called()
        client.delete_by_query.assert_not_called()
