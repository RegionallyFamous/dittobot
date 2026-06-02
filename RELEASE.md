# Release Checklist

Dittobot's detailed release runbook lives in the wiki:

https://github.com/RegionallyFamous/dittobot/wiki/Release-Checklist

Short version:

1. Update `CHANGELOG.md`.
2. Run deterministic proof: `python3 scripts/validate_skill.py`, `python3 scripts/regression_100.py`, and `python3 scripts/scorecard.py --format json`.
3. Build and check the plugin package: `python3 scripts/build_plugin.py --version X.Y.Z`, then `python3 scripts/check_plugin_package.py dist/dittobot-plugin --version X.Y.Z`.
4. Build release assets: `python3 scripts/build_skill_zip.py --version X.Y.Z`, `python3 scripts/build_plugin_zip.py dist/dittobot-plugin --version X.Y.Z`, and `python3 scripts/write_checksums.py dist/dittobot-skill-vX.Y.Z.zip dist/dittobot-plugin-vX.Y.Z.zip`.
5. Generate the public scorecard with `scripts/scorecard.py --plugin-dir dist/dittobot-plugin --version X.Y.Z`.
6. Push and wait for GitHub Actions.
7. Confirm `gh skill publish --dry-run skills` is warning-free and the `Immutable v* release tags` ruleset is active.
8. Tag the validated commit and create the GitHub release with `dittobot-skill-vX.Y.Z.zip`, `dittobot-plugin-vX.Y.Z.zip`, and `SHA256SUMS`.

Use live eval only as a bounded smoke test. Deterministic checks are release proof. Only call a live transcript score "passing" if it was run with an explicit threshold such as `--fail-under-score 0.95`.
