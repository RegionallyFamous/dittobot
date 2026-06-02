#!/usr/bin/env python3
"""Build an uploadable Youish skill ZIP from the spec package mirror."""

from __future__ import annotations

import argparse
import stat
import zipfile
from pathlib import Path

from package_files import PACKAGE_FILES, assert_mirror_fresh
from plugin_manifest import DEFAULT_VERSION, require_semver


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "youish"
ZIP_MTIME = (2026, 1, 1, 0, 0, 0)


def package_path(version: str, output_dir: Path) -> Path:
    return output_dir / f"youish-skill-v{version}.zip"


def add_file(handle: zipfile.ZipFile, source: Path, archive_name: str) -> None:
    info = zipfile.ZipInfo(archive_name, ZIP_MTIME)
    mode = stat.S_IMODE(source.stat().st_mode)
    info.external_attr = (mode or 0o644) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    handle.writestr(info, source.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Strict semver release version.")
    parser.add_argument("--output-dir", default="dist", help="Directory for the generated ZIP.")
    parser.add_argument("--output", help="Explicit ZIP path. Overrides --output-dir.")
    args = parser.parse_args()

    require_semver(args.version)
    if not SKILL_ROOT.exists():
        raise SystemExit("Missing skills/youish package mirror; run scripts/sync_skill_package.py.")
    assert_mirror_fresh(ROOT)

    missing = [rel for rel in PACKAGE_FILES if not (SKILL_ROOT / rel).exists()]
    if missing:
        raise SystemExit("Cannot build ZIP; package file(s) missing: " + ", ".join(missing))

    output = Path(args.output).expanduser() if args.output else package_path(args.version, Path(args.output_dir))
    output = output.resolve()
    if output.suffix != ".zip":
        raise SystemExit("Output path must end in .zip")
    output.parent.mkdir(parents=True, exist_ok=True)

    temp = output.with_name(f".{output.name}.tmp")
    if temp.exists():
        temp.unlink()

    with zipfile.ZipFile(temp, "w") as handle:
        for rel in PACKAGE_FILES:
            add_file(handle, SKILL_ROOT / rel, f"youish/{rel}")

    temp.replace(output)
    print(f"Built skill ZIP: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
