#!/usr/bin/env python3
"""Build a documentation-only index. This script never contacts a robot."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urldefrag, urljoin, urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup


BASE = "https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/"
START = BASE + "01-a3_overview"
TYPE_RE = re.compile(
    r"\b[a-z][a-z0-9_]*(?:::(?:msg|srv)::|/(?:msg|srv)/)[A-Z]\w*\b"
    r"|\baimdk(?:::protocol::|\.protocol\.)[A-Z]\w*\b"
)
NAME_RE = re.compile(r"pb:/[A-Za-z_][\w.]*/[A-Za-z_]\w*|/[A-Za-z0-9_][A-Za-z0-9_/-]*")
EXAMPLE_RE = re.compile(r"\bexamples?/[A-Za-z0-9_./-]+")


def clean(node):
    return " ".join(node.get_text(" ", strip=True).split())


def document_url(href, current):
    url = urldefrag(urljoin(current, href))[0]
    if url == BASE.rstrip("/"):
        url = BASE
    if url.startswith(BASE) and not urlparse(url).query:
        suffix = url[len(BASE):]
        if not suffix or re.fullmatch(r"[\w-]+", suffix):
            return url
    return None


def fetch(url, cache):
    # Only the public documentation origin and version are permitted.
    if document_url(url, START) != url:
        raise ValueError(f"Not a versioned documentation URL: {url}")
    path = cache / (hashlib.sha256(url.encode()).hexdigest() + ".html")
    if not path.exists():
        result = subprocess.run(
            ["curl", "--fail", "--silent", "--show-error", "--location",
             "--max-time", "30", "--proto", "=https", "--proto-redir", "=https", url],
            check=True, capture_output=True,
        )
        path.write_bytes(result.stdout)
    return path.read_text(encoding="utf-8")


def transport(label, name, endpoint):
    label = label.lower()
    if "rpc" in label or name.startswith("pb:/") or "/rpc/" in endpoint:
        return "HTTP JSON RPC" if endpoint.startswith("http") or "http" in label else "RPC"
    if "service" in label:
        return "ROS2 Service"
    if "topic" in label:
        return "ROS2 Topic"
    return "Unspecified"


def interface_record(fields, name, table, page_url):
    heading = table.find_previous(["h1", "h2", "h3"], id=True)
    heading_id = heading.get("id") if heading else None
    source_url = page_url + ("#" + heading_id if heading_id else "")
    endpoint_match = re.search(r"https?://[^\s<>]+", fields.get("url", ""))
    endpoint = endpoint_match.group() if endpoint_match else ""
    kind = transport(fields.get("interface type", ""), name, endpoint)
    warnings = []
    if not heading_id:
        warnings.append("No source heading anchor was present; source_url points to the page.")
    if kind.endswith("RPC") and endpoint and name.rsplit("/", 1)[-1] != urlparse(endpoint).path.rsplit("/", 1)[-1]:
        warnings.append(f"Document method mismatch: Interface Name is {name}; URL is {endpoint}. Neither value was corrected.")
    text = " ".join(value for key, value in fields.items() if key not in ("interface name", "url", "example script"))
    notes = " ".join(fields.get(key, "") for key in ("notes", "remarks"))
    if "iceoryx" in notes.lower():
        warnings.append("The source describes an iceoryx/default transport condition; ROS2 availability requires checking the source and installed configuration.")
    if "asynchronous" in notes.lower() or "does not mean" in notes.lower():
        warnings.append("Request acceptance does not establish completion; consult the documented status interface.")
    if "fail silently" in notes.lower():
        warnings.append("The source warns that playback can fail silently while is_success is true.")
    types = sorted(set(TYPE_RE.findall(text)))
    if "imu" in name.lower() and "foxglove_msgs::msg::CompressedVideo" in types:
        warnings.append("The source lists CompressedVideo for an IMU topic. This apparent type inconsistency is preserved and requires runtime verification.")
    summary = next((fields[key] for key in ("function overview", "interface description", "overview", "summary") if fields.get(key)), "")
    identity = "|".join((source_url, kind, name))
    return {
        "id": hashlib.sha256(identity.encode()).hexdigest()[:16],
        "name": name,
        "transport": kind,
        "summary": summary,
        "page_url": page_url,
        "heading_title": clean(heading) if heading else "",
        "heading_id": heading_id,
        "source_url": source_url,
        "message_types": types,
        "target_host": urlparse(endpoint).hostname if endpoint else None,
        "example_paths": sorted(set(EXAMPLE_RE.findall(fields.get("example script", "")))),
        "warnings": warnings,
    }


def parse_interfaces(body, page_url):
    records = {}
    for table in body.select("table"):
        cells_by_row = [row.find_all(["th", "td"], recursive=False) for row in table.select("tr")]
        cells_by_row = [cells for cells in cells_by_row if cells]
        rows = [[clean(cell) for cell in cells] for cells in cells_by_row]
        if not rows:
            continue
        headers = [value.lower() for value in rows[0]]
        for row, cells in zip(rows, cells_by_row):
            # Inline code can split one URL without any source whitespace.
            if row[0].lower() == "url" and len(row) == 2:
                row[1] = " ".join(cells[1].get_text("", strip=True).split())
            elif "url" in headers and len(row) > headers.index("url"):
                index = headers.index("url")
                row[index] = " ".join(cells[index].get_text("", strip=True).split())
        candidates = []
        if headers[0] == "interface name" and len(headers) == 2:
            fields = {row[0].lower(): " ".join(row[1:]) for row in rows if len(row) >= 2}
            candidates = [(fields, name) for name in NAME_RE.findall(fields["interface name"])]
        elif "interface name" in headers:
            for row in rows[1:]:
                fields = dict(zip(headers, row))
                candidates.extend((fields, name) for name in NAME_RE.findall(fields.get("interface name", "")))
        elif "topic" in headers or "topic name" in headers:
            topic_columns = [i for i, value in enumerate(headers) if value in ("topic", "topic name")]
            for row in rows[1:]:
                fields = dict(zip(headers, row))
                fields["interface type"] = "ROS2 Topic"
                fields["summary"] = "; ".join(
                    f"{headers[i]}: {value}" for i, value in enumerate(row)
                    if i < len(headers) and i not in topic_columns and value
                    and headers[i] not in ("message type", "protobuf type")
                )
                for index in topic_columns:
                    if index < len(row):
                        candidates.extend((fields, name) for name in NAME_RE.findall(row[index]))
        elif "url" in headers and "example:" in headers:
            for row in rows[1:]:
                fields = dict(zip(headers, row))
                if "/rpc/" in fields.get("url", ""):
                    candidates.append((fields, fields.get("example:", "")))
        for fields, name in candidates:
            record = interface_record(fields, name, table, page_url)
            previous = records.get(record["id"])
            if previous:
                for key in ("message_types", "example_paths", "warnings"):
                    previous[key] = sorted(set(previous[key] + record[key]))
                if record["summary"] and record["summary"] not in previous["summary"]:
                    previous["summary"] = "; ".join(filter(None, (previous["summary"], record["summary"])))
            else:
                records[record["id"]] = record
    return list(records.values())


def parse_page(html, url):
    soup = BeautifulSoup(html, "html.parser")
    body = soup.select_one(".doc-prose") or soup
    title = body.select_one("h1[id]") or body.find("h1") or soup.find("title")
    if title is None:
        raise ValueError(f"Page has no title: {url}")
    headings = [
        {"level": int(node.name[1]), "id": node["id"], "title": clean(node), "url": url + "#" + node["id"]}
        for node in body.select("h1[id], h2[id], h3[id]")
    ]
    links = []
    seen = set()
    for node in body.select("a[href]"):
        target = urljoin(url, node["href"])
        if urlparse(target).scheme in ("http", "https") and target not in seen:
            seen.add(target)
            links.append({"label": clean(node), "url": target})
    page = {"slug": url[len(BASE):] or "index", "title": clean(title), "url": url, "headings": headings, "links": links}
    discovered = {value for node in soup.select("a[href]") if (value := document_url(node["href"], url))}
    return page, parse_interfaces(body, url), discovered


def build_catalog(fetch_page):
    pending = {START}
    visited = set()
    pages = []
    interfaces = []
    while pending:
        batch = sorted(pending - visited)
        if not batch:
            break
        with ThreadPoolExecutor(max_workers=4) as pool:
            documents = list(pool.map(fetch_page, batch))
        pending = set()
        for url, html in zip(batch, documents):
            page, found, discovered = parse_page(html, url)
            pages.append(page)
            interfaces.extend(found)
            visited.add(url)
            pending.update(discovered - visited)
    pages.sort(key=lambda page: (page["slug"] != "index", page["slug"]))
    interfaces.sort(key=lambda entry: (entry["page_url"], entry["source_url"], entry["name"]))
    return {
        "schema_version": 1,
        "product": "A3 Ultra",
        "doc_version": "v3_3",
        "checked_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "source_base": BASE,
        "runtime_verified": False,
        "pages": pages,
        "interfaces": interfaces,
        "coverage": {
            "page_count": len(pages),
            "heading_count": sum(len(page["headings"]) for page in pages),
            "interface_count": len(interfaces),
            "notes": [
                "Documentation-only index; no robot connection, command, message publication, or runtime verification was performed.",
                "Scope is the English v3_3 developer-guide URLs linked from the overview and discovered pages, including the guide index.",
                "Interface entries are source occurrences, not a count of unique runtime endpoints. Repeated names can occur under different source sections.",
                "Only structured interface/topic/example tables are indexed. Interfaces appearing solely in prose or code examples require following the source links.",
                "Only source H1/H2/H3 elements with actual id attributes are anchors; no fragment is generated from a title.",
                "Message types retain the exact qualified spelling found in source cells. Missing types are empty; ROS.msg spellings are not converted.",
                "Hosts come only from documented RPC URLs. Conflicting board-to-IP mappings are not resolved or inferred.",
                "Payloads, credentials, full manuals, remote commands, and complete operational notes are not copied. Read the linked source for constraints and current details.",
                "Rows with the same name, transport, and source heading are merged; different source sections remain separate.",
            ],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "catalog.json")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="a3-doc-catalog-") as directory:
        catalog = build_catalog(lambda url: fetch(url, Path(directory)))
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(catalog["coverage"], ensure_ascii=False))


if __name__ == "__main__":
    main()
