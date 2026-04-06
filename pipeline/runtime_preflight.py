#!/usr/bin/env python3
import json
import os
from urllib import request


def check_ollama(host: str = "http://localhost:11434") -> dict:
    try:
        resp = request.urlopen(f"{host}/api/tags", timeout=8)
        data = json.loads(resp.read().decode("utf-8"))
        models = [m.get("name", "") for m in data.get("models", [])]
        return {
            "ok": any("gemma4:26b" in m for m in models),
            "models_seen": models[:10],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "models_seen": []}


def check_env() -> dict:
    required = ["PWD"]
    missing = [k for k in required if not os.environ.get(k)]
    return {"ok": not missing, "missing": missing}


def run_preflight() -> dict:
    ollama = check_ollama()
    env = check_env()
    return {
        "runtime": "WSL2/host-compatible",
        "ollama": ollama,
        "env": env,
        "ok": ollama.get("ok", False) and env.get("ok", False),
    }


if __name__ == "__main__":
    print(json.dumps(run_preflight(), indent=2))
