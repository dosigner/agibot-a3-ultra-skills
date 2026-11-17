import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

MODULE = Path(__file__).resolve().parents[1] / "scripts/install_bundle.py"
spec = importlib.util.spec_from_file_location("installer", MODULE)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class BundleInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "checkout"
        self.home = Path(self.temp.name).resolve() / "codex"
        self.root.mkdir()
        self.manifest = {"schema_version": 1, "local_skills": ["a3-guide"],
                         "nvidia": {"repository": "NVIDIA/skills", "ref": "a" * 40,
                                    "skills": ["jetson-diagnostic", "deepstream-dev"]}}
        (self.root / "install-manifest.json").write_text(json.dumps(self.manifest))
        for relative in ["catalog.json", "index.html", "scripts/find_interface.py",
                         "references/guide-notes.md", "references/search-aliases.json",
                         "references/related-links.json", "skills/a3-guide/SKILL.md"]:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture")
        helper = self.home / installer.HELPER
        helper.parent.mkdir(parents=True)
        helper.write_text("fixture")

    def fake_runner(self, command, **kwargs):
        self.assertEqual(command[command.index("--ref") + 1], "a" * 40)
        self.assertEqual(command[command.index("--method") + 1], "download")
        for name in command[command.index("--path") + 1:]:
            target = self.home / name / "SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("downloaded fixture")

    def test_check_does_not_write_or_use_network(self):
        runner = Mock()
        before = sorted(str(p) for p in self.home.rglob("*"))
        result = installer.install_bundle(self.root, self.home, True, runner)
        self.assertTrue(result["check_only"])
        self.assertEqual(before, sorted(str(p) for p in self.home.rglob("*")))
        runner.assert_not_called()

    def test_install_preserves_shared_references_and_reruns_without_replacing(self):
        result = installer.install_bundle(self.root, self.home, runner=self.fake_runner)
        self.assertEqual([e["status"] for e in result["skills"]], ["linked", "installed", "installed"])
        installed = self.home / "skills/a3-guide"
        self.assertEqual((installed / "SKILL.md").resolve().parents[2], self.root)
        self.assertEqual((installed / "../../catalog.json").read_text(), "fixture")
        runner = Mock()
        again = installer.install_bundle(self.root, self.home, runner=runner)
        self.assertEqual([e["status"] for e in again["skills"]],
                         ["already_linked", "existing_unverified", "existing_unverified"])
        runner.assert_not_called()

    def test_conflicting_directory_prevents_all_installation(self):
        target = self.home / "skills/a3-guide"
        target.mkdir()
        (target / "user-file").write_text("keep")
        runner = Mock()
        with self.assertRaisesRegex(ValueError, "preserved"):
            installer.install_bundle(self.root, self.home, runner=runner)
        self.assertEqual((target / "user-file").read_text(), "keep")
        runner.assert_not_called()

    def test_dangling_symlink_is_a_conflict(self):
        target = self.home / "skills/a3-guide"
        target.symlink_to(self.home / "missing")
        with self.assertRaisesRegex(ValueError, "preserved"):
            installer.make_plan(self.root, self.home)
        self.assertTrue(target.is_symlink())

    def test_external_failure_does_not_create_a3_links(self):
        runner = Mock(side_effect=subprocess.CalledProcessError(1, ["fixture"]))
        with self.assertRaises(subprocess.CalledProcessError):
            installer.install_bundle(self.root, self.home, runner=runner)
        self.assertFalse((self.home / "skills/a3-guide").exists())

    def test_missing_helper_and_path_traversal_are_rejected(self):
        (self.home / installer.HELPER).unlink()
        with self.assertRaisesRegex(ValueError, "helper is missing"):
            installer.make_plan(self.root, self.home)
        self.manifest["local_skills"] = ["../outside"]
        (self.root / "install-manifest.json").write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, "plain folder names"):
            installer.make_plan(self.root, self.home)

    def test_existing_nvidia_skill_is_preserved_and_marked_unverified(self):
        target = self.home / "skills/jetson-diagnostic/SKILL.md"
        target.parent.mkdir()
        target.write_text("user's version")
        result = installer.install_bundle(self.root, self.home, runner=self.fake_runner)
        self.assertEqual(target.read_text(), "user's version")
        self.assertEqual(result["skills"][1]["status"], "existing_unverified")

    def test_user_certificate_configuration_is_preserved(self):
        for key in ["SSL_CERT_FILE", "SSL_CERT_DIR"]:
            with patch.dict(installer.os.environ, {key: "/custom/trust"}, clear=True):
                env = installer.helper_environment()
                self.assertEqual(env, {key: "/custom/trust"})


if __name__ == "__main__":
    unittest.main()
