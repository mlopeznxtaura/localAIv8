#!/usr/bin/env python3
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK_FILE = ROOT / "task.json"
STATE_FILE = ROOT / "task_state.json"
VALIDATOR = ROOT / "scripts" / "validate_tasks.py"
VALIDATION_RESULTS = ROOT / "task_validation_results.json"


def load_tasks():
    return json.loads(TASK_FILE.read_text(encoding="utf-8"))["tasks"]


def init_state(tasks):
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    state = {
        "started_at": datetime.utcnow().isoformat() + "Z",
        "status": {t["id"]: "pending" for t in tasks},
        "history": [],
    }
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def run_realtime_validation():
    proc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(ROOT))
    if proc.returncode != 0:
        raise RuntimeError("validate_tasks.py failed")
    return json.loads(VALIDATION_RESULTS.read_text(encoding="utf-8"))


def find_task(tasks, task_id):
    return next(t for t in tasks if t["id"] == task_id)


def next_runnable(tasks, state):
    for t in tasks:
        tid = t["id"]
        if state["status"].get(tid) != "pending":
            continue
        deps = t.get("depends_on", [])
        if all(state["status"].get(d) == "complete" for d in deps):
            return tid
    return None


def mark(state, task_id, status, note):
    state["status"][task_id] = status
    state["history"].append(
        {
            "task_id": task_id,
            "status": status,
            "note": note,
            "at": datetime.utcnow().isoformat() + "Z",
        }
    )
    save_state(state)


def main():
    tasks = load_tasks()
    state = init_state(tasks)

    # Initial trigger: first dependency-free task (acts like initial cron trigger).
    current = next_runnable(tasks, state)
    if not current:
        print(json.dumps({"ok": True, "message": "No runnable pending tasks."}, indent=2))
        return 0

    print(f"START_TRIGGER task={current}")

    while current:
        mark(state, current, "running", "validation started")

        results = run_realtime_validation()
        cur = next((r for r in results if r["task_id"] == current), None)
        if not cur or not cur.get("passed"):
            err = cur.get("error", "task validation failed") if cur else "missing validation result"
            mark(state, current, "failed", err)
            print(json.dumps({"ok": False, "failed_task": current, "error": err}, indent=2))
            return 1

        mark(state, current, "complete", "validation passed")

        # NOcron behavior: schedule exactly one next runnable task.
        nxt = next_runnable(tasks, state)
        if not nxt:
            break
        mark(state, nxt, "scheduled", f"scheduled by python loop after {current}")
        current = nxt

    print(json.dumps({"ok": True, "message": "Loop complete; no pending runnable tasks."}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

