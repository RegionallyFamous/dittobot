#!/usr/bin/env python3
"""Install Dittobot into the local Codex skills directory."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def backup_path(target: Path) -> Path:
    return target.with_name(f"{target.name}.backup.{int(time.time())}")


def is_repo_symlink(target: Path, repo: Path) -> bool:
    return target.is_symlink() and target.resolve() == repo


def install_copy(repo: Path, target: Path) -> None:
    shutil.copytree(
        repo,
        target,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "*.local.jsonl",
            ".DS_Store",
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install-dir",
        default=os.path.expanduser("~/.codex/skills/dittobot"),
        help="Destination skill directory.",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of creating a symlink.",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    target = Path(args.install_dir).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)

    if is_repo_symlink(target, repo) and not args.copy:
        print(f"Already installed as symlink: {target}", flush=True)
    else:
        if target.exists() or target.is_symlink():
            backup = backup_path(target)
            shutil.move(str(target), str(backup))
            print(f"Backed up existing install to: {backup}", flush=True)

        if args.copy:
            install_copy(repo, target)
            print(f"Installed copy: {target}", flush=True)
        else:
            target.symlink_to(repo, target_is_directory=True)
            print(f"Installed symlink: {target} -> {repo}", flush=True)

    result = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "check_install.py"),
            "--install-dir",
            str(target),
        ],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
