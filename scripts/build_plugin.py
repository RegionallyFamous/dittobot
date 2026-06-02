#!/usr/bin/env python3
"""Build a local Codex plugin package for Youish."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from package_files import PACKAGE_FILES
from plugin_manifest import DEFAULT_VERSION, PLUGIN_NAME, manifest, require_semver


def copy_skill_package(repo: Path, plugin_root: Path) -> None:
    skill_root = plugin_root / "skills" / PLUGIN_NAME
    for rel in PACKAGE_FILES:
        source = repo / rel
        destination = skill_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def validate_plugin(plugin_root: Path, validator: str | None) -> int:
    if not validator:
        return 0
    validator_path = Path(validator).expanduser()
    if not validator_path.exists():
        print(f"Plugin validator not found, skipping: {validator_path}")
        return 0
    return subprocess.run(
        [sys.executable, str(validator_path), str(plugin_root)],
        check=False,
    ).returncode


def check_plugin_package(plugin_root: Path, version: str) -> int:
    return subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parent / "check_plugin_package.py"),
            str(plugin_root),
            "--version",
            version,
        ],
        check=False,
    ).returncode


def is_youish_plugin_dir(path: Path) -> bool:
    manifest_path = path / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        return False
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return payload.get("name") == PLUGIN_NAME


def assert_safe_output(repo: Path, output: Path, dist_root: Path) -> None:
    if output == dist_root:
        raise SystemExit("Refusing to replace the whole dist directory.")
    if output == repo or (
        repo in output.parents and output != dist_root and dist_root not in output.parents
    ):
        raise SystemExit("Refusing unsafe output directory inside the repo.")
    if output.exists() and not is_youish_plugin_dir(output):
        raise SystemExit(
            "Refusing to replace an existing directory that is not a Youish plugin package."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="dist/youish-plugin",
        help="Directory to create or replace.",
    )
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Strict semver plugin version.")
    parser.add_argument(
        "--validator",
        default=str(
            Path.home()
            / ".codex"
            / "skills"
            / ".system"
            / "plugin-creator"
            / "scripts"
            / "validate_plugin.py"
        ),
        help="Optional plugin validator path. Pass an empty string to skip.",
    )
    parser.add_argument(
        "--require-validator",
        action="store_true",
        help="Fail if the plugin validator path is empty or missing.",
    )
    parser.add_argument(
        "--skip-package-check",
        action="store_true",
        help="Skip Youish's local package checker. Intended only for checker failure tests.",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    output = (repo / args.output_dir).resolve()
    dist_root = (repo / "dist").resolve()
    require_semver(args.version, "Plugin version")
    assert_safe_output(repo, output, dist_root)
    if args.require_validator:
        validator = Path(args.validator).expanduser() if args.validator else None
        if validator is None or not validator.exists():
            raise SystemExit("Plugin validator is required but was not found.")
    if output.exists():
        shutil.rmtree(output)
    (output / ".codex-plugin").mkdir(parents=True, exist_ok=True)
    (output / ".codex-plugin" / "plugin.json").write_text(
        json.dumps(manifest(args.version), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    copy_skill_package(repo, output)
    code = validate_plugin(output, args.validator or None)
    if code != 0:
        return code
    if not args.skip_package_check:
        code = check_plugin_package(output, args.version)
        if code != 0:
            return code
    print(f"Built plugin package: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
