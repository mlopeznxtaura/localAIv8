#!/usr/bin/env python3
from pathlib import Path


def validate_export_path(path_value: str) -> dict:
    if not path_value or not path_value.strip():
        return {"ok": False, "reason": "empty_path"}

    path_obj = Path(path_value).expanduser()
    try:
        path_obj.mkdir(parents=True, exist_ok=True)
        test_file = path_obj / ".localai_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
    except Exception as exc:
        return {"ok": False, "reason": f"not_writable: {exc}"}

    return {"ok": True, "resolved": str(path_obj.resolve())}
