import argparse
import os
from pathlib import Path

from analyzer.model_provider import OllamaHttpProvider
from analyzer.runner import run_analysis


def default_repo_path() -> str:
    return os.environ.get("ANALYZER_REPO_PATH", ".")


def default_skills_root() -> str:
    configured = os.environ.get("ANALYZER_SKILLS_ROOT")
    if configured:
        return configured

    project_root = Path(__file__).resolve().parents[1]
    candidates = [
        Path.cwd() / "skills",
        project_root / "skills",
        project_root.parent / "skills",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(project_root / "skills")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="analyzer")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run")
    run_cmd.add_argument("--repo", default=default_repo_path())
    run_cmd.add_argument("--prompt", required=True)
    run_cmd.add_argument("--scope", default="auto", choices=["auto", "full"])
    run_cmd.add_argument("--out", required=True)
    run_cmd.add_argument("--model", default="llama3")
    run_cmd.add_argument("--ollama-url", default="http://localhost:11434")
    run_cmd.add_argument("--state-file", default=".analyzer/run_state.json")
    run_cmd.add_argument("--skills-root", default=default_skills_root())
    run_cmd.add_argument("--max-changed-files", type=int, default=200)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        provider = OllamaHttpProvider(base_url=args.ollama_url)
        run_analysis(
            repo_path=Path(args.repo),
            user_prompt=args.prompt,
            scope=args.scope,
            out_path=Path(args.out),
            model_name=args.model,
            provider=provider,
            state_store_path=Path(args.state_file),
            skills_root=Path(args.skills_root),
            max_changed_files=args.max_changed_files,
        )
        return 0
    return 1
