#!/usr/bin/env python3
"""Check whether the installed Dittobot skill matches this repo."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path


FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "scripts/regression_100.py",
    "scripts/check_install.py",
    "scripts/live_eval.py",
    "scripts/validate_skill.py",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install-dir",
        default=os.path.expanduser("~/.codex/skills/dittobot"),
        help="Installed skill directory to compare.",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    installed = Path(args.install_dir).expanduser().resolve()

    if not installed.exists():
        print(f"Install missing: {installed}")
        return 1

    mismatches: list[str] = []
    missing: list[str] = []

    for rel in FILES:
        repo_file = repo / rel
        installed_file = installed / rel
        if not installed_file.exists():
            missing.append(rel)
        elif digest(repo_file) != digest(installed_file):
            mismatches.append(rel)

    if missing or mismatches:
        print(f"Installed skill differs from repo: {installed}")
        for rel in missing:
            print(f"  missing: {rel}")
        for rel in mismatches:
            print(f"  mismatch: {rel}")
        print("\nPrefer a symlink install to avoid drift:")
        print("  mv ~/.codex/skills/dittobot ~/.codex/skills/dittobot.backup.$(date +%s)")
        print(f"  ln -s {repo} ~/.codex/skills/dittobot")
        return 1

    link_note = "symlink" if Path(args.install_dir).expanduser().is_symlink() else "copy"
    print(f"Installed skill matches repo ({link_note}): {installed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
