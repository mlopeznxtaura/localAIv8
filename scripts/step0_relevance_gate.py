#!/usr/bin/env python3
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "user_prompt.txt"
SOURCE_FILE = ROOT / "bash.md"
OUTPUT_FILE = ROOT / "validated_prompt"
REPORT_FILE = ROOT / "step0_relevance_report.json"


ANCHORS = [
    "step0_ground.py",
    "step1_compress.py",
    "step2_mockui.py",
    "step3_parse.py",
    "step4_dag.py",
    "step5_tasks.py",
    "step6_build.py",
    "tool_cache",
    "training_data",
    "online_trainer.py",
    "export_student.py",
    "tasks.json",
    "tests.json",
    "output.zip",
    "react",
    "express",
]


def run_tool_queries() -> list:
    queries = [
        "stateless llm orchestration architecture validation",
        "beautifulsoup parse visible buttons headings",
        "deterministic md5 cache key pattern",
    ]
    out = []
    for q in queries:
        url = f"https://api.duckduckgo.com/?q={quote_plus(q)}&format=json&no_html=1&skip_disambig=1"
        item = {"tool": "web_search", "query": q, "url": url}
        try:
            with urlopen(url, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            snippet = (data.get("AbstractText") or data.get("Definition") or "").strip()
            item["ok"] = True
            item["snippet"] = snippet[:400]
            item["evidence_non_empty"] = bool(snippet)
        except Exception as exc:
            item["ok"] = False
            item["snippet"] = ""
            item["evidence_non_empty"] = False
            item["error"] = str(exc)
        out.append(item)
    return out


def anchor_coverage(text: str) -> dict:
    lower = text.lower()
    present = [a for a in ANCHORS if a.lower() in lower]
    missing = [a for a in ANCHORS if a.lower() not in lower]
    ratio = len(present) / len(ANCHORS) if ANCHORS else 1.0
    return {"present": present, "missing": missing, "ratio": ratio}


def normalize_prompt(prompt: str) -> str:
    prompt = prompt.replace("\r\n", "\n").replace("\r", "\n")
    prompt = re.sub(r"\n{3,}", "\n\n", prompt)
    return prompt.strip() + "\n"


def main() -> int:
    source_text = SOURCE_FILE.read_text(encoding="utf-8", errors="ignore")
    INPUT_FILE.write_text(source_text, encoding="utf-8")
    normalized = normalize_prompt(source_text)
    OUTPUT_FILE.write_text(normalized, encoding="utf-8")

    tools = run_tool_queries()
    coverage = anchor_coverage(source_text)

    non_empty_evidence = sum(1 for t in tools if t.get("evidence_non_empty"))
    cutoff = "2025-04-01"
    today = datetime.now(timezone.utc).date().isoformat()

    gate = {
        "anchor_coverage_pass": coverage["ratio"] >= 0.85,
        "tool_evidence_pass": non_empty_evidence >= 1,
        "cutoff_check_pass": today > cutoff,
    }
    go = all(gate.values())
    missing = []
    if not gate["anchor_coverage_pass"]:
        missing.append("anchor_coverage_below_threshold")
    if not gate["tool_evidence_pass"]:
        missing.append("insufficient_tool_evidence")
    if not gate["cutoff_check_pass"]:
        missing.append("cutoff_check_failed")

    report = {
        "step": 0,
        "name": "tool_function_relevance_gate",
        "input": "user_prompt.txt",
        "output": "validated_prompt",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "thresholds": {"anchor_ratio_min": 0.85, "tool_non_empty_min": 1},
        "coverage": coverage,
        "tool_calls": tools,
        "tool_non_empty_count": non_empty_evidence,
        "cutoff": {"training_cutoff": cutoff, "today_utc": today, "status": "today_after_cutoff" if today > cutoff else "today_on_or_before_cutoff"},
        "risk_level": "low" if go else "high",
        "decision": "go" if go else "no_go",
        "blockers": missing,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "risk_level": report["risk_level"], "tool_non_empty_count": non_empty_evidence, "coverage_ratio": coverage["ratio"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
