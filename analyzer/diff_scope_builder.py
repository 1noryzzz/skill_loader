from dataclasses import dataclass
from pathlib import Path

from analyzer.git_utils import run_git


@dataclass
class DiffScope:
    diff_base: str
    focus_paths: list[str]
    scope_mode: str
    partial_context: bool


def _list_all_repo_files(repo_path: Path) -> list[str]:
    out = run_git(repo_path, ["ls-files"])
    files = [line.strip() for line in out.splitlines() if line.strip()]
    return sorted(files)


def build_diff_scope(
    repo_path: Path,
    baseline_commit: str | None,
    max_changed_files: int = 200,
) -> DiffScope:
    if not baseline_commit:
        return DiffScope(
            diff_base="",
            focus_paths=_list_all_repo_files(repo_path),
            scope_mode="full_repo_no_baseline",
            partial_context=False,
        )

    changed = run_git(repo_path, ["diff", "--name-only", f"{baseline_commit}..HEAD"])
    changed_files = [line.strip() for line in changed.splitlines() if line.strip()]

    if not changed_files or len(changed_files) > max_changed_files:
        return DiffScope(
            diff_base=baseline_commit,
            focus_paths=_list_all_repo_files(repo_path),
            scope_mode="full_repo_diff_fallback",
            partial_context=False,
        )

    return DiffScope(
        diff_base=baseline_commit,
        focus_paths=sorted(set(changed_files)),
        scope_mode="diff_only",
        partial_context=True,
    )

