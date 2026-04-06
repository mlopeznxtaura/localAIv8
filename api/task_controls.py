#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TASKS_FILE = ROOT / "tasks.json"


def _read_tasks() -> dict:
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))


def _write_tasks(payload: dict) -> None:
    TASKS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def list_tasks() -> dict:
    return _read_tasks()


def accelerate_task(task_id: str) -> dict:
    data = _read_tasks()
    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            task["status"] = "complete"
            _write_tasks(data)
            return {"ok": True, "task_id": task_id, "status": "complete"}
    return {"ok": False, "task_id": task_id, "reason": "not_found"}
