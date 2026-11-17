#!/usr/bin/env python3
"""Build the local A3 documentation guide from the shared source catalog."""

import argparse
import html
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
GUIDES = [
    {
        "id": "beginner", "name": "처음 시작하기", "skill": "a3-getting-started",
        "description": "A3 Ultra의 보드 구성과 개발 환경을 이해하고, 첫 읽기 작업에 필요한 문서를 순서대로 찾는다.",
        "question": "어느 보드에 연결하고, 어떤 환경에서 시작해야 할까?",
        "prefixes": ("01-", "02-", "04-", "06-"),
    },
    {
        "id": "interfaces", "name": "인터페이스 이해하기", "skill": "a3-interface-guide",
        "description": "ROS 2 Topic과 HTTP JSON RPC의 역할을 구분하고, 메시지 형식과 호출 조건의 원문으로 이동한다.",
        "question": "이 기능은 Topic인가, RPC인가? 호출 전에 무엇을 확인해야 할까?",
        "prefixes": ("03-", "05-", "07-00-"),
    },
    {
        "id": "hardware", "name": "하드웨어 찾아보기", "skill": "a3-hardware-guide",
        "description": "MDU, HDU, ADU와 센서, 연결부의 문서를 찾는다. 문서 사양과 실제 장비에서 확인한 값을 구분한다.",
        "question": "이 센서와 연결부는 어디에 있고, 어떤 보드와 연결될까?",
        "prefixes": ("01-", "07-06-", "09-"),
    },
    {
        "id": "finder-guide", "name": "정확한 Topic과 RPC 찾기", "skill": "a3-ros-interface-finder",
        "description": "기능이나 정확한 이름으로 인터페이스 후보를 찾고, 해당 API가 설명된 H1/H2/H3 절까지 바로 이동한다.",
        "question": "팔 관절, 카메라, 상태 조회에 해당하는 정확한 이름은 무엇일까?",
        "prefixes": ("03-", "07-"),
    },
]


def escape(value):
    return html.escape(str(value), quote=True)


def public_url(value):
    parsed = urlparse(str(value))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError(f"Expected a public source URL, got {value!r}")
    return str(value)


def source_link(url, label, class_name=""):
    return f'<a class="{escape(class_name)}" href="{escape(public_url(url))}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>'


def json_for_html(value):
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def heading_list(page):
    items = []
    for heading in page.get("headings", []):
        if not heading.get("id") or not heading.get("url"):
            continue
        level = int(heading["level"])
        items.append(
            f'<li data-level="{level}"><span class="heading-level">H{level}</span>'
            + source_link(heading["url"], heading["title"]) + "</li>"
        )
    return '<ul class="heading-list">' + "".join(items) + "</ul>"


def page_details(page, compact=False):
    count = sum(bool(h.get("id")) for h in page.get("headings", []))
    return (
        f'<details class="source-doc{ " compact" if compact else "" }">'
        f'<summary><span>{escape(page["title"])}</span><span class="minor">{count}개 절</span></summary>'
        f'<div class="source-content">{source_link(page["url"], "문서 전체 열기", "document-link")}'
        + heading_list(page) + "</div></details>"
    )


def render(catalog, aliases, related):
    pages = catalog["pages"]
    interfaces = catalog["interfaces"]
    guide_html = []
    for guide in GUIDES:
        selected = [p for p in pages if p["slug"].startswith(guide["prefixes"])]
        # The finder links to the complete index instead of repeating every API heading.
        if guide["id"] == "finder-guide":
            selected = [p for p in selected if p["slug"].startswith(("03-", "07-00-"))]
        guide_html.append(
            f'<section class="guide" id="{guide["id"]}" aria-labelledby="{guide["id"]}-title">'
            f'<div class="guide-intro"><span class="badge">스킬 초안</span><h2 id="{guide["id"]}-title">{guide["name"]}</h2>'
            f'<p>{guide["description"]}</p><p class="guide-question">{guide["question"]}</p>'
            f'<a class="skill-link" href="skills/{guide["skill"]}/SKILL.md">{guide["skill"]}<span>스킬 초안 열기 ↗</span></a>'
            + ('<a class="primary-link" href="#topic-search">인터페이스 검색으로 이동 →</a>' if guide["id"] == "finder-guide" else "")
            + '</div><div class="guide-sources">' + "".join(page_details(p, True) for p in selected) + '</div></section>'
        )
    related_html = []
    for item in related:
        related_html.append(
            '<li class="related-item"><div>' + source_link(item["url"], item["label"])
            + f'<p>{escape(item.get("note", ""))}</p></div><span class="source-status">{escape(item.get("status", "출처 확인 필요"))}</span></li>'
        )
    source_notes = catalog.get("coverage", {}).get("notes", [])
    topic_count = sum("topic" in x.get("transport", "").lower() for x in interfaces)
    rpc_count = sum("rpc" in x.get("transport", "").lower() for x in interfaces)
    data = {"interfaces": interfaces, "aliases": aliases}
    replacements = {
        "__GUIDES__": "".join(guide_html),
        "__PAGES__": "".join(page_details(p) for p in pages),
        "__RELATED__": "".join(related_html) or '<li class="empty">관련 저장소 링크가 아직 등록되지 않았어.</li>',
        "__COVERAGE_NOTES__": "".join(f"<li>{escape(note)}</li>" for note in source_notes),
        "__CHECKED_AT__": escape(catalog.get("checked_at", "확인 날짜 없음")),
        "__PAGE_COUNT__": str(len(pages)),
        "__HEADING_COUNT__": str(sum(len(p.get("headings", [])) for p in pages)),
        "__INTERFACE_COUNT__": str(len(interfaces)),
        "__TOPIC_COUNT__": str(topic_count),
        "__RPC_COUNT__": str(rpc_count),
        "__DATA__": json_for_html(data),
    }
    result = TEMPLATE
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


TEMPLATE = r'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>A3 Ultra 개발 문서와 스킬 가이드</title>
<style>
:root{--bg:#eef2f4;--paper:#fff;--text:#172b3a;--muted:#526675;--line:#cad5dd;--accent:#185d87;--tint:#e7f0f6;--code:#edf1f4;--warn:#755010;--warn-bg:#fff4d8;--focus:#087db9;--space:24px;--radius:7px;color-scheme:light}
@media(prefers-color-scheme:dark){:root{--bg:#111b23;--paper:#182731;--text:#e6eef3;--muted:#a6bac8;--line:#3a4d5a;--accent:#9ad1f3;--tint:#203b4d;--code:#243641;--warn:#f1ce83;--warn-bg:#3d3321;--focus:#72c9ff;color-scheme:dark}}
*{box-sizing:border-box}html{scroll-padding-top:24px}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.65 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",sans-serif}a{color:var(--accent);text-underline-offset:3px;overflow-wrap:anywhere}a:hover{text-decoration-thickness:2px}button,input,select{font:inherit}button,a,summary,input,select{-webkit-tap-highlight-color:transparent}:focus-visible{outline:3px solid var(--focus);outline-offset:4px}button{cursor:pointer}h1,h2,h3,p{margin:0}h1{font-size:26px;line-height:1.35;letter-spacing:-.03em}h2{font-size:21px;line-height:1.4;letter-spacing:-.02em}h3{font-size:16px}p{max-width:68ch}code,.mono{font:13px/1.6 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow-wrap:anywhere}code{background:var(--code);padding:2px 5px;border-radius:3px}ul{margin:0;padding-left:21px}small,.minor{font-size:12px;color:var(--muted)}.skip{position:fixed;left:12px;top:-80px;z-index:10;background:var(--paper);padding:12px}.skip:focus{top:12px}.shell{max-width:1530px;margin:auto;display:grid;grid-template-columns:224px minmax(0,1fr);gap:34px;padding:30px 34px 60px}.sidebar{align-self:start;position:sticky;top:28px;display:grid;gap:24px}.brand{display:grid;gap:7px;border-bottom:2px solid var(--text);padding-bottom:17px}.brand strong{font:700 18px/1.3 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.03em}.brand span{color:var(--muted);font-size:12px}.sidebar nav{display:grid;gap:4px}.sidebar nav a{display:block;padding:8px 10px;border-radius:var(--radius);text-decoration:none;color:var(--text)}.sidebar nav a:hover{background:var(--tint)}.nav-separator{border-top:1px solid var(--line);margin-top:8px;padding-top:8px}.sidebar-note{font-size:12px;color:var(--muted);display:grid;gap:10px}.sidebar-note a{display:block}.main{min-width:0;display:grid;gap:28px}.page-header{display:grid;gap:15px;padding:3px 0 24px;border-bottom:1px solid var(--line)}.page-header>p{color:var(--muted)}.status-line{display:flex;flex-wrap:wrap;align-items:center;gap:8px;font-size:12px}.badge{padding:3px 8px;background:var(--tint);color:var(--accent);border-radius:4px;font-weight:600}.status-line time{color:var(--muted);overflow-wrap:anywhere}.coverage{display:flex;flex-wrap:wrap;gap:10px 25px;color:var(--muted);font-size:13px}.coverage strong{font-size:17px;font-variant-numeric:tabular-nums;color:var(--text);margin-right:4px}.notice{display:grid;gap:6px;padding:14px 17px;border:1px solid var(--line);background:var(--paper);border-radius:var(--radius);font-size:13px}.notice strong{font-weight:650}.guide{display:grid;grid-template-columns:minmax(220px,.8fr) minmax(0,1.2fr);gap:24px;padding:26px 0;border-bottom:1px solid var(--line)}.guide-intro{display:flex;flex-direction:column;align-items:flex-start;gap:12px}.guide-intro>p{color:var(--muted);font-size:14px}.guide-question{font-size:13px!important;color:var(--text)!important}.skill-link{display:flex;flex-direction:column;gap:2px;font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;text-decoration:none;padding:9px 11px;border:1px solid var(--line);border-radius:var(--radius);max-width:100%;background:var(--paper)}.skill-link span{font:12px/1.5 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;color:var(--muted)}.primary-link{font-weight:600;font-size:13px}.guide-sources{display:grid;align-content:start;gap:9px;min-width:0}.source-doc{border:1px solid var(--line);border-radius:var(--radius);background:var(--paper);min-width:0}.source-doc summary{display:flex;gap:12px;align-items:baseline;justify-content:space-between;padding:13px 15px;cursor:pointer;font-size:14px;font-weight:600;list-style:none}.source-doc summary::-webkit-details-marker{display:none}.source-doc summary:before{content:"+";font:16px/1 ui-monospace,monospace;color:var(--accent);flex:0 0 12px}.source-doc[open] summary:before{content:"−"}.source-doc summary>span:first-of-type{flex:1;overflow-wrap:anywhere}.source-doc summary .minor{white-space:nowrap;font-weight:400}.source-doc[open] summary{border-bottom:1px solid var(--line)}.source-content{display:grid;gap:12px;padding:13px 15px}.document-link{font-size:12px;justify-self:start}.heading-list{display:grid;gap:9px;padding:0;list-style:none}.heading-list li{display:flex;align-items:baseline;gap:9px;font-size:13px}.heading-list li[data-level="2"]{padding-left:12px}.heading-list li[data-level="3"]{padding-left:24px}.heading-list li[data-level="4"]{padding-left:36px}.heading-level{flex:0 0 23px;font:10px/1.5 ui-monospace,monospace;color:var(--muted);border:1px solid var(--line);text-align:center}.section-head{display:flex;gap:15px;justify-content:space-between;align-items:baseline;flex-wrap:wrap}.section{display:grid;gap:17px;min-width:0;scroll-margin-top:24px}.section-description{color:var(--muted);font-size:14px}.search-panel{padding:20px;background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);display:grid;gap:13px}.search-controls{display:grid;grid-template-columns:minmax(0,1fr) 150px auto;gap:12px;align-items:end}.field{display:grid;gap:5px;min-width:0}.field label{font-size:12px;font-weight:600;color:var(--muted)}input,select{width:100%;min-width:0;border:1px solid var(--line);border-radius:5px;padding:10px 11px;background:var(--bg);color:var(--text)}input[type=search]{appearance:none}button{border:1px solid var(--line);border-radius:5px;padding:10px 13px;background:var(--paper);color:var(--text)}button:hover{background:var(--tint)}.search-help{color:var(--muted);font-size:12px;display:grid;gap:3px}.search-feedback{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px;font-size:12px;color:var(--muted)}#interface-count{font-weight:600;color:var(--text)}.interface-list{display:grid;gap:0;border-top:1px solid var(--line)}.interface-row{background:var(--paper);border:1px solid var(--line);border-top:0;min-width:0}.interface-row summary{padding:15px 17px;cursor:pointer;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px 14px;list-style:none}.interface-row summary::-webkit-details-marker{display:none}.interface-name{font:600 13px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:anywhere;color:var(--accent)}.interface-summary{font-size:13px;color:var(--muted);grid-column:1/-1}.transport{font:11px/1.5 ui-monospace,monospace;align-self:start;background:var(--code);padding:3px 6px;white-space:nowrap;border-radius:3px}.interface-row[open] summary{border-bottom:1px solid var(--line)}.interface-detail{padding:15px 17px;display:grid;gap:12px}.interface-detail dl{margin:0;display:grid;grid-template-columns:110px minmax(0,1fr);gap:9px 14px;font-size:13px}.interface-detail dt{color:var(--muted)}.interface-detail dd{margin:0;overflow-wrap:anywhere}.interface-detail ul{display:grid;gap:5px}.warning{padding:10px 12px;background:var(--warn-bg);color:var(--warn);font-size:12px;border-radius:4px}.empty{padding:26px 20px;border:1px dashed var(--line);color:var(--muted);background:var(--paper);font-size:14px}.empty strong{display:block;color:var(--text);margin-bottom:6px}.docs-list{display:grid;gap:10px}.related-list{list-style:none;padding:0;display:grid;gap:0;border-top:1px solid var(--line)}.related-item{display:flex;gap:16px;justify-content:space-between;align-items:flex-start;padding:17px 0;border-bottom:1px solid var(--line)}.related-item a{font-weight:600}.related-item p{font-size:13px;color:var(--muted);margin-top:5px}.source-status{font-size:11px;border:1px solid var(--line);border-radius:4px;padding:3px 7px;max-width:170px;flex:0 0 auto}.provenance{font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:20px;display:grid;gap:10px}.provenance ul{display:grid;gap:5px}.noscript{padding:14px;border:1px solid var(--line);background:var(--paper)}[hidden]{display:none!important}
@media(max-width:1050px){.shell{grid-template-columns:185px minmax(0,1fr);gap:24px;padding:24px}.guide{grid-template-columns:1fr}.guide-intro{max-width:70ch}.search-controls{grid-template-columns:minmax(0,1fr) 125px}.search-controls button{grid-column:1/-1;justify-self:start;padding:7px 13px}}
@media(max-width:700px){.shell{display:block;padding:18px 16px 40px}.sidebar{position:static;gap:14px;margin-bottom:24px}.brand{padding-bottom:12px}.sidebar nav{display:flex;flex-wrap:wrap;gap:4px}.sidebar nav a{padding:6px 9px;background:var(--paper);border:1px solid var(--line);font-size:12px}.nav-separator{border:0;margin:0;padding:0}.sidebar-note{display:none}.main{gap:24px}h1{font-size:24px}h2{font-size:20px}.guide{padding:19px 0;gap:16px}.search-panel{padding:14px}.search-controls{grid-template-columns:1fr}.search-controls button{grid-column:auto}.interface-row summary{padding:13px;grid-template-columns:1fr}.transport{justify-self:start}.interface-detail{padding:13px}.interface-detail dl{grid-template-columns:1fr;gap:3px}.interface-detail dd{margin-bottom:7px}.heading-list li[data-level="3"]{padding-left:14px}.heading-list li[data-level="2"]{padding-left:7px}.source-doc summary{padding:12px}.source-content{padding:12px}.related-item{flex-direction:column;gap:9px}.source-status{max-width:100%}.coverage{gap:6px 18px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>
</head>
<body>
<a class="skip" href="#main-content">본문으로 이동</a>
<div class="shell">
<aside class="sidebar" aria-label="가이드 목차">
<div class="brand"><strong>A3 ULTRA</strong><span>AimDK v3.3 / 문서 탐색 가이드</span></div>
<nav aria-label="주요 섹션">
<a href="#beginner">처음 시작하기</a><a href="#interfaces">인터페이스 이해하기</a><a href="#hardware">하드웨어 찾아보기</a><a href="#finder-guide">Topic 찾기 스킬</a><a class="nav-separator" href="#topic-search">Topic / RPC 검색</a><a href="#source-documents">공식 문서 전체 목차</a><a href="#related-sources">GitHub와 관련 자료</a>
</nav>
<div class="sidebar-note"><p>문서의 실제 절 주소를 연결한 로컬 가이드야. 로봇 연결이나 제어 명령은 실행하지 않아.</p><a href="catalog.json">공통 출처 목록 JSON</a><a href="references/guide-notes.md">검토 메모와 문서 불일치</a></div>
</aside>
<main class="main" id="main-content">
<header class="page-header">
<div class="status-line"><span class="badge">검토용 초안</span><span>A3 Ultra 소프트웨어 3.3.x 문서 기준</span></div>
<h1>필요한 기능에서 정확한 원문까지</h1>
<p>스킬 가이드, 공식 문서의 H1/H2/H3, 인터페이스 이름, GitHub 자료를 한곳에서 찾아봐. 원문 절 링크는 수집한 HTML의 실제 헤더 주소를 사용해.</p>
<div class="coverage" aria-label="수집 범위"><span><strong>__PAGE_COUNT__</strong>문서</span><span><strong>__HEADING_COUNT__</strong>헤더</span><span><strong>__TOPIC_COUNT__</strong>Topic 항목</span><span><strong>__RPC_COUNT__</strong>RPC 항목</span></div>
<div class="status-line"><span>출처 확인 시각</span><time>__CHECKED_AT__</time></div>
</header>
<div class="notice"><strong>문서에서 찾은 이름과 장비에서 확인한 상태를 구분해.</strong><p>여기의 결과는 원문을 찾아가는 후보 목록이야. 실제 설치 버전, 보드, 메시지 정의, QoS와 실행 조건은 장비에서 아직 검증하지 않았어. 네 스킬 초안도 이 범위를 기준으로 검토해 줘.</p></div>
<div class="guides">__GUIDES__</div>
<section class="section" id="topic-search" aria-labelledby="topic-search-title">
<div class="section-head"><h2 id="topic-search-title">Topic / RPC 검색</h2><span class="minor">원문 항목 __INTERFACE_COUNT__개 / 중복 출처 포함</span></div>
<p class="section-description">정확한 이름, 메시지 타입 또는 기능을 입력해. 결과를 펼치면 해당 API의 원문 절로 바로 이동할 수 있어.</p>
<div class="search-panel">
<form class="search-controls" id="interface-search-form" role="search">
<div class="field"><label for="interface-query">기능 또는 정확한 인터페이스 이름</label><input id="interface-query" type="search" placeholder="예: 팔 관절, 카메라, /motion/control/arm_joint_command" autocomplete="off" spellcheck="false" aria-describedby="search-help"></div>
<div class="field"><label for="transport-filter">인터페이스 종류</label><select id="transport-filter"><option value="all">전체</option><option value="topic">ROS 2 Topic</option><option value="rpc">HTTP / RPC</option></select></div>
<button type="button" id="clear-search">검색 초기화</button>
</form>
<div class="search-help" id="search-help"><span>한국어 검색은 등록된 동의어를 함께 찾고, 정확한 인터페이스 이름을 먼저 보여줘.</span><span>메시지 타입이나 보드 정보가 빠져 있으면 원문 확인이 필요해. Topic과 RPC는 따로 표시해.</span></div>
<div class="search-feedback"><span id="interface-count" role="status" aria-live="polite"></span><span>원문 색인 / 실제 장비 미검증</span></div>
</div>
<noscript><p class="noscript">검색에는 JavaScript가 필요해. 아래 공식 문서 목차와 스킬 원문 링크는 그대로 사용할 수 있어.</p></noscript>
<div id="interface-results" class="interface-list"></div>
</section>
<section class="section" id="source-documents" aria-labelledby="source-documents-title"><div class="section-head"><h2 id="source-documents-title">공식 문서 전체 목차</h2><span class="minor">제목을 펼쳐 실제 절로 이동</span></div><p class="section-description">원문 헤더 수준을 그대로 표시했어. API 세부 항목은 H3에도 있으므로 함께 연결했어.</p><div class="docs-list">__PAGES__</div></section>
<section class="section" id="related-sources" aria-labelledby="related-sources-title"><h2 id="related-sources-title">GitHub와 관련 자료</h2><p class="section-description">저장소와 문서 링크는 확인된 출처로 이어져. 공개 코드가 현재 장비에서 동작하는지는 별도 검증이 필요해.</p><ul class="related-list">__RELATED__</ul></section>
<footer class="provenance"><strong>출처와 검토 범위</strong><p>공식 문서는 바뀔 수 있어. 실제 개발 전에는 연결된 절의 최신 내용과 설치된 소프트웨어 버전을 다시 확인해.</p><ul>__COVERAGE_NOTES__</ul><p><a href="catalog.json">공통 출처 목록</a> / <a href="references/guide-notes.md">문서 불일치와 검토 메모</a></p></footer>
</main></div>
<script id="guide-data" type="application/json">__DATA__</script>
<script>
"use strict";
const data = JSON.parse(document.getElementById("guide-data").textContent);
const queryInput = document.getElementById("interface-query");
const transportFilter = document.getElementById("transport-filter");
const results = document.getElementById("interface-results");
const count = document.getElementById("interface-count");
const normalize = value => String(value || "").normalize("NFKC").toLowerCase().trim();
const aliases = Object.fromEntries(Object.entries(data.aliases).filter(([, words]) => Array.isArray(words)).map(([key, words]) => [normalize(key), words.map(normalize)]));
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function sourceLink(url, text) {
  const node = element("a", text);
  try {
    const parsed = new URL(url);
    if (!["https:", "http:"].includes(parsed.protocol) || parsed.username || parsed.password) return element("span", "원문 링크 확인 필요");
    node.href = parsed.href;
    node.target = "_blank";
    node.rel = "noopener noreferrer";
  } catch (_) { return element("span", "원문 링크 확인 필요"); }
  return node;
}
function addDefinition(list, term, content, code = false) {
  list.append(element("dt", term));
  const value = element("dd");
  value.append(typeof content === "string" ? element(code ? "code" : "span", content) : content);
  list.append(value);
}
const indexed = data.interfaces.map((item, index) => ({
  item, index,
  name: normalize(item.name),
  primary: normalize([item.name, item.summary].join(" ")),
  text: normalize([item.name, item.summary, item.heading_title, ...(item.message_types || [])].join(" ")),
  transport: normalize(item.transport)
}));
function score(entry, query, groups) {
  if (!query) return 1;
  if (entry.name === query) return 4;
  if (entry.name.includes(query)) return 3;
  if (groups.every(group => group.some(term => term && entry.primary.includes(term)))) return 2;
  return groups.every(group => group.some(term => term && entry.text.includes(term))) ? 1 : 0;
}
function renderResults() {
  const query = normalize(queryInput.value);
  const groups = (aliases[query] ? [query] : query.split(/\s+/).filter(Boolean)).map(term => [term, ...(aliases[term] || [])]);
  const kind = transportFilter.value;
  const textCompare = (a,b) => a === b ? 0 : (a < b ? -1 : 1);
  let matched = indexed.map(entry => ({...entry, rank: score(entry, query, groups)})).filter(entry => entry.rank && (kind === "all" || (kind === "topic" ? entry.transport.includes("topic") && !entry.transport.includes("rpc") : entry.transport.includes("rpc"))));
  if (matched.some(entry => entry.rank >= 2)) matched = matched.filter(entry => entry.rank >= 2);
  matched.sort((a,b) => b.rank - a.rank || textCompare(a.item.name,b.item.name) || textCompare(a.item.source_url,b.item.source_url));
  count.textContent = `${matched.length}개 문서 후보 / 전체 ${indexed.length}개 원문 항목`;
  results.replaceChildren();
  if (!matched.length) {
    const empty = element("div", undefined, "empty");
    empty.append(element("strong", "일치하는 인터페이스를 찾지 못했어."), element("p", "정확한 Topic 이름이나 다른 기능어로 찾아봐. 결과가 없다는 이유만으로 해당 기능이 없다고 판단하지 말고, 공식 문서 목차와 설치된 SDK를 확인해."));
    results.append(empty);
    return;
  }
  const fragment = document.createDocumentFragment();
  for (const {item} of matched) {
    const row = element("details", undefined, "interface-row");
    const summary = element("summary");
    summary.append(element("span", item.name, "interface-name"), element("span", item.transport || "종류 확인 필요", "transport"), element("span", item.summary || item.heading_title, "interface-summary"));
    row.append(summary);
    const detail = element("div", undefined, "interface-detail");
    const fields = element("dl");
    addDefinition(fields, "원문 절", sourceLink(item.source_url || item.page_url, item.heading_title || "관련 문서 열기"));
    addDefinition(fields, "메시지 타입", (item.message_types || []).join(" / ") || "색인에 없음. 원문과 설치된 메시지 정의 확인", Boolean(item.message_types && item.message_types.length));
    addDefinition(fields, "문서 대상 주소", item.target_host || "색인에서 확인되지 않음", Boolean(item.target_host));
    if (item.example_paths && item.example_paths.length) addDefinition(fields, "예제 경로", item.example_paths.join(" / "), true);
    addDefinition(fields, "실행 조건", "필드, 단위, QoS, 호출 주기와 제어 모드는 연결된 원문에서 확인");
    detail.append(fields);
    if (item.warnings && item.warnings.length) {
      const warning = element("div", undefined, "warning");
      warning.append(element("strong", "문서 확인 필요"));
      const list = element("ul");
      for (const text of item.warnings) list.append(element("li", text));
      warning.append(list); detail.append(warning);
    }
    row.append(detail); fragment.append(row);
  }
  results.append(fragment);
}
document.getElementById("interface-search-form").addEventListener("submit", event => { event.preventDefault(); renderResults(); });
queryInput.addEventListener("input", renderResults);
transportFilter.addEventListener("change", renderResults);
document.getElementById("clear-search").addEventListener("click", () => { queryInput.value = ""; transportFilter.value = "all"; renderResults(); queryInput.focus(); });
renderResults();
</script>
</body></html>
'''


class LinkCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.local_fragments = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
            if attrs["href"].startswith("#"):
                self.local_fragments.append(attrs["href"][1:])


def validate_output(output, catalog):
    parser = LinkCheck()
    parser.feed(output)
    missing = set(parser.local_fragments) - parser.ids
    if missing:
        raise ValueError(f"Missing internal sections: {missing}")
    expected = {h["url"] for p in catalog["pages"] for h in p.get("headings", []) if h.get("id") and h.get("url")}
    if not expected.issubset(set(parser.links)):
        raise ValueError("A source heading link was lost while rendering")
    start = output.index('<script id="guide-data" type="application/json">') + len('<script id="guide-data" type="application/json">')
    payload = output[start:output.index("</script>", start)]
    if json.loads(payload)["interfaces"] != catalog["interfaces"]:
        raise ValueError("The embedded interface catalog changed")


def self_check():
    dangerous = {"name": "</script><script>test</script>", "text": "<a>&\""}
    encoded = json_for_html(dangerous)
    assert "<" not in encoded and json.loads(encoded) == dangerous
    try:
        public_url("javascript:alert(1)")
    except ValueError:
        pass
    else:
        raise AssertionError("Executable URLs must be rejected")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate the existing output without writing it")
    args = parser.parse_args()
    self_check()
    catalog = json.loads((ROOT / "catalog.json").read_text())
    aliases = json.loads((ROOT / "references/search-aliases.json").read_text())
    related = json.loads((ROOT / "references/related-links.json").read_text())
    output = render(catalog, aliases, related)
    validate_output(output, catalog)
    target = ROOT / "index.html"
    if args.check:
        if target.read_text() != output:
            raise SystemExit("index.html is stale; run build_guide.py")
    else:
        target.write_text(output)
    print(f"{'Checked' if args.check else 'Built'} {target}: {len(catalog['pages'])} documents, {len(catalog['interfaces'])} interfaces")


if __name__ == "__main__":
    main()
