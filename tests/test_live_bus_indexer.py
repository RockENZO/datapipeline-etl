"""Refresh ordering must preserve the previous map on failed ingestion."""
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import live_bus_indexer as buses


class BusRefreshTests(unittest.TestCase):
    def refresh(self, bulk_error=None):
        events = []
        client = Mock()
        client.delete_by_query.side_effect = lambda **kwargs: events.append(('cleanup', kwargs))
        def bulk(*args, **kwargs):
            events.append(('bulk', None))
            if bulk_error:
                raise bulk_error
        with patch.object(buses, 'es', client), patch.object(buses, 'fetch_bus_data', return_value={'features': [{}]}), patch.object(buses, 'transform_bus_data', return_value=[{'_id': 'bus'}]), patch.object(buses.helpers, 'bulk', side_effect=bulk):
            before = datetime.utcnow()
            buses.index_bus_data()
            after = datetime.utcnow()
        return events, before, after

    def test_success_indexes_before_expiring_only_five_minute_old_data(self):
        events, before, after = self.refresh()
        self.assertEqual([e[0] for e in events], ['bulk', 'cleanup'])
        cutoff = datetime.fromisoformat(events[1][1]['body']['query']['range']['properties.last_updated']['lt'])
        self.assertGreaterEqual(cutoff, before - timedelta(minutes=5))
        self.assertLessEqual(cutoff, after - timedelta(minutes=5))

    def test_bulk_failure_preserves_existing_documents(self):
        for error in [RuntimeError('connection lost'), buses.helpers.BulkIndexError('partial batch failure', [])]:
            with self.subTest(error=type(error).__name__):
                events, _, _ = self.refresh(error)
                self.assertEqual([e[0] for e in events], ['bulk'])

    def test_empty_upstream_does_not_write_or_delete(self):
        with patch.object(buses, 'es') as client, patch.object(buses.helpers, 'bulk') as bulk, patch.object(buses, 'fetch_bus_data', return_value=None):
            buses.index_bus_data()
        bulk.assert_not_called()
        client.delete_by_query.assert_not_called()
