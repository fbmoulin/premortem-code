#!/usr/bin/env python3
"""Convert a PREMORTEM-<ISO8601>.md into SARIF 2.1.0 for GitHub Code Scanning.

CLI (R1-PRC003):
    python sarif_export.py --input .premortems/PREMORTEM-<ts>.md
Writes `<input without .md>.sarif.json` next to the input and exits 0 on success.

Written independently from the public SARIF 2.1.0 schema
(https://json.schemastore.org/sarif-2.1.0.json) and GitHub's documented Code
Scanning ingestion (the `security-severity` and `partialFingerprints` properties and
the result `level` mapping). It does NOT reuse any AGPL-licensed source; see CREDITS.md.

Requires Python >= 3.10 and pyyaml.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

# Severity -> SARIF result.level (GitHub renders error/warning/note).
_LEVEL: dict[str, str] = {"high": "error", "medium": "warning", "low": "note"}
# Severity -> a CVSS-style 0-10 number; Code Scanning sorts on `security-severity`.
_SECURITY_SEVERITY: dict[str, str] = {"high": "8.0", "medium": "5.0", "low": "3.0"}
_SEV_RANK: dict[str, int] = {"high": 0, "medium": 1, "low": 2}
_CONFIDENCE = {"confirmed", "likely", "speculative"}

_INFO_URI = "https://github.com/fbmoulin/premortem-code"
_TOOL_VERSION = "1.0.0"

_LOCATION_RE = re.compile(r"^(.+):(\d+)(?:-(\d+))?$")
_FIELD_RE = {
    "category": re.compile(r"\*\*Category:\*\*\s*(.+)"),
    "severity": re.compile(r"\*\*Severity:\*\*\s*(.+)"),
    "confidence": re.compile(r"\*\*Confidence:\*\*\s*(.+)"),
    "location": re.compile(r"\*\*Location:\*\*\s*(.+)"),
    "mitigation": re.compile(r"\*\*Mitigation verified absent:\*\*\s*(.+)"),
}


def parse_location(raw: str) -> tuple[str | None, int | None, int | None, bool]:
    """Return (file, start_line, end_line, valid). Enforces file:line[-line]."""
    cleaned = raw.strip().strip("`").strip()
    m = _LOCATION_RE.match(cleaned)
    if not m:
        return None, None, None, False
    file, start, end = m.group(1), int(m.group(2)), m.group(3)
    return file, start, (int(end) if end else start), True


def _first_narrative_line(block: str) -> str:
    after = block.split("#### Failure narrative", 1)
    if len(after) < 2:
        return ""
    for line in after[1].splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def parse_premortem(text: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    """Parse frontmatter, detailed findings, and dropped findings.

    Dropped findings are returned separately and never become SARIF results.
    """
    fm: dict[str, Any] = {}
    if text.lstrip().startswith("---"):
        chunks = text.split("---", 2)
        if len(chunks) >= 3:
            fm = yaml.safe_load(chunks[1]) or {}

    # Isolate the "Detailed findings" region (exclude "Dropped findings").
    detailed = text
    dropped_text = ""
    if "## Dropped findings" in text:
        detailed, dropped_text = text.split("## Dropped findings", 1)
    if "## Detailed findings" in detailed:
        detailed = detailed.split("## Detailed findings", 1)[1]

    findings: list[dict[str, Any]] = []
    blocks = re.split(r"^### Finding\s+\d+:\s*", detailed, flags=re.MULTILINE)
    for block in blocks[1:]:  # blocks[0] is preamble before the first finding
        title = block.splitlines()[0].strip()
        rec: dict[str, Any] = {"title": title}
        for key, rx in _FIELD_RE.items():
            mm = rx.search(block)
            rec[key] = mm.group(1).strip() if mm else ""
        file, start, end, valid = parse_location(rec.get("location", ""))
        rec.update(file=file, start_line=start, end_line=end, location_valid=valid)
        narrative = _first_narrative_line(block)
        rec["message_text"] = f"{title} — {narrative}" if narrative else title
        # Severity normalization: a source-catalogue "critical" maps to high
        # (the contract has only high/medium/low). Without this a "critical"
        # finding would fall through to low — a severity inversion.
        sev = rec.get("severity", "").strip().lower()
        if sev == "critical":
            sev = "high"
        rec["severity"] = sev if sev in _LEVEL else "low"
        # Confidence normalization to the fixed enum (R2-PRC001).
        conf = rec.get("confidence", "").strip().lower()
        rec["confidence"] = conf if conf in _CONFIDENCE else "speculative"
        if not valid:
            print(
                f"WARNING: finding '{title}' has a non-structured location "
                f"({rec.get('location')!r}); defaulting to line 1.",
                file=sys.stderr,
            )
        findings.append(rec)

    dropped = [ln.strip() for ln in dropped_text.splitlines() if ln.strip()]
    return fm, findings, dropped


def _fingerprint(rec: dict[str, Any]) -> str:
    key = f"{rec.get('category')}|{rec.get('file')}|{rec.get('title')}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def build_sarif(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a SARIF 2.1.0 log from parsed findings."""
    # Rule per category; rule severity = most severe finding in that category.
    rule_sev: dict[str, str] = {}
    for f in findings:
        cat = f.get("category") or "uncategorized"
        cur = rule_sev.get(cat)
        if cur is None or _SEV_RANK[f["severity"]] < _SEV_RANK[cur]:
            rule_sev[cat] = f["severity"]

    rules: list[dict[str, Any]] = []
    rule_index: dict[str, int] = {}
    for f in findings:
        cat = f.get("category") or "uncategorized"
        if cat in rule_index:
            continue
        rule_index[cat] = len(rules)
        rules.append(
            {
                "id": cat,
                "name": cat,
                "shortDescription": {"text": f"premortem fragility: {cat}"},
                "properties": {"security-severity": _SECURITY_SEVERITY[rule_sev[cat]]},
            }
        )

    results: list[dict[str, Any]] = []
    for f in findings:
        cat = f.get("category") or "uncategorized"
        uri = f["file"] if f["location_valid"] else (f.get("location") or ".")
        start = f["start_line"] if f["location_valid"] else 1
        region: dict[str, Any] = {"startLine": start}
        if f["location_valid"] and f["end_line"] and f["end_line"] != start:
            region["endLine"] = f["end_line"]
        props = {
            "security-severity": _SECURITY_SEVERITY[f["severity"]],
            "confidence": f["confidence"],  # normalized to the enum in parse
        }
        results.append(
            {
                "ruleId": cat,
                "ruleIndex": rule_index[cat],
                "level": _LEVEL[f["severity"]],
                "message": {"text": f["message_text"]},
                "locations": [
                    {"physicalLocation": {"artifactLocation": {"uri": uri}, "region": region}}
                ],
                "partialFingerprints": {"premortemCode/v1": _fingerprint(f)},
                "properties": props,
            }
        )

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "premortem-code",
                        "version": _TOOL_VERSION,
                        "informationUri": _INFO_URI,
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }


def export(input_path: Path) -> Path:
    text = input_path.read_text(encoding="utf-8")
    _, findings, _ = parse_premortem(text)
    sarif = build_sarif(findings)
    out_path = input_path.with_suffix("")  # drop .md
    out_path = out_path.with_name(out_path.name + ".sarif.json")
    out_path.write_text(json.dumps(sarif, indent=2) + "\n", encoding="utf-8")
    n_cat = len({f.get("category") for f in findings})
    print(
        f"Wrote SARIF to {out_path} ({len(findings)} findings across {n_cat} categories)",
        file=sys.stderr,
    )
    return out_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Export a PREMORTEM markdown to SARIF 2.1.0.")
    ap.add_argument("--input", required=True, help="path to PREMORTEM-<ts>.md")
    args = ap.parse_args(argv)
    in_path = Path(args.input)
    if not in_path.is_file():
        print(f"ERROR: input not found: {in_path}", file=sys.stderr)
        return 1
    export(in_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
