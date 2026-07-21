"""The review gate itself is load-bearing process infrastructure — test it
like code (docs/process/review-gate.md). Loaded from scripts/ by path."""

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "review_gate", Path(__file__).parents[1] / "scripts" / "review_gate.py"
)
assert _SPEC and _SPEC.loader
review_gate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(review_gate)

HASH = "a" * 64

# Each vendor's legs must carry a model from that vendor's allowlist.
MODEL_FOR_VENDOR = {"claude": "claude-fable-5", "codex": "gpt-5.6-sol"}


def artifact(leg: str, findings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "leg": leg,
        "model": MODEL_FOR_VENDOR[leg.split("-", 1)[0]],
        "reviewed_diff_sha256": HASH,
        "reviewed_at": "2026-07-21",
        "raw_output": "full leg output here",
        "findings": findings or [],
    }


def finding(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "F1",
        "summary": "a finding",
        "severity_claimed": "P2",
        "validated": True,
        "severity_validated": "P2",
        "disposition": "fixed",
    }
    base.update(overrides)
    return base


def write(tmp_path: Path, leg: str, data: dict[str, Any]) -> Path:
    p = tmp_path / f"{leg}.json"
    p.write_text(json.dumps(data))
    return p


class TestCheckArtifact:
    def test_clean_artifact_passes(self, tmp_path: Path) -> None:
        p = write(tmp_path, "codex-review", artifact("codex-review"))
        assert review_gate.check_artifact(p, "codex-review", "review", HASH) == []

    def test_stale_hash_fails(self, tmp_path: Path) -> None:
        p = write(tmp_path, "codex-review", artifact("codex-review"))
        fails = review_gate.check_artifact(p, "codex-review", "review", "b" * 64)
        assert any("STALE" in f for f in fails)

    def test_validated_p1_not_fixed_blocks(self, tmp_path: Path) -> None:
        f = finding(severity_validated="P1", disposition="dismissed", reason="nah")
        p = write(tmp_path, "codex-review", artifact("codex-review", [f]))
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("BLOCKING" in m for m in fails)

    def test_validated_high_security_not_fixed_blocks(self, tmp_path: Path) -> None:
        f = finding(
            severity_claimed="high",
            severity_validated="high",
            disposition="dismissed",
            reason="accepted",
        )
        p = write(tmp_path, "codex-security", artifact("codex-security", [f]))
        fails = review_gate.check_artifact(p, "codex-security", "security", HASH)
        assert any("BLOCKING" in m for m in fails)

    def test_validated_p1_fixed_passes(self, tmp_path: Path) -> None:
        f = finding(severity_validated="P1", disposition="fixed")
        p = write(tmp_path, "codex-review", artifact("codex-review", [f]))
        assert review_gate.check_artifact(p, "codex-review", "review", HASH) == []

    def test_unvalidated_finding_needs_reason(self, tmp_path: Path) -> None:
        f = finding(validated=False, reason="")
        p = write(tmp_path, "codex-review", artifact("codex-review", [f]))
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("require a reason" in m for m in fails)

    def test_dismissed_p2_with_reason_passes(self, tmp_path: Path) -> None:
        f = finding(severity_validated="P2", disposition="dismissed", reason="cosmetic only")
        p = write(tmp_path, "codex-review", artifact("codex-review", [f]))
        assert review_gate.check_artifact(p, "codex-review", "review", HASH) == []

    def test_wrong_severity_enum_for_leg_type(self, tmp_path: Path) -> None:
        f = finding(severity_validated="high")  # security enum on a review leg
        p = write(tmp_path, "codex-review", artifact("codex-review", [f]))
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("not in" in m for m in fails)

    def test_empty_raw_output_fails(self, tmp_path: Path) -> None:
        a = artifact("codex-review")
        a["raw_output"] = "  "
        p = write(tmp_path, "codex-review", a)
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("raw_output" in m for m in fails)

    def test_missing_fields_and_bad_json(self, tmp_path: Path) -> None:
        p = tmp_path / "codex-review.json"
        p.write_text("{not json")
        assert review_gate.check_artifact(p, "codex-review", "review", HASH)
        a = artifact("claude-code-review")
        del a["reviewed_at"]
        p2 = write(tmp_path, "claude-code-review", a)
        fails = review_gate.check_artifact(p2, "claude-code-review", "review", HASH)
        assert any("missing fields" in m for m in fails)


class TestModelAllowlist:
    def test_disallowed_claude_model_fails(self, tmp_path: Path) -> None:
        a = artifact("claude-code-review")
        a["model"] = "claude-haiku-4-5-20251001"  # below the floor
        p = write(tmp_path, "claude-code-review", a)
        fails = review_gate.check_artifact(p, "claude-code-review", "review", HASH)
        assert any("allowlist" in m for m in fails)

    def test_vendor_crossover_fails(self, tmp_path: Path) -> None:
        a = artifact("codex-review")
        a["model"] = "claude-fable-5"  # right floor, wrong vendor leg
        p = write(tmp_path, "codex-review", a)
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("allowlist" in m for m in fails)

    def test_allowed_models_pass(self, tmp_path: Path) -> None:
        for leg, model in [
            ("claude-code-review", "claude-opus-4-8"),
            ("claude-code-review", "claude-fable-5"),
        ]:
            a = artifact(leg)
            a["model"] = model
            p = write(tmp_path, leg, a)
            assert review_gate.check_artifact(p, leg, "review", HASH) == []

    def test_non_string_model_diagnostic_not_traceback(self, tmp_path: Path) -> None:
        a = artifact("codex-review")
        a["model"] = ["gpt-5.6-sol"]
        p = write(tmp_path, "codex-review", a)
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("model" in m for m in fails)


class TestRunGate:
    def test_missing_pr_dir_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(review_gate, "REVIEWS_ROOT", tmp_path)
        monkeypatch.setattr(review_gate, "compute_diff_hash", lambda base: HASH)
        assert review_gate.run_gate(999, "origin/main") == 1

    def test_missing_one_leg_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(review_gate, "REVIEWS_ROOT", tmp_path)
        monkeypatch.setattr(review_gate, "compute_diff_hash", lambda base: HASH)
        pr_dir = tmp_path / "pr-7"
        pr_dir.mkdir()
        for leg in ["claude-code-review", "claude-security-review", "codex-review"]:
            write(pr_dir, leg, artifact(leg))  # codex-security omitted
        assert review_gate.run_gate(7, "origin/main") == 1

    def test_all_four_legs_clean_passes(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(review_gate, "REVIEWS_ROOT", tmp_path)
        monkeypatch.setattr(review_gate, "compute_diff_hash", lambda base: HASH)
        pr_dir = tmp_path / "pr-7"
        pr_dir.mkdir()
        for leg in review_gate.REQUIRED_LEGS:
            write(pr_dir, leg, artifact(leg))
        assert review_gate.run_gate(7, "origin/main") == 0

    def test_hash_is_deterministic(self) -> None:
        # HEAD...HEAD is an empty diff but exercises the full subprocess
        # path; origin/main is NOT used — it may not exist in a shallow
        # CI checkout.
        h1 = review_gate.compute_diff_hash("HEAD")
        h2 = review_gate.compute_diff_hash("HEAD")
        assert h1 == h2 and len(h1) == 64

    def test_hash_rejects_option_injection_base(self) -> None:
        with pytest.raises(SystemExit):
            review_gate.compute_diff_hash("--output=/tmp/pwn")

    def test_hash_restales_when_merge_base_moves_with_identical_diff_bytes(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Security regression (codex, PR #1): a base advance that doesn't
        # touch the PR's files leaves the diff BYTES identical, but the
        # semantics may change — the hash must bind the merge-base id too.
        def git(*args: str) -> bytes:
            return subprocess.run(
                ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
                cwd=tmp_path,
                capture_output=True,
                check=True,
            ).stdout

        git("init", "-q", "-b", "main")
        (tmp_path / "f1.txt").write_text("base\n")
        (tmp_path / "f2.txt").write_text("y\n")
        git("add", "-A")
        git("commit", "-qm", "c1")
        git("checkout", "-qb", "feature")
        (tmp_path / "f2.txt").write_text("w\n")
        git("add", "f2.txt")
        git("commit", "-qm", "feature change")
        git("checkout", "-q", "main")
        (tmp_path / "f1.txt").write_text("advanced\n")  # doesn't touch f2
        git("add", "f1.txt")
        git("commit", "-qm", "c2")
        git("checkout", "-q", "feature")
        monkeypatch.setattr(review_gate, "REPO_ROOT", tmp_path)
        h_before = review_gate.compute_diff_hash("main")
        d_before = git("diff", "main...HEAD")
        git("rebase", "-q", "main")
        h_after = review_gate.compute_diff_hash("main")
        d_after = git("diff", "main...HEAD")
        assert d_before == d_after  # the bypass precondition really holds
        assert h_before != h_after  # ...and the hash restales anyway

    def test_hash_sees_submodule_pointer_change_despite_ignore_all(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Security regression (codex, PR #1): .gitmodules with ignore=all
        # must not hide a gitlink change from the staleness hash.
        def git(cwd: Path, *args: str) -> None:
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.email=t@t",
                    "-c",
                    "user.name=t",
                    "-c",
                    "protocol.file.allow=always",
                    *args,
                ],
                cwd=cwd,
                capture_output=True,
                check=True,
            )

        sub = tmp_path / "sub"
        sub.mkdir()
        git(sub, "init", "-q")
        git(sub, "commit", "-q", "--allow-empty", "-m", "one")
        git(sub, "commit", "-q", "--allow-empty", "-m", "two")
        host = tmp_path / "host"
        host.mkdir()
        git(host, "init", "-q")
        git(host, "commit", "-q", "--allow-empty", "-m", "root")
        git(host, "submodule", "add", "-q", "../sub", "subdir")
        git(host, "config", "-f", ".gitmodules", "submodule.subdir.ignore", "all")
        git(host, "add", "-A")
        git(host, "commit", "-qm", "add submodule, ignore=all")
        git(host / "subdir", "checkout", "-q", "HEAD~1")
        git(host, "add", "subdir")
        git(host, "commit", "-qm", "flip pointer only")
        monkeypatch.setattr(review_gate, "REPO_ROOT", host)
        assert review_gate.compute_diff_hash("HEAD~1") != review_gate.compute_diff_hash(
            "HEAD"
        )

    def test_hash_of_non_empty_diff(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Regression: the orderFile pin once made git fatal on any NON-empty
        # diff, which HEAD...HEAD tests can't catch. Build a real two-commit
        # repo and hash an actual diff.
        def git(*args: str) -> None:
            subprocess.run(
                ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
                cwd=tmp_path,
                capture_output=True,
                check=True,
            )

        git("init", "-q")
        (tmp_path / "f.txt").write_text("one\n")
        git("add", "f.txt")
        git("commit", "-qm", "c1")
        (tmp_path / "f.txt").write_text("two\n")
        git("add", "f.txt")
        git("commit", "-qm", "c2")
        monkeypatch.setattr(review_gate, "REPO_ROOT", tmp_path)
        h1 = review_gate.compute_diff_hash("HEAD~1")
        h2 = review_gate.compute_diff_hash("HEAD~1")
        assert h1 == h2 and len(h1) == 64
        # And a distinct diff hashes differently.
        assert h1 != review_gate.compute_diff_hash("HEAD")


class TestMalformedArtifacts:
    """Malformed inputs must produce diagnostics, never tracebacks (and the
    gate must stay fail-closed either way)."""

    def test_non_dict_finding_entry(self, tmp_path: Path) -> None:
        a = artifact("codex-review", findings=[])
        a["findings"] = ["not a dict"]
        p = write(tmp_path, "codex-review", a)
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("must be an object" in m for m in fails)

    def test_top_level_non_dict(self, tmp_path: Path) -> None:
        p = tmp_path / "codex-review.json"
        p.write_text(json.dumps(["a", "list"]))
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("top-level" in m for m in fails)

    def test_leg_name_filename_mismatch(self, tmp_path: Path) -> None:
        p = write(tmp_path, "claude-security-review", artifact("claude-code-review"))
        fails = review_gate.check_artifact(p, "claude-security-review", "security", HASH)
        assert any("leg is" in m for m in fails)

    def test_invalid_disposition(self, tmp_path: Path) -> None:
        f = finding(disposition="wontfix")
        p = write(tmp_path, "codex-review", artifact("codex-review", [f]))
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("disposition" in m for m in fails)

    def test_invalid_severity_claimed(self, tmp_path: Path) -> None:
        f = finding(severity_claimed="high")  # security enum on review leg
        p = write(tmp_path, "codex-review", artifact("codex-review", [f]))
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("severity_claimed" in m for m in fails)

    def test_unhashable_severity_diagnostic_not_traceback(self, tmp_path: Path) -> None:
        f = finding(severity_claimed=[], severity_validated={"x": 1})
        p = write(tmp_path, "codex-review", artifact("codex-review", [f]))
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("severities must be strings" in m for m in fails)

    def test_unhashable_disposition_diagnostic(self, tmp_path: Path) -> None:
        f = finding(disposition=["fixed"])
        p = write(tmp_path, "codex-review", artifact("codex-review", [f]))
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("disposition" in m for m in fails)

    def test_non_utf8_artifact_diagnostic_not_traceback(self, tmp_path: Path) -> None:
        p = tmp_path / "codex-review.json"
        p.write_bytes(b'{"leg": "\xff\xfe bad bytes"}')
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("unreadable or invalid JSON" in m for m in fails)

    @pytest.mark.parametrize(
        "field,value", [("id", None), ("id", ""), ("summary", {}), ("summary", "  ")]
    )
    def test_non_string_or_empty_id_summary_rejected(
        self, tmp_path: Path, field: str, value: Any
    ) -> None:
        f = finding(**{field: value})
        p = write(tmp_path, "codex-review", artifact("codex-review", [f]))
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("must be non-empty strings" in m for m in fails)

    def test_non_string_raw_output(self, tmp_path: Path) -> None:
        a = artifact("codex-review")
        a["raw_output"] = False
        p = write(tmp_path, "codex-review", a)
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("raw_output" in m for m in fails)

    @pytest.mark.parametrize("bad_hash", [12345, None, True, {"a": 1}, ["x"]])
    def test_non_string_diff_hash_diagnostic_not_traceback(
        self, tmp_path: Path, bad_hash: Any
    ) -> None:
        a = artifact("codex-review")
        a["reviewed_diff_sha256"] = bad_hash
        p = write(tmp_path, "codex-review", a)
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("reviewed_diff_sha256 must be a string" in m for m in fails)

    @pytest.mark.parametrize("bad_reason", [None, False, 0, ["because"]])
    def test_non_string_reason_rejected(self, tmp_path: Path, bad_reason: Any) -> None:
        f = finding(disposition="dismissed", reason=bad_reason)
        p = write(tmp_path, "codex-review", artifact("codex-review", [f]))
        fails = review_gate.check_artifact(p, "codex-review", "review", HASH)
        assert any("require a reason" in m for m in fails)
