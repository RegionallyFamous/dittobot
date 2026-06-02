#!/usr/bin/env python3
"""Check that public install and release version strings agree."""

from __future__ import annotations

import json
import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from plugin_manifest import DEFAULT_VERSION


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Expected strict semver version.")
    args = parser.parse_args()
    version = args.version
    errors: list[str] = []
    if DEFAULT_VERSION != version:
        errors.append(f"scripts/plugin_manifest.py DEFAULT_VERSION is {DEFAULT_VERSION}, expected {version}")
    checks = {
        "CHANGELOG.md": rf"^## {re.escape(version)} - ",
        "install.sh": rf'REF="\$\{{DITTOBOT_REF:-v{re.escape(version)}\}}"',
        "README.md": rf"v{re.escape(version)}",
        ".github/workflows/validate.yml": rf"{re.escape(version)}",
        "scripts/scorecard.py": rf'default="{re.escape(version)}"',
    }
    for rel, pattern in checks.items():
        flags = re.MULTILINE
        if not re.search(pattern, read(rel), flags):
            errors.append(f"{rel} is not pinned to {version}")

    manifest = json.loads(read(".codex-plugin/plugin.json"))
    if manifest.get("version") != version:
        errors.append(f".codex-plugin/plugin.json version is {manifest.get('version')}, expected {version}")
    mirror_manifest = json.loads(read("plugins/dittobot/.codex-plugin/plugin.json"))
    if mirror_manifest.get("version") != version:
        errors.append(
            f"plugins/dittobot/.codex-plugin/plugin.json version is {mirror_manifest.get('version')}, "
            f"expected {version}"
        )

    if errors:
        print("Version check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Version check passed: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
