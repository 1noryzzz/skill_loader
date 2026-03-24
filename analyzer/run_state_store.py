import json
from dataclasses import dataclass
from pathlib import Path

from analyzer.types import JsonObject


@dataclass
class RunStateStore:
    state_file: Path

    def _read(self) -> JsonObject:
        if not self.state_file.exists():
            return {"repos": {}}
        with self.state_file.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, payload: JsonObject) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with self.state_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

    def get_last_successful_commit(self, repo_path: Path) -> str | None:
        data = self._read()
        repo_key = str(repo_path.resolve())
        repo_data = data.get("repos", {}).get(repo_key, {})
        return repo_data.get("last_successful_commit")

    def set_last_successful_commit(self, repo_path: Path, commit: str) -> None:
        data = self._read()
        repo_key = str(repo_path.resolve())
        repos = data.setdefault("repos", {})
        repo_data = repos.setdefault(repo_key, {})
        repo_data["last_successful_commit"] = commit
        self._write(data)
