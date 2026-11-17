import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_catalog.py"
spec = importlib.util.spec_from_file_location("build_catalog", SCRIPT)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)
URL = catalog.START


def vertical(name, kind, extra=""):
    return f"""<table><tr><th>Interface Name</th><th>{name}</th></tr>
    <tr><td>Interface Type</td><td>{kind}</td></tr>{extra}</table>"""


class CatalogTests(unittest.TestCase):
    def test_actual_nearest_heading_and_message_type(self):
        html = '<h1>Duplicate shell title</h1><div class="doc-prose"><h1 id="real">Real title</h1><h2 id="group">Group</h2><h3 id="actual-anchor">Arm</h3>'
        html += vertical('/arm/state', 'ROS2 Topic', '<tr><td>Remarks</td><td>sensor_msgs::msg::JointState</td></tr>') + '</div>'
        page, records, _ = catalog.parse_page(html, URL)
        self.assertEqual(page["title"], "Real title")
        self.assertEqual(records[0]["source_url"], URL + "#actual-anchor")
        self.assertEqual(records[0]["message_types"], ["sensor_msgs::msg::JointState"])
        self.assertEqual([h["level"] for h in page["headings"]], [1, 2, 3])

    def test_rpc_topic_service_and_method_mismatch(self):
        html = '<h1 id="top">Interfaces</h1>'
        html += vertical('pb:/aimdk.protocol.MotionService/CheckArmCompliance', 'HTTP JSON RPC', '<tr><td>URL</td><td>http://10.42.10.12:56322/rpc/aimdk.protocol.MotionService/DisableArmCompliance</td></tr>')
        html += vertical('/motion/command', 'ROS2 Topic')
        html += vertical('/audio_5Fmsgs/srv/RequestAudioFocus', 'services')
        _, records, _ = catalog.parse_page(html, URL)
        self.assertEqual([r["transport"] for r in records], ["HTTP JSON RPC", "ROS2 Topic", "ROS2 Service"])
        self.assertEqual(records[0]["target_host"], "10.42.10.12")
        self.assertIn("DisableArmCompliance", records[0]["warnings"][0])
        self.assertTrue(records[0]["name"].endswith("CheckArmCompliance"))
        self.assertEqual(records[0]["message_types"], [])

    def test_url_split_by_inline_code_is_one_endpoint(self):
        html = '<h1 id="rpc">RPC</h1>' + vertical('pb:/aimdk.protocol.PncService/ActionPause', 'RPC', '<tr><td>URL</td><td>http://10.42.10.11:53176/rpc/<code>aimdk.protocol.PncService/ActionPause</code></td></tr>')
        _, records, _ = catalog.parse_page(html, URL)
        self.assertEqual(records[0]["warnings"], [])
        self.assertEqual(records[0]["target_host"], "10.42.10.11")

    def test_missing_anchor_is_not_invented(self):
        _, records, _ = catalog.parse_page('<h1>No Anchor</h1>' + vertical('/state', 'topic'), URL)
        self.assertIsNone(records[0]["heading_id"])
        self.assertEqual(records[0]["source_url"], URL)
        self.assertTrue(records[0]["warnings"])

    def test_horizontal_navigation_and_two_topic_columns(self):
        html = '''<h1 id="nav">Navigation</h1><table>
        <tr><th>Interface Name</th><th>Interface Description</th><th>URL</th></tr>
        <tr><td>pb:/aimdk.protocol.PncService/ActionPause</td><td>Pause task</td><td>http://10.42.10.11:53176/rpc/aimdk.protocol.PncService/ActionPause</td></tr></table>
        <h2 id="cameras">Cameras</h2><table><tr><th>Topic</th><th>Topic</th><th>Message Type</th></tr>
        <tr><td>/left/rgb</td><td>/right/rgb</td><td>sensor_msgs::msg::Image</td></tr></table>'''
        _, records, _ = catalog.parse_page(html, URL)
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["transport"], "HTTP JSON RPC")
        self.assertEqual({r["name"] for r in records[1:]}, {"/left/rgb", "/right/rgb"})
        self.assertEqual(records[2]["message_types"], ["sensor_msgs::msg::Image"])

    def test_no_type_conversion_and_no_payload_copy(self):
        html = '<h1 id="test">Types</h1>' + vertical('/command', 'topic', '<tr><td>Input Parameters</td><td>{"secret_payload":"do not copy"}</td></tr><tr><td>Remarks</td><td>ROS.sensor_msgs.msg.JointState</td></tr>')
        _, records, _ = catalog.parse_page(html, URL)
        self.assertEqual(records[0]["message_types"], [])
        self.assertNotIn("secret_payload", str(records))

    def test_discovery_counts_and_runtime_false(self):
        second = catalog.BASE + "07-01-motion_control"
        fixtures = {
            URL: '<h1 id="overview">Overview</h1><a href="07-01-motion_control">Motion</a><a href="/docs/en/aimdk/a3-ultra/v3_2/dev_guide/x">Other version</a>',
            second: '<h1 id="motion">Motion</h1><a href="01-a3_overview">Overview</a>' + vertical('/state', 'topic'),
        }
        result = catalog.build_catalog(fixtures.__getitem__)
        self.assertEqual(result["coverage"]["page_count"], 2)
        self.assertEqual(result["coverage"]["heading_count"], 2)
        self.assertEqual(result["coverage"]["interface_count"], 1)
        self.assertIs(result["runtime_verified"], False)

    def test_sensor_duplicates_merge_and_suspicious_type_warns(self):
        html = '''<h1 id="sensors">Sensors</h1>
        <table><tr><th>Topic Name</th><th>Message Type</th></tr><tr><td>/sensor/imu</td><td>foxglove_msgs::msg::CompressedVideo</td></tr></table>
        <table><tr><th>Topic</th><th>Normal Mode</th></tr><tr><td>/sensor/imu</td><td>Published</td></tr></table>'''
        _, records, _ = catalog.parse_page(html, URL)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["message_types"], ["foxglove_msgs::msg::CompressedVideo"])
        self.assertIn("IMU", records[0]["warnings"][0])


if __name__ == "__main__":
    unittest.main()
