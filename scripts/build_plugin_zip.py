#!/usr/bin/env python3
"""Build a deterministic Youish plugin ZIP from a checked plugin directory."""

from __future__ import annotations

import argparse
import stat
import zipfile
from pathlib import Path

from package_files import PACKAGE_FILES
from plugin_manifest import DEFAULT_VERSION, require_semver


EXPECTED_FILES = {".codex-plugin/plugin.json"} | {
    f"skills/youish/{rel}" for rel in PACKAGE_FILES
}
ZIP_MTIME = (2026, 1, 1, 0, 0, 0)


def output_path(version: str, output_dir: Path) -> Path:
    return output_dir / f"youish-plugin-v{version}.zip"


def files_in(path: Path) -> set[str]:
    return {
        item.relative_to(path).as_posix()
        for item in path.rglob("*")
        if item.is_file()
    }


def add_file(handle: zipfile.ZipFile, source: Path, archive_name: str) -> None:
    info = zipfile.ZipInfo(archive_name, ZIP_MTIME)
    mode = stat.S_IMODE(source.stat().st_mode)
    info.external_attr = (mode or 0o644) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    handle.writestr(info, source.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_dir", help="Generated plugin package directory.")
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Strict semver release version.")
    parser.add_argument("--output-dir", default="dist", help="Directory for the generated ZIP.")
    parser.add_argument("--output", help="Explicit ZIP path. Overrides --output-dir.")
    args = parser.parse_args()

    require_semver(args.version)
    plugin = Path(args.plugin_dir).expanduser().resolve()
    if not plugin.exists():
        raise SystemExit(f"Plugin directory not found: {plugin}")

    actual = files_in(plugin)
    missing = sorted(EXPECTED_FILES - actual)
    unexpected = sorted(actual - EXPECTED_FILES)
    if missing or unexpected:
        for rel in missing:
            print(f"missing plugin file: {rel}")
        for rel in unexpected:
            print(f"unexpected plugin file: {rel}")
        raise SystemExit("Plugin directory is not a clean Youish plugin package.")

    output = Path(args.output).expanduser() if args.output else output_path(args.version, Path(args.output_dir))
    output = output.resolve()
    if output.suffix != ".zip":
        raise SystemExit("Output path must end in .zip")
    output.parent.mkdir(parents=True, exist_ok=True)

    temp = output.with_name(f".{output.name}.tmp")
    if temp.exists():
        temp.unlink()
    with zipfile.ZipFile(temp, "w") as handle:
        for rel in sorted(EXPECTED_FILES):
            add_file(handle, plugin / rel, rel)
    temp.replace(output)
    print(f"Built plugin ZIP: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
