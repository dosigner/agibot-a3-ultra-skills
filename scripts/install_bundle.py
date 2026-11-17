#!/usr/bin/env python3
"""Link the A3 guides and install the three reviewed NVIDIA skills for Codex."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HELPER = Path("skills/.system/skill-installer/scripts/install-skill-from-github.py")


def make_plan(root, codex_home):
    root = Path(root).resolve()
    codex_home = Path(codex_home).expanduser().resolve()
    manifest = json.loads((root / "install-manifest.json").read_text())
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported install manifest version")
    local = manifest["local_skills"]
    external = manifest["nvidia"]
    names = local + external["skills"]
    if len(names) != len(set(names)) or not all(
        isinstance(name, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
        for name in names
    ):
        raise ValueError("Skill names must be unique, plain folder names")
    if external["repository"] != "NVIDIA/skills" or not re.fullmatch(r"[0-9a-f]{40}", external["ref"]):
        raise ValueError("NVIDIA skills must use the reviewed repository and a full commit SHA")
    for relative in ("catalog.json", "index.html", "scripts/find_interface.py",
                     "references/guide-notes.md", "references/search-aliases.json",
                     "references/related-links.json"):
        if not (root / relative).is_file():
            raise ValueError(f"Missing shared bundle file: {relative}")

    entries = []
    conflicts = []
    for name in local:
        source = root / "skills" / name
        destination = codex_home / "skills" / name
        if not (source / "SKILL.md").is_file():
            raise ValueError(f"Missing local skill: {name}")
        present = destination.exists() or destination.is_symlink()
        matching = destination.is_symlink() and destination.resolve() == source.resolve()
        if present and not matching:
            conflicts.append(f"Existing A3 destination is preserved: {destination}")
        entries.append({"name": name, "kind": "a3", "source": str(source),
                        "destination": str(destination),
                        "status": "already_linked" if matching else "pending_link"})
    for name in external["skills"]:
        destination = codex_home / "skills" / name
        present = destination.exists() or destination.is_symlink()
        if present and not (destination / "SKILL.md").is_file():
            conflicts.append(f"Existing NVIDIA destination is not a valid skill: {destination}")
        entries.append({"name": name, "kind": "nvidia", "destination": str(destination),
                        "status": "existing_unverified" if present else "pending_install"})
    if any(entry["status"] == "pending_install" for entry in entries) and not (codex_home / HELPER).is_file():
        conflicts.append(f"Codex's bundled skill-installer helper is missing: {codex_home / HELPER}")
    if conflicts:
        raise ValueError("\n".join(conflicts))
    return {"codex_home": str(codex_home), "nvidia_repository": external["repository"],
            "nvidia_ref": external["ref"], "skills": entries}


def helper_environment():
    env = os.environ.copy()
    # Use the OS CA bundle when Python has no explicit certificate configuration.
    if not env.get("SSL_CERT_FILE") and not env.get("SSL_CERT_DIR") and Path("/etc/ssl/cert.pem").is_file():
        env["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"
    return env


def install_bundle(root, codex_home, check_only=False, runner=subprocess.run):
    plan = make_plan(root, codex_home)
    plan["check_only"] = check_only
    if check_only:
        return plan
    missing = [entry for entry in plan["skills"] if entry["status"] == "pending_install"]
    if missing:
        home = Path(plan["codex_home"])
        command = [sys.executable, str(home / HELPER), "--repo", plan["nvidia_repository"],
                   "--ref", plan["nvidia_ref"], "--method", "download",
                   "--dest", str(home / "skills"), "--path",
                   *["skills/" + entry["name"] for entry in missing]]
        runner(command, check=True, env=helper_environment())
        for entry in missing:
            if not (Path(entry["destination"]) / "SKILL.md").is_file():
                raise ValueError(f"Installer did not produce SKILL.md: {entry['name']}")
            entry["status"] = "installed"
    for entry in plan["skills"]:
        if entry["status"] == "pending_link":
            destination = Path(entry["destination"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            # shortcut: Links depend on this checkout; use a copied bundle if it must move.
            destination.symlink_to(entry["source"], target_is_directory=True)
            entry["status"] = "linked"
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Show the plan without installing or contacting GitHub")
    args = parser.parse_args(argv)
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    try:
        result = install_bundle(ROOT, home, args.check)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Bundle installation stopped: {error}\nExisting skills were not replaced.\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
