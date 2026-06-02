# Dittobot

Voice-faithful rewrites for people who want AI to sound like them, not like a committee laminated a thesaurus.

## Why This Exists

The answer is not "never use AI." The answer is "teach the tool your voice."

Generic AI writing is real. It can be padded, shiny, over-balanced, weirdly eager, allergic to risk, and full of phrases nobody says unless they are trapped in a webinar. But banning AI because bad AI writing exists is like banning spellcheck because someone once accepted the wrong suggestion. It treats the worst workflow as the only workflow.

If your AI writes badly, the answer is not to throw away the tool. The answer is to teach it taste.

Dittobot is built around that idea. It does not try to replace the writer. It tries to become the editor who knows what the writer sounds like, what they care about, what they would never say, and where their draft is hiding the good part under three blankets of filler.

That matters because AI writing tools can flatten expression. Research on human-AI co-writing has found that writers care about preserving authentic voice and that personalization can help when it supports the writer rather than replacing them. Other work has found AI suggestions can homogenize writing toward dominant styles and reduce cultural nuance. Dittobot is a practical answer to that risk: keep the speed, reject the flattening.

- ["It was 80% me, 20% AI": Seeking Authenticity in Co-Writing with Large Language Models](https://arxiv.org/abs/2411.13032)
- [AI Suggestions Homogenize Writing Toward Western Styles and Diminish Cultural Nuances](https://arxiv.org/abs/2409.11360)

## What Dittobot Does

Dittobot is a Codex skill for rewriting, tightening, diagnosing, and punching up prose while preserving the user's voice.

It:

- preserves voice, intent, facts, stance, rhythm, humor, and formality;
- tightens prose without sanding off the human parts;
- removes bland AI tells like generic openers, shiny abstractions, tidy triples, and dash dependency;
- avoids invented specifics, fake confidence, unsupported claims, and convenient made-up evidence;
- keeps private ledgers for constraints, claims/facts, and voice markers;
- uses fast editorial gates by default and expands into a 20-pass checklist for hard work;
- includes a deterministic 100-case fixture harness plus an optional live model smoke test.

Dittobot is not a ghostwriter. It is a voice-preserving editor. The goal is not "sounds professional." The goal is "sounds like you on a very good writing day."

## For Writers Worried About Voice Loss

Dittobot edits from the draft outward. It treats your wording as evidence, not debris.

It preserves odd phrasing when the odd phrasing carries intent. It keeps justified anger, tenderness, awkwardness, bluntness, and dry humor when those are part of the point. It treats smoothness as optional. Sometimes the best edit is one sentence left alone.

## What Dittobot Will Not Do

Dittobot will not:

- invent anecdotes, claims, citations, customers, numbers, or evidence;
- add "humanizing" typos or fake casualness;
- mimic a famous living writer;
- disguise unethical AI use;
- override legal, medical, financial, academic, or technical precision;
- turn every draft into a shiny professional announcement.

## Why Handwriting Everything Is The Wrong Fight

Handwriting every draft to prove you are not using AI is not virtue. It is a slow ritual of avoidance. If the real issue is "the tool does not write like me yet," then refusing to teach it your taste is, frankly, insane.

The real problem is not that AI can help with writing. The real problem is letting an untrained tool flatten your work into beige committee paste, then pretending the only options are "publish the paste" or "never use the tool." That is the wrong fight.

The sane move is to encode taste.

Teach the system what to preserve. Teach it which claims it cannot change. Teach it when to be blunt, when to be warm, when to leave the weird phrase alone because the weird phrase is the whole point. Teach it that a better sentence is not always a smoother sentence. Teach it that "less AI-sounding" does not mean adding typos, fake casualness, or random little messes. It means restoring intent.

Writing with AI should not mean outsourcing your voice. It should mean giving your voice a better editor.

## Install

Clone the repo:

```bash
git clone https://github.com/RegionallyFamous/dittobot.git
cd dittobot
```

Symlink it into your Codex skills folder:

```bash
mkdir -p ~/.codex/skills
if [ -e ~/.codex/skills/dittobot ]; then
  mv ~/.codex/skills/dittobot ~/.codex/skills/dittobot.backup.$(date +%s)
fi
ln -s "$(pwd)" ~/.codex/skills/dittobot
```

Symlinks are preferred because they prevent drift. If you need a copy, use `rsync` so updates replace stale files:

```bash
mkdir -p ~/.codex/skills/dittobot
rsync -a --delete ./ ~/.codex/skills/dittobot/
```

Then invoke it as `$dittobot`.

Check that your installed skill still matches the repo:

```bash
python3 scripts/check_install.py
```

## Use

```text
Use $dittobot to tighten this email but keep my voice.
```

```text
Use $dittobot to make this less AI-sounding. Do not add facts, do not make it more formal, and keep the dry little joke.
```

```text
Use $dittobot to punch this up, but preserve the weird phrasing where it works.
```

```text
Use $dittobot to clean this legal-ish note without changing the claims or making it sound more certain.
```

```text
Use $dittobot to rewrite this in exactly 40 words. No dashes. No notes.
```

```text
Use $dittobot to infer a voice profile from these samples. Do not rewrite yet.
```

```text
Use $dittobot to show what changed and why after the rewrite.
```

## Examples

Generic AI:

```text
In today's rapidly evolving landscape, our robust platform empowers teams to unlock seamless collaboration and drive meaningful impact.
```

Dittobot rewrite:

```text
We are updating the platform so teams can find the work, make a decision, and move on. The draft still needs specifics: what changed, who it helps, and what people can do now.
```

Why it works: it cuts the shiny abstractions, keeps the claim modest, and asks for real details instead of inventing them.

Voicey draft:

```text
This draft is not bad. It just walks into the room and immediately apologizes for existing.
```

Dittobot rewrite:

```text
The draft is not bad. It just walks into the room and immediately apologizes for existing. The idea works; the framing is getting in its way.
```

Why it works: it keeps the dry image because that is the writer's fingerprint.

Precision-sensitive draft:

```text
I think we probably need to send notice within 10 business days, but I am not counsel and the clause had weird carveouts.
```

Dittobot rewrite:

```text
I think we may need to send notice within 10 business days. I would not state that as definitive, though, because I am not counsel and the clause had unusual carveouts.
```

Why it works: it improves clarity without turning uncertainty into legal certainty.

## Validate

Run the deterministic fixture validator:

```bash
python3 scripts/validate_skill.py
python3 scripts/regression_100.py
python3 -m py_compile scripts/*.py
tmpdir="$(mktemp -d)"
mkdir -p "$tmpdir/codex-skills"
ln -s "$(pwd)" "$tmpdir/codex-skills/dittobot"
python3 scripts/check_install.py --install-dir "$tmpdir/codex-skills/dittobot"
```

Expected result:

```text
Skill repo validation passed.
VALIDATOR SELF-TESTS: PASS
TOTAL: 100/100 passed
Installed skill matches repo (symlink): ...
```

This validates the fixtures and the validator itself. It covers corporate slop, blunt Slack, legal precision, apologies, concision, odd voice, technical notes, unsupported claims, sensitive writing, and exact constraint handling.

Run the optional live model smoke test when you have an API key. This is not a benchmark or a guarantee of voice fidelity; it is a sampled smoke test against one model/API configuration and the deterministic string/marker validators. A pass means no obvious fixture failures in that sample.

```bash
export OPENAI_API_KEY="sk-..."
python3 scripts/live_eval.py --limit 10
python3 scripts/live_eval.py --case legal_precision_01 --model "$OPENAI_MODEL"
python3 scripts/live_eval.py --limit 20 --model gpt-5-mini --save-jsonl live-eval-results.local.jsonl
```

Use `--limit` or `--case` to keep cost bounded. If `OPENAI_API_KEY` is not set, the live eval skips cleanly. Saved JSONL transcripts are local debugging artifacts and must use `.local.jsonl` so they stay ignored.

Custom API URLs are blocked unless you pass `--allow-custom-api-url`; do that only for endpoints you trust with your bearer token and sample text.

## Privacy

Voice samples are personal. Dittobot does not require storing them in this repo. If you create local voice profiles or live-eval transcripts, keep them out of git unless every person represented in the samples is comfortable with publication.

## Contributing

Contributions should make the skill sharper without making it bloated. The skill body is intentionally lean so normal use stays fast and token-responsible.

Good changes usually do one of three things:

- preserve voice more reliably;
- prevent factual or tonal drift;
- add regression coverage for a real writing failure mode.

When adding regression cases, include:

- source text with the bad pattern;
- expected rewritten behavior;
- protected facts and voice markers;
- forbidden generic phrases or drift markers;
- a short reason the case belongs.

Before opening a PR, run:

```bash
python3 scripts/regression_100.py
```

If a change makes the skill more verbose without making it more reliable, it probably belongs in the test harness, not in `SKILL.md`.

## License

GPL-2.0-or-later.
