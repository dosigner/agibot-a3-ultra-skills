import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts/find_interface.py"
spec = importlib.util.spec_from_file_location("lookup", MODULE)
lookup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lookup)


class LookupTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            {"name": "/motion/control/arm_joint_command", "transport": "ROS2 Topic",
             "summary": "Arm joint command", "heading_title": "Arm Command and State Interfaces",
             "source_url": "https://example.test/motion#arm", "message_types": ["sensor_msgs::msg::JointState"]},
            {"name": "/motion/control/arm_joint_state", "transport": "ROS2 Topic",
             "summary": "Arm joint state", "heading_title": "Arm state",
             "source_url": "https://example.test/motion#arm-state", "message_types": []},
            {"name": "pb:/aimdk.protocol.MotionService/GetArmJointState", "transport": "HTTP JSON RPC",
             "summary": "Query arm joint state", "heading_title": "Arm query",
             "source_url": "https://example.test/motion#query", "message_types": [],
             "warnings": ["Source mismatch"]},
        ]
        self.aliases = {"팔": ["arm"], "상태": ["state", "status"]}

    def test_korean_state_query_does_not_return_command(self):
        found = lookup.search_interfaces(self.records, "팔 상태", self.aliases)
        self.assertEqual(len(found), 2)
        self.assertNotIn(self.records[0], found)

    def test_topic_filter_excludes_rpc(self):
        found = lookup.search_interfaces(self.records, "팔 상태", self.aliases, "topic")
        self.assertEqual(found, [self.records[1]])

    def test_exact_identifier_preserves_source(self):
        found = lookup.search_interfaces(self.records, self.records[1]["name"], self.aliases)
        self.assertEqual(found, [self.records[1]])
        self.assertIs(found[0], self.records[1])

    def test_rpc_warnings_survive_lookup(self):
        found = lookup.search_interfaces(self.records, "GetArmJointState", self.aliases, "rpc")
        self.assertEqual(found[0]["warnings"], ["Source mismatch"])

    def test_message_type_search_remains_available(self):
        found = lookup.search_interfaces(self.records, "sensor_msgs::msg::JointState", self.aliases)
        self.assertEqual(found, [self.records[0]])

    def test_metadata_fallback_can_find_a_documented_gain_option(self):
        self.records[0]["heading_title"] = "Arm Control Configurable Kp/Kd"
        self.aliases["강성"] = ["stiffness", "kp"]
        found = lookup.search_interfaces(self.records, "팔 강성", self.aliases)
        self.assertEqual(found, [self.records[0]])

    def test_unknown_and_empty_queries_do_not_invent_matches(self):
        for query in ["", "unpublished_crane_braking_api"]:
            self.assertEqual(lookup.search_interfaces(self.records, query, self.aliases), [])


if __name__ == "__main__":
    unittest.main()
