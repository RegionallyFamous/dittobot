#!/usr/bin/env python3
"""Files that make up the installable Youish skill package."""

from __future__ import annotations

import hashlib
from pathlib import Path


PACKAGE_FILES = (
    "SKILL.md",
    "LICENSE",
    "metadata.json",
    "agents/openai.yaml",
    "assets/icon-large.svg",
    "assets/icon-small.svg",
    "references/fact-fences.md",
    "references/quality-gates.md",
    "references/voice-profile-cards.md",
    "scripts/audit.py",
    "scripts/case_lab.py",
    "scripts/check_install.py",
    "scripts/failure_fixture.py",
    "scripts/failure_taxonomy.py",
    "scripts/install.py",
    "scripts/ledger.py",
    "scripts/live_eval.py",
    "scripts/live_report.py",
    "scripts/package_files.py",
    "scripts/plugin_manifest.py",
    "scripts/regression_100.py",
    "scripts/redact_case.py",
    "scripts/rewrite_report.py",
    "scripts/scorecard.py",
    "scripts/validate_skill.py",
    "scripts/voice_profile.py",
    "scripts/voice_probe.py",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mirror_mismatches(root: Path) -> list[str]:
    mirror = root / "skills" / "youish"
    plugin_mirror = root / "plugins" / "youish" / "skills" / "youish"
    mismatches: list[str] = []
    for label, package_root in (
        ("skills/youish", mirror),
        ("plugins/youish/skills/youish", plugin_mirror),
    ):
        for rel in PACKAGE_FILES:
            source = root / rel
            packaged = package_root / rel
            if not source.exists() or not packaged.exists() or digest(source) != digest(packaged):
                mismatches.append(f"{label}/{rel}")
    return mismatches


def assert_mirror_fresh(root: Path) -> None:
    mismatches = mirror_mismatches(root)
    if mismatches:
        raise SystemExit(
            "skills/youish mirror is stale; run scripts/sync_skill_package.py "
            "and commit the updated package mirror. Mismatched file(s): "
            + ", ".join(mismatches)
        )
