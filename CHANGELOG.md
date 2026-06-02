# Changelog

## Unreleased

Nothing yet.

## 0.3.2 - 2026-06-02

- Add spelled-out metric invention checks, such as `forty percent`, to the deterministic validator.
- Add narrow lowercase vendor detection for unsupported entity checks.
- Add required-claim polarity checks so `Do not send the job ID` cannot satisfy `send the job ID`.
- Add clarifying-refusal and wrapper-label coverage, including `I need to know the audience` and `Edited version:`.
- Mirror clarification and question-count controls in `rewrite_report.py`.
- Fill out Skills.sh-facing metadata and README listing fields for the public skill page.
- Add current research notes on LLM meaning drift and reusable skill quality.

## 0.3.1 - 2026-06-02

- Add Vercel-style skills.sh listing metadata and sharpen the public skill preview for voice-faithful rewriting.
- Require live transcript scorecards to use a complete 100-case suite unless partial private scoring is explicitly requested.
- Add a contract-registration guard so new regression contract groups cannot be omitted from public scorecards.
- Reject release scorecards generated from a dirty or stale commit.
- Add polarity checks for reader actions so a negated action cannot pass by substring match.
- Update release pins from `v0.3.0` to `v0.3.1` for GitHub CLI and one-line installs.

## 0.3.0 - 2026-06-02

- Rename the project from Dittobot to Youish to avoid confusion with an existing Ditto writing app.
- Rename the installable skill, Codex plugin package, marketplace metadata, release asset names, scorecard schema, and public docs to Youish.
- Expose deterministic contract-test groups in public scorecards and release validation.
- Add source-only artifact contracts for buried asks, owner/action recaps, and keyword-salad failures.
- Add sentence-quality guards for finished source-only prose so protected-term clusters cannot pass as rewrites.

## 0.2.7 - 2026-06-02

- Add reader-action preservation as a first-class deterministic guardrail for asks, owners, deadlines, and next steps.
- Add messy-dump contract tests for self-corrections and voice-density restraint without changing the public 100-case suite size.
- Thread reader-action checks through audit, rewrite-report, case-lab, and failure-fixture tools.
- Thread reader-action requirements through optional live-eval prompts and contract tests.
- Tighten SKILL.md while keeping it under the public word budget.
- Verify release scorecard skill and validator hashes against the shipped plugin ZIP contents.
- Strengthen release CI so scorecard hash negative tests reach the intended plugin mismatch guard.

## 0.2.6 - 2026-06-02

- Teach the install verifier to accept full repo-root skill copies, matching installers such as `npx skills add RegionallyFamous/youish`.
- Add CI coverage for root-copy installs so package-copy, symlink, and full-repo install paths stay supported.

## 0.2.5 - 2026-06-02

- Add auditable boundary extraction for explicit "do not use," "avoid," "does not apply," and "do not apply X to Y" guidance.
- Thread boundary rules through audit, rewrite-report, failure-fixture, case-lab, regression, and public scorecard tooling.
- Strengthen release builds so packaging verifies a clean committed state and fresh mirrors instead of mutating mirrors during release.
- Make README install commands copy-safe, add the open skills CLI path, and keep the public story centered on voice-preserving editing.
- Improve bad-rewrite and regression issue templates with prompt mode, precision context, boundary, and runnable fixture fields.
- Add CI coverage for boundary failure fixtures, numeric-context case lab output, dirty release guards, and version-drift failures.

## 0.2.4 - 2026-06-02

- Normalize GitHub CLI skill frontmatter whitespace in copied install checks so pinned `gh skill install` packages validate from the source repo checker.

## 0.2.3 - 2026-06-02

- Make the Codex plugin marketplace path installable by adding a `plugins/youish` package mirror and validating it.
- Strengthen regression coverage for unsupported entities, generic AI patterns, stance preservation, artifact leaks, over-formalizing, extra jokes, therapy-speak, dialect preservation, and plain-word flattening.
- Add new public scorecard guardrails for stance preservation, artifact cleanup, unsupported entity protection, and anti-generic polish.
- Make copied install checks tolerate GitHub CLI source metadata without ignoring the actual skill body.
- Harden release builds by building assets in a verified temporary directory before replacing the final `dist/release-vX.Y.Z` folder.
- Harden the one-line installer against unsafe custom archive paths, symlinks, and hardlinks.
- Tighten README persuasion with clearer proof, limits, skeptic-facing framing, and annotated research takeaways.

## 0.2.2 - 2026-06-02

- Let installed-copy validation tolerate GitHub CLI source-tracking metadata while keeping source repo frontmatter strict.

## 0.2.1 - 2026-06-02

- Add repo plugin marketplace metadata so Youish can be exposed as a Codex marketplace source.
- Add one-command release asset building, exact release asset verification, scorecard checksums, and stricter plugin package validation.
- Tighten README examples and skeptic-facing copy so the argument lands faster with less manifesto echo.
- Add optional archive checksum verification to the terminal installer and make the default install ref release-pinned.

## 0.2.0 - 2026-06-02

### Install And Distribution

- Add `$skill-installer`-first setup docs, a no-git terminal installer, and a GitHub CLI-compatible `skills/youish` package mirror.
- Make copied installs safer by detecting drift, replacing stale package files cleanly, backing up existing installs, and refusing unsafe targets.
- Add deterministic Codex plugin package building, plugin verification, uploadable skill ZIPs, plugin ZIPs, checksums, and CI release-asset checks.
- Add Codex UI icon assets, wire them into skill/plugin metadata, and add a risograph README banner for the voice-preserving editing metaphor.

### Voice Behavior

- Strengthen voice preservation, emotional anti-flattening, mixed anger/hope handling, format preservation, and source-only thought-dump defaults.
- Add guidance for reader comprehension, user corrections, dialect/code-switching/regional idiom, interpersonal precision, and no-wrapper rewrite output.
- Add reusable fact-fence and voice-profile-card references, real `[[boundary: ...]]` ledger parsing, and compact voice profile contracts.

### Validation And Tooling

- Add portable repo validation, progressive-disclosure word-budget checks, public README copy checks, and GitHub Actions validation.
- Expand deterministic regression coverage for protected facts, claim fidelity, uncertainty, modality drift, causality drift, invented details, no-dash constraints, wrapper detection, ordered terms, artifact cleanup, and exact formatting.
- Add model-free audit, rewrite report, voice probe, case lab, redaction, failure fixture, live report, and scorecard tools.
- Add optional live-model smoke testing with safer API handling, source-only prompt inspection, replayable transcripts, fail-fast controls, hash-only saved transcript defaults, and API-error transcript records.

### Docs And Governance

- Refocus the README on the anti-slop argument, Youish's origin story, and in-process examples.
- Move operational runbooks into the GitHub wiki.
- Add bad-rewrite and regression-case issue templates, a pull request checklist, contributor guide, security/privacy guidance, and release checklist.

## 0.1.0

- Initial public Youish skill release.
