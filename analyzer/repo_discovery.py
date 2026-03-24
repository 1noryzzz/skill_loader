from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess

from analyzer.git_utils import run_git
from analyzer.types import JsonObject


SENSITIVE_DIRS = {".env", "secrets", "private", "credentials", "keys"}


@dataclass
class RepoDiscovery:
    language: str
    frameworks: list[str]
    entry_points: list[str]
    config_files: list[str]
    sensitive_dirs: list[str]

    def to_dict(self) -> JsonObject:
        return asdict(self)


def _infer_language(files: list[str]) -> str:
    if any(f.endswith(".py") for f in files):
        return "python"
    if any(f.endswith(".ts") or f.endswith(".tsx") for f in files):
        return "typescript"
    if any(f.endswith(".js") or f.endswith(".jsx") for f in files):
        return "javascript"
    if any(f.endswith(".go") for f in files):
        return "go"
    if any(f.endswith(".rs") for f in files):
        return "rust"
    return "unknown"


def _rg_match(repo_path: Path, pattern: str, targets: list[str]) -> bool:
    cmd = ["rg", "-n", "-i", pattern, *targets]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False
    return proc.returncode == 0 and bool(proc.stdout.strip())


def discover_repo(repo_path: Path, focus_paths: list[str]) -> RepoDiscovery:
    all_files_out = run_git(repo_path, ["ls-files"])
    all_files = [line.strip() for line in all_files_out.splitlines() if line.strip()]
    files = sorted(set(focus_paths or all_files))

    frameworks: set[str] = set()
    if "requirements.txt" in all_files or "pyproject.toml" in all_files:
        if (repo_path / "manage.py").exists():
            frameworks.add("django")
        targets = [f for f in ("pyproject.toml", "requirements.txt") if f in all_files]
        if targets and _rg_match(repo_path, "fastapi", targets):
            frameworks.add("fastapi")
        if targets and _rg_match(repo_path, "flask", targets):
            frameworks.add("flask")
    if "package.json" in all_files:
        targets = ["package.json"]
        if _rg_match(repo_path, '"next"', targets):
            frameworks.add("nextjs")
        if _rg_match(repo_path, '"react"', targets):
            frameworks.add("react")
        if _rg_match(repo_path, '"express"', targets):
            frameworks.add("express")

    entry_points = [
        f
        for f in files
        if f.endswith(("main.py", "app.py", "manage.py", "server.py", "index.js", "index.ts"))
        or f == "main.go"
        or f == "src/main.rs"
    ]
    config_files = [
        f
        for f in files
        if f.endswith(
            (
                ".toml",
                ".yaml",
                ".yml",
                ".json",
                ".ini",
                ".cfg",
                ".conf",
            )
        )
        or f in {"Dockerfile", ".env", ".env.example"}
    ]
    sensitive = sorted({p for p in files for seg in p.split("/") if seg.lower() in SENSITIVE_DIRS})

    return RepoDiscovery(
        language=_infer_language(files),
        frameworks=sorted(frameworks),
        entry_points=sorted(set(entry_points)),
        config_files=sorted(set(config_files)),
        sensitive_dirs=sensitive,
    )
