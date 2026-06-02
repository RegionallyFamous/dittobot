#!/usr/bin/env python3
"""Check an uploadable Youish skill ZIP."""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from package_files import PACKAGE_FILES, assert_mirror_fresh


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "youish"
PREFIX = "youish/"


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_path(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", help="Generated Youish skill ZIP.")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).expanduser()
    errors: list[str] = []
    assert_mirror_fresh(ROOT)

    if not zip_path.exists():
        errors.append(f"missing ZIP: {zip_path}")
    elif not zipfile.is_zipfile(zip_path):
        errors.append(f"not a valid ZIP: {zip_path}")

    if errors:
        print("Skill ZIP check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    expected = {f"{PREFIX}{rel}" for rel in PACKAGE_FILES}
    seen: list[str] = []

    with zipfile.ZipFile(zip_path) as handle:
        for info in handle.infolist():
            name = info.filename
            if name.endswith("/"):
                continue
            seen.append(name)
            if name.startswith("/") or ".." in Path(name).parts:
                errors.append(f"unsafe ZIP path: {name}")
            if not name.startswith(PREFIX):
                errors.append(f"file is outside youish/ prefix: {name}")

        duplicates = sorted({name for name in seen if seen.count(name) > 1})
        for name in duplicates:
            errors.append(f"duplicate ZIP entry: {name}")

        actual = set(seen)
        for name in sorted(expected - actual):
            errors.append(f"missing ZIP entry: {name}")
        for name in sorted(actual - expected):
            errors.append(f"unexpected ZIP entry: {name}")

        for rel in PACKAGE_FILES:
            entry = f"{PREFIX}{rel}"
            source = SKILL_ROOT / rel
            if entry not in actual:
                continue
            if not source.exists():
                errors.append(f"source mirror file missing: {rel}")
                continue
            if digest_bytes(handle.read(entry)) != digest_path(source):
                errors.append(f"ZIP entry differs from mirror: {entry}")

        if f"{PREFIX}SKILL.md" in actual:
            skill = handle.read(f"{PREFIX}SKILL.md").decode("utf-8")
            if "name: youish" not in skill[:500]:
                errors.append("SKILL.md frontmatter must name youish")

    if errors:
        print("Skill ZIP check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Skill ZIP check passed: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
