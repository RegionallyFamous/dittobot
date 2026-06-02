#!/usr/bin/env python3
"""Shared Youish plugin manifest values."""

from __future__ import annotations

import re


PLUGIN_NAME = "youish"
DEFAULT_VERSION = "0.3.0"
PLUGIN_DESCRIPTION = "Voice-faithful rewrites that keep your claims, stance, and rhythm."
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def require_semver(version: str, label: str = "Version") -> None:
    if SEMVER_RE.fullmatch(version) is None:
        raise SystemExit(f"{label} must be strict semver: {version}")


def manifest(version: str) -> dict:
    require_semver(version, "Plugin version")
    return {
        "name": PLUGIN_NAME,
        "version": version,
        "description": PLUGIN_DESCRIPTION,
        "skills": "./skills/",
        "author": {
            "name": "Regionally Famous",
            "url": "https://github.com/RegionallyFamous",
        },
        "homepage": "https://github.com/RegionallyFamous/youish",
        "repository": "https://github.com/RegionallyFamous/youish",
        "license": "GPL-2.0-or-later",
        "keywords": ["writing", "editing", "voice", "rewrites", "skills"],
        "interface": {
            "displayName": "Youish",
            "shortDescription": "Voice-faithful rewrites without factual drift.",
            "longDescription": (
                "Youish rewrites messy drafts, notes, emails, and posts while "
                "preserving the user's claims, stance, uncertainty, rhythm, "
                "distinctive phrases, reader action, and constraints."
            ),
            "developerName": "Regionally Famous",
            "category": "Productivity",
            "capabilities": [
                "Voice-preserving rewrites",
                "Messy-note cleanup",
                "Fact and claim protection",
                "Refuses unsupported details",
            ],
            "websiteURL": "https://github.com/RegionallyFamous/youish",
            "privacyPolicyURL": "https://github.com/RegionallyFamous/youish/blob/main/SECURITY.md",
            "termsOfServiceURL": "https://github.com/RegionallyFamous/youish/blob/main/LICENSE",
            "brandColor": "#4F46E5",
            "composerIcon": "skills/youish/assets/icon-small.svg",
            "logo": "skills/youish/assets/icon-large.svg",
            "defaultPrompt": [
                "Use $youish on this. Paste the messy draft below.",
                "Use $youish to infer a compact voice profile.",
                "Use $youish and show what changed and why.",
            ],
        },
    }
