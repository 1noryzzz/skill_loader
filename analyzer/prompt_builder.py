import json

from analyzer.diff_scope_builder import DiffScope
from analyzer.repo_discovery import RepoDiscovery


GLOBAL_SYSTEM_ROLE = (
    "You are a strict security analysis engine. "
    "Return only valid JSON that exactly matches the required schema."
)

TASK_TEMPLATE = (
    "Task: Analyze the repository scope for security issues and produce findings "
    "with concrete evidence and recommendations."
)

JSON_OUTPUT_CONTRACT = {
    "skill": "string",
    "task_type": "string",
    "summary": "string",
    "findings": [
        {
            "id": "string",
            "title": "string",
            "severity": "string",
            "category": "string",
            "description": "string",
            "evidence": "string",
            "recommendation": "string",
        }
    ],
    "metadata": {
        "repo_path": "string",
        "head_commit": "string",
        "diff_base": "string",
        "scope_mode": "string",
        "focus_paths": ["string"],
        "frameworks_detected": ["string"],
        "model_name": "string",
        "partial_context": "boolean",
    },
}


def build_prompt(
    *,
    skill_prompt: str,
    repo_discovery: RepoDiscovery,
    diff_scope: DiffScope,
    user_input: str,
    repo_path: str,
    head_commit: str,
    model_name: str,
) -> str:
    sections = [
        "1) Global system role",
        GLOBAL_SYSTEM_ROLE,
        "",
        "2) Skill system prompt",
        skill_prompt,
        "",
        "3) Task template",
        TASK_TEMPLATE,
        "",
        "4) Repo discovery",
        json.dumps(repo_discovery.to_dict(), indent=2, sort_keys=True),
        "",
        "5) Diff / focus_paths",
        json.dumps(
            {
                "diff_base": diff_scope.diff_base,
                "scope_mode": diff_scope.scope_mode,
                "focus_paths": diff_scope.focus_paths,
                "partial_context": diff_scope.partial_context,
            },
            indent=2,
            sort_keys=True,
        ),
        "",
        "6) User input",
        user_input,
        "",
        "7) JSON output contract",
        json.dumps(JSON_OUTPUT_CONTRACT, indent=2, sort_keys=True),
        "",
        "Required metadata values:",
        json.dumps(
            {
                "repo_path": repo_path,
                "head_commit": head_commit,
                "diff_base": diff_scope.diff_base,
                "scope_mode": diff_scope.scope_mode,
                "focus_paths": diff_scope.focus_paths,
                "frameworks_detected": repo_discovery.frameworks,
                "model_name": model_name,
                "partial_context": diff_scope.partial_context,
            },
            indent=2,
            sort_keys=True,
        ),
    ]
    return "\n".join(sections)

