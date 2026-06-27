"""End-to-end test for the SARIF exporter CLI (`sarif_export.main`).

The unit tests in `test_sarif_export.py` exercise the internal functions
(`parse_premortem`, `build_sarif`). This test drives the public CLI entry point
end-to-end: it writes a PREMORTEM file, runs `main(["--input", ...])`, and
validates the written `.sarif.json` — including against the bundled OASIS
SARIF 2.1.0 schema (`fixtures/sarif-schema-2.1.0.json`, JSON Schema draft-04).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sarif_export as sx  # noqa: E402
from test_sarif_export import SAMPLE  # reuse the canonical PREMORTEM fixture  # noqa: E402

_SCHEMA_PATH = Path(__file__).resolve().parent / "fixtures" / "sarif-schema-2.1.0.json"


def _run(tmp_path, name="PREMORTEM-2026-06-27T00-00-00Z.md"):
    src = tmp_path / name
    src.write_text(SAMPLE, encoding="utf-8")
    rc = sx.main(["--input", str(src)])
    out = src.with_name(src.stem + ".sarif.json")
    return rc, out


def test_cli_writes_sarif_file(tmp_path):
    """main() exits 0 and writes a sibling .sarif.json with the core invariants."""
    rc, out = _run(tmp_path)
    assert rc == 0
    assert out.is_file(), f"exporter did not write {out}"
    sarif = json.loads(out.read_text(encoding="utf-8"))
    # Run unconditionally so a missing jsonschema cannot turn this into a false green.
    assert sarif["version"] == "2.1.0"
    assert "runs" in sarif and sarif["runs"]
    assert sarif["runs"][0]["results"], "expected at least one SARIF result"


def test_cli_output_validates_against_oasis_schema(tmp_path):
    """The emitted SARIF validates against the official OASIS 2.1.0 schema (draft-04).

    jsonschema is a declared dev dependency (requirements-dev.txt), so import it
    directly — a missing dep should fail loudly here, not silently skip the check.
    """
    import jsonschema
    _, out = _run(tmp_path)
    sarif = json.loads(out.read_text(encoding="utf-8"))
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    # The schema declares $schema: draft-04, so validate with Draft4Validator explicitly.
    jsonschema.Draft4Validator(schema).validate(sarif)


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        test_cli_writes_sarif_file(Path(d))
    with tempfile.TemporaryDirectory() as d:
        test_cli_output_validates_against_oasis_schema(Path(d))
    print("ok")
