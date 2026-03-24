import subprocess
from pathlib import Path

import pytest

from analyzer.git_utils import GitError
from analyzer.repo_updater import ensure_clean_working_tree


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True, capture_output=True, text=True)


def test_dirty_repo_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init"], repo)
    _run(["git", "config", "user.email", "test@example.com"], repo)
    _run(["git", "config", "user.name", "Test"], repo)
    (repo / "a.txt").write_text("hello\n", encoding="utf-8")
    _run(["git", "add", "."], repo)
    _run(["git", "commit", "-m", "init"], repo)

    (repo / "a.txt").write_text("changed\n", encoding="utf-8")

    with pytest.raises(GitError):
        ensure_clean_working_tree(repo)

