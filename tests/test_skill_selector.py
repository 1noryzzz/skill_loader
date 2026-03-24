from pathlib import Path

from analyzer.skill_system import load_compiled_skill_prompt, select_skill


def test_select_skill_threat_model() -> None:
    assert select_skill("Please build a threat model for this change") == "security-threat-model"


def test_select_skill_default() -> None:
    assert select_skill("General security review") == "security-best-practices"


def test_load_compiled_skill_prompt_from_skills_root(tmp_path: Path) -> None:
    compiled = tmp_path / "skills" / "compiled"
    compiled.mkdir(parents=True)
    asset = compiled / "security-best-practices.txt"
    asset.write_text("hello", encoding="utf-8")

    content = load_compiled_skill_prompt(tmp_path / "skills", "security-best-practices")
    assert content == "hello"


def test_load_compiled_skill_prompt_from_compiled_root(tmp_path: Path) -> None:
    compiled = tmp_path / "compiled"
    compiled.mkdir(parents=True)
    asset = compiled / "security-threat-model.txt"
    asset.write_text("threat", encoding="utf-8")

    content = load_compiled_skill_prompt(tmp_path / "compiled", "security-threat-model")
    assert content == "threat"
