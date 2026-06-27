#!/usr/bin/env python3
"""Recommend a premortem-code effort/mode (quick|standard|deep) for a diff.

Advisory only. It suggests how much adversarial effort a change likely warrants,
keyed on blast radius and sensitivity — the same idea as spending more test-time
compute on harder problems (alloc by difficulty). It is deliberately conservative:
when the diff touches a sensitive surface (migrations, auth/RLS, concurrency, infra)
it never recommends below `deep`, and when signals are ambiguous it rounds up. The
human decides; this only sets a starting point.

Usage:
    git diff | python scripts/classify_effort.py
    python scripts/classify_effort.py --diff changes.patch

Output: JSON {recommended_mode, signals, rationale, stats} on stdout; exit 0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Sensitive surfaces. A hit forces at least `deep` (high blast radius / non-obvious failure).
# Path-keyed signals are matched on changed file paths; content-keyed on added/removed lines.
_PATH_SIGNALS = {
    "migration": re.compile(r"(^|/)(migrations?|alembic)/|\.sql$", re.I),
    "infra": re.compile(
        r"(^|/)(Dockerfile|docker-compose[^/]*|k8s)/?|\.(tf|cdk\.(ts|py))$"
        r"|(deployment|statefulset|daemonset)\.ya?ml$",
        re.I,
    ),
}
_CONTENT_SIGNALS = {
    "auth": re.compile(r"\b(auth|rls|policy|permission|login|password|token|jwt|oauth)\b", re.I),
    "concurrency": re.compile(
        r"\b(lock|mutex|semaphore|threading|asyncio|atomic|incr|decr|transaction|for\s+update|race)\b",
        re.I,
    ),
}
_DOCY = re.compile(r"\.(md|rst|txt)$|(^|/)docs?/|(^|/)(LICENSE|NOTICE|CREDITS)", re.I)
_TESTY = re.compile(r"(^|/)tests?/|(^|/)test_|_test\.", re.I)

# Tuning constants (documented to avoid voodoo numbers).
_SMALL_LOC = 40   # a one-spot change a single reviewer can hold in their head
_BIG_LOC = 400    # large enough that multi-lens deep review pays off


def _parse_diff(text: str):
    """Return (changed_files, added_lines, removed_lines, content_added)."""
    files: set[str] = set()
    added = removed = 0
    content_added: list[str] = []
    for line in text.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            m = re.match(r"^[+-]{3} [ab]/(.+)$", line)
            if m and m.group(1) != "/dev/null":
                files.add(m.group(1))
            continue
        if line.startswith("diff --git"):
            m = re.search(r" b/(.+)$", line)
            if m:
                files.add(m.group(1))
            continue
        if line.startswith("+"):
            added += 1
            content_added.append(line[1:])
        elif line.startswith("-"):
            removed += 1
    return files, added, removed, content_added


def classify(diff_text: str) -> dict:
    files, added, removed, content_added = _parse_diff(diff_text)
    loc = added + removed
    content = "\n".join(content_added)

    signals = []
    for name, rx in _PATH_SIGNALS.items():
        if any(rx.search(f) for f in files):
            signals.append(name)
    for name, rx in _CONTENT_SIGNALS.items():
        if rx.search(content):
            signals.append(name)
    signals = sorted(set(signals))

    # Top-level path segment ~ "module"; distinct count approximates blast radius.
    modules = {f.split("/")[0] for f in files}
    doc_or_test_only = bool(files) and all(_DOCY.search(f) or _TESTY.search(f) for f in files)

    if signals:
        mode = "deep"
        rationale = (
            f"touches sensitive surface(s): {', '.join(signals)} — non-obvious failure modes "
            "warrant the deep lens; never recommended below deep for these."
        )
    elif doc_or_test_only:
        mode = "quick"
        rationale = "docs/tests only — minimal production blast radius."
    elif loc <= _SMALL_LOC and len(files) <= 1 and len(modules) <= 1:
        mode = "quick"
        rationale = f"small, local change ({loc} LOC, 1 file/module) with no sensitive signal."
    elif len(modules) >= 3 or loc >= _BIG_LOC:
        mode = "deep"
        rationale = f"wide blast radius ({len(modules)} modules, {loc} LOC) — cross-cutting review."
    else:
        mode = "standard"
        rationale = f"non-trivial but bounded change ({len(files)} files, {len(modules)} modules, {loc} LOC)."

    return {
        "recommended_mode": mode,
        "signals": signals,
        "rationale": rationale,
        "stats": {
            "files": len(files),
            "modules": sorted(modules),
            "added": added,
            "removed": removed,
        },
        "advisory": True,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Recommend a premortem-code mode for a diff.")
    ap.add_argument("--diff", help="path to a unified diff (default: read stdin)")
    args = ap.parse_args(argv)
    text = Path(args.diff).read_text(encoding="utf-8") if args.diff else sys.stdin.read()
    print(json.dumps(classify(text), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
