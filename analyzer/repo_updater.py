from pathlib import Path

from analyzer.git_utils import GitError, run_git


def ensure_git_repo(repo_path: Path) -> None:
    if not (repo_path / ".git").exists():
        raise GitError("only git repositories are supported")


def ensure_clean_working_tree(repo_path: Path) -> None:
    status = run_git(repo_path, ["status", "--porcelain"])
    if status.strip():
        raise GitError("working tree is dirty; commit or stash changes first")


def update_repo(repo_path: Path) -> None:
    ensure_git_repo(repo_path)
    ensure_clean_working_tree(repo_path)
    run_git(repo_path, ["fetch", "--all", "--prune"])
    run_git(repo_path, ["pull", "--ff-only"])


def get_head_commit(repo_path: Path) -> str:
    return run_git(repo_path, ["rev-parse", "HEAD"])

