import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from analyzer.types import JsonObject


REQUIRED_TOP_LEVEL = {"skill", "task_type", "summary", "findings", "metadata"}
REQUIRED_FINDING = {
    "id",
    "title",
    "severity",
    "category",
    "description",
    "evidence",
    "recommendation",
}
REQUIRED_METADATA = {
    "repo_path",
    "head_commit",
    "diff_base",
    "scope_mode",
    "focus_paths",
    "frameworks_detected",
    "model_name",
    "partial_context",
}


def validate_output_json(payload: JsonObject) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return False, ["payload must be an object"]

    missing_top = REQUIRED_TOP_LEVEL - payload.keys()
    if missing_top:
        errors.append(f"missing top-level keys: {sorted(missing_top)}")

    if "findings" in payload:
        if not isinstance(payload["findings"], list):
            errors.append("findings must be a list")
        else:
            for idx, item in enumerate(payload["findings"]):
                if not isinstance(item, dict):
                    errors.append(f"findings[{idx}] must be an object")
                    continue
                missing = REQUIRED_FINDING - item.keys()
                if missing:
                    errors.append(f"findings[{idx}] missing keys: {sorted(missing)}")
                for k in REQUIRED_FINDING & item.keys():
                    if not isinstance(item[k], str):
                        errors.append(f"findings[{idx}].{k} must be a string")

    if "metadata" in payload:
        metadata = payload["metadata"]
        if not isinstance(metadata, dict):
            errors.append("metadata must be an object")
        else:
            missing = REQUIRED_METADATA - metadata.keys()
            if missing:
                errors.append(f"metadata missing keys: {sorted(missing)}")
            for key in ("repo_path", "head_commit", "diff_base", "scope_mode", "model_name"):
                if key in metadata and not isinstance(metadata[key], str):
                    errors.append(f"metadata.{key} must be a string")
            if "focus_paths" in metadata and not isinstance(metadata["focus_paths"], list):
                errors.append("metadata.focus_paths must be a list")
            if "frameworks_detected" in metadata and not isinstance(metadata["frameworks_detected"], list):
                errors.append("metadata.frameworks_detected must be a list")
            if "partial_context" in metadata and not isinstance(metadata["partial_context"], bool):
                errors.append("metadata.partial_context must be a boolean")

    for key in ("skill", "task_type", "summary"):
        if key in payload and not isinstance(payload[key], str):
            errors.append(f"{key} must be a string")

    return not errors, errors


@dataclass
class ResultHandler:
    out_path: Path
    repair_func: Callable[[str], str]

    def _parse_and_validate(self, text: str) -> tuple[JsonObject | None, list[str]]:
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            return None, [f"invalid json: {exc}"]
        ok, errors = validate_output_json(obj)
        if not ok:
            return None, errors
        return obj, []

    def handle(self, raw_output: str) -> JsonObject:
        parsed, errors = self._parse_and_validate(raw_output)
        if parsed is not None:
            self._write_json(parsed)
            return parsed

        repaired_raw = self.repair_func(raw_output)
        repaired, repaired_errors = self._parse_and_validate(repaired_raw)
        if repaired is not None:
            self._write_json(repaired)
            return repaired

        self._persist_raw(raw_output, repaired_raw, errors, repaired_errors)
        raise RuntimeError("model output is invalid after one repair pass")

    def _write_json(self, payload: JsonObject) -> None:
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        with self.out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

    def _persist_raw(
        self,
        initial_raw: str,
        repaired_raw: str,
        initial_errors: list[str],
        repaired_errors: list[str],
    ) -> None:
        raw_path = self.out_path.with_suffix(self.out_path.suffix + ".raw.txt")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        text = (
            "INITIAL OUTPUT\n"
            f"{initial_raw}\n\n"
            "INITIAL ERRORS\n"
            f"{json.dumps(initial_errors, indent=2)}\n\n"
            "REPAIRED OUTPUT\n"
            f"{repaired_raw}\n\n"
            "REPAIRED ERRORS\n"
            f"{json.dumps(repaired_errors, indent=2)}\n"
        )
        raw_path.write_text(text, encoding="utf-8")
