"""Tests for sarif_export.py — written test-first (R1-PRC006).

Runs under pytest, or standalone: `python tests/test_sarif_export.py`.
Cases pinned by the plan-review-cycle:
 (a) file:line-line  -> region startLine/endLine          (R1-PRC004)
 (b) prose location  -> warning + default line 1          (R1-PRC006)
 (c) two findings preserve order                          (R1-PRC006)
 (d) Dropped findings excluded from SARIF results         (R1-PRC006)
 (e) message.text = title + first narrative line, non-empty (R2-PRC004)
 (f) Code-Scanning required fields present                (R1-PRC005)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sarif_export as sx  # noqa: E402

SAMPLE = """---
generated: 2026-06-19T14:30:00Z
skill: premortem-code
mode: standard
target: pr/test
scope: pr
stack_detected: [python-fastapi]
addenda_loaded: [stack-python-fastapi.md]
verdict: REWORK
risk_counts:
  high: 1
  medium: 1
  low: 0
dropped_findings_count: 1
---

## Detailed findings

### Finding 1: Race in counter increment

**Category:** concurrency
**Severity:** high
**Confidence:** confirmed
**Location:** `src/worker.py:142-150`
**Mitigation verified absent:** no lock around check-then-act; grep 'Lock(' -> 0

#### Failure narrative
Two requests incremented the same counter and one update was lost.
More detail on the second line.

### Finding 2: Default page size assumed

**Category:** load_bearing_defaults
**Severity:** medium
**Confidence:** likely
**Location:** prose location not structured
**Mitigation verified absent:** no validation of page_size

#### Failure narrative
A caller passed page_size=0 and the loop never terminated.

## Dropped findings (for transparency)

Suspected race in cache.py:30 - DROPPED at Evidence gate: a lock IS present.
"""


def test_parse_two_findings_in_order():
    fm, findings, dropped = sx.parse_premortem(SAMPLE)
    assert fm["verdict"] == "REWORK"
    assert len(findings) == 2  # (c) + (d): dropped not in findings
    assert findings[0]["title"] == "Race in counter increment"
    assert findings[1]["title"] == "Default page size assumed"


def test_structured_location_range():
    _, findings, _ = sx.parse_premortem(SAMPLE)
    f0 = findings[0]
    assert f0["file"] == "src/worker.py"
    assert f0["start_line"] == 142
    assert f0["end_line"] == 150
    assert f0["location_valid"] is True


def test_prose_location_defaults_to_line_1_with_warning(capsys=None):
    _, findings, _ = sx.parse_premortem(SAMPLE)
    f1 = findings[1]
    assert f1["location_valid"] is False
    sarif = sx.build_sarif(findings)
    region = sarif["runs"][0]["results"][1]["locations"][0]["physicalLocation"]["region"]
    assert region["startLine"] == 1  # (b) default


def test_message_text_is_title_plus_first_narrative_line():
    _, findings, _ = sx.parse_premortem(SAMPLE)
    sarif = sx.build_sarif(findings)
    msg = sarif["runs"][0]["results"][0]["message"]["text"]
    assert msg  # (e) non-empty
    assert "Race in counter increment" in msg
    assert "lost" in msg  # first narrative line included


def test_code_scanning_required_fields():
    _, findings, _ = sx.parse_premortem(SAMPLE)
    sarif = sx.build_sarif(findings)
    assert sarif["version"] == "2.1.0"
    driver = sarif["runs"][0]["tool"]["driver"]
    assert driver["rules"]  # (f) populated rules[]
    res0 = sarif["runs"][0]["results"][0]
    assert res0["level"] == "error"  # high -> error
    assert res0["ruleId"]
    assert isinstance(res0["ruleIndex"], int)
    assert res0["properties"]["security-severity"]  # sort key
    assert res0["partialFingerprints"]  # dedup/track
    # medium -> warning
    assert sarif["runs"][0]["results"][1]["level"] == "warning"


def test_dropped_section_not_in_results():
    _, _, dropped = sx.parse_premortem(SAMPLE)
    assert dropped  # captured separately
    sarif = sx.build_sarif(sx.parse_premortem(SAMPLE)[1])
    assert len(sarif["runs"][0]["results"]) == 2  # (d)


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
