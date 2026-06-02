#!/usr/bin/env python3
"""Check a generated Youish plugin package."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from package_files import PACKAGE_FILES
from plugin_manifest import PLUGIN_NAME, SEMVER_RE


EXPECTED_PLUGIN_FILES = {".codex-plugin/plugin.json"} | {
    f"skills/youish/{rel}" for rel in PACKAGE_FILES
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_files_in(path: Path) -> set[str]:
    files: set[str] = set()
    for item in path.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(path)
        files.add(rel.as_posix())
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_dir", help="Generated plugin root.")
    parser.add_argument("--version", help="Expected plugin manifest version.")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    plugin = Path(args.plugin_dir).expanduser().resolve()
    manifest_path = plugin / ".codex-plugin" / "plugin.json"
    errors: list[str] = []

    if not manifest_path.exists():
        errors.append("missing .codex-plugin/plugin.json")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("name") != PLUGIN_NAME:
            errors.append(f"plugin name must be {PLUGIN_NAME}")
        version = manifest.get("version")
        if not isinstance(version, str) or SEMVER_RE.fullmatch(version) is None:
            errors.append("plugin version must be strict semver")
        if args.version and version != args.version:
            errors.append(f"plugin version must be {args.version}")
        if manifest.get("skills") != "./skills/":
            errors.append("plugin skills path must be ./skills/")
        if manifest.get("license") != "GPL-2.0-or-later":
            errors.append("plugin license must be GPL-2.0-or-later")
        interface = manifest.get("interface", {})
        if interface.get("displayName") != "Youish":
            errors.append("plugin interface.displayName must be Youish")
        default_prompt = interface.get("defaultPrompt")
        if not isinstance(default_prompt, list):
            errors.append("plugin interface.defaultPrompt must be a list")
        elif len(default_prompt) > 3:
            errors.append("plugin interface.defaultPrompt must contain at most 3 prompts")
        else:
            for index, prompt in enumerate(default_prompt, start=1):
                if not isinstance(prompt, str) or not prompt.strip():
                    errors.append(f"plugin interface.defaultPrompt[{index}] must be a non-empty string")
                elif len(prompt) > 128:
                    errors.append(f"plugin interface.defaultPrompt[{index}] must be 128 characters or fewer")
            if not any(isinstance(prompt, str) and "$youish" in prompt for prompt in default_prompt):
                errors.append("plugin defaultPrompt must mention $youish")
        if interface.get("brandColor") != "#4F46E5":
            errors.append("plugin interface.brandColor must be #4F46E5")
        for field, expected in (
            ("composerIcon", "skills/youish/assets/icon-small.svg"),
            ("logo", "skills/youish/assets/icon-large.svg"),
        ):
            if interface.get(field) != expected:
                errors.append(f"plugin interface.{field} must be {expected}")
            elif not (plugin / expected).exists():
                errors.append(f"plugin interface.{field} points to a missing file")

    skill_root = plugin / "skills" / "youish"
    actual_files = package_files_in(plugin) if plugin.exists() else set()
    for rel in sorted(EXPECTED_PLUGIN_FILES - actual_files):
        errors.append(f"missing plugin file: {rel}")
    for rel in sorted(actual_files - EXPECTED_PLUGIN_FILES):
        errors.append(f"unexpected plugin file: {rel}")

    for rel in PACKAGE_FILES:
        source = repo / rel
        packaged = skill_root / rel
        if not packaged.exists():
            errors.append(f"missing packaged file: {rel}")
        elif digest(source) != digest(packaged):
            errors.append(f"packaged file differs: {rel}")

    if errors:
        print("Plugin package check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Plugin package check passed: {plugin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
