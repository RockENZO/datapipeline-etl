import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.build_demo_data import build, main


class DemoDataBuildTests(unittest.TestCase):
    def test_invalid_source_does_not_replace_earlier_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            source.mkdir()
            out = root / 'out'
            out.mkdir()
            (source / 'valid.geojson').write_text('{"features":[]}')
            (source / 'invalid.json').write_text('{"Sites":{"feature":[]}}')
            existing = out / 'valid.geojson'
            existing.write_text('previous export')

            with patch('tools.build_demo_data.FILES',
                       [('valid.geojson', None), ('invalid.json', 'Sites')]):
                with self.assertRaisesRegex(
                    ValueError, r'invalid\.json \(Sites\): expected a features array'
                ):
                    main(['build_demo_data.py', str(source), str(out)])

            self.assertEqual(existing.read_text(), 'previous export')
            self.assertEqual(list(out.iterdir()), [existing])

    def test_valid_empty_and_wrapped_collections_are_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            path = source / 'sites.json'
            path.write_text(json.dumps({'Sites': {'features': []}}))

            payload, before, after = build(source, path.name, 'Sites')

            self.assertEqual(payload, {'Sites': {
                'type': 'FeatureCollection', 'features': [],
            }})
            self.assertEqual((before, after), (0, 0))
