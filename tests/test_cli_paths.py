from pathlib import Path

from analyzer.cli import default_repo_path, default_skills_root


def test_default_repo_path_from_env(monkeypatch) -> None:
    monkeypatch.setenv("ANALYZER_REPO_PATH", "/tmp/repo-x")
    assert default_repo_path() == "/tmp/repo-x"


def test_default_repo_path_without_env(monkeypatch) -> None:
    monkeypatch.delenv("ANALYZER_REPO_PATH", raising=False)
    assert default_repo_path() == "."


def test_default_skills_root_from_env(monkeypatch) -> None:
    monkeypatch.setenv("ANALYZER_SKILLS_ROOT", "/tmp/skills-x")
    assert default_skills_root() == "/tmp/skills-x"


def test_default_skills_root_prefers_existing_candidates(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("ANALYZER_SKILLS_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "skills").mkdir()
    assert Path(default_skills_root()) == tmp_path / "skills"
