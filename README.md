# Youish

Voice-faithful rewrites for people who want AI to sound like them, not like a committee laminated a thesaurus.

[![Validate](https://github.com/RegionallyFamous/youish/actions/workflows/validate.yml/badge.svg)](https://github.com/RegionallyFamous/youish/actions/workflows/validate.yml)
![License: GPL-2.0-or-later](https://img.shields.io/badge/license-GPL--2.0--or--later-blue.svg)
![Runtime dependencies: none](https://img.shields.io/badge/runtime_deps-none-brightgreen.svg)
[![skills.sh](https://skills.sh/b/RegionallyFamous/youish)](https://skills.sh/RegionallyFamous/youish)

![A risograph-style Youish workshop turning messy notes into clean prose](assets/readme-riso-banner.jpg)

Paste messy notes. Get sharp prose that still sounds like you. That should not be controversial. Apparently we needed a tool anyway.

Youish turns rough drafts, notes, and rants into clear writing without sanding off the parts that sound like you. It is not AI trying to borrow a soul. It is an editor protecting the one already in the draft.

## What Youish Is

Youish is a Codex skill that edits from your source instead of inventing a new voice. It finds the point, protects facts and uncertainty, keeps useful rough edges, and cuts bland AI tells.

It is not a ghostwriter. It is a voice-preserving editor: your claims, your taste, your stance, your rhythm, just cleaned up enough that the reader does not have to excavate the point with a tiny shovel.

It also thinks about what the reader needs: the point, the stakes, the limits, and what to do next.

For heavier edits, it has a stricter internal checklist and tests for the promises people actually care about: facts stay put, uncertainty stays uncertainty, constraints get obeyed, and the weird good phrase survives.

Normal use is still simple: paste the mess and get the clean version.

Voice-faithful is not a vibe here:

- It keeps your claims, stance, uncertainty, rhythm, distinctive phrases, and reader action.
- It refuses fake facts, fake certainty, extra jokes, and generic polish that says less.
- The tests try to break those promises before a release does.

## The Point

The answer is not "let AI write for you." The answer is "teach the tool your voice."

This started because I watched a real critique turn into a dumb rule. People saw verbose, generic, dash-happy AI writing and jumped straight to "nobody should use AI for writing." I get the rage. Bad AI writing is padded, fake-confident, weirdly bloodless, and somehow proud of saying almost nothing.

I agreed with the diagnosis and hated the prescription.

Banning AI because bad AI writing exists treats the worst workflow as the only workflow. That is a very confident way to lose the plot.

If your AI writes badly, the answer is not to throw away the tool. The answer is to teach it taste.

## Watch It Work

### Stream Of Consciousness

Source:

```text
ok the launch note is somehow both too long and allergic to information. what i actually mean is we fixed the importer bug, people can retry failed rows now, and i need it to sound calm, useful, and not like a haunted changelog wearing a meeting lanyard
```

What Youish protects:

- The facts are "importer bug fixed" and "failed rows can be retried."
- The voice markers worth keeping are "allergic to information" and "haunted changelog wearing a meeting lanyard."

Rewrite:

```text
We fixed the importer bug. Failed rows can now be retried, so the note can be calm and useful instead of a haunted changelog wearing a meeting lanyard.
```

### Generic AI Paste

Source:

```text
In today's rapidly evolving landscape, our robust platform empowers teams to unlock seamless collaboration and drive meaningful impact. This sentence is wearing a borrowed suit and refusing to say where it works.
```

What Youish notices:

- The buzzword sentence has no usable facts, so inventing specifics would make it worse.
- The user's real voice is the complaint: "wearing a borrowed suit" and "refusing to say where it works."

Rewrite:

```text
This draft sounds like it is wearing a borrowed suit and refusing to say where it works. Add what changed, who it helps, and what people can do now.
```

### Voice Worth Keeping

Source:

```text
This draft is not bad. It just walks into the room, apologizes for existing, and hands the reader a damp napkin labeled strategy.
```

What Youish protects:

- The image is the point, not a joke to sand down.
- A smoother rewrite would be worse.

Rewrite:

```text
The draft is not bad. It just walks into the room, apologizes for existing, and hands the reader a damp napkin labeled strategy. The idea works; the framing is getting in its way.
```

### Precision-Sensitive Writing

Source:

```text
I think we probably need to send notice within 10 business days, but I am not counsel, the clause had weird carveouts, and I do not want to turn "maybe" into a courtroom kazoo.
```

What Youish protects:

- "Probably," "I think," and "not counsel" are precision, not clutter.
- The rewrite must keep the strange but useful warning: do not turn "maybe" into a courtroom kazoo.

Rewrite:

```text
I think we may need to send notice within 10 business days. I would not state that as definitive, because I am not counsel, the clause had unusual carveouts, and I do not want to turn "maybe" into a courtroom kazoo.
```

### Mixed Human Stance

Source:

```text
I am a little angry that people saw bad AI writing and decided the answer was banning the tool, but I am also genuinely excited because we can teach it taste instead of joining the pencils-are-holy club and polishing our typewriters by candlelight.
```

What Youish protects:

- The anger and hope both matter.
- The weird stance matters too: annoyed, hopeful, and unwilling to pretend pencils are holy.

Rewrite:

```text
I am annoyed that people saw bad AI writing and decided the answer was banning the tool. But I am also genuinely excited, because we can teach it taste instead of joining the pencils-are-holy club and polishing our typewriters by candlelight.
```

## What Skeptics Are Right About

The AI-writing backlash has receipts. People have seen enough soulless, padded, fake-confident slop to be annoyed. Good. Stay annoyed. Just aim the annoyance at the workflow instead of pretending the tool has only one possible setting.

- **"It sounds like nobody."** Correct, if you ask it to invent a voice. Youish starts from your words. The stance, rhythm, humor, pressure, and weird little phrase are already there.
- **"It gets bloated."** Bad AI writes like it is being paid by the clause. Youish cuts filler and returns the rewrite without a lecture unless you ask for one.
- **"It flattens everyone into the same house style."** Yes, if everyone accepts the first generic draft. Youish keeps dry jokes, justified edge, warmth, awkwardness, and useful rough edges.
- **"It invents confidence."** That is a real failure mode. Youish does not add numbers, customers, citations, examples, legal certainty, or convenient details that were not in the source.
- **"It hides who wrote it."** Editing is not the same as outsourcing authorship. Youish keeps your claims, taste, and decisions in charge.
- **"The tells give it away."** Dashes are not the crime. Predictability is. Youish can obey no-dash rules, but the deeper fix is cadence and taste.

The problem is not using AI. The problem is accepting the first bland answer, then blaming the whole category because nobody steered.

So the behavior is deliberately boring where bad AI gets cute:

- If the draft has no facts, Youish will not invent facts.
- If the draft has uncertainty, Youish keeps the uncertainty.
- If the draft has a weird good phrase, Youish protects it.
- If the draft is bloated, Youish cuts before it decorates.
- If a constraint says no dashes, no notes, or exactly 40 words, Youish treats that like the job.

## When Not To Use It

Youish needs source text or a real voice sample. It is not for making up legal, medical, financial, academic, or factual certainty. It should not bypass publication policies, disclosure rules, or common sense around private data.

When disclosure matters, say the true thing: edited with AI from my draft, grammar and clarity assistance only, or AI-assisted line edit with facts checked by me. Authorship is not a magic spell. Be honest about the workflow and keep responsibility where it belongs.

| Good For | Not For |
|---|---|
| Emails, posts, notes, announcements, bios, captions, messy drafts, and half-formed thoughts | Inventing facts, citations, customers, legal certainty, medical certainty, or financial advice |
| Making a real draft cleaner, sharper, shorter, warmer, stranger, or more readable | Hiding authorship, bypassing disclosure rules, or pretending nobody edited anything |
| Preserving a personal, team, or publication voice | Replacing judgment, policy, review, or the writer's responsibility |

## Use It

Install Youish from inside Codex:

```text
Use $skill-installer to install Youish from GitHub repo RegionallyFamous/youish. Use path "skills/youish" and install it as "youish".
```

Restart Codex, then most prompts can stay this boring:

```text
Use $youish on this:

[paste the messy draft, notes, rant, email, announcement, post, caption, or half-formed thought]
```

To verify the install with a real rewrite:

```text
Use $youish on this and return only the rewrite:

ok the launch note is somehow both too long and allergic to information. what i actually mean is we fixed the importer bug, people can retry failed rows now, and i need it to sound calm, useful, and not like a haunted changelog wearing a meeting lanyard
```

A good result should keep the facts: `importer bug fixed` and `failed rows can be retried`. It should also keep at least one live voice marker, like `haunted changelog`.

That is the point. Drop in the stream of consciousness; get back the version that sounds like you after sleep, coffee, and one more pass.

You do not need to say "preserve my voice," "do not add facts," or "keep uncertainty." That is the job. Add instructions only when you mean it: exact word count, no dashes, a specific audience, options, diagnosis-only, or show what changed.

Other install paths:

```bash
npx skills add https://github.com/RegionallyFamous/youish --skill youish
```

```bash
gh skill install RegionallyFamous/youish skills/youish --agent codex --scope user --pin v0.3.3
```

```bash
curl -fsSL https://raw.githubusercontent.com/RegionallyFamous/youish/v0.3.3/install.sh | YOUISH_REF=v0.3.3 bash
```

For a deterministic release-asset install that pulls the published skill ZIP and verifies it against `SHA256SUMS`:

```bash
curl -fsSL https://raw.githubusercontent.com/RegionallyFamous/youish/v0.3.3/install.sh | YOUISH_REF=v0.3.3 YOUISH_SOURCE=release-zip bash
```

Install destinations differ by tool: `npx skills` currently installs Codex-compatible skills into `~/.agents/skills/youish`; `gh skill install --agent codex --scope user` installs into `~/.codex/skills/youish`.

More options live in the [Install wiki](https://github.com/RegionallyFamous/youish/wiki/Install).

## Skills.sh Listing

The live skill page is [skills.sh/regionallyfamous/youish/youish](https://www.skills.sh/regionallyfamous/youish/youish). The repo supplies every listing field it can control; Skills.sh fills the rest from its index, GitHub, telemetry, and partner audits.

| Listing Field | Youish Value |
|---|---|
| Name | `youish` |
| Installation | `npx skills add https://github.com/RegionallyFamous/youish --skill youish` |
| Repository | `regionallyfamous/youish` |
| Group | Writing & Editing |
| Topics | Writing, editing, copywriting, agent workflows |
| Agents | Codex, Claude Code, Cursor, GitHub Copilot, Windsurf, Gemini, Cline, AMP, Antigravity |
| Summary | Voice-faithful rewriting for messy drafts, notes, emails, posts, captions, docs, and reusable voice profiles |
| SKILL.md Preview | The public preview starts with the voice-preservation contract, then when-to-apply, defaults, intake, modes, gates, anti-generic rules, output, and validation |
| Generated By Skills.sh | Installs, GitHub stars, first seen, related skills, topic chips, and security audit status |

## Proof, Not Vibes

Youish's quality story is not "trust me, it feels good."

Youish has tests for the stuff bad AI writing usually breaks: facts, uncertainty, voice markers, exact quotes, identity markers, no-dash rules, exact word counts, requested output shape, reader actions, empty buzzword paste, and scorecard integrity.

This does not prove literary taste. It proves Youish keeps the constraints it claims to protect: facts, uncertainty, length, format, and anti-generic behavior.

| Promise | How It Is Tested |
|---|---|
| Keep the user's voice | Voice marker fixtures, profile contracts, and mutation tests that remove keeper phrases |
| Preserve facts and claims | Protected fact checks, required claims, forbidden assertions, numeric drift checks |
| Preserve uncertainty | Legal and technical cases that fail if "maybe" becomes false certainty |
| Preserve exact quotes and identity markers | Quote and identity contracts for punctuation, diacritics, pronouns, protected names, and source-specific phrasing |
| Refuse invented details | Unsupported detail markers, invented numbers, and unsupported entity detection |
| Avoid generic AI polish | Buzzword checks plus pattern tests for shiny but empty phrasing |
| Respect constraints | Exact word count, no-dash, format, wrapper, and paragraph-shape checks |
| Keep requested output shape | Format contracts for options, option diversity, greetings, signoffs, diagnosis-only responses, code fences, and line prefixes |
| Turn notes into usable text | Source-only thought-dump cases with artifact cleanup and reader-action checks |
| Keep scorecards honest | Transcript integrity checks recompute from raw output, reject unproven passing records, and distinguish partial suites from complete public scores |

The scorecard is intentionally boring: full-suite gates, stable failure codes, hashes, package checks, marketplace checks, and public-safe reporting. That is the point. Taste up front. Receipts in the back.

## The Useful Boring Stuff

The manuals live in the wiki so the README can stay focused on the why and the examples:

- [Install](https://github.com/RegionallyFamous/youish/wiki/Install)
- [Validation](https://github.com/RegionallyFamous/youish/wiki/Validation)
- [Youish Lab](https://github.com/RegionallyFamous/youish/wiki/Youish-Lab)
- [Voice Profiles](https://github.com/RegionallyFamous/youish/wiki/Voice-Profiles)
- [Privacy And Fixtures](https://github.com/RegionallyFamous/youish/wiki/Privacy-And-Fixtures)
- [Live Eval And Scorecards](https://github.com/RegionallyFamous/youish/wiki/Live-Eval-And-Scorecards)
- [Distribution](https://github.com/RegionallyFamous/youish/wiki/Distribution)
- [Release Checklist](https://github.com/RegionallyFamous/youish/wiki/Release-Checklist)

## Research Thread

The critique is worth taking seriously. Research on human-AI co-writing has found that writers care about preserving authentic voice, and other work has found AI suggestions can flatten writing toward dominant styles. Youish is a practical answer to that risk: keep the speed, reject the flattening.

- ["It was 80% me, 20% AI": Seeking Authenticity in Co-Writing with Large Language Models](https://arxiv.org/abs/2411.13032): authenticity depends on writers feeling the final piece still carries their choices.
- [AI Suggestions Homogenize Writing Toward Western Styles and Diminish Cultural Nuances](https://arxiv.org/abs/2409.11360): suggestion systems can flatten voice, so voice preservation has to be a first-class requirement.
- [How LLMs Distort Our Written Language](https://arxiv.org/abs/2603.18161): even edits framed as grammar help can alter meaning, neutrality, and perceived voice. Youish treats meaning and stance preservation as release-tested behavior, not a nice-to-have.
- [Voice Under Revision](https://arxiv.org/abs/2604.22142): even voice-preserving rewrite prompts can normalize personal narrative style, reduce situated markers, and make texts harder to match back to their source. Youish treats source markers as protected evidence, not decoration.
- [The Cost of Perfect English](https://arxiv.org/abs/2605.13055): grammar polishing can preserve propositions while erasing dialogic engagement, politeness, and sociopragmatic stance. Youish now tests culturally situated indirectness, honorifics, local idiom, and family framing.
- [What Keeps Agent Skills from Being Reusable? Evidence from 138K SKILL.md Files](https://openreview.net/pdf?id=n0AIlfxDU0): reusable skills need clear routing metadata, lean bodies, local procedural knowledge, validation, and low context waste. Youish keeps runtime guidance compact and pushes proof into scripts.
- [Digital.gov: Principles of plain language](https://digital.gov/guides/plain-language/principles): write for the audience, make the useful action clear, and cut clutter.
- [CPSC: Plain Language Principles](https://www.cpsc.gov/About-CPSC/Policies-Statements-and-Directives/plain-language-principles): plain writing is not dumbed-down writing. It is respect for the reader's time.

| Research Risk | Youish Behavior | Tested By |
|---|---|---|
| The writer stops feeling like the piece is theirs | Prefer light edits, protected voice markers, and tradeoff notes for high-authorship text | Voice marker fixtures, authorship boundary contracts |
| AI suggestions flatten culturally situated voice | Preserve dialect, code-switching, local idiom, indirectness, honorifics, family/community framing, and story-first structure unless the user asks otherwise | Cultural voice, identity, dialect, and boundary contracts |
| Options become the same template in different pants | Use meaningfully different strategies: cleaner, warmer, sharper, plainer, or more source-textured | Option-count, option-diversity, and output-shape contracts |
| Plain language turns into generic simplification | Put source-supported actors next to actions, keep uncertainty, and refuse invented facts | Reader-action, protected-fact, polarity, and numeric/entity drift checks |
| Skills waste context or hide behavior | Keep `SKILL.md` compact, move heavy checks to scripts, and publish scorecards | Progressive-disclosure validation and release-asset checks |

## About The Name

Youish means the output should still sound like the writer: cleaned up, sharpened, and more readable, but not flattened into generic AI paste.

## License

SPDX-License-Identifier: GPL-2.0-or-later.

Copyright (C) 2026 Regionally Famous.

Youish does not claim ownership of text you write, rewrite, or edit with it. Your drafts and outputs are yours.
