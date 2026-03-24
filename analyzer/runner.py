from pathlib import Path

from analyzer.diff_scope_builder import build_diff_scope
from analyzer.model_provider import ModelProvider
from analyzer.prompt_builder import build_prompt
from analyzer.repo_discovery import discover_repo
from analyzer.repo_updater import get_head_commit, update_repo
from analyzer.result_handler import ResultHandler
from analyzer.run_state_store import RunStateStore
from analyzer.skill_system import load_compiled_skill_prompt, select_skill
from analyzer.types import JsonObject


def run_analysis(
    *,
    repo_path: Path,
    user_prompt: str,
    scope: str,
    out_path: Path,
    model_name: str,
    provider: ModelProvider,
    state_store_path: Path,
    skills_root: Path,
    max_changed_files: int = 200,
) -> JsonObject:
    if scope not in {"auto", "full"}:
        raise ValueError("scope must be one of: auto, full")

    update_repo(repo_path)
    head_commit = get_head_commit(repo_path)

    state_store = RunStateStore(state_store_path)
    baseline = state_store.get_last_successful_commit(repo_path)
    diff_scope = build_diff_scope(
        repo_path=repo_path,
        baseline_commit=None if scope == "full" else baseline,
        max_changed_files=max_changed_files,
    )
    discovery = discover_repo(repo_path, diff_scope.focus_paths)

    skill_name = select_skill(user_prompt)
    skill_prompt = load_compiled_skill_prompt(skills_root, skill_name)
    assembled_prompt = build_prompt(
        skill_prompt=skill_prompt,
        repo_discovery=discovery,
        diff_scope=diff_scope,
        user_input=user_prompt,
        repo_path=str(repo_path.resolve()),
        head_commit=head_commit,
        model_name=model_name,
    )
    raw_output = provider.generate(model_name=model_name, prompt=assembled_prompt)

    def repair_func(invalid_output: str) -> str:
        repair_prompt = (
            "Repair the following model output into valid JSON that exactly matches the schema. "
            "Return JSON only.\n\n"
            f"{invalid_output}"
        )
        return provider.generate(model_name=model_name, prompt=repair_prompt)

    handler = ResultHandler(out_path=out_path, repair_func=repair_func)
    parsed = handler.handle(raw_output)
    state_store.set_last_successful_commit(repo_path, head_commit)
    return parsed
