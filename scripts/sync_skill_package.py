#!/usr/bin/env python3
"""Sync the Agent Skills spec package mirror from the repo root."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from package_files import PACKAGE_FILES
from plugin_manifest import DEFAULT_VERSION, PLUGIN_NAME, manifest


ROOT = Path(__file__).resolve().parents[1]
SKILL_MIRROR = ROOT / "skills" / PLUGIN_NAME
PLUGIN_MIRROR = ROOT / "plugins" / PLUGIN_NAME


def write_plugin_manifest(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(manifest(DEFAULT_VERSION), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def copy_skill_files(destination_root: Path) -> None:
    for rel in PACKAGE_FILES:
        source = ROOT / rel
        destination = destination_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def sync_skill_mirror() -> None:
    if SKILL_MIRROR.exists():
        shutil.rmtree(SKILL_MIRROR)
    SKILL_MIRROR.mkdir(parents=True)
    copy_skill_files(SKILL_MIRROR)


def sync_plugin_mirror() -> None:
    if PLUGIN_MIRROR.exists():
        shutil.rmtree(PLUGIN_MIRROR)
    (PLUGIN_MIRROR / ".codex-plugin").mkdir(parents=True)
    write_plugin_manifest(PLUGIN_MIRROR / ".codex-plugin" / "plugin.json")
    copy_skill_files(PLUGIN_MIRROR / "skills" / PLUGIN_NAME)


def main() -> int:
    missing = [rel for rel in PACKAGE_FILES if not (ROOT / rel).exists()]
    if missing:
        print("Cannot sync package mirrors; source files missing:")
        for rel in missing:
            print(f"  - {rel}")
        return 1

    sync_skill_mirror()
    write_plugin_manifest(ROOT / ".codex-plugin" / "plugin.json")
    sync_plugin_mirror()
    print(f"Synced {len(PACKAGE_FILES)} files to {SKILL_MIRROR.relative_to(ROOT)}")
    print(f"Synced marketplace plugin to {PLUGIN_MIRROR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
