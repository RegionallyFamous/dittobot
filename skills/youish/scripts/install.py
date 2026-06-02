#!/usr/bin/env python3
"""Install Youish into the local Codex skills directory."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from package_files import PACKAGE_FILES


def backup_path(target: Path) -> Path:
    while True:
        candidate = target.with_name(f"{target.name}.backup.{time.time_ns()}")
        if not candidate.exists() and not candidate.is_symlink():
            return candidate


def temp_copy_path(target: Path) -> Path:
    return target.with_name(f".{target.name}.tmp.{int(time.time())}.{os.getpid()}")


def path_present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def is_repo_symlink(target: Path, repo: Path) -> bool:
    return target.is_symlink() and target.resolve() == repo


def preflight_package(repo: Path) -> None:
    missing = [rel for rel in PACKAGE_FILES if not (repo / rel).exists()]
    if missing:
        raise SystemExit(
            "Cannot install: package file(s) missing: " + ", ".join(missing)
        )


def looks_like_youish(path: Path) -> bool:
    skill = path / "SKILL.md"
    if not skill.exists():
        return False
    try:
        text = skill.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return "name: youish" in text[:500]


def guard_install_target(repo: Path, target: Path, force: bool) -> None:
    resolved_repo = repo.resolve()
    resolved_target = target.resolve(strict=False)
    if target.name != "youish":
        raise SystemExit("Refusing install: --install-dir basename must be 'youish'.")
    if target.is_symlink() and target.resolve() == resolved_repo:
        return
    if resolved_target == resolved_repo:
        raise SystemExit("Refusing install: --install-dir points at the source repo.")
    if resolved_repo in resolved_target.parents:
        raise SystemExit("Refusing install: --install-dir cannot be inside the source repo.")
    if path_present(target) and not looks_like_youish(target.resolve()) and not force:
        raise SystemExit(
            "Refusing install: existing target does not look like Youish. "
            "Pass --force only if you intentionally want to replace it."
        )


def install_copy(repo: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for rel in PACKAGE_FILES:
        source = repo / rel
        destination = target / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install-dir",
        default=os.path.expanduser("~/.agents/skills/youish"),
        help="Destination skill directory.",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of creating a symlink.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacing an existing non-Youish target directory.",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    target = Path(args.install_dir).expanduser()
    preflight_package(repo)
    guard_install_target(repo, target, args.force)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_target = temp_copy_path(target)
    backup: Path | None = None

    try:
        if is_repo_symlink(target, repo) and not args.copy:
            print(f"Already installed as symlink: {target}", flush=True)
        else:
            remove_path(temp_target)
            if args.copy:
                if temp_target.exists():
                    shutil.rmtree(temp_target)
                install_copy(repo, temp_target)
            else:
                temp_target.symlink_to(repo, target_is_directory=True)

            if path_present(target):
                backup = backup_path(target)
                shutil.move(str(target), str(backup))
                print(f"Backed up existing install to: {backup}", flush=True)

            try:
                shutil.move(str(temp_target), str(target))
            except Exception:
                if backup is not None and not path_present(target) and path_present(backup):
                    shutil.move(str(backup), str(target))
                    print(f"Restored existing install after failure: {target}", flush=True)
                raise

            if args.copy:
                print(f"Installed copy: {target}", flush=True)
            else:
                print(f"Installed symlink: {target} -> {repo}", flush=True)
    finally:
        if path_present(temp_target):
            remove_path(temp_target)

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
