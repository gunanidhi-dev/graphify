"""Dependency-free structural extraction for CFML source files."""
from __future__ import annotations

import re
from pathlib import Path
from graphify.extractors.base import _file_stem, _make_id

_ATTR_RE = re.compile(r"([A-Za-z_][\w.-]*)\s*=\s*(['\"])(.*?)\2", re.DOTALL)
_COMPONENT_RE = re.compile(r"<cfcomponent\b([^>]*)>|\bcomponent\b([^\{;]*)\{", re.IGNORECASE)
_TAG_FUNCTION_RE = re.compile(r"<cffunction\b([^>]*)>", re.IGNORECASE)
_SCRIPT_FUNCTION_RE = re.compile(r"(?im)^\s*(?:(?:public|private|package|remote|static|final|abstract)\s+)*(?:[\w.$:\[\]]+\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(")
_INCLUDE_RE = re.compile(r"<cfinclude\b[^>]*\btemplate\s*=\s*(['\"])(.*?)\1|\binclude\s+(['\"])(.*?)\3\s*;", re.IGNORECASE)
_IMPORT_RE = re.compile(r"\bimport\s+([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+)\s*;", re.IGNORECASE)


def _attributes(raw: str) -> dict[str, str]:
    return {m.group(1).lower(): m.group(3).strip() for m in _ATTR_RE.finditer(raw)}


def extract_cfml(path: Path) -> dict:
    """Extract tag/CFScript components, functions, inheritance and imports."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"nodes": [], "edges": []}
    str_path, stem = str(path), _file_stem(path)
    file_nid = _make_id(str_path)
    nodes: list[dict] = []
    edges: list[dict] = []
    seen: set[str] = set()

    def line_at(offset: int) -> int:
        return source.count("\n", 0, offset) + 1

    def add_node(nid: str, label: str, line: int) -> None:
        if nid not in seen:
            seen.add(nid)
            nodes.append({"id": nid, "label": label, "file_type": "code", "source_file": str_path, "source_location": f"L{line}"})

    def add_edge(src: str, target: str, relation: str, line: int) -> None:
        edges.append({"source": src, "target": target, "relation": relation, "confidence": "EXTRACTED", "source_file": str_path, "source_location": f"L{line}", "weight": 1.0})

    add_node(file_nid, path.name, 1)
    component_nid = file_nid
    match = _COMPONENT_RE.search(source)
    if match:
        attrs = _attributes(match.group(1) or match.group(2) or "")
        name, line = attrs.get("name") or path.stem, line_at(match.start())
        component_nid = _make_id(stem, name)
        add_node(component_nid, name, line)
        add_edge(file_nid, component_nid, "contains", line)
        for attr, relation in (("extends", "inherits"), ("implements", "implements")):
            for target in filter(None, re.split(r"\s*,\s*", attrs.get(attr, ""))):
                target_nid = _make_id(target)
                add_node(target_nid, target, line)
                add_edge(component_nid, target_nid, relation, line)

    declarations: list[tuple[int, str]] = []
    for fn in _TAG_FUNCTION_RE.finditer(source):
        name = _attributes(fn.group(1)).get("name")
        if name:
            declarations.append((fn.start(), name))
    declarations.extend((fn.start(), fn.group(1)) for fn in _SCRIPT_FUNCTION_RE.finditer(source))
    function_ids: set[str] = set()
    for offset, name in sorted(declarations):
        function_nid = _make_id(component_nid, name)
        if function_nid in function_ids:
            continue
        function_ids.add(function_nid)
        line = line_at(offset)
        add_node(function_nid, f".{name}()" if component_nid != file_nid else f"{name}()", line)
        add_edge(component_nid, function_nid, "method" if component_nid != file_nid else "contains", line)

    for include in _INCLUDE_RE.finditer(source):
        target, line = include.group(2) or include.group(4), line_at(include.start())
        target_nid = _make_id(target)
        add_node(target_nid, target, line)
        add_edge(file_nid, target_nid, "imports", line)
    for imp in _IMPORT_RE.finditer(source):
        target, line = imp.group(1), line_at(imp.start())
        target_nid = _make_id(target)
        add_node(target_nid, target, line)
        add_edge(file_nid, target_nid, "imports", line)
    return {"nodes": nodes, "edges": edges, "input_tokens": 0, "output_tokens": 0}
