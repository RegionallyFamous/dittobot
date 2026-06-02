#!/usr/bin/env python3
"""Check whether the installed Youish skill matches this repo."""

from __future__ import annotations

import argparse
import hashlib
import os
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from package_files import PACKAGE_FILES


IGNORED_EXTRA_NAMES = {".DS_Store"}
IGNORED_EXTRA_SUFFIXES = {".pyc"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skill_parts(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    _start, frontmatter, body = text.split("---\n", 2)
    scalars: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        scalars[key.strip()] = value.strip()
    return scalars, body.lstrip()


def files_match(repo_file: Path, installed_file: Path, rel: str) -> bool:
    if rel != "SKILL.md":
        return digest(repo_file) == digest(installed_file)
    repo_meta, repo_body = skill_parts(repo_file)
    installed_meta, installed_body = skill_parts(installed_file)
    if repo_body != installed_body:
        return False
    for key in ("name", "license", "description"):
        if repo_meta.get(key) != installed_meta.get(key):
            return False
    return True


def package_files_in(path: Path) -> set[str]:
    files: set[str] = set()
    for item in path.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(path)
        if any(part == "__pycache__" for part in rel.parts):
            continue
        if item.name in IGNORED_EXTRA_NAMES or item.suffix in IGNORED_EXTRA_SUFFIXES:
            continue
        files.add(rel.as_posix())
    return files


def tracked_files_in(path: Path) -> set[str] | None:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def looks_like_repo_root_copy(path: Path) -> bool:
    markers = (
        "README.md",
        "LICENSE",
        ".codex-plugin/plugin.json",
        "skills/youish/SKILL.md",
        "plugins/youish/.codex-plugin/plugin.json",
    )
    return all((path / marker).exists() for marker in markers)


def default_install_dir() -> str:
    codex_home = os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex"))
    return str(Path(codex_home) / "skills" / "youish")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install-dir",
        default=default_install_dir(),
        help="Installed skill directory to compare.",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    install_path = Path(args.install_dir).expanduser()
    installed = install_path.resolve()

    if not installed.exists():
        print(f"Install missing: {install_path}")
        return 1

    mismatches: list[str] = []
    missing: list[str] = []
    source_missing: list[str] = []
    unexpected: list[str] = []

    for rel in PACKAGE_FILES:
        repo_file = repo / rel
        installed_file = installed / rel
        if not repo_file.exists():
            source_missing.append(rel)
        elif not installed_file.exists():
            missing.append(rel)
        elif not files_match(repo_file, installed_file, rel):
            mismatches.append(rel)

    install_kind = "copy"
    if not install_path.is_symlink():
        if looks_like_repo_root_copy(installed):
            install_kind = "root copy"
            expected = tracked_files_in(repo)
            if expected is None:
                expected = set(PACKAGE_FILES)
        else:
            expected = set(PACKAGE_FILES)
        unexpected = sorted(package_files_in(installed) - expected)

    if source_missing or missing or mismatches or unexpected:
        print(f"Installed skill differs from repo: {installed}")
        for rel in source_missing:
            print(f"  source missing: {rel}")
        for rel in missing:
            print(f"  missing: {rel}")
        for rel in mismatches:
            print(f"  mismatch: {rel}")
        for rel in unexpected:
            print(f"  unexpected: {rel}")
        print("\nPrefer a symlink install to avoid drift:")
        quoted_install_path = shlex.quote(str(install_path))
        print(f"  mv {quoted_install_path} {quoted_install_path}.backup.$(date +%s)")
        print(f"  ln -s {shlex.quote(str(repo))} {quoted_install_path}")
        return 1

    if install_path.is_symlink():
        print(f"Installed skill matches repo (symlink): {install_path} -> {installed}")
    else:
        print(f"Installed skill matches repo ({install_kind}): {installed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
