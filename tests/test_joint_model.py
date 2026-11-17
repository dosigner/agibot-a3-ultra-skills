import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/inspect_joint_model.py"
spec = importlib.util.spec_from_file_location("joint_model", SOURCE)
joint_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(joint_model)


def fixture(mimic='joint="a" multiplier="1.3" offset="0.1"'):
    return f'''<robot name="fixture">
      <link name="root"/><link name="one"/><link name="two"/>
      <!-- <joint name="ignored" type="floating"/> -->
      <joint name="a" type="revolute"><parent link="root"/><child link="one"/>
        <origin xyz="1 2 3" rpy="0 0 0"/><axis xyz="0 1 0"/>
        <limit lower="-1" upper="2" effort="3" velocity="4"/></joint>
      <joint name="b" type="revolute"><parent link="one"/><child link="two"/>
        <mimic {mimic}/></joint>
    </robot>'''.encode()


class JointModelTests(unittest.TestCase):
    def test_tree_units_limits_and_mimic_are_preserved(self):
        data = joint_model.inspect_urdf(fixture(), "fixture.urdf")
        self.assertEqual(data["root_link"], "root")
        self.assertEqual(data["counts"]["joints"], 2)
        self.assertEqual(data["counts"]["non_mimic_revolute_count"], 1)
        self.assertEqual(data["joints"][0]["origin_xyz_m"], [1, 2, 3])
        self.assertEqual(data["joints"][0]["limit"], {"lower": -1, "upper": 2, "effort": 3, "velocity": 4})
        self.assertEqual(data["joints"][1]["mimic"], {"joint": "a", "multiplier": 1.3, "offset": 0.1})
        self.assertFalse(data["hardware_verified"])

    def test_missing_link_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown parent or child"):
            joint_model.inspect_urdf(fixture().replace(b'parent link="one"', b'parent link="missing"'), "bad.urdf")

    def test_missing_mimic_and_mimic_cycle_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown mimic target"):
            joint_model.inspect_urdf(fixture('joint="missing"'), "bad.urdf")
        with self.assertRaisesRegex(ValueError, "Cycle in mimic"):
            joint_model.inspect_urdf(fixture('joint="b"'), "bad.urdf")

    def test_disconnected_cycle_is_rejected(self):
        data = fixture().replace(b'parent link="root"', b'parent link="two"')
        with self.assertRaisesRegex(ValueError, "Cycle in link tree"):
            joint_model.inspect_urdf(data, "bad.urdf")


if __name__ == "__main__":
    unittest.main()
