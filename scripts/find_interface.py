#!/usr/bin/env python3
"""Search documented A3 interfaces without contacting a robot."""

import argparse
import json
from pathlib import Path
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def normalize(value):
    return unicodedata.normalize("NFKC", str(value)).casefold().strip()


def matches_kind(transport, kind):
    value = normalize(transport).replace(" ", "")
    if kind == "topic":
        return "topic" in value and "rpc" not in value
    if kind == "rpc":
        return "rpc" in value
    return True


def search_interfaces(interfaces, query, aliases, kind="all"):
    query = normalize(query)
    if not query:
        return []
    words = [query] if query in aliases else query.split()
    groups = [[word, *map(normalize, aliases.get(word, []))] for word in words]
    matches = []
    for record in interfaces:
        if not matches_kind(record.get("transport", ""), kind):
            continue
        name = normalize(record["name"])
        primary = normalize(" ".join([record["name"], record.get("summary", "")]))
        haystack = normalize(" ".join([
            primary,
            record.get("heading_title", ""),
            " ".join(record.get("message_types", [])),
        ]))
        if name == query:
            score = 4
        elif query in name:
            score = 3
        elif all(any(term in primary for term in group) for group in groups):
            score = 2
        elif all(any(term in haystack for term in group) for group in groups):
            score = 1
        else:
            continue
        matches.append((score, record))
    # Shared headings and message classes can mention both commands and states.
    if any(score >= 2 for score, _ in matches):
        matches = [item for item in matches if item[0] >= 2]
    return [record for _, record in sorted(
        matches, key=lambda item: (-item[0], item[1]["name"], item[1]["source_url"])
    )]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Exact identifier or Korean/English search words")
    parser.add_argument("--kind", choices=["all", "topic", "rpc"], default="all")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true", help="Return source-backed records as JSON")
    args = parser.parse_args(argv)
    if not args.query.strip():
        parser.error("검색어를 입력해 주세요.")
    if args.limit < 1:
        parser.error("--limit은 1 이상이어야 합니다.")
    try:
        catalog = json.loads((ROOT / "catalog.json").read_text())
        aliases = json.loads((ROOT / "references/search-aliases.json").read_text())
    except (OSError, json.JSONDecodeError) as error:
        parser.exit(2, f"색인 파일을 읽을 수 없습니다: {error}\n")
    found = search_interfaces(catalog["interfaces"], args.query, aliases, args.kind)
    result = {
        "query": args.query,
        "kind": args.kind,
        "doc_version": catalog["doc_version"],
        "checked_at": catalog["checked_at"],
        "runtime_verified": False,
        "total_matches": len(found),
        "results": found[:args.limit],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(f"문서 후보 {len(found)}개 | {catalog['doc_version']} | 실제 장비 미검증")
    if not found:
        print("색인에서 찾지 못했습니다. 지원 여부를 단정하지 말고 공식 원문과 설치된 SDK를 확인하세요.")
    for record in result["results"]:
        print(f"\n{record['name']} [{record['transport']}]")
        print(f"  메시지 타입: {', '.join(record['message_types']) or '색인에 없음. 원문 확인 필요'}")
        print(f"  원문 절: {record['heading_title']}")
        print(f"  출처: {record['source_url']}")
        for warning in record.get("warnings", []):
            print(f"  확인 사항: {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
