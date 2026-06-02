#!/usr/bin/env python3
"""Verify a complete local Youish release asset directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from plugin_manifest import DEFAULT_VERSION, require_semver


ROOT = Path(__file__).resolve().parents[1]


def release_asset_names(version: str) -> set[str]:
    return {
        f"youish-skill-v{version}.zip",
        f"youish-plugin-v{version}.zip",
        f"youish-scorecard-v{version}.json",
        "SHA256SUMS",
    }


def checksummed_asset_names(version: str) -> set[str]:
    return release_asset_names(version) - {"SHA256SUMS"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: list[str]) -> None:
    result = subprocess.run(args, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def git_value(args: list[str]) -> str | None:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def parse_checksums(path: Path) -> tuple[dict[str, str], list[str]]:
    hashes: dict[str, str] = {}
    errors: list[str] = []
    for index, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"bad checksum line {index}: {raw_line!r}")
            continue
        checksum, name = parts
        if len(checksum) != 64 or any(char not in "0123456789abcdef" for char in checksum):
            errors.append(f"bad sha256 on line {index}: {checksum!r}")
        if "/" in name or "\\" in name or name in {".", ".."}:
            errors.append(f"unsafe checksum filename on line {index}: {name!r}")
        if name in hashes:
            errors.append(f"duplicate checksum entry: {name}")
        hashes[name] = checksum
    return hashes, errors


def load_scorecard(path: Path) -> tuple[dict | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"scorecard is not valid JSON: {exc}"]
    if not isinstance(payload, dict):
        return None, ["scorecard must be a JSON object"]
    return payload, []


def check_scorecard_payload(payload: dict, version: str) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != "youish.scorecard.v1":
        errors.append("scorecard schema_version must be youish.scorecard.v1")
    if payload.get("project") != "youish":
        errors.append("scorecard project must be youish")
    if payload.get("score", {}).get("status") != "PASS":
        errors.append("scorecard status must be PASS")
    if payload.get("suite", {}).get("case_count") != 100:
        errors.append("scorecard suite.case_count must be 100")
    if payload.get("plugin", {}).get("version") != version:
        errors.append(f"scorecard plugin version must be {version}")
    if payload.get("plugin", {}).get("status") != "PASS":
        errors.append("scorecard plugin package status must be PASS")
    subject = payload.get("subject", {})
    if subject.get("dirty") is not False:
        errors.append("scorecard subject.dirty must be false")
    current_commit = git_value(["rev-parse", "--short", "HEAD"])
    if current_commit and subject.get("commit") != current_commit:
        errors.append(
            "scorecard subject.commit must match current HEAD "
            f"({current_commit}), got {subject.get('commit')}"
        )
    contracts = payload.get("contract_tests")
    if not isinstance(contracts, dict):
        errors.append("scorecard contract_tests must be present")
    else:
        if contracts.get("status") != "PASS":
            errors.append("scorecard contract_tests status must be PASS")
        groups = contracts.get("groups")
        if not isinstance(groups, list) or len(groups) != 14:
            errors.append("scorecard contract_tests.groups must contain 14 groups")
        elif "contract_registration_contracts" not in {
            str(group.get("name")) for group in groups if isinstance(group, dict)
        }:
            errors.append("scorecard contract_tests.groups must include contract_registration_contracts")
    return errors


def check_scorecard_hashes(payload: dict, plugin_root: Path) -> list[str]:
    errors: list[str] = []
    hash_checks = (
        (
            "subject.skill_sha256",
            payload.get("subject", {}).get("skill_sha256"),
            plugin_root / "skills" / "youish" / "SKILL.md",
        ),
        (
            "suite.validator_sha256",
            payload.get("suite", {}).get("validator_sha256"),
            plugin_root / "skills" / "youish" / "scripts" / "regression_100.py",
        ),
    )
    for label, expected, path in hash_checks:
        if not isinstance(expected, str) or len(expected) != 64:
            errors.append(f"scorecard {label} must be a sha256")
        elif not path.exists():
            errors.append(f"scorecard hash target missing: {path.relative_to(plugin_root)}")
        elif digest(path) != expected:
            errors.append(f"scorecard {label} does not match {path.relative_to(plugin_root)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "release_dir",
        nargs="?",
        default=f"dist/release-v{DEFAULT_VERSION}",
        help="Directory containing release assets.",
    )
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Strict semver release version.")
    args = parser.parse_args()

    require_semver(args.version)
    release_dir = Path(args.release_dir).expanduser().resolve()
    expected = release_asset_names(args.version)
    checksummed = checksummed_asset_names(args.version)
    errors: list[str] = []

    if not release_dir.is_dir():
        print(f"Release asset check failed: missing directory {release_dir}")
        return 1

    actual_files = {item.name for item in release_dir.iterdir() if item.is_file()}
    for name in sorted(expected - actual_files):
        errors.append(f"missing release asset: {name}")
    for name in sorted(actual_files - expected):
        errors.append(f"unexpected release asset: {name}")

    sums_path = release_dir / "SHA256SUMS"
    if sums_path.exists():
        hashes, checksum_errors = parse_checksums(sums_path)
        errors.extend(checksum_errors)
        for name in sorted(checksummed - set(hashes)):
            errors.append(f"missing checksum entry: {name}")
        for name in sorted(set(hashes) - checksummed):
            errors.append(f"unexpected checksum entry: {name}")
        for name in sorted(checksummed & set(hashes)):
            asset = release_dir / name
            if asset.exists() and digest(asset) != hashes[name]:
                errors.append(f"checksum mismatch: {name}")

    scorecard_payload: dict | None = None
    scorecard = release_dir / f"youish-scorecard-v{args.version}.json"
    if scorecard.exists():
        scorecard_payload, scorecard_errors = load_scorecard(scorecard)
        errors.extend(scorecard_errors)
        if scorecard_payload is not None:
            errors.extend(check_scorecard_payload(scorecard_payload, args.version))

    if errors:
        print("Release asset check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    skill_zip = release_dir / f"youish-skill-v{args.version}.zip"
    plugin_zip = release_dir / f"youish-plugin-v{args.version}.zip"
    run([sys.executable, str(ROOT / "scripts" / "check_skill_zip.py"), str(skill_zip)])
    run(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_plugin_zip.py"),
            str(plugin_zip),
            "--version",
            args.version,
        ]
    )

    temp = Path(tempfile.mkdtemp(prefix="youish-release-check."))
    try:
        with zipfile.ZipFile(plugin_zip) as handle:
            handle.extractall(temp)
        if scorecard_payload is not None:
            errors.extend(check_scorecard_hashes(scorecard_payload, temp))
        run(
            [
                sys.executable,
                str(ROOT / "scripts" / "check_plugin_package.py"),
                str(temp),
                "--version",
                args.version,
            ]
        )
    finally:
        shutil.rmtree(temp, ignore_errors=True)

    if errors:
        print("Release asset check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Release asset check passed: {release_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
