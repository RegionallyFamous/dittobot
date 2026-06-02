# Release Checklist

Youish's detailed release runbook lives in the wiki:

https://github.com/RegionallyFamous/youish/wiki/Release-Checklist

Short version:

1. Update `CHANGELOG.md`.
2. Run the one-command release builder: `python3 scripts/build_release_assets.py --version X.Y.Z`.
3. Push and wait for GitHub Actions.
4. Confirm `gh skill publish --dry-run skills` is warning-free and the `Immutable v* release tags` ruleset is active.
5. Tag the validated commit and push the tag.
6. Create the GitHub release from the already-pushed tag:

```bash
gh release create vX.Y.Z \
  dist/release-vX.Y.Z/youish-skill-vX.Y.Z.zip \
  dist/release-vX.Y.Z/youish-plugin-vX.Y.Z.zip \
  dist/release-vX.Y.Z/youish-scorecard-vX.Y.Z.json \
  dist/release-vX.Y.Z/SHA256SUMS \
  --verify-tag \
  --fail-on-no-commits \
  --title "Youish vX.Y.Z" \
  --generate-notes
```

Use `--verify-tag`; without it, `gh release create` can create a missing tag from the default branch, which is exactly the kind of release magic trick nobody asked for.

Run GitHub CLI skill publishing from `skills`, not the repo root. The repo root also has `SKILL.md` for local Codex installs, and `gh skill publish /path/to/repo --dry-run` treats the root directory name as the skill slug.

Use live eval only as a bounded smoke test. Deterministic checks are release proof. Only call a live transcript score "passing" if it was run with an explicit threshold such as `--fail-under-score 0.95`.
