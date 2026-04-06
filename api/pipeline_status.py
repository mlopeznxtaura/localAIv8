#!/usr/bin/env python3
from typing import Dict, List


PIPELINE_STEPS: List[Dict[str, str]] = [
    {"id": "0", "name": "context_tool_ready"},
    {"id": "1", "name": "compress"},
    {"id": "2", "name": "mock_ui"},
    {"id": "3", "name": "html_parse"},
    {"id": "4", "name": "dag"},
    {"id": "5", "name": "file_scaffold_tests"},
    {"id": "6", "name": "write"},
    {"id": "7", "name": "export"},
]


def status_payload(active_step: str) -> Dict[str, object]:
    return {
        "software_title": "localAIv8",
        "active_step": active_step,
        "steps": PIPELINE_STEPS,
    }
