#!/usr/bin/env python3
"""Shared Dittobot plugin manifest values."""

from __future__ import annotations

import re


PLUGIN_NAME = "dittobot"
DEFAULT_VERSION = "0.2.7"
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
        "homepage": "https://github.com/RegionallyFamous/dittobot",
        "repository": "https://github.com/RegionallyFamous/dittobot",
        "license": "GPL-2.0-or-later",
        "keywords": ["writing", "editing", "voice", "rewrites", "skills"],
        "interface": {
            "displayName": "Dittobot",
            "shortDescription": "Voice-faithful rewrites without factual drift.",
            "longDescription": (
                "Dittobot rewrites messy drafts, notes, emails, and posts while "
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
            "websiteURL": "https://github.com/RegionallyFamous/dittobot",
            "privacyPolicyURL": "https://github.com/RegionallyFamous/dittobot/blob/main/SECURITY.md",
            "termsOfServiceURL": "https://github.com/RegionallyFamous/dittobot/blob/main/LICENSE",
            "brandColor": "#4F46E5",
            "composerIcon": "skills/dittobot/assets/icon-small.svg",
            "logo": "skills/dittobot/assets/icon-large.svg",
            "defaultPrompt": [
                "Use $dittobot on this. Paste the messy draft below.",
                "Use $dittobot to infer a compact voice profile.",
                "Use $dittobot and show what changed and why.",
            ],
        },
    }
