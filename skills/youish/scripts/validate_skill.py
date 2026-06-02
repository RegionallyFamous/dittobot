#!/usr/bin/env python3
"""Validate the standalone Youish skill repo."""

from __future__ import annotations

import ast
import hashlib
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from package_files import PACKAGE_FILES


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
OPENAI_YAML = ROOT / "agents" / "openai.yaml"
INSTALL_SH = ROOT / "install.sh"
SPEC_SKILL_ROOT = ROOT / "skills" / "youish"
SKILL_WORD_LIMIT = 1900
SOURCE_REPO_ROOT = (ROOT / "README.md").exists() and SPEC_SKILL_ROOT.exists()
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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_files() -> list[Path]:
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in {".git", "__pycache__", "dist"} for part in rel.parts):
            continue
        if path.suffix in {".pyc", ".jsonl"} or path.name == ".DS_Store":
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        paths.append(path)
    return paths


def imported_top_level_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".", 1)[0])
    return modules


def yaml_string_field(text: str, field: str) -> str | None:
    match = re.search(rf"^\s*{field}:\s*\"(.+)\"", text, re.MULTILINE)
    return match.group(1) if match else None


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
            license_id = data.get("license")
            description = data.get("description")
            if name != "youish":
                fail("frontmatter name must be youish", errors)
            if license_id != "GPL-2.0-or-later":
                fail("frontmatter license must be GPL-2.0-or-later", errors)
            if not description or len(description.split()) < 20:
                fail("frontmatter description must be informative", errors)
            allowed_keys = {"name", "license", "description"}
            if not SOURCE_REPO_ROOT:
                allowed_keys |= {"metadata"} | {
                    key for key in data if key.startswith("github-")
                }
            if any(key not in allowed_keys for key in data):
                if SOURCE_REPO_ROOT:
                    fail("frontmatter must contain only name, license, and description", errors)
                else:
                    fail("frontmatter contains unsupported install metadata", errors)
            if "# Youish" not in body:
                fail("SKILL.md body must contain # Youish heading", errors)
            if "python3 scripts/regression_100.py" not in body:
                fail("SKILL.md validation command must be repo-relative", errors)
            if any(marker in body for marker in LOCAL_PATH_MARKERS):
                fail("SKILL.md body must not contain machine-local paths", errors)
            word_count = len(body.split())
            if word_count > SKILL_WORD_LIMIT:
                fail(
                    f"SKILL.md must stay under {SKILL_WORD_LIMIT} words for progressive disclosure; got {word_count}",
                    errors,
                )

    if not OPENAI_YAML.exists():
        fail("agents/openai.yaml is missing", errors)
    else:
        text = OPENAI_YAML.read_text(encoding="utf-8")
        for field in (
            "display_name",
            "short_description",
            "icon_small",
            "icon_large",
            "brand_color",
            "default_prompt",
        ):
            if yaml_string_field(text, field) is None:
                fail(f"agents/openai.yaml missing quoted {field}", errors)
        if "$youish" not in text:
            fail("agents/openai.yaml default_prompt must mention $youish", errors)
        if yaml_string_field(text, "brand_color") != "#4F46E5":
            fail("agents/openai.yaml brand_color must be #4F46E5", errors)
        for field in ("icon_small", "icon_large"):
            raw_path = yaml_string_field(text, field)
            if raw_path is None:
                continue
            rel = raw_path.removeprefix("./")
            if not (ROOT / rel).exists():
                fail(f"agents/openai.yaml {field} points to missing file {raw_path}", errors)

    for rel in PACKAGE_FILES:
        path = ROOT / rel
        if not path.exists():
            fail(f"{rel} is missing", errors)
        elif rel.endswith(".py") and not path.read_text(encoding="utf-8").startswith("#!/usr/bin/env python3"):
            fail(f"{rel} must have a python3 shebang", errors)

    if (ROOT / "README.md").exists() and not INSTALL_SH.exists():
        fail("install.sh is missing", errors)
    elif INSTALL_SH.exists():
        install_text = INSTALL_SH.read_text(encoding="utf-8")
        if not install_text.startswith("#!/usr/bin/env bash"):
            fail("install.sh must have a bash shebang", errors)
        if not os.access(INSTALL_SH, os.X_OK):
            fail("install.sh must be executable", errors)
        if re.search(r"\bsudo\b", install_text):
            fail("install.sh must not ask for sudo", errors)

    repo_script_modules = {
        path.stem for path in (ROOT / "scripts").glob("*.py") if path.is_file()
    }
    packaged_script_modules = {
        Path(rel).stem for rel in PACKAGE_FILES if rel.startswith("scripts/") and rel.endswith(".py")
    }
    for rel in PACKAGE_FILES:
        if not rel.startswith("scripts/") or not rel.endswith(".py"):
            continue
        path = ROOT / rel
        if not path.exists():
            continue
        missing_imports = sorted(
            (imported_top_level_modules(path) & repo_script_modules)
            - packaged_script_modules
        )
        for module in missing_imports:
            fail(f"{rel} imports unpackaged helper module {module!r}", errors)

    if (ROOT / "README.md").exists():
        if not SPEC_SKILL_ROOT.exists():
            fail("skills/youish package mirror is missing", errors)
        else:
            for rel in PACKAGE_FILES:
                source = ROOT / rel
                mirror = SPEC_SKILL_ROOT / rel
                if not mirror.exists():
                    fail(f"skills/youish/{rel} is missing from package mirror", errors)
                elif source.exists() and digest(source) != digest(mirror):
                    fail(f"skills/youish/{rel} is out of sync with root package file", errors)

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
