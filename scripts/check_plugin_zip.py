#!/usr/bin/env python3
"""Check a Youish plugin ZIP release asset."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from package_files import PACKAGE_FILES
from plugin_manifest import PLUGIN_NAME, SEMVER_RE


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FILES = {".codex-plugin/plugin.json"} | {
    f"skills/youish/{rel}" for rel in PACKAGE_FILES
}


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_path(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", help="Generated Youish plugin ZIP.")
    parser.add_argument("--version", help="Expected plugin manifest version.")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).expanduser()
    errors: list[str] = []

    if not zip_path.exists():
        errors.append(f"missing ZIP: {zip_path}")
    elif not zipfile.is_zipfile(zip_path):
        errors.append(f"not a valid ZIP: {zip_path}")

    if errors:
        print("Plugin ZIP check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    seen: list[str] = []
    with zipfile.ZipFile(zip_path) as handle:
        for info in handle.infolist():
            name = info.filename
            if name.endswith("/"):
                continue
            seen.append(name)
            if name.startswith("/") or ".." in Path(name).parts:
                errors.append(f"unsafe ZIP path: {name}")

        duplicates = sorted({name for name in seen if seen.count(name) > 1})
        for name in duplicates:
            errors.append(f"duplicate ZIP entry: {name}")

        actual = set(seen)
        for name in sorted(EXPECTED_FILES - actual):
            errors.append(f"missing ZIP entry: {name}")
        for name in sorted(actual - EXPECTED_FILES):
            errors.append(f"unexpected ZIP entry: {name}")

        if ".codex-plugin/plugin.json" in actual:
            manifest = json.loads(handle.read(".codex-plugin/plugin.json").decode("utf-8"))
            if manifest.get("name") != PLUGIN_NAME:
                errors.append(f"plugin name must be {PLUGIN_NAME}")
            version = manifest.get("version")
            if not isinstance(version, str) or SEMVER_RE.fullmatch(version) is None:
                errors.append("plugin version must be strict semver")
            if args.version and version != args.version:
                errors.append(f"plugin version must be {args.version}")
            if manifest.get("license") != "GPL-2.0-or-later":
                errors.append("plugin license must be GPL-2.0-or-later")

        for rel in PACKAGE_FILES:
            entry = f"skills/youish/{rel}"
            source = ROOT / rel
            if entry not in actual:
                continue
            if digest_bytes(handle.read(entry)) != digest_path(source):
                errors.append(f"ZIP entry differs from source: {entry}")

    if errors:
        print("Plugin ZIP check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Plugin ZIP check passed: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
