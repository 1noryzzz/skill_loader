from analyzer.result_handler import validate_output_json


def test_json_validation_success() -> None:
    payload = {
        "skill": "security-best-practices",
        "task_type": "security_review",
        "summary": "ok",
        "findings": [
            {
                "id": "F-1",
                "title": "Issue",
                "severity": "high",
                "category": "auth",
                "description": "desc",
                "evidence": "evidence",
                "recommendation": "fix",
            }
        ],
        "metadata": {
            "repo_path": "/tmp/repo",
            "head_commit": "abc",
            "diff_base": "def",
            "scope_mode": "diff_only",
            "focus_paths": ["a.py"],
            "frameworks_detected": ["fastapi"],
            "model_name": "llama3",
            "partial_context": True,
        },
    }
    ok, errors = validate_output_json(payload)
    assert ok is True
    assert errors == []


def test_json_validation_failure() -> None:
    payload = {
        "skill": "security-best-practices",
        "task_type": "security_review",
        "summary": "bad",
        "findings": [{"id": "F-1"}],
        "metadata": {"repo_path": "/tmp/repo"},
    }
    ok, errors = validate_output_json(payload)
    assert ok is False
    assert errors

