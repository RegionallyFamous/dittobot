#!/usr/bin/env python3
"""Check Youish's repo plugin manifest and marketplace entry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from plugin_manifest import DEFAULT_VERSION, manifest, require_semver
from package_files import PACKAGE_FILES, digest


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Expected plugin version.")
    args = parser.parse_args()
    require_semver(args.version)

    errors: list[str] = []
    manifest_path = ROOT / ".codex-plugin" / "plugin.json"
    marketplace_path = ROOT / ".agents" / "plugins" / "marketplace.json"

    if not manifest_path.exists():
        errors.append("missing .codex-plugin/plugin.json")
    else:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = manifest(args.version)
        if payload != expected:
            errors.append(".codex-plugin/plugin.json differs from scripts/plugin_manifest.py")
        interface = payload.get("interface", {})
        for field in ("composerIcon", "logo"):
            value = interface.get(field)
            if not isinstance(value, str) or not (ROOT / value).exists():
                errors.append(f"plugin interface.{field} points to a missing file")

    if not marketplace_path.exists():
        errors.append("missing .agents/plugins/marketplace.json")
    else:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        if marketplace.get("name") != "youish":
            errors.append("marketplace name must be youish")
        if marketplace.get("interface", {}).get("displayName") != "Youish":
            errors.append("marketplace interface.displayName must be Youish")
        plugins = marketplace.get("plugins")
        if not isinstance(plugins, list) or len(plugins) != 1:
            errors.append("marketplace must contain exactly one plugin entry")
        else:
            entry = plugins[0]
            if entry.get("name") != "youish":
                errors.append("marketplace plugin name must be youish")
            source = entry.get("source", {})
            if source != {"source": "local", "path": "./plugins/youish"}:
                errors.append(
                    'marketplace source must be {"source": "local", "path": "./plugins/youish"}'
                )
            policy = entry.get("policy", {})
            if policy.get("installation") != "AVAILABLE":
                errors.append("marketplace policy.installation must be AVAILABLE")
            if policy.get("authentication") != "ON_INSTALL":
                errors.append("marketplace policy.authentication must be ON_INSTALL")
            if entry.get("category") != "Productivity":
                errors.append("marketplace category must be Productivity")

    plugin_mirror = ROOT / "plugins" / "youish"
    mirror_manifest = plugin_mirror / ".codex-plugin" / "plugin.json"
    if not mirror_manifest.exists():
        errors.append("missing marketplace plugin mirror manifest")
    else:
        payload = json.loads(mirror_manifest.read_text(encoding="utf-8"))
        if payload != manifest(args.version):
            errors.append("marketplace plugin mirror manifest differs from scripts/plugin_manifest.py")
    for rel in PACKAGE_FILES:
        source = ROOT / rel
        packaged = plugin_mirror / "skills" / "youish" / rel
        if not packaged.exists():
            errors.append(f"missing marketplace plugin skill file: {rel}")
        elif source.exists() and digest(source) != digest(packaged):
            errors.append(f"stale marketplace plugin skill file: {rel}")

    if errors:
        print("Marketplace check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Marketplace check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
