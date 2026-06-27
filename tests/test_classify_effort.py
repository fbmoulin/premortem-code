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


def test_removed_sensitive_guard_forces_deep():
    # Deleting a lock (or any sensitive guard) must be caught even though it is a
    # removal, not an addition — it must not slip below `deep`.
    diff = (
        "diff --git a/worker.py b/worker.py\n--- a/worker.py\n+++ b/worker.py\n"
        "@@ -1,2 +1 @@\n-    with lock:\n-        counter += 1\n+    counter += 1\n"
    )
    out = ce.classify(diff)
    assert "concurrency" in out["signals"]
    assert out["recommended_mode"] == "deep"


def test_removed_permission_check_in_snake_case_forces_deep():
    # `check_permission` (snake_case) must trigger even on removal.
    diff = (
        "diff --git a/view.py b/view.py\n--- a/view.py\n+++ b/view.py\n"
        "@@ -1 +0,0 @@\n-    check_permission(user)\n"
    )
    out = ce.classify(diff)
    assert "auth" in out["signals"]
    assert out["recommended_mode"] == "deep"


def test_block_keyword_does_not_false_trigger_concurrency():
    # `blocked`/`block` (letter before 'lock') must NOT be read as a lock.
    diff = _diff("src/ui.py") + "@@ x @@\n+    render_blocked_state()\n"
    out = ce.classify(diff)
    assert "concurrency" not in out["signals"]


def test_diff_header_with_timestamp_is_parsed():
    # Plain `diff -u` appends a tab + timestamp after the path; it must not leak
    # into the captured filename (which would break signal detection).
    diff = (
        "--- a/db/migrations/x.sql\t2026-06-27 12:00:00\n"
        "+++ b/db/migrations/x.sql\t2026-06-27 12:00:01\n"
        "@@ -1 +1 @@\n+UPDATE t SET x = x + 1;\n"
    )
    out = ce.classify(diff)
    assert out["stats"]["files"] == 1
    assert "migration" in out["signals"]
    assert out["recommended_mode"] == "deep"


def test_root_files_do_not_inflate_to_deep():
    # Three root-level, non-sensitive code files must not masquerade as 3 modules.
    diff = _diff("a.py", 5) + _diff("b.py", 5) + _diff("c.py", 5)
    out = ce.classify(diff)
    assert out["stats"]["modules"] == [""]  # collapsed to one bucket
    assert out["recommended_mode"] != "deep"


def test_main_emits_json(tmp_path, capsys):
    p = tmp_path / "changes.patch"
    p.write_text(_diff("README.md"), encoding="utf-8")
    rc = ce.main(["--diff", str(p)])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"recommended_mode"' in out


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except TypeError:
                pass  # skip fixture-taking tests in standalone mode
    print("ok")
