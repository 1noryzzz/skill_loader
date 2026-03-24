import subprocess
from pathlib import Path


class GitError(RuntimeError):
    """Raised when git operations fail."""


def run_git(repo_path: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise GitError(proc.stderr.strip() or proc.stdout.strip() or "git command failed")
    return proc.stdout.strip()

