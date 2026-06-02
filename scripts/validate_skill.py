#!/usr/bin/env python3
"""Validate the standalone Dittobot skill repo."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
OPENAI_YAML = ROOT / "agents" / "openai.yaml"
LOCAL_PATH_MARKERS = (
    "/" + "Users" + "/",
    "C:" + "\\" + "Users" + "\\",
    "/" + "home" + "/" + "nick" + "/",
)


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("SKILL.md frontmatter must close with ---")
    raw = text[4:end]
    body = text[end + 5 :]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data, body


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def text_files() -> list[Path]:
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in {".git", "__pycache__"} for part in rel.parts):
            continue
        if path.suffix in {".pyc", ".jsonl"} or path.name == ".DS_Store":
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        paths.append(path)
    return paths


def main() -> int:
    errors: list[str] = []

    if not SKILL.exists():
        fail("SKILL.md is missing", errors)
    else:
        try:
            data, body = frontmatter(SKILL.read_text(encoding="utf-8"))
        except ValueError as exc:
            fail(str(exc), errors)
        else:
            name = data.get("name")
            description = data.get("description")
            if name != "dittobot":
                fail("frontmatter name must be dittobot", errors)
            if not description or len(description.split()) < 20:
                fail("frontmatter description must be informative", errors)
            if any(key not in {"name", "description"} for key in data):
                fail("frontmatter must contain only name and description", errors)
            if "# Dittobot" not in body:
                fail("SKILL.md body must contain # Dittobot heading", errors)
            if "python3 scripts/regression_100.py" not in body:
                fail("SKILL.md validation command must be repo-relative", errors)
            if any(marker in body for marker in LOCAL_PATH_MARKERS):
                fail("SKILL.md body must not contain machine-local paths", errors)

    if not OPENAI_YAML.exists():
        fail("agents/openai.yaml is missing", errors)
    else:
        text = OPENAI_YAML.read_text(encoding="utf-8")
        for field in ("display_name", "short_description", "default_prompt"):
            if re.search(rf"^\s*{field}:\s*\".+\"", text, re.MULTILINE) is None:
                fail(f"agents/openai.yaml missing quoted {field}", errors)
        if "$dittobot" not in text:
            fail("agents/openai.yaml default_prompt must mention $dittobot", errors)

    for rel in (
        "scripts/regression_100.py",
        "scripts/check_install.py",
        "scripts/install.py",
        "scripts/live_eval.py",
        "scripts/validate_skill.py",
    ):
        path = ROOT / rel
        if not path.exists():
            fail(f"{rel} is missing", errors)
        elif not path.read_text(encoding="utf-8").startswith("#!/usr/bin/env python3"):
            fail(f"{rel} must have a python3 shebang", errors)

    for path in text_files():
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        for marker in LOCAL_PATH_MARKERS:
            if marker in text:
                fail(f"{rel} contains machine-local path marker {marker!r}", errors)

    if errors:
        print("Skill repo validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Skill repo validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
