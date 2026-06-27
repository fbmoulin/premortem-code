"""Tests for classify_effort.py — the advisory mode/effort classifier."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import classify_effort as ce  # noqa: E402


def _diff(path: str, body_lines: int = 3) -> str:
    body = "\n".join(f"+    line {i}" for i in range(body_lines))
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -1 +1 @@\n{body}\n"


def test_docs_only_is_quick():
    assert ce.classify(_diff("README.md"))["recommended_mode"] == "quick"


def test_small_local_change_is_quick():
    out = ce.classify(_diff("src/util.py", body_lines=5))
    assert out["recommended_mode"] == "quick"
    assert out["signals"] == []


def test_migration_path_forces_deep():
    out = ce.classify(_diff("db/migrations/0007_backfill.sql"))
    assert out["recommended_mode"] == "deep"
    assert "migration" in out["signals"]


def test_concurrency_keyword_in_content_forces_deep():
    diff = (
        "diff --git a/worker.py b/worker.py\n--- a/worker.py\n+++ b/worker.py\n"
        "@@ -1 +1 @@\n+    with lock:  # atomic increment\n"
    )
    out = ce.classify(diff)
    assert out["recommended_mode"] == "deep"
    assert "concurrency" in out["signals"]


def test_infra_path_forces_deep():
    out = ce.classify(_diff("k8s/deployment.yaml"))
    assert out["recommended_mode"] == "deep"
    assert "infra" in out["signals"]


def test_multi_module_nontrivial_is_at_least_standard():
    diff = _diff("api/handlers.py", 10) + _diff("billing/charge.py", 10)
    mode = ce.classify(diff)["recommended_mode"]
    assert mode in {"standard", "deep"}
    assert mode != "quick"


def test_main_emits_json(capsys):
    rc = ce.main(["--diff", str(_write_tmp())])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"recommended_mode"' in out


def _write_tmp() -> Path:
    import tempfile

    p = Path(tempfile.mkstemp(suffix=".patch")[1])
    p.write_text(_diff("README.md"), encoding="utf-8")
    return p


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except TypeError:
                pass  # skip fixture-taking tests in standalone mode
    print("ok")
