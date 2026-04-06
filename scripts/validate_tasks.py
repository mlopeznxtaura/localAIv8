#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK_FILE = ROOT / "task.json"
SPEC_FILE = ROOT / "bash.md"


def load_spec_json():
    text = SPEC_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "# NEXUS v8":
        raise AssertionError("Spec title must be '# NEXUS v8'.")
    payload = "\n".join(lines[1:]).strip()
    return json.loads(payload)


def no_legacy_labels(spec_text: str) -> bool:
    return re.search(r"(?i)\bv3\b|\bv5\b|\bv6\b", spec_text) is None


def validate_task(task, spec, spec_text):
    tid = task["id"]

    if tid == "T001":
        assert no_legacy_labels(spec_text), "Legacy labels detected in bash.md"

    elif tid == "T002":
        flow = spec["nocron_flow"]
        assert "first task" in flow["trigger_model"].lower(), "Missing first-task trigger rule"
        assert "one next cron job" in flow["loop_model"].lower(), "Missing one-next-job rule"
        assert "exits cleanly" in flow["termination"].lower(), "Missing clean termination rule"

    elif tid == "T003":
        ui = spec["ui_api_layer"]
        assert ui["mandatory"] is True, "React+Express layer must be mandatory"
        assert "react" in ui["stack"] and "express" in ui["stack"], "React+Express stack incomplete"

    elif tid == "T004":
        slider = spec["pipeline"]["step_1"]["ui_control"]
        assert slider["type"] == "user_slider", "Slider type must be user_slider"
        assert slider["min"] == 0 and slider["max"] == 50, "Slider range must be 0..50"

    elif tid == "T005":
        exp = spec["export_path_contract"]
        assert exp["user_defined"] is True, "Export path must be user-defined"
        assert exp["input_required"] is True, "Export path input must be required"
        assert any("writable" in x.lower() for x in exp["validation"]), "Writable-path check missing"

    elif tid == "T006":
        gap = spec["gap_policy"]
        assert "immediate" in gap["required_action"].lower(), "Gap policy must require immediate resolution"

    elif tid == "T007":
        assert "execution_contract" in spec, "execution_contract missing"
        assert "md5" in spec["tooling"]["cache"]["strategy"].lower(), "MD5 cache strategy missing"
        for k in ["step_0", "step_1", "step_2", "step_3", "step_4", "step_5", "step_6", "step_7"]:
            assert k in spec["pipeline"], f"Pipeline {k} missing"
        assert "qlora" in spec["training_and_learning"]["online_update"]["method"].lower(), "QLoRA update rule missing"
        assert any("do not invent architecture" == x for x in spec["invariants"]), "Invariant missing: do not invent architecture"


def main():
    tasks = json.loads(TASK_FILE.read_text(encoding="utf-8"))["tasks"]
    spec_text = SPEC_FILE.read_text(encoding="utf-8")
    spec = load_spec_json()

    results = []
    for task in tasks:
        try:
            validate_task(task, spec, spec_text)
            results.append({"task_id": task["id"], "passed": True})
        except Exception as exc:
            results.append({"task_id": task["id"], "passed": False, "error": str(exc)})

    out = ROOT / "task_validation_results.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")

    failed = [r for r in results if not r["passed"]]
    if failed:
        print(json.dumps({"ok": False, "failed": failed}, indent=2))
        raise SystemExit(1)

    print(json.dumps({"ok": True, "count": len(results)}, indent=2))


if __name__ == "__main__":
    main()