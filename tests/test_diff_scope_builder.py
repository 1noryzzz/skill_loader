import subprocess
from pathlib import Path

from analyzer.diff_scope_builder import build_diff_scope
from analyzer.git_utils import run_git


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True, capture_output=True, text=True)


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init"], repo)
    _run(["git", "config", "user.email", "test@example.com"], repo)
    _run(["git", "config", "user.name", "Test"], repo)
    return repo


def test_fallback_when_no_baseline(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / "a.py").write_text("print('x')\n", encoding="utf-8")
    _run(["git", "add", "."], repo)
    _run(["git", "commit", "-m", "init"], repo)

    result = build_diff_scope(repo, baseline_commit=None, max_changed_files=1)
    assert result.scope_mode == "full_repo_no_baseline"
    assert result.partial_context is False
    assert "a.py" in result.focus_paths


def test_fallback_when_diff_too_large(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / "a.py").write_text("print('x')\n", encoding="utf-8")
    (repo / "b.py").write_text("print('y')\n", encoding="utf-8")
    _run(["git", "add", "."], repo)
    _run(["git", "commit", "-m", "init"], repo)
    baseline = run_git(repo, ["rev-parse", "HEAD"])

    (repo / "a.py").write_text("print('x2')\n", encoding="utf-8")
    (repo / "b.py").write_text("print('y2')\n", encoding="utf-8")
    _run(["git", "add", "."], repo)
    _run(["git", "commit", "-m", "update"], repo)

    result = build_diff_scope(repo, baseline_commit=baseline, max_changed_files=1)
    assert result.scope_mode == "full_repo_diff_fallback"
    assert result.partial_context is False
    assert "a.py" in result.focus_paths
    assert "b.py" in result.focus_paths

