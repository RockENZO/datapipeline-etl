import shutil
import subprocess
import unittest
from pathlib import Path


class PopupSafetyTests(unittest.TestCase):
    def test_external_values_remain_text_in_actual_popup_functions(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for popup regression checks")
        result = subprocess.run([node, str(Path(__file__).with_name("popup_safety.cjs"))],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_page_loads_the_served_escape_helper(self):
        import web_map.app as web
        client=web.app.test_client()
        self.assertIn('/static/popup_safety.js', client.get('/').get_data(as_text=True))
        self.assertEqual(client.get('/static/popup_safety.js').status_code,200)
