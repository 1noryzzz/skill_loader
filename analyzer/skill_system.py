from pathlib import Path


def select_skill(user_prompt: str) -> str:
    text = user_prompt.lower()
    keywords = [
        "threat model",
        "threat-model",
        "attack surface",
        "abuse case",
        "trust boundary",
        "stride",
    ]
    if any(k in text for k in keywords):
        return "security-threat-model"
    return "security-best-practices"


def load_compiled_skill_prompt(skills_root: Path, skill_name: str) -> str:
    if skills_root.name == "compiled":
        compiled_root = skills_root
    else:
        compiled_root = skills_root / "compiled"
    if not compiled_root.exists():
        raise FileNotFoundError(
            f"compiled skills directory not found: {compiled_root} "
            f"(input skills_root={skills_root})"
        )
    target = compiled_root / f"{skill_name}.txt"
    if not target.exists():
        raise FileNotFoundError(f"compiled skill asset not found: {target}")
    return target.read_text(encoding="utf-8").strip()
