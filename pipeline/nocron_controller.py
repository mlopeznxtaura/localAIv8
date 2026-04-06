#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parent.parent


def load_tasks(path: Path = ROOT / "tasks.json") -> list:
    return json.loads(path.read_text(encoding="utf-8"))["tasks"]


def next_runnable(tasks: list, status: dict) -> Optional[str]:
    for t in tasks:
        tid = t["id"]
        if status.get(tid) not in (None, "pending", "scheduled"):
            continue
        deps = t.get("depends_on", [])
        if all(status.get(dep) == "complete" for dep in deps):
            return tid
    return None


def schedule_one_next(tasks: list, status: dict) -> Optional[str]:
    nxt = next_runnable(tasks, status)
    if not nxt:
        return None
    status[nxt] = "scheduled"
    return nxt


def build_empty_status(tasks: list) -> dict:
    return {t["id"]: "pending" for t in tasks}
