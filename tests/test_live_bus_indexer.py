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

class BusCoordinateTests(unittest.TestCase):
    def feature(self, lat=0, lon=0, identity='bus'):
        props = {'vehicle.position.latitude': lat, 'vehicle.position.longitude': lon}
        if identity is not None:
            props['vehicle.vehicle.id'] = identity
        return {'properties': props}

    def test_zero_coordinates_and_zero_ids_are_valid(self):
        actions = buses.transform_bus_data({'features': [self.feature(identity=0)]})
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['_id'], '0')
        self.assertEqual(actions[0]['_source']['geometry'], {'lat': 0., 'lon': 0.})

    def test_invalid_coordinates_are_not_sent_to_elasticsearch(self):
        bad = [(91, 151), (-91, 151), (-33, 181), (-33, -181), (float('nan'), 151), (-33, float('inf')), (True, 151)]
        for lat, lon in bad:
            with self.subTest(lat=lat, lon=lon):
                self.assertEqual(buses.transform_bus_data({'features': [self.feature(lat, lon)]}), [])

    def test_missing_identity_does_not_get_an_unstable_process_hash(self):
        self.assertEqual(buses.transform_bus_data({'features': [self.feature(-33, 151, None)]}), [])

    def test_geojson_and_arcgis_point_fallback(self):
        for geometry in [{'type': 'Point', 'coordinates': [151, 0]}, {'x': 151, 'y': 0}]:
            with self.subTest(geometry=geometry):
                feature = {'attributes': {'id': 'bus'}, 'geometry': geometry}
                action = buses.transform_bus_data({'features': [feature]})[0]
                self.assertEqual(action['_source']['geometry'], {'lat': 0., 'lon': 151.})

    def test_all_invalid_refresh_never_writes_or_deletes(self):
        data = {'features': [self.feature(float('nan'), 151)]}
        with patch.object(buses, 'fetch_bus_data', return_value=data), patch.object(buses.helpers, 'bulk') as bulk, patch.object(buses, 'es') as client:
            buses.index_bus_data()
        bulk.assert_not_called()
        client.delete_by_query.assert_not_called()

    def test_response_level_spatial_reference_is_inherited(self):
        feature = {'attributes': {'id': 'bus'}, 'geometry': {'x': 151, 'y': -33}}
        for reference in [{'wkid': 4283}, {'wkid': 3857}, {'wkt': 'unknown'}]:
            with self.subTest(reference=reference):
                self.assertEqual(buses.transform_bus_data({'spatialReference': reference, 'features': [feature]}), [])
        self.assertEqual(len(buses.transform_bus_data({'spatialReference': {'wkid': 4326}, 'features': [feature]})), 1)
        feature['geometry']['spatialReference'] = {'wkid': 4326}
        self.assertEqual(len(buses.transform_bus_data({'spatialReference': {'wkid': 4283}, 'features': [feature]})), 1)
