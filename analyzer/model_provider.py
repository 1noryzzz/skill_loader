import json
from dataclasses import dataclass
from typing import Protocol
from urllib import request


class ModelProvider(Protocol):
    def generate(self, model_name: str, prompt: str) -> str:
        ...


@dataclass
class OllamaHttpProvider:
    base_url: str = "http://localhost:11434"

    def generate(self, model_name: str, prompt: str) -> str:
        payload = json.dumps(
            {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
            }
        ).encode("utf-8")
        req = request.Request(
            url=f"{self.base_url.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return str(body.get("response", "")).strip()

