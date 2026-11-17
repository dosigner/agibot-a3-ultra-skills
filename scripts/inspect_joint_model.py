#!/usr/bin/env python3
"""Extract URDF joint evidence without loading a simulator or contacting hardware."""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from xml.parsers import expat


def vector(node, attribute, default):
    values = [float(v) for v in node.get(attribute, default).split()] if node is not None else list(map(float, default.split()))
    if len(values) != 3 or not all(math.isfinite(v) for v in values):
        raise ValueError(f"Invalid {attribute} vector")
    return values


def group_for(name):
    if name.startswith(("L_", "R_")):
        return "left_hand" if name.startswith("L_") else "right_hand"
    if name.startswith("waist_"):
        return "waist"
    if name in ("head_yaw_joint", "ultra_head_pitch_joint"):
        return "head"
    for side in ("left", "right"):
        if name.startswith(tuple(f"{side}_{part}_" for part in ("shoulder", "elbow", "wrist"))):
            return side + "_arm"
        if name.startswith(tuple(f"{side}_{part}_" for part in ("hip", "knee", "ankle"))):
            return side + "_leg"
    return "mounts_and_other"


def inspect_urdf(data, source_name, source_url=None):
    document = ET.fromstring(data)
    if document.tag != "robot":
        raise ValueError("The XML root must be robot")
    links = [node.get("name") for node in document.findall("link")]
    if not links or None in links or len(set(links)) != len(links):
        raise ValueError("Links must have unique names")

    # Expat reports only real elements, so commented-out joints stay excluded.
    lines = {}
    parser = expat.ParserCreate()
    parser.StartElementHandler = lambda tag, attrs: lines.setdefault(attrs.get("name"), parser.CurrentLineNumber) if tag == "joint" else None
    parser.Parse(data, True)

    joints = []
    children = {}
    names = set()
    for node in document.findall("joint"):
        name, kind = node.get("name"), node.get("type")
        if not name or name in names or kind not in {"fixed", "revolute", "continuous", "prismatic", "floating", "planar"}:
            raise ValueError("Joint names must be unique and joint types valid")
        names.add(name)
        parent_node, child_node = node.find("parent"), node.find("child")
        parent = parent_node.get("link") if parent_node is not None else None
        child = child_node.get("link") if child_node is not None else None
        if parent not in links or child not in links:
            raise ValueError(f"Unknown parent or child link: {name}")
        if child in children:
            raise ValueError(f"Link has multiple parent joints: {child}")
        children[child] = parent
        origin = node.find("origin")
        axis = vector(node.find("axis"), "xyz", "1 0 0") if kind in {"revolute", "continuous", "prismatic"} else None
        if axis is not None and sum(v * v for v in axis) == 0:
            raise ValueError(f"Zero-length joint axis: {name}")
        limit_node = node.find("limit")
        limit = {key: float(value) for key, value in limit_node.attrib.items()} if limit_node is not None else None
        if limit and not all(math.isfinite(v) for v in limit.values()):
            raise ValueError(f"Non-finite joint limit: {name}")
        if limit and "lower" in limit and "upper" in limit and limit["lower"] > limit["upper"]:
            raise ValueError(f"Inverted joint limits: {name}")
        mimic_node = node.find("mimic")
        mimic = None
        if mimic_node is not None:
            mimic = {"joint": mimic_node.get("joint"), "multiplier": float(mimic_node.get("multiplier", "1")), "offset": float(mimic_node.get("offset", "0"))}
            if not all(math.isfinite(mimic[key]) for key in ("multiplier", "offset")):
                raise ValueError(f"Non-finite mimic relation: {name}")
        joints.append({
            "name": name, "type": kind, "group": group_for(name),
            "parent": parent, "child": child,
            "origin_xyz_m": vector(origin, "xyz", "0 0 0"),
            "origin_rpy_rad": vector(origin, "rpy", "0 0 0"),
            "axis_in_joint_frame": axis, "limit": limit, "mimic": mimic,
            "source_line": lines[name],
        })

    roots = sorted(set(links) - set(children))
    if len(roots) != 1:
        raise ValueError(f"Expected one root link, found {len(roots)}")
    for link in links:
        visited = set()
        current = link
        while current in children:
            if current in visited:
                raise ValueError(f"Cycle in link tree at {current}")
            visited.add(current)
            current = children[current]
        if current != roots[0]:
            raise ValueError(f"Disconnected link: {link}")
    mimic_targets = {j["name"]: j["mimic"]["joint"] for j in joints if j["mimic"]}
    for name, target in mimic_targets.items():
        if target not in names:
            raise ValueError(f"Unknown mimic target: {name}")
        visited, current = set(), name
        while current in mimic_targets:
            if current in visited:
                raise ValueError(f"Cycle in mimic relations at {current}")
            visited.add(current)
            current = mimic_targets[current]

    groups = {}
    for group in dict.fromkeys(j["group"] for j in joints):
        subset = [j for j in joints if j["group"] == group]
        groups[group] = {
            "joint_types": dict(Counter(j["type"] for j in subset)),
            "mimic_count": sum(j["mimic"] is not None for j in subset),
            "non_mimic_revolute_count": sum(j["type"] == "revolute" and j["mimic"] is None for j in subset),
        }
    return {
        "schema_version": 1,
        "source": {"filename": source_name, "url": source_url, "sha256": hashlib.sha256(data).hexdigest()},
        "robot": document.get("name"), "root_link": roots[0],
        "counts": {"links": len(links), "joints": len(joints), "joint_types": dict(Counter(j["type"] for j in joints)),
                   "mimic_count": len(mimic_targets),
                   "non_mimic_revolute_count": sum(j["type"] == "revolute" and j["mimic"] is None for j in joints),
                   "transmissions": len(document.findall("transmission"))},
        "units": {"origin_xyz": "m", "origin_rpy": "rad", "axis": "dimensionless, expressed in joint frame",
                  "revolute_limit_position": "rad", "revolute_limit_velocity": "rad/s", "revolute_limit_effort": "N m",
                  "prismatic_limit_position": "m", "prismatic_limit_velocity": "m/s", "prismatic_limit_effort": "N"},
        "groups": groups, "joints": joints,
        "hardware_verified": False,
        "notes": ["Counts describe this URDF, not verified motors, runtime command dimensions or hardware limits.",
                  "A3 semantic groups use joint-name prefixes; unrelated model names fall into mounts_and_other.",
                  "Missing URDF origins and axes use URDF defaults. Fixed joints have no motion axis.",
                  "Mimic relations are preserved as q_child = multiplier * q_target + offset.",
                  "The non-mimic count covers revolute variables only; floating and planar joints are not counted as one degree of freedom."]
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urdf", type=Path)
    parser.add_argument("--source-url", help="Verified source permalink; not fetched by this script")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect_urdf(args.urdf.read_bytes(), args.urdf.name, args.source_url)
        text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    except (OSError, ValueError, ET.ParseError) as error:
        parser.exit(2, f"URDF extraction failed: {error}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
