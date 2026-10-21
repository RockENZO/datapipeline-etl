import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class StaticDemoTests(unittest.TestCase):
    def test_browser_pipeline_matches_indexer_and_search_semantics(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for the static demo checks")
        result = subprocess.run([node, str(Path(__file__).with_name("pipeline.test.cjs"))],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_demo_data_matches_what_the_indexer_reads(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_demo_data", ROOT / "tools/build_demo_data.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name, wrapper in module.FILES:
            payload = json.loads((ROOT / "demo/data" / name).read_text())
            collection = payload[wrapper] if wrapper else payload
            self.assertEqual(collection["type"], "FeatureCollection", name)
            self.assertTrue(collection["features"], name + " is empty")

    def test_demo_uses_the_same_wrappers_as_the_indexer(self):
        import es_index_multi_docker as indexer
        import inspect
        source = inspect.getsource(indexer.index_all_datasets)
        self.assertIn("'NSW Ambulance Station'", source)
        self.assertIn("'BuildingComplexPoint'", source)

    def test_demo_data_documents_its_provenance(self):
        readme = (ROOT / "demo/data/README.md").read_text()
        self.assertIn("Knia-data-repo", readme)
        self.assertIn("not synthetic", readme.lower())

    def test_pages_build_includes_shared_escape_helper(self):
        out = ROOT / "_site_test"
        try:
            subprocess.run([str(ROOT / "tools/build_pages.sh"), str(out)], check=True, capture_output=True)
            self.assertTrue((out / "index.html").is_file())
            self.assertTrue((out / "popup_safety.js").is_file())
            self.assertTrue((out / ".nojekyll").is_file())
        finally:
            shutil.rmtree(out, ignore_errors=True)


class IndexerRealDataTests(unittest.TestCase):
    """Behaviours the real Knia-data-repo exports require of the indexer."""

    def _index(self, name, payload, data_path=None):
        import tempfile
        from unittest.mock import Mock, patch
        import es_index_multi_docker as indexer
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f.json"
            path.write_text(json.dumps(payload))
            bulk = Mock()
            with patch.object(indexer, "es", Mock()), patch.object(indexer.helpers, "bulk", bulk):
                indexer.index_dataset(name, str(path), "OBJECTID", data_path)
        return bulk

    def test_records_without_coordinates_do_not_abort_non_spatial_datasets(self):
        table = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": None, "properties": {"Name": "x"}}]}
        self.assertFalse(self._index("library_details", table).called)

    def test_non_spatial_exemption_needs_real_geometry_free_records(self):
        empty = {"type": "FeatureCollection", "features": []}
        with self.assertRaises(ValueError):
            self._index("library_details", empty)
        broken = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": []}, "properties": {}}]}
        with self.assertRaises(ValueError):
            self._index("library_details", broken)
        falsy = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {}, "properties": {}}]}
        with self.assertRaises(ValueError):
            self._index("library_details", falsy)

    def test_spatial_dataset_with_no_usable_geometry_is_still_fatal(self):
        table = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": None, "properties": {"Name": "x"}}]}
        with self.assertRaises(ValueError):
            self._index("stairs", table)

    def test_ambulance_stations_are_read_from_their_wrapper_key(self):
        point = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [151.2, -33.9, 0]}, "properties": {"OBJECTID": 1}}
        payload = {"Hospital": {"features": []}, "NSW Ambulance Station": {"features": [point]}}
        bulk = self._index("nsw_ambulance_stations", payload, "NSW Ambulance Station")
        self.assertEqual(len(bulk.call_args.args[1]), 1)
