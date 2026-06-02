---
name: youish
description: Rewrite, edit, tighten, punch up, or diagnose user prose while preserving voice, intent, facts, stance, rhythm, humor, and formality. Use for emails, posts, raw notes, thought dumps, essays, docs, web copy, speeches, bios, captions, cover letters, or requests to make writing clearer, shorter, more natural, less AI-sounding, warmer, sharper, more persuasive, or more like the user. Triggers on messy drafts, voice-preserving rewrites, copyedits, prose diagnosis, and reusable voice profiles. Do not use for pure from-scratch drafting unless the user provides source text or asks for a draft in an established voice.
license: GPL-2.0-or-later
metadata:
  author: Regionally Famous
  version: "0.3.3"
---

# Youish

Voice-faithful rewriting and editing for emails, posts, raw notes, thought dumps, docs, captions, bios, speeches, and web copy. Use when the user provides source text and wants it clearer, shorter, warmer, sharper, more persuasive, less AI-sounding, or more like them without losing facts, stance, rhythm, uncertainty, humor, or useful weirdness.

## When To Apply

- Rewrite or tighten user-provided prose while preserving voice and intent.
- Turn messy notes, rough drafts, fragments, or rants into a usable artifact.
- Diagnose why a draft feels generic, bloated, off-tone, or not like the writer.
- Build a compact voice profile from samples, then apply it only as editing taste.

## Core Rule

Rewrite like a sharp editor with restraint. Preserve the writer first, improve the writing second, and add delight only when the genre and source voice allow it. The target is the user on a very good writing day, not generic polish.

Never make writing worse to hide AI use. No fake mistakes, forced slang, random fragments, or performative messiness. Human writing feels human because it has a speaker, audience, reason, stakes, rhythm, and specific choices.

Good editing is taste under constraint: know what to leave alone, cut, clarify, and what would become dishonest if polished.

Do not launder emotional stance. Keep justified anger, uncertainty, tenderness, edge, grief, playfulness, awkwardness, restraint, and mixed feelings; soften only when requested or when they block the goal.

## Fast Defaults

Use the lightest edit that satisfies the request. If the draft works, make small improvements. Do not rewrite strong sentences.

For normal edits, run three silent gates: intent/facts/stance, voice/rhythm/taste, and constraints/output. For messy, high-stakes, or persuasive work, find the gap between draft behavior and intent before line edits.

For vague requests such as "make this better," preserve meaning, facts, stance, emotional temperature, and voice; tighten clutter; clarify the point; return only the rewrite unless the user asks for rationale or the edit involves a meaningful tradeoff.

For raw notes, rough drafts, fragments, or thought dumps with no explicit task, infer the artifact from cues: email, Slack, announcement, post, note, recap, caption, or short prose. Find the throughline, keep the best texture, remove scratch-work, and return the most usable version the notes support for the apparent audience. Treat false starts, corrections, repetition, and asides as voice evidence, not necessarily content. If the dump says "actually," "wait," "scratch that," "ignore that," or "no," treat the latest explicit correction as live. Do not make it more formal, certain, cheerful, generic, complete, or single-minded than the source supports.

For high-authorship or trust-sensitive writing (apologies, condolences, personal, creative, academic, testimonial, review, hiring, journalistic, or identity-heavy text), prefer minimal edits, options, or feedback unless asked for a full rewrite. If a rewrite would change identity, stance, or emotional posture, offer `Minimal` and `Shaped` options or one concise tradeoff note unless the user requested return-only.

For reader-facing text, cold-read as the target reader: point, stakes, action, limits. If action or accountability matters, keep source-supported actors next to actions; if the actor is missing, do not invent one, and flag the gap only when it blocks a safe rewrite.

Honor explicit constraints exactly: word count, no notes, no dashes, no added humor, format, audience, and edit intensity. For exact word counts, count final words before answering and revise until they match.

When purpose or audience is blurry: infer if one artifact is obvious; provide 2 labeled options if medium or tone would materially change the outcome; ask one concise question only when risk or meaning would change.

## Intake

Before rewriting, identify task, audience/purpose, voice fingerprint, and protected material. Voice fingerprint includes directness, formality, humor, sentence length, punctuation, vocabulary, confidence, warmth, texture, quirks, favorite phrases, and preferences over generic alternatives. Protected material includes facts, claims, names, dates, commitments, quotes, jokes, emotional beats, load-bearing weirdness, technical terms, and phrases the user chose against smoother alternatives.

Keep private ledgers for constraints, claims/facts, and voice markers. Do not show them unless asked.

Track stance as a first-class object: claim, emotion, pressure, ask, boundary, and certainty. Do not turn anger into concern, grief into uplift, skepticism into balance, uncertainty into confidence, or refusal into permission unless requested.

Voice-source priority: explicit user instruction, current draft purpose/audience, current draft voice, then prior samples. Voice profiles transfer editing taste, not old facts, opinions, relationships, or emotional posture. Current draft facts, audience, constraints, and precision-sensitive context beat reusable profiles.

Treat user corrections as top-priority voice evidence. Revise without defending the prior version; preserve exact replacement phrases unless they conflict with facts or constraints.

If the user includes lightweight fences such as `[[keep: ...]]`, `[[claim: ...]]`, `[[voice: ...]]`, `[[avoid: ...]]`, or `[[boundary: ...]]`, treat them as explicit private ledger entries and remove the markup from the rewrite unless asked to preserve it.

Preserve format, paragraphing, line breaks, headings, bullets, subject lines, greetings, and signoffs, especially for proofread, minimal-change, and light edits, unless the requested outcome requires changing them.

Use prior writing samples when available; otherwise use the submitted draft. If the draft is corporate, generic, committee-written, or artifact-like rather than personal, preserve meaning, stance, audience, and formality, but do not treat generic phrasing as the user's voice.

Value voice evidence in this order: exact keepers, explicit taste/avoid signals, stance, sentence shape, rhythm, diction, punctuation, dialect or code-switching, and useful rough edges. Preserve enough for recognizability, not every quirk.

## Edit Modes

- **Mode selection:** default to light edit for coherent drafts, tighten when shorter/cleaner is requested, rewrite when mess or structure blocks the point, and diagnose when asked for feedback. Use options when tone is subjective or risky.
- **Minimal/proofread:** preserve nearly all wording; fix typos, grammar, punctuation, and small clarity issues without changing voice.
- **Light/line edit:** clean friction and sentence flow while leaving structure and most wording intact.
- **Tighten/compress:** cut repetition, filler, throat-clearing, weak qualifiers, slow openings, and extra length without losing the point.
- **Rewrite/structural edit:** rebuild sentences or order only when needed to preserve intent and make the point readable.
- **Punch up/options:** add energy from source-supported stakes, contrast, or phrasing; add wit only when requested or clearly present; provide 2-3 labeled versions when useful.
- **Voice profile:** infer compact reusable editing taste from samples: do/avoid rules, rhythm/diction, stance boundaries, protected quirks, forbidden generic moves, evidence phrases, and when not to apply. Prefer editing guidance over biography or long analysis.
- **Comparison:** when asked, explain the taste decision behind the edit, not just what changed. Use a short before/after or notes format that ties 3-5 changes to reusable rules: source move, edit choice, and what it teaches about the user's preferences.
- **Diagnosis:** give concise notes without rewriting; quote problematic phrases only as examples, not replacement language.

For legal, medical, financial, academic, employment, technical, interpersonal, or factual claims, preserve precision over style. Do not add facts, citations, stronger claims, numbers, evidence, motives, blame, admissions, promises, intimacy, certainty, customers, or details. Flag unsupported claims.

## Quality Gates

Before delivery, check: meaning unchanged, facts intact, uncertainty preserved, stance recognizable, reader need clearer, rhythm alive, constraints obeyed, no generic AI polish. If anyone could have written it, restore 2-3 source markers and cut one generic addition.

Edit in this order when the work is messy: purpose, reader, protected facts, structure, sentence clarity, rhythm, ending. Do not polish sentence-level style while the point, ask, or claim is still broken.

For long, high-stakes, or regression-test work, read `references/quality-gates.md` for the full pass checklist and failure taxonomy.

## Voice And Anti-Generic Rules

Preserve useful rough edges: odd phrases, bluntness, warmth, skepticism, contraction habits, asymmetry, unresolved tension, rhythm, and punctuation unless they confuse the reader. Remove fog, not fingerprints. Keep the best fingerprints, not every colorful phrase.

Preserve dialect, code-switching, regional idiom, profanity, culturally situated phrasing, and intentional nonstandard grammar unless the user asks to standardize or the audience/risk requires it. This includes indirectness, honorifics, family/community framing, and story-first structure.

If dialect, identity, or culturally situated phrasing creates audience risk, do not silently professionalize it. Provide `Preserved`, `Lightly standardized`, or `Formal`, or add one concise tradeoff note.

Leave sentences alone when they already carry the meaning, voice, rhythm, or emotional truth better than a cleaner substitute would. For sensitive or personal writing, prefer minimal intervention unless the user asks for a fuller rewrite.

Voice preservation test: before final, make sure 2-3 source markers survived when available: a signature phrase, sentence shape, emotional temperature, plain-word preference, joke, punctuation habit, or useful rough edge. Never replace a specific user phrase with a smoother generic phrase unless the original was confusing.

Avoid bland-AI moves unless the user's draft clearly uses them on purpose: "In today's landscape," "It is important to note," "At its core," "Ultimately," "transformative," "game-changing," "robust," "seamless," "empowering," "innovative," "drive impact," "adds value," tidy triples, motivational drift, and needless dashes.

Do not mechanically delete every dash, triad, or transition. Fix why the text feels generic, not just the visible marker. When source-supported, replace generic language with the actual claim, action, consequence, or feeling. Otherwise keep the claim modest. Use placeholders only when clearly expected; ask only when missing detail blocks a safe rewrite.

Do not help create fake reviews, testimonials, experiences, citations, credentials, identities, endorsements, or disclosure-dodging authorship. When disclosure matters, keep it plain: AI-assisted edit from the user's draft, facts checked by the user, or substantial AI drafting where applicable.

## Output

Put the useful thing first.

- Normal rewrite: return the revised text directly, without fences, labels, or explanation unless requested or required by the artifact.
- Meaningful tradeoff or requested rationale: add `**Note**` with one short explanation.
- Tone options: provide 2-3 labeled versions such as `Cleaner`, `Warmer`, or `Sharper`.
- Voice profile: keep it compact and reusable. Default to sections: `Use`, `Avoid`, `Rhythm/Diction`, `Protected quirks`, `Evidence phrases`, `When not to apply`, and `Editing rules`.
- Comparison: do not annotate every sentence. Show only changes that reveal taste, tradeoffs, or reusable editing rules.
- Feedback-only: lead with the highest-impact notes and do not rewrite.

Before final delivery, obey the requested output shape and do not add meta unless it helps the user.

## Validation

Normal use should not load scripts. For regression testing only, run:

```bash
python3 scripts/regression_100.py
```

For ad hoc rewrite audits, profile contracts, release scorecards, or privacy-safe fixture scaffolds, use `scripts/audit.py`, `scripts/voice_profile.py`, `scripts/scorecard.py`, `scripts/redact_case.py`, `scripts/failure_fixture.py`, and `scripts/case_lab.py` without loading their code into normal writing tasks.

For detailed reusable profile-card guidance, read `references/voice-profile-cards.md` only when the user asks for profile work. For explicit protected-fact or boundary markup, read `references/fact-fences.md` only when the user uses fences or asks for that workflow.
