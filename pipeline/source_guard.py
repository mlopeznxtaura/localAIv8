#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = ROOT / "bash.md"


def source_exists() -> bool:
    return SOURCE_FILE.exists()


def source_text() -> str:
    return SOURCE_FILE.read_text(encoding="utf-8", errors="ignore")


def assert_source_authority() -> None:
    if not source_exists():
        raise FileNotFoundError("bash.md missing; source authority cannot be enforced")
