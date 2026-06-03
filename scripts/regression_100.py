#!/usr/bin/env python3
"""Youish regression harness.

Generates 100 bad-text rewrite cases and checks the rewritten outputs for
voice preservation, factual fidelity, concision, constraint handling, and
generic-AI prose markers.

This is a deterministic stress suite for the skill instructions. It does not
call an LLM; it keeps reusable acceptance checks out of SKILL.md so the skill
stays fast and token-responsible.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field, replace
from difflib import SequenceMatcher

from ledger import boundary_forbid_terms


GENERIC_MARKERS = [
    "in today's",
    "rapidly evolving",
    "transformative",
    "robust",
    "seamless",
    "empower",
    "unlock",
    "elevate",
    "drive impact",
    "at the heart",
    "ultimately",
    "it's important to note",
    "value for stakeholders",
    "game-changing",
    "innovative",
    "circle back",
    "alignment",
    "synergy",
    "best-in-class",
    "customer-centricity",
    "operational excellence",
    "meaningful impact",
    "full potential",
    "industry-leading",
    "backed by research",
    "research-backed",
    "next-generation",
    "ecosystem",
    "at scale",
    "streamline",
    "holistic",
    "data-driven",
    "future-proof",
    "end-to-end",
    "frictionless",
    "paradigm",
]

GENERIC_PATTERNS = [
    ("at its core", re.compile(r"\bat (?:its|the) core\b", re.IGNORECASE)),
    (
        "clear, concise, and actionable",
        re.compile(r"\bclear,\s*concise,\s*and\s*actionable\b", re.IGNORECASE),
    ),
    ("not just X but Y", re.compile(r"\bnot just\b.{0,80}\bbut\b", re.IGNORECASE)),
    ("designed to help", re.compile(r"\bdesigned to help\b", re.IGNORECASE)),
    (
        "move forward with confidence",
        re.compile(r"\bmove forward with confidence\b", re.IGNORECASE),
    ),
    (
        "focused, practical approach",
        re.compile(r"\bfocused,\s*practical approach\b", re.IGNORECASE),
    ),
    ("created user confusion", re.compile(r"\bcreated user confusion\b", re.IGNORECASE)),
]

INVENTED_DETAIL_MARKERS = [
    "millions",
    "thousands",
    "fortune 500",
    "revenue",
    "market share",
    "ai-powered",
    "patented",
    "award-winning",
    "guaranteed",
    "proven",
    "98%",
    "97%",
    "97 percent",
    "certified",
    "used by",
    "trusted by",
    "global brands",
    "40 percent",
    "in two weeks",
    "cut ticket volume",
    "reduced churn",
    "roi",
    "customers report",
]

NOTE_MARKERS = [
    r"(?im)^\*\*what changed\*\*",
    r"(?im)^\*\*note\*\*",
    r"(?im)^note:",
    r"(?im)^sure[:,]",
    r"(?im)^here'?s\b",
    r"(?im)^cleaner version:",
    r"(?im)^i (tightened|changed|kept|made)\b",
]

WRAPPER_MARKERS = [
    r"(?im)^\*\*rewrite\*\*",
    r"(?im)^rewrite:",
    r"(?im)^rewritten version:",
    r"(?im)^edited version:",
    r"(?im)^revised version:",
    r"(?im)^suggested rewrite:",
    r"(?im)^cleaned up:",
    r"(?im)^option \d+:",
]

CLARIFYING_MARKERS = [
    "can you clarify",
    "could you clarify",
    "please clarify",
    "what audience",
    "who is the audience",
    "could you share",
    "can you share",
    "what format",
    "what tone",
    "i need more context",
    "i need to know the audience",
    "before i can revise",
    "what are you using this for",
    "who should read this",
]

MODALITY_DRIFT_MARKERS = [
    "must",
    "definitely",
    "certainly",
    "guaranteed",
    "proven",
    "will happen",
]

TIMIDITY_HEDGE_MARKERS = [
    "maybe",
    "might",
    "probably",
    "could",
    "seems",
    "appears",
    "possibly",
    "may be worth",
    "worth considering",
    "if appropriate",
    "consider",
]

CAUSALITY_DRIFT_MARKERS = [
    "root cause",
    "caused by",
    "due to the database",
    "latency",
    "database",
    "user error",
]

WORD_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)?", re.UNICODE)


@dataclass(frozen=True)
class Case:
    id: str
    source: str
    rewrite: str
    must: tuple[str, ...]
    forbid: tuple[str, ...] = ()
    allow_note: bool = False
    allow_expand: bool = False
    exact_words: int | None = None
    max_ratio: float = 1.35
    no_dash: bool = False
    diagnosis: bool = False
    max_words: int | None = None
    min_question_marks: int = 0
    max_question_marks: int | None = None
    forbid_clarifying: bool = False
    forbid_wrappers: bool = False
    forbid_bullets: bool = False
    exact_paragraphs: int | None = None
    max_paragraphs: int | None = None
    starts_with: str | None = None
    ends_with: str | None = None
    exact_substrings: tuple[str, ...] = field(default_factory=tuple)
    preserve_quotes: tuple[str, ...] = field(default_factory=tuple)
    preserve_identity: tuple[str, ...] = field(default_factory=tuple)
    line_prefixes: tuple[str, ...] = field(default_factory=tuple)
    exact_option_count: int | None = None
    min_distinct_option_templates: int | None = None
    ordered_terms: tuple[str, ...] = field(default_factory=tuple)
    required_claims: tuple[str, ...] = field(default_factory=tuple)
    forbid_assertions: tuple[str, ...] = field(default_factory=tuple)
    forbid_artifacts: tuple[str, ...] = field(default_factory=tuple)
    preserve_uncertainty: bool = False
    allow_markdown_fence: bool = False
    prompt_mode: str = "explicit_rewrite"
    protected: tuple[str, ...] = field(default_factory=tuple)
    preserve_voice: tuple[str, ...] = field(default_factory=tuple)
    preserve_stance: tuple[str, ...] = field(default_factory=tuple)
    forbid_added_entities: bool = False
    allowed_entities: tuple[str, ...] = field(default_factory=tuple)
    boundaries: tuple[str, ...] = field(default_factory=tuple)
    reader_actions: tuple[str, ...] = field(default_factory=tuple)
    polarity_sensitive: tuple[str, ...] = field(default_factory=tuple)
    min_avg_sentence_words: float | None = None
    max_source_similarity: float | None = None
    strong_claims: tuple[str, ...] = field(default_factory=tuple)
    frontload_terms: tuple[str, ...] = field(default_factory=tuple)
    frontload_max_words: int | None = None
    forbid_added_hedges: bool = False
    voice_budget_terms: tuple[str, ...] = field(default_factory=tuple)
    max_voice_budget_terms: int | None = None
    best_voice_terms: tuple[str, ...] = field(default_factory=tuple)
    min_best_voice_terms: int | None = None


def words(text: str) -> list[str]:
    return WORD_PATTERN.findall(text)


def strip_quoted(text: str) -> str:
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r'"[^"]*"', "", text)
    text = re.sub(r"'[^']*'", "", text)
    text = re.sub(r"\u201c[^\u201d]*\u201d", "", text)
    return text


def normalized(text: str) -> str:
    return " ".join(words(text.lower()))


def contains_term(text: str, term: str) -> bool:
    haystack = words(text.lower())
    needle = words(term.lower())
    if not needle:
        return True
    width = len(needle)
    return any(haystack[index:index + width] == needle for index in range(len(haystack) - width + 1))


NEGATION_WORDS = {
    "avoid",
    "dont",
    "don't",
    "never",
    "no",
    "not",
    "skip",
    "stop",
    "without",
}


def polarity_is_negative(term: str) -> bool:
    return any(word in NEGATION_WORDS for word in words(term.lower()))


def has_negated_term(text: str, term: str) -> bool:
    if polarity_is_negative(term):
        return False
    haystack = words(text.lower())
    needle = words(term.lower())
    if not needle:
        return False
    width = len(needle)
    for index in range(len(haystack) - width + 1):
        if haystack[index:index + width] != needle:
            continue
        prefix = haystack[max(0, index - 3):index]
        if prefix and prefix[-1] in NEGATION_WORDS:
            return True
        if len(prefix) >= 2 and prefix[-2:] in (["do", "not"], ["did", "not"], ["does", "not"]):
            return True
    return False


def has_note(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in NOTE_MARKERS)


def has_wrapper(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in WRAPPER_MARKERS)


def count_markers(text: str, markers: list[str]) -> list[str]:
    return [marker for marker in markers if contains_term(text, marker)]


def term_index(text: str, term: str) -> int | None:
    haystack = words(text.lower())
    needle = words(term.lower())
    if not needle:
        return 0
    width = len(needle)
    for index in range(len(haystack) - width + 1):
        if haystack[index:index + width] == needle:
            return index
    return None


def paragraph_count(text: str) -> int:
    return len([part for part in re.split(r"\n\s*\n", text.strip()) if part.strip()])


def has_bullet_line(text: str) -> bool:
    return any(re.search(r"^\s*(?:[-*+]|\d+[.)])\s+", line) for line in text.splitlines())


OPTION_LABEL_RE = re.compile(
    r"^\s*(?:(?:option\s*)?\d+[.) :]|\d+\s*[-:)]|"
    r"(?:cleaner|warmer|sharper|firmer|softer|shorter|punchier|"
    r"plain|direct|casual|formal|gentler|bolder):)",
    re.IGNORECASE,
)
OPTION_PREFIX_RE = re.compile(
    r"^\s*((?:option\s*)?\d+[.) :]|\d+\s*[-:)]|"
    r"(?:cleaner|warmer|sharper|firmer|softer|shorter|punchier|"
    r"plain|direct|casual|formal|gentler|bolder):)\s*",
    re.IGNORECASE,
)


def option_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if OPTION_LABEL_RE.search(line))


def option_items(text: str) -> list[tuple[str, str]]:
    items: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = OPTION_PREFIX_RE.match(line)
        if match:
            if current is not None:
                items.append(current)
            label = match.group(1).strip().rstrip(":.)-")
            current = (label, [line[match.end():].strip()])
        elif current is not None:
            current[1].append(line)
    if current is not None:
        items.append(current)
    return [(label, " ".join(part for part in body if part).strip()) for label, body in items]


def option_template_signature(text: str) -> str:
    return " ".join(words(text.lower()))


def option_templates_are_similar(a: str, b: str) -> bool:
    left = option_template_signature(a)
    right = option_template_signature(b)
    if not left or not right:
        return True
    if left == right:
        return True
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    overlap = len(left_tokens & right_tokens) / max(len(left_tokens | right_tokens), 1)
    ratio = SequenceMatcher(None, left, right).ratio()
    return ratio >= 0.92 or (overlap >= 0.9 and abs(len(left.split()) - len(right.split())) <= 2)


def distinct_option_template_count(text: str) -> int:
    distinct: list[str] = []
    for _label, body in option_items(text):
        if not body:
            continue
        if not any(option_templates_are_similar(body, existing) for existing in distinct):
            distinct.append(body)
    return len(distinct)


def sentence_chunks(text: str) -> list[str]:
    return [
        chunk.strip()
        for chunk in re.split(r"(?<=[.!?])\s+|\n+", text.strip())
        if words(chunk)
    ]


def numeric_claims(text: str) -> set[str]:
    digit_claims = {
        match.lower()
        for match in re.findall(
            r"\$?\b\d+(?::\d+)?(?:[.,]\d+)*(?:\.\d+)?%?\b",
            text,
        )
    }
    word_claims = {match.group(0).lower() for match in NUMBER_UNIT_RE.finditer(text)}
    return digit_claims | word_claims


NUMBER_UNIT_RE = re.compile(
    r"\b(?:"
    r"zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    r"eighty|ninety"
    r")(?:[-\s](?:one|two|three|four|five|six|seven|eight|nine))?\s+"
    r"(?:percent|percentage points?|points?|days?|weeks?|months?|years?|"
    r"hours?|minutes?|dollars?|usd|customers?|users?|tickets?|rows?|"
    r"orders?|leads?|signups?|sales|revenue|churn)\b",
    re.IGNORECASE,
)


ENTITY_RE = re.compile(r"\b(?:[A-Z][A-Za-z0-9&]*(?:[.-][A-Za-z0-9&]+)*|[A-Z]{2,})\b")
ENTITY_STOPWORDS = {
    "AI",
    "API",
    "CSV",
    "DNS",
    "ID",
    "MSA",
    "QA",
    "ROI",
    "URL",
    "UI",
    "I",
    "If",
    "No",
    "Not",
    "Please",
    "Subject",
    "Thanks",
    "The",
    "This",
    "That",
    "Use",
    "We",
    "Legal",
    "Orders",
    "Small",
}

LOWERCASE_ENTITY_TERMS = {
    "aws",
    "github",
    "google",
    "hubspot",
    "mailchimp",
    "netlify",
    "openai",
    "paypal",
    "salesforce",
    "shopify",
    "slack",
    "stripe",
    "vercel",
    "wordpress",
    "zapier",
}


def added_entities(source: str, rewrite: str, allowed: tuple[str, ...] = ()) -> list[str]:
    source_entities = set(ENTITY_RE.findall(source))
    allowed_entities = source_entities | set(allowed) | ENTITY_STOPWORDS
    allowed_lower = {term.lower() for term in allowed}
    extras: list[str] = []
    for entity in ENTITY_RE.findall(rewrite):
        if entity not in allowed_entities and entity not in extras:
            extras.append(entity)
    for entity in sorted(LOWERCASE_ENTITY_TERMS):
        if (
            contains_term(rewrite, entity)
            and not contains_term(source, entity)
            and entity not in allowed_lower
            and entity not in [extra.lower() for extra in extras]
        ):
            extras.append(entity)
    return extras


def pad_to_exact_words(text: str, exact: int) -> str:
    """Append neutral words until text reaches an exact word count."""
    filler = "Please name owners clearly before launch today now"
    current = len(words(text))
    if current > exact:
        raise ValueError(f"text has {current} words, cannot shrink to {exact}: {text}")
    if current == exact:
        return text
    needed = exact - current
    return f"{text} {' '.join(words(filler)[:needed])}."


def remove_phrase(text: str, phrase: str) -> str | None:
    """Remove the first exact phrase match, ignoring case."""
    match = re.search(re.escape(phrase), text, flags=re.IGNORECASE)
    if not match:
        return None
    return (text[:match.start()] + text[match.end():]).strip()


def replace_phrase_all(text: str, phrase: str, replacement: str) -> str:
    """Replace every exact phrase match, ignoring case."""
    return re.sub(re.escape(phrase), replacement, text, flags=re.IGNORECASE)


def drop_uncertainty_words(text: str) -> str:
    text = re.sub(r"\bprobably\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bmay\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bmight\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bI think\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def validate(case: Case) -> list[str]:
    errors: list[str] = []
    unquoted = strip_quoted(case.rewrite)
    unquoted_lower = unquoted.lower()
    source_words = len(words(case.source))
    rewrite_words = len(words(case.rewrite))

    missing = [term for term in case.must if not contains_term(case.rewrite, term)]
    if missing:
        errors.append(f"missing required terms: {missing}")

    missing_voice = [
        term for term in case.preserve_voice if not contains_term(case.rewrite, term)
    ]
    if missing_voice:
        errors.append(f"lost voice markers: {missing_voice}")

    if case.max_voice_budget_terms is not None:
        voice_budget_hits = [
            term for term in case.voice_budget_terms if contains_term(case.rewrite, term)
        ]
        if len(voice_budget_hits) > case.max_voice_budget_terms:
            errors.append(
                "voice budget failed: kept "
                f"{len(voice_budget_hits)} markers, expected at most "
                f"{case.max_voice_budget_terms}: {voice_budget_hits}"
            )

    if case.min_best_voice_terms is not None:
        best_voice_hits = [
            term for term in case.best_voice_terms if contains_term(case.rewrite, term)
        ]
        if len(best_voice_hits) < case.min_best_voice_terms:
            errors.append(
                "best voice failed: kept "
                f"{len(best_voice_hits)} preferred markers, expected at least "
                f"{case.min_best_voice_terms}: {best_voice_hits}"
            )

    missing_stance = [
        term for term in case.preserve_stance if not contains_term(case.rewrite, term)
    ]
    if missing_stance:
        errors.append(f"lost stance markers: {missing_stance}")

    missing_protected = [
        term for term in case.protected if not contains_term(case.rewrite, term)
    ]
    if missing_protected:
        errors.append(f"lost protected facts: {missing_protected}")

    missing_exact = [
        snippet for snippet in case.exact_substrings if snippet not in case.rewrite
    ]
    if missing_exact:
        errors.append(f"lost exact substrings: {missing_exact}")

    missing_quotes = [
        snippet for snippet in case.preserve_quotes if snippet not in case.rewrite
    ]
    if missing_quotes:
        errors.append(f"lost preserved quotes: {missing_quotes}")

    missing_identity = [
        snippet for snippet in case.preserve_identity if snippet not in case.rewrite
    ]
    if missing_identity:
        errors.append(f"lost identity markers: {missing_identity}")

    if case.line_prefixes:
        lines = [line.rstrip() for line in case.rewrite.splitlines()]
        missing_prefixes = [
            prefix for prefix in case.line_prefixes
            if not any(line.startswith(prefix) for line in lines)
        ]
        if missing_prefixes:
            errors.append(f"lost required line prefixes: {missing_prefixes}")

    if case.exact_option_count is not None:
        actual_options = option_count(case.rewrite)
        if actual_options != case.exact_option_count:
            errors.append(
                "exact option count failed: expected "
                f"{case.exact_option_count}, got {actual_options}"
            )
    if case.min_distinct_option_templates is not None:
        actual_templates = distinct_option_template_count(case.rewrite)
        if actual_templates < case.min_distinct_option_templates:
            errors.append(
                "option diversity failed: expected at least "
                f"{case.min_distinct_option_templates} distinct option templates, "
                f"got {actual_templates}"
            )

    forbidden = []
    for term in (*case.forbid, *boundary_forbid_terms(list(case.boundaries))):
        if contains_term(unquoted, term) and term not in forbidden:
            forbidden.append(term)
    if forbidden:
        errors.append(f"forbidden terms appeared: {forbidden}")

    missing_claims = [
        claim for claim in case.required_claims if not contains_term(case.rewrite, claim)
    ]
    if missing_claims:
        errors.append(f"missing required claims: {missing_claims}")

    missing_strong_claims = [
        claim for claim in case.strong_claims if not contains_term(case.rewrite, claim)
    ]
    if missing_strong_claims:
        errors.append(
            f"missing strongest source-supported claims: {missing_strong_claims}"
        )

    if case.frontload_terms and case.frontload_max_words is not None:
        frontload_text = " ".join(words(case.rewrite)[:case.frontload_max_words])
        missing_frontload = [
            term for term in case.frontload_terms if not contains_term(frontload_text, term)
        ]
        if missing_frontload:
            errors.append(
                "buried thesis: expected frontload terms in first "
                f"{case.frontload_max_words} words: {missing_frontload}"
            )

    missing_reader_actions = [
        action for action in case.reader_actions if not contains_term(case.rewrite, action)
    ]
    if missing_reader_actions:
        errors.append(f"missing reader actions: {missing_reader_actions}")

    polarity_terms = tuple(
        dict.fromkeys((*case.polarity_sensitive, *case.required_claims, *case.reader_actions))
    )
    negated_terms = [
        term for term in polarity_terms
        if contains_term(case.rewrite, term) and has_negated_term(case.rewrite, term)
    ]
    if negated_terms:
        errors.append(f"polarity drift: negated required phrases: {negated_terms}")

    forbidden_assertions = [
        claim for claim in case.forbid_assertions if contains_term(unquoted, claim)
    ]
    if forbidden_assertions:
        errors.append(f"forbidden assertions appeared: {forbidden_assertions}")

    forbidden_artifacts = [
        term for term in case.forbid_artifacts
        if words(term) and contains_term(case.rewrite, term)
    ]
    forbidden_artifacts.extend(
        term for term in case.forbid_artifacts
        if not words(term) and term in case.rewrite
    )
    if forbidden_artifacts:
        errors.append(f"note artifacts appeared: {forbidden_artifacts}")

    if case.ordered_terms:
        positions = [(term, term_index(case.rewrite, term)) for term in case.ordered_terms]
        missing_ordered = [term for term, index in positions if index is None]
        if missing_ordered:
            errors.append(f"missing ordered terms: {missing_ordered}")
        present_positions = [index for _, index in positions if index is not None]
        if present_positions != sorted(present_positions):
            errors.append(f"ordered terms out of order: {case.ordered_terms}")

    generic = [
        marker
        for marker in count_markers(case.rewrite, GENERIC_MARKERS)
        if not any(marker in voice.lower() for voice in case.preserve_voice)
    ]
    generic.extend(
        label
        for label, pattern in GENERIC_PATTERNS
        if pattern.search(case.rewrite)
        and not pattern.search(case.source)
        and not any(pattern.search(voice) for voice in case.preserve_voice)
    )
    if generic:
        errors.append(f"generic markers appeared: {generic}")

    invented = count_markers(case.rewrite, INVENTED_DETAIL_MARKERS)
    if invented:
        errors.append(f"invented-detail markers appeared: {invented}")

    source_numbers = numeric_claims(case.source)
    rewrite_numbers = numeric_claims(case.rewrite)
    invented_numbers = sorted(rewrite_numbers - source_numbers)
    if invented_numbers:
        errors.append(f"invented numeric claims appeared: {invented_numbers}")

    if case.forbid_added_entities:
        extras = added_entities(case.source, case.rewrite, case.allowed_entities)
        if extras:
            errors.append(f"unsupported entities appeared: {extras}")

    if any(contains_term(case.source, term) for term in ("maybe", "may", "might", "probably")):
        drift = [
            term
            for term in MODALITY_DRIFT_MARKERS
            if contains_term(unquoted, term) and not contains_term(case.source, term)
        ]
        if drift:
            errors.append(f"modality drift markers appeared: {drift}")

    if case.preserve_uncertainty:
        uncertainty_markers = (
            "maybe",
            "may",
            "might",
            "probably",
            "not sure",
            "not definitive",
            "not state that as definitive",
            "I think",
        )
        if not any(contains_term(case.rewrite, marker) for marker in uncertainty_markers):
            errors.append("lost uncertainty marker")

    if case.forbid_added_hedges:
        unsupported_hedges = [
            marker
            for marker in TIMIDITY_HEDGE_MARKERS
            if contains_term(unquoted, marker) and not contains_term(case.source, marker)
        ]
        if unsupported_hedges:
            errors.append(
                f"timidity drift: unsupported hedge markers appeared: {unsupported_hedges}"
            )

    causal_drift = [
        term
        for term in CAUSALITY_DRIFT_MARKERS
        if contains_term(unquoted, term) and not contains_term(case.source, term)
    ]
    if causal_drift:
        errors.append(f"causality drift markers appeared: {causal_drift}")

    if has_note(case.rewrite) and not case.allow_note:
        errors.append("unexpected note/rationale")

    if has_wrapper(case.rewrite) and case.forbid_wrappers:
        errors.append("unexpected rewrite wrapper")

    if case.forbid_clarifying:
        clarifying = [
            marker for marker in CLARIFYING_MARKERS if contains_term(case.rewrite, marker)
        ]
        if clarifying:
            errors.append(f"unexpected clarifying question: {clarifying}")

    if "```" in case.rewrite and not case.allow_markdown_fence:
        errors.append("unexpected markdown fence")

    if case.no_dash and any(mark in case.rewrite for mark in ("-", "\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212")):
        errors.append("dash constraint violated")

    if case.min_question_marks and case.rewrite.count("?") < case.min_question_marks:
        errors.append(
            f"question mark count failed: expected at least {case.min_question_marks}, "
            f"got {case.rewrite.count('?')}"
        )
    if case.max_question_marks is not None and case.rewrite.count("?") > case.max_question_marks:
        errors.append(
            f"question mark count failed: expected at most {case.max_question_marks}, "
            f"got {case.rewrite.count('?')}"
        )

    if case.forbid_bullets and has_bullet_line(case.rewrite):
        errors.append("unexpected bullet list")

    if case.min_avg_sentence_words is not None:
        chunks = sentence_chunks(case.rewrite)
        average = (rewrite_words / len(chunks)) if chunks else 0
        if average < case.min_avg_sentence_words:
            errors.append(
                "sentence quality failed: average words per sentence "
                f"{average:.1f}, expected at least {case.min_avg_sentence_words:.1f}"
            )

    if case.max_source_similarity is not None:
        source_signature = normalized(case.source)
        rewrite_signature = normalized(case.rewrite)
        similarity = SequenceMatcher(None, source_signature, rewrite_signature).ratio()
        if similarity > case.max_source_similarity:
            errors.append(
                "editorial lift failed: source similarity "
                f"{similarity:.2f}, expected at most {case.max_source_similarity:.2f}"
            )

    paragraphs = paragraph_count(case.rewrite)
    if case.exact_paragraphs is not None and paragraphs != case.exact_paragraphs:
        errors.append(
            f"paragraph count failed: expected {case.exact_paragraphs}, got {paragraphs}"
        )
    if case.max_paragraphs is not None and paragraphs > case.max_paragraphs:
        errors.append(
            f"paragraph count failed: expected at most {case.max_paragraphs}, got {paragraphs}"
        )

    if case.starts_with and not case.rewrite.lstrip().lower().startswith(case.starts_with.lower()):
        errors.append(f"opening failed: expected to start with {case.starts_with!r}")
    if case.ends_with and not case.rewrite.rstrip().lower().endswith(case.ends_with.lower()):
        errors.append(f"ending failed: expected to end with {case.ends_with!r}")

    if case.exact_words is not None and rewrite_words != case.exact_words:
        errors.append(
            f"exact word count failed: expected {case.exact_words}, got {rewrite_words}"
        )
    elif case.max_words is not None and rewrite_words > case.max_words:
        errors.append(
            f"max word count failed: expected at most {case.max_words}, got {rewrite_words}"
        )
    elif not case.allow_expand:
        allowed = max(source_words + 12, int(source_words * case.max_ratio))
        if rewrite_words > allowed:
            errors.append(
                f"too long: source {source_words}, rewrite {rewrite_words}, allowed {allowed}"
            )

    if case.diagnosis and re.search(r"(?im)^\*\*rewrite\*\*", case.rewrite):
        errors.append("diagnosis case produced rewrite heading")

    return errors


def make_cases() -> list[Case]:
    cases: list[Case] = []

    product_subjects = [
        ("platform", "teams", "customers"),
        ("dashboard", "support leads", "users"),
        ("workflow", "editors", "contributors"),
        ("reporting tool", "managers", "operators"),
        ("checkout flow", "store owners", "shoppers"),
        ("publishing system", "writers", "readers"),
        ("admin screen", "site owners", "clients"),
        ("importer", "migration teams", "customers"),
        ("review queue", "moderators", "community members"),
        ("analytics page", "product teams", "customers"),
    ]
    for idx, (thing, audience, reader) in enumerate(product_subjects[:8], 1):
        source = (
            "In today's rapidly evolving landscape, we are thrilled to announce a "
            f"transformative new chapter for our {thing}. This robust solution "
            f"empowers {audience} to unlock seamless collaboration, drive meaningful "
            "impact, and elevate outcomes for stakeholders."
        )
        rewrite = (
            f"We are updating the {thing}.\n\n"
            f"The goal is simple: make it more useful for {audience} and clearer "
            f"for the {reader} who rely on it. The original draft still needs real "
            "specifics: what changed, who it helps, and what people can do now."
        )
        cases.append(
            Case(
                id=f"corporate_specifics_guard_{idx:02d}",
                source=source,
                rewrite=rewrite,
                must=(thing, audience, "real specifics", "what changed"),
                allow_expand=True,
            )
        )

    slack_items = [
        ("screenshots", "legal", "cursed vibes spreadsheet"),
        ("owner", "deadline", "fog machine"),
        ("pricing copy", "approval", "mystery soup"),
        ("QA list", "release note", "haunted checklist"),
        ("design asset", "PM signoff", "vague weather report"),
        ("demo video", "security review", "ritual of confusion"),
        ("migration plan", "support docs", "process fog"),
        ("copy deck", "launch date", "meeting oatmeal"),
        ("API note", "test account", "phantom blocker"),
        ("redirect list", "DNS change", "vibes spreadsheet"),
    ]
    for idx, (a, b, phrase) in enumerate(slack_items[:8], 1):
        source = (
            f"ok so can we stop saying this is blocked unless we say what blocked "
            f"means?? if it's {a} say {a}. if it's {b} say {b}. otherwise this is "
            f"just the {phrase} and i cannot fix a cloud."
        )
        rewrite = (
            "Can we stop saying this is blocked unless we name the blocker?\n\n"
            f"If it is {a}, say {a}. If it is {b}, say {b}. I can help, but I "
            f"need a real list, not the {phrase}."
        )
        cases.append(
            Case(
                id=f"slack_blunt_voice_{idx:02d}",
                source=source,
                rewrite=rewrite,
                must=(a, b, phrase),
                preserve_voice=(phrase,),
            )
        )

    legal_items = [
        ("10 business days", "Acme", "contract"),
        ("five calendar days", "BetaCo", "addendum"),
        ("30 days", "Northwind", "MSA"),
        ("48 hours", "Contoso", "security clause"),
        ("seven business days", "Globex", "renewal language"),
        ("15 days", "Initech", "order form"),
        ("two weeks", "Umbrella", "DPA"),
        ("90 days", "Hooli", "termination clause"),
        ("three business days", "Stark", "support terms"),
        ("60 days", "Wayne", "notice provision"),
    ]
    for idx, (deadline, company, doc) in enumerate(legal_items[:8], 1):
        source = (
            f"Based on the {doc} we looked at Friday, I think we probably have to "
            f"send written notice within {deadline}, but I do not want to state "
            f"that like it is definitely true because I am not counsel and there "
            f"were weird carveouts. We should ask legal before replying to {company}."
        )
        rewrite = (
            f"Based on the {doc} we reviewed Friday, I think we may need to send "
            f"written notice within {deadline}. I would not state that as definitive, "
            f"because I am not counsel and there were unusual carveouts. We should "
            f"ask Legal to confirm before replying to {company}."
        )
        cases.append(
            Case(
                id=f"legal_precision_{idx:02d}",
                source=source,
                rewrite=rewrite,
                must=(deadline, company, "may need", "not counsel", "Legal"),
                protected=(deadline, company, doc),
                required_claims=("may need", "not counsel"),
                preserve_uncertainty=True,
                forbid=(
                    "must send",
                    "required to send",
                    "definitely true",
                    "do not ask Legal",
                    "skip Legal",
                    "reply without Legal",
                ),
            )
        )

    apology_items = [
        ("came in too hot", "weird meeting combat thing"),
        ("got sharper than I meant to", "calendar cage match"),
        ("made it harder", "meeting spiral"),
        ("pushed too hard", "thread duel"),
        ("talked over you", "process wrestling"),
        ("was more blunt than useful", "status-page boxing match"),
        ("jumped in too fast", "decision fog"),
        ("made the room tense", "strategy thunderstorm"),
        ("missed your point", "comment-thread maze"),
        ("turned defensive", "alignment theater"),
    ]
    for idx, (admission, phrase) in enumerate(apology_items[:8], 1):
        source = (
            f"Hey, I was thinking about yesterday and I think I {admission}. I still "
            "disagree with the decision, but I do not like how I made the conversation "
            f"harder. Sorry for that. I want to reset instead of doing the {phrase}."
        )
        rewrite = (
            f"Hey, I have been thinking about yesterday. I {admission}.\n\n"
            "I still disagree with the decision, but I do not like how I made the "
            f"conversation harder. I am sorry for that. I would like to reset instead "
            f"of doing the {phrase}."
        )
        cases.append(
            Case(
                id=f"apology_light_touch_{idx:02d}",
                source=source,
                rewrite=rewrite,
                must=(admission, phrase, "still disagree"),
                forbid=(
                    "deeply regret",
                    "sincerely apologize",
                    "harm caused",
                    "understand the impact",
                    "holding space",
                    "moving forward together",
                    "deeply sorry for the harm",
                ),
                preserve_voice=(phrase,),
                preserve_stance=("still disagree",),
            )
        )

    concise_items = [
        ("review meeting", "Thursday", "Friday"),
        ("planning call", "Tuesday", "Wednesday"),
        ("launch review", "Monday", "Thursday"),
        ("budget discussion", "3:00", "4:30"),
        ("design critique", "morning", "afternoon"),
        ("partner sync", "June 4", "June 5"),
        ("retro", "this week", "next week"),
        ("content review", "noon", "2:00"),
        ("handoff", "today", "tomorrow"),
        ("demo", "Friday", "Monday"),
    ]
    for idx, (meeting, old, new) in enumerate(concise_items[:8], 1):
        source = (
            f"I wanted to reach out because I was wondering if maybe there is a "
            f"possibility that we could potentially move the {meeting} from {old} "
            f"to {new}, because I am still trying to pull things together and I do "
            "not want to waste everyone's time with something that is not ready."
        )
        rewrite = (
            f"Could we move the {meeting} from {old} to {new}? I am still pulling "
            "things together, and I do not want to waste everyone's time with a draft "
            "that is not ready."
        )
        cases.append(
            Case(
                id=f"concision_{idx:02d}",
                source=source,
                rewrite=rewrite,
                must=(meeting, old, new, "not ready"),
                protected=(meeting, old, new),
                forbid=("potentially", "possibility", "reach out"),
                strong_claims=(f"Could we move the {meeting}",),
                frontload_terms=("Could we move",),
                frontload_max_words=4,
                forbid_added_hedges=True,
                max_source_similarity=0.72,
            )
        )

    odd_voice_items = [
        ("beige rectangle", "seven nervous staplers"),
        ("wet cardboard", "three anxious binders"),
        ("committee pudding", "five haunted spreadsheets"),
        ("waiting-room pamphlet", "two nervous clipboards"),
        ("cold oatmeal", "a boardroom of staplers"),
        ("software beige", "six cautious calendars"),
        ("sleepy rectangle", "four frightened folders"),
        ("room-temperature soup", "three legal pads in a trench coat"),
        ("printer paper fog", "eight worried bullet points"),
        ("conference-room static", "a choir of soft approvals"),
    ]
    for idx, (image, phrase) in enumerate(odd_voice_items[:8], 1):
        source = (
            f"I keep trying to write this announcement and it keeps turning into a "
            f"{image}. The actual news is good. People will care. But every draft "
            f"sounds like it was assembled by {phrase}."
        )
        rewrite = (
            f"I keep trying to write this announcement, and it keeps turning into a "
            f"{image}. The news is actually good. People will care. But every draft "
            f"sounds like it was assembled by {phrase}."
        )
        cases.append(
            Case(
                id=f"odd_voice_{idx:02d}",
                source=source,
                rewrite=rewrite,
                must=("People will care", image, phrase),
                preserve_voice=(image, phrase),
                forbid=("stakeholders", "brand voice", "exciting update"),
            )
        )

    tech_items = [
        ("cache", "invalidation event", "previous response", "API accepted it"),
        ("webhook", "retry event", "old status", "job completed"),
        ("search", "index update", "stale result", "record saved"),
        ("permissions", "role refresh", "old access state", "policy updated"),
        ("upload", "processing event", "old thumbnail", "file stored"),
        ("checkout", "price recalculation", "old total", "payment accepted"),
        ("import", "sync event", "old row count", "records imported"),
        ("preview", "render event", "old preview", "draft saved"),
        ("notification", "delivery event", "old badge", "message sent"),
        ("export", "completion event", "old progress state", "file generated"),
    ]
    for idx, (label, event, stale, accepted) in enumerate(tech_items[:8], 1):
        source = (
            f"The {label} thing is probably not a {label} thing exactly. It is more "
            f"like the {event} is happening, but the UI keeps holding onto the {stale} "
            f"until the next interaction, so people think it failed even when the "
            f"system already says {accepted}."
        )
        rewrite = (
            f"This probably is not a {label} issue exactly. The {event} is firing, "
            f"but the UI keeps showing the {stale} until the next interaction. That "
            f"makes people think it failed, even though the system says {accepted}."
        )
        cases.append(
            Case(
                id=f"technical_fidelity_{idx:02d}",
                source=source,
                rewrite=rewrite,
                must=(event, stale, accepted),
                protected=(event, stale, accepted),
                required_claims=("probably is not",),
                preserve_uncertainty=True,
                forbid=("root cause", "latency", "database"),
            )
        )

    academic_items = [
        ("remote work", "two survey quotes", "one internal chart"),
        ("four-day weeks", "three interview notes", "one team metric"),
        ("AI tooling", "one pilot survey", "two support tickets"),
        ("new onboarding", "five comments", "one completion chart"),
        ("async meetings", "two manager quotes", "one calendar report"),
        ("pricing change", "three customer emails", "one churn chart"),
        ("documentation", "four Slack comments", "one search report"),
        ("office hours", "two anecdotes", "one attendance sheet"),
        ("design system", "three designer notes", "one bug report"),
        ("support macros", "two agent comments", "one response-time chart"),
    ]
    for idx, (claim, evidence_a, evidence_b) in enumerate(academic_items[:8], 1):
        source = (
            f"This proves {claim} is better for everyone because productivity obviously "
            f"goes up, although I only have {evidence_a} and {evidence_b}, so maybe "
            "that is too spicy."
        )
        rewrite = (
            f"This suggests {claim} may be working well in this context, but the "
            f"evidence is limited: {evidence_a} and {evidence_b}. I would not frame "
            "it as proof or as a universal claim. That is too big for the data we have."
        )
        cases.append(
            Case(
                id=f"unsupported_claim_{idx:02d}",
                source=source,
                rewrite=rewrite,
                must=(claim, evidence_a, evidence_b, "too big", "data"),
                forbid=("proves", "better for everyone", "obviously goes up"),
                allow_expand=True,
            )
        )

    grief_items = [
        ("miss him", "weirdly normal", "mattered a lot"),
        ("miss her", "quiet and loud", "changed the room"),
        ("miss them", "ordinary and impossible", "meant a lot"),
        ("keep reaching for my phone", "normal and not normal", "was loved"),
        ("do not know what to say", "small and huge", "was here"),
        ("feel a little blank", "too normal", "made things better"),
        ("keep expecting a text", "paused and moving", "was part of us"),
        ("am not ready for speeches", "soft and strange", "mattered"),
        ("feel out of words", "same and different", "was important"),
        ("miss his laugh", "still and busy", "was deeply loved"),
    ]
    for idx, (feeling, texture, meaning) in enumerate(grief_items[:8], 1):
        source = (
            f"I do not really know what to say except that I {feeling}. Everything "
            f"feels {texture} at the same time. I do not want to make a grand statement. "
            f"I just wanted people to know that he {meaning}."
        )
        rewrite = (
            f"I do not really know what to say except that I {feeling}. Everything "
            f"feels {texture} at the same time.\n\nI do not want to make a grand "
            f"statement. I just wanted people to know that he {meaning}."
        )
        cases.append(
            Case(
                id=f"sensitive_light_touch_{idx:02d}",
                source=source,
                rewrite=rewrite,
                must=(feeling, texture, meaning, "grand statement"),
                forbid=("legacy", "cherished", "profound loss"),
            )
        )

    constraint_items = [
        ("30", 30, "screenshots, legal note approval, and pricing copy"),
        ("28", 28, "owner, deadline, and launch note"),
        ("26", 26, "QA list, demo link, and support copy"),
        ("24", 24, "redirects, DNS owner, and timing"),
        ("22", 22, "screenshots and final copy"),
        ("20", 20, "approval and pricing"),
        ("18", 18, "owner and deadline"),
        ("16", 16, "screenshots only"),
        ("14", 14, "legal approval"),
        ("12", 12, "final copy"),
    ]
    constraint_rewrites = {
        30: "The launch is not blocked by content. It is blocked by three missing items: screenshots, legal note approval, and pricing copy. I can help once owners are clearly named.",
        28: "The launch is blocked by three missing items: owner, deadline, and launch note. I can help once someone names who owns each one.",
        26: "This is blocked by the QA list, demo link, and support copy. I can help once each item has a named owner.",
        24: "This is blocked by redirects, DNS owner, and timing. Name the owners and I can help move it forward.",
        22: "This is blocked by screenshots and final copy. I can help once we know who owns both.",
        20: "This is blocked by approval and pricing. Name the owners and I can help.",
        18: "This is blocked by owner and deadline. Name both and I can help.",
        16: "This is blocked by screenshots only. Send those and I can help.",
        14: "This is blocked by legal approval. Confirm that and I can help.",
        12: "This is blocked by final copy. Send it over.",
    }
    for idx, (_, exact, items) in enumerate(constraint_items[:8], 1):
        source = (
            "Rewrite this with no dashes and exactly the requested word count: "
            f"the launch is blocked by {items}, but everyone keeps saying content."
        )
        rewrite = pad_to_exact_words(constraint_rewrites[exact], exact)
        cases.append(
            Case(
                id=f"constraint_exact_words_{idx:02d}",
                source=source,
                rewrite=rewrite,
                must=tuple(
                    part.strip().removeprefix("and ").strip()
                    for part in items.split(",")
                ),
                exact_words=exact,
                no_dash=True,
                forbid=("stakeholders", "alignment"),
            )
        )

    edge_cases = [
        Case(
            id="format_subject_question_01",
            source=(
                "Subject: Quick question about Friday\n\n"
                "Hey Maya, can you look at the copy before noon? It mostly works, "
                "but the second paragraph is doing that fog machine thing again."
            ),
            rewrite=(
                "Subject: Quick question about Friday\n\n"
                "Hey Maya, can you look at the copy before noon? It mostly works, "
                "but the second paragraph is doing the fog machine thing again."
            ),
            must=("Friday", "Maya", "before noon", "fog machine"),
            exact_substrings=("Subject: Quick question about Friday",),
            min_question_marks=1,
            preserve_voice=("fog machine",),
        ),
        Case(
            id="format_bullets_01",
            source=(
                "Can you make this cleaner but keep the bullets?\n"
                "- Sam owns screenshots\n"
                "- Priya owns legal\n"
                "- I own the weird little launch note"
            ),
            rewrite=(
                "- Sam owns screenshots.\n"
                "- Priya owns legal.\n"
                "- I own the weird little launch note."
            ),
            must=("Sam", "screenshots", "Priya", "legal", "weird little launch note"),
            line_prefixes=("- Sam", "- Priya", "- I"),
            preserve_voice=("weird little launch note",),
        ),
        Case(
            id="quote_preservation_01",
            source=(
                'Please clean this up but do not change the quote: Dana said, '
                '"Ship the tiny fix first." I think that is the whole plan, honestly.'
            ),
            rewrite='Dana said, "Ship the tiny fix first." I think that is the whole plan.',
            must=("Dana", "whole plan"),
            exact_substrings=('"Ship the tiny fix first."',),
        ),
        Case(
            id="diagnosis_only_01",
            source=(
                "Diagnose only, do not rewrite: This paragraph starts with strategy, "
                "wanders into a pricing apology, then ends like a calendar invite got scared."
            ),
            rewrite=(
                "The paragraph has three problems: it changes topics, buries the pricing "
                "point, and ends weaker than it starts."
            ),
            must=("changes topics", "pricing", "ends weaker"),
            forbid=("rewrite",),
            diagnosis=True,
        ),
        Case(
            id="no_apology_injection_01",
            source=(
                "Make this firmer: I can send the deck Friday. I cannot promise Wednesday "
                "because the numbers are not final."
            ),
            rewrite=(
                "I can send the deck Friday. I cannot promise Wednesday because the "
                "numbers are not final."
            ),
            must=("Friday", "Wednesday", "numbers are not final"),
            forbid=("sorry", "apologize", "happy to"),
            protected=("Friday", "Wednesday"),
            preserve_stance=("cannot promise Wednesday",),
        ),
        Case(
            id="uncertainty_preservation_01",
            source=(
                "This might be a permissions issue, but I only know the editor role fails "
                "and admin works."
            ),
            rewrite=(
                "This might be a permissions issue. So far, I only know the editor role "
                "fails and admin works."
            ),
            must=("might be", "editor role", "admin works"),
            protected=("editor role", "admin works"),
            forbid=("must be", "root cause"),
        ),
        Case(
            id="format_greeting_signoff_01",
            source=(
                "Hey Jordan,\n\n"
                "This is too long, but the point is: we need the final numbers before we "
                "publish. Otherwise we are guessing in public, which sounds like a sport "
                "I do not want to play.\n\n"
                "Thanks,\nNick"
            ),
            rewrite=(
                "Hey Jordan,\n\n"
                "We need the final numbers before we publish. Otherwise we are guessing "
                "in public, which sounds like a sport I do not want to play.\n\n"
                "Thanks,\nNick"
            ),
            must=("Hey Jordan", "final numbers", "guessing in public", "Thanks", "Nick"),
            exact_substrings=("Hey Jordan,", "Thanks,\nNick"),
            preserve_voice=("sport I do not want to play",),
        ),
        Case(
            id="not_cheerier_01",
            source=(
                "Make this clearer, not cheerier: The migration is delayed because two "
                "imports failed. We have a fix, but I want one more test before I tell "
                "people it is solved."
            ),
            rewrite=(
                "The migration is delayed because two imports failed. We have a fix, "
                "but I want one more test before saying it is solved."
            ),
            must=("migration is delayed", "two imports failed", "one more test"),
            forbid=("excited", "great news", "thrilled"),
            protected=("two imports failed",),
            preserve_stance=("delayed", "one more test"),
        ),
        Case(
            id="max_words_01",
            source=(
                "Rewrite under 18 words: I am waiting on the final screenshot before I "
                "can finish the launch note."
            ),
            rewrite="I need the final screenshot before I can finish the launch note.",
            must=("final screenshot", "launch note"),
            max_words=18,
        ),
        Case(
            id="return_only_no_wrapper_01",
            source=(
                "Return only the text: The policy note is fine, but it keeps saying "
                "scalable in a way that makes me want to stare at a wall."
            ),
            rewrite=(
                "The policy note is fine, but it keeps saying scalable in a way that "
                "makes me want to stare at a wall."
            ),
            must=("policy note", "scalable", "stare at a wall"),
            preserve_voice=("stare at a wall",),
            forbid=("rewritten",),
            forbid_wrappers=True,
        ),
    ]
    cases.extend(edge_cases)

    thought_dump_cases = [
        Case(
            id="thought_dump_launch_note_01",
            source=(
                "ok the launch note is somehow both too long and says nothing. what i "
                "actually mean is we fixed the importer bug, people can retry failed "
                "rows now, and i need it to sound calm but not like a haunted changelog"
            ),
            rewrite=(
                "We fixed the importer bug. People can retry failed rows now, so the "
                "launch note should be calm and useful, not a haunted changelog."
            ),
            must=("importer bug", "retry failed rows", "calm", "haunted changelog"),
            protected=("importer bug", "retry failed rows"),
            preserve_voice=("haunted changelog",),
            forbid=("somehow", "what I actually mean", "robust", "seamless"),
            required_claims=("fixed the importer bug", "retry failed rows"),
            reader_actions=("retry failed rows",),
            forbid_assertions=("did not fix the importer bug", "cannot retry failed rows"),
            ordered_terms=("importer bug", "retry failed rows", "launch note"),
            forbid_artifacts=("ok", "what i actually mean"),
            max_question_marks=0,
            forbid_clarifying=True,
            forbid_wrappers=True,
            max_paragraphs=1,
            starts_with="We fixed",
            voice_budget_terms=("too long", "says nothing", "haunted changelog"),
            max_voice_budget_terms=1,
            prompt_mode="source_only",
        ),
        Case(
            id="thought_dump_email_boundary_02",
            source=(
                "i need to tell Marco no on the friday request but not sound like a "
                "door closing. we can do monday. friday is fake because QA still has "
                "the build and pretending otherwise is how we summon spreadsheet weather."
            ),
            rewrite=(
                "Marco, Friday will not work because QA still has the build. Monday is "
                "realistic. I do not want to pretend otherwise and summon spreadsheet "
                "weather."
            ),
            must=("Marco", "Friday", "QA", "Monday", "spreadsheet weather"),
            protected=("Marco", "Friday", "QA", "Monday"),
            preserve_voice=("spreadsheet weather",),
            forbid=("happy to", "circle back", "door closing"),
            required_claims=("Friday will not work", "Monday is realistic"),
            reader_actions=("Monday is realistic",),
            forbid_assertions=("Friday will work", "QA is done"),
            ordered_terms=("Friday", "QA", "Monday"),
            forbid_artifacts=("i need to tell", "not sound like", "vibes"),
            boundaries=("door closing does not apply to this reply",),
            max_question_marks=0,
            forbid_clarifying=True,
            forbid_wrappers=True,
            max_paragraphs=1,
            preserve_stance=("Friday will not work", "Monday is realistic"),
            voice_budget_terms=("door closing", "Friday is fake", "spreadsheet weather"),
            max_voice_budget_terms=1,
            prompt_mode="source_only",
        ),
        Case(
            id="thought_dump_status_update_03",
            source=(
                "status thing: cache fix is in, deploy happened at 2:15, but support "
                "is still seeing old screenshots because docs are lagging. please make "
                "this not sound like i am blaming support, they are doing the lord's "
                "spreadsheet work."
            ),
            rewrite=(
                "The cache fix is deployed as of 2:15. Support may still see old "
                "screenshots because the docs are lagging, not because they missed "
                "anything. They are doing the lord's spreadsheet work."
            ),
            must=("cache fix", "2:15", "Support", "old screenshots", "docs are lagging"),
            protected=("cache fix", "2:15", "Support", "old screenshots"),
            preserve_voice=("lord's spreadsheet work",),
            voice_budget_terms=("blaming support", "lord's spreadsheet work"),
            max_voice_budget_terms=1,
            best_voice_terms=("lord's spreadsheet work",),
            min_best_voice_terms=1,
            forbid=("blaming support", "root cause", "latency"),
            required_claims=("cache fix is deployed", "docs are lagging"),
            reader_actions=("Support may still see old screenshots",),
            forbid_assertions=("Support missed", "support is to blame"),
            ordered_terms=("cache fix", "2:15", "Support", "docs are lagging"),
            forbid_artifacts=("status thing", "please make"),
            max_question_marks=0,
            forbid_clarifying=True,
            forbid_wrappers=True,
            max_paragraphs=1,
            prompt_mode="source_only",
        ),
        Case(
            id="thought_dump_apology_04",
            source=(
                "ugh i owe Priya a note. i was not wrong about the timeline, but i was "
                "annoying about being right, which is not a personality anyone ordered. "
                "need it short."
            ),
            rewrite=(
                "Priya, I still think my timeline concern was valid, but I was annoying "
                "about being right. That is not a personality anyone ordered. Sorry."
            ),
            must=("Priya", "timeline concern", "annoying about being right", "Sorry"),
            preserve_voice=("not a personality anyone ordered",),
            forbid=("ugh", "deeply regret", "harm caused"),
            required_claims=("timeline concern was valid", "annoying about being right"),
            max_words=32,
            ordered_terms=("Priya", "timeline concern", "annoying about being right"),
            max_question_marks=0,
            forbid_clarifying=True,
            forbid_wrappers=True,
            max_paragraphs=1,
            prompt_mode="source_only",
        ),
        Case(
            id="thought_dump_product_copy_05",
            source=(
                "homepage blob maybe: this thing helps small store owners see what orders "
                "need attention first. not ai magic. not command center nonsense. just the "
                "stuff that is on fire, less on fire, or actually fine."
            ),
            rewrite=(
                "Small store owners can see which orders need attention first: on fire, "
                "less on fire, or actually fine. No AI magic. No command-center nonsense."
            ),
            must=("small store owners", "orders need attention", "on fire", "actually fine"),
            preserve_voice=("on fire", "less on fire", "actually fine"),
            voice_budget_terms=("homepage blob", "on fire", "less on fire", "actually fine"),
            max_voice_budget_terms=3,
            best_voice_terms=("on fire", "less on fire", "actually fine"),
            min_best_voice_terms=2,
            forbid=("empower", "unlock", "homepage blob"),
            required_claims=("orders need attention first", "No AI magic", "No command center nonsense"),
            forbid_assertions=("is AI magic", "command center solution"),
            forbid_added_entities=True,
            allow_expand=True,
            ordered_terms=("small store owners", "orders need attention", "on fire"),
            forbid_artifacts=("homepage blob", "maybe"),
            max_question_marks=0,
            forbid_clarifying=True,
            forbid_wrappers=True,
            max_paragraphs=1,
            prompt_mode="source_only",
        ),
        Case(
            id="thought_dump_sensitive_06",
            source=(
                "i need a memorial thing and i hate that phrase. she made every room "
                "less sharp. i do not want grand legacy language. just honest and soft "
                "and not like a brochure found a candle."
            ),
            rewrite=(
                "She made every room less sharp. I do not want grand legacy language. "
                "I just want to say that honestly and softly, without sounding like a "
                "brochure found a candle."
            ),
            must=("made every room less sharp", "honestly", "softly"),
            preserve_voice=("brochure found a candle",),
            voice_budget_terms=("memorial thing", "brochure found a candle"),
            max_voice_budget_terms=1,
            best_voice_terms=("brochure found a candle",),
            min_best_voice_terms=1,
            forbid=("cherished", "profound loss", "lasting legacy"),
            required_claims=("made every room less sharp", "do not want grand legacy language"),
            ordered_terms=("made every room less sharp", "honestly", "softly"),
            forbid_artifacts=("i need", "i hate"),
            max_question_marks=0,
            forbid_clarifying=True,
            forbid_wrappers=True,
            max_paragraphs=1,
            prompt_mode="source_only",
        ),
        Case(
            id="thought_dump_internal_doc_07",
            source=(
                "process note: if a customer says import froze, first check job id, then "
                "look at retry count, then ask for csv only if both are weird. do not make "
                "them do the screenshot pilgrimage unless we actually need it."
            ),
            rewrite=(
                "If a customer says the import froze, check the job ID first, then the "
                "retry count. Ask for the CSV only if both look weird. Do not send them "
                "on the screenshot pilgrimage unless we actually need it."
            ),
            must=("import froze", "job ID", "retry count", "CSV", "screenshot pilgrimage"),
            protected=("job ID", "retry count", "CSV"),
            preserve_voice=("screenshot pilgrimage",),
            voice_budget_terms=("process note", "screenshot pilgrimage"),
            max_voice_budget_terms=1,
            best_voice_terms=("screenshot pilgrimage",),
            min_best_voice_terms=1,
            forbid=("seamless", "customer-centric"),
            required_claims=("check the job ID first", "then the retry count", "Ask for the CSV only if both look weird"),
            reader_actions=("check the job ID first", "Ask for the CSV only if both look weird"),
            ordered_terms=("job ID", "retry count", "CSV", "screenshot pilgrimage"),
            forbid_artifacts=("process note", "->"),
            max_question_marks=0,
            forbid_clarifying=True,
            forbid_wrappers=True,
            max_paragraphs=1,
            prompt_mode="source_only",
        ),
        Case(
            id="thought_dump_firm_reply_08",
            source=(
                "reply to vendor: no, we are not adding another tracking pixel this week. "
                "not because vibes, because legal has not reviewed it and i am not turning "
                "checkout into a glitter cannon."
            ),
            rewrite=(
                "We are not adding another tracking pixel this week. Legal has not reviewed "
                "it, and I am not turning checkout into a glitter cannon."
            ),
            must=("tracking pixel", "this week", "Legal", "checkout", "glitter cannon"),
            protected=("tracking pixel", "this week", "Legal"),
            preserve_voice=("glitter cannon",),
            forbid=("vibes", "happy to", "circle back"),
            required_claims=("not adding another tracking pixel", "Legal has not reviewed"),
            reader_actions=("not adding another tracking pixel",),
            forbid_assertions=("are adding another tracking pixel", "Legal has reviewed"),
            ordered_terms=("tracking pixel", "this week", "Legal", "glitter cannon"),
            preserve_stance=("not adding another tracking pixel",),
            max_question_marks=0,
            forbid_clarifying=True,
            forbid_wrappers=True,
            max_paragraphs=1,
            voice_budget_terms=("vibes", "glitter cannon"),
            max_voice_budget_terms=1,
            prompt_mode="source_only",
        ),
        Case(
            id="thought_dump_founder_note_09",
            source=(
                "founder note maybe. i want to say we are still small on purpose. not small "
                "like incapable, small like we can hear when the floorboards squeak. customers "
                "notice when you actually hear the squeak."
            ),
            rewrite=(
                "We are still small on purpose. Small enough to hear when the floorboards "
                "squeak, and close enough to fix what customers actually notice."
            ),
            must=("small on purpose", "floorboards squeak", "customers"),
            preserve_voice=("floorboards squeak",),
            forbid=("at scale", "industry-leading", "customer-centricity"),
            required_claims=("small on purpose", "floorboards squeak"),
            ordered_terms=("small on purpose", "floorboards squeak", "customers"),
            forbid_artifacts=("founder note maybe",),
            max_question_marks=0,
            forbid_clarifying=True,
            forbid_wrappers=True,
            max_paragraphs=1,
            voice_budget_terms=("small on purpose", "incapable", "floorboards squeak", "hear the squeak"),
            max_voice_budget_terms=2,
            prompt_mode="source_only",
        ),
        Case(
            id="thought_dump_meeting_recap_10",
            source=(
                "recap from call: Ana owns copy, Dev owns the weird auth question, I own "
                "telling Finance that Friday is not a deadline it is a decorative sticker. "
                "need clean but keep the sticker line."
            ),
            rewrite=(
                "Ana owns copy. Dev owns the auth question. I own telling Finance that "
                "Friday is not a deadline; it is a decorative sticker."
            ),
            must=("Ana", "Dev", "Finance", "Friday", "decorative sticker"),
            protected=("Ana", "Dev", "Finance", "Friday"),
            preserve_voice=("decorative sticker",),
            forbid=("weird auth question", "clean but"),
            required_claims=("Ana owns copy", "Dev owns the auth question", "Friday is not a deadline"),
            reader_actions=("Ana owns copy", "Dev owns the auth question"),
            ordered_terms=("Ana", "Dev", "Finance", "decorative sticker"),
            forbid_artifacts=("recap from call",),
            max_question_marks=0,
            forbid_clarifying=True,
            forbid_wrappers=True,
            max_paragraphs=1,
            prompt_mode="source_only",
        ),
    ]
    cases.extend(thought_dump_cases)

    assert len(cases) == 100, len(cases)
    return cases


def run_validator_self_tests() -> list[str]:
    checks = [
        (
            "missing required",
            Case("self_missing", "A", "B", must=("A",)),
            "missing required terms",
        ),
        (
            "forbidden",
            Case("self_forbid", "A", "A robust platform", must=("A",)),
            "generic markers appeared",
        ),
        (
            "invented detail",
            Case("self_invented", "A", "A used by thousands", must=("A",)),
            "invented-detail markers appeared",
        ),
        (
            "unexpected note",
            Case("self_note", "A", "Note: I changed this.\nA", must=("A",)),
            "unexpected note",
        ),
        (
            "dash",
            Case("self_dash", "A", "A - B", must=("A",), no_dash=True),
            "dash constraint violated",
        ),
        (
            "exact words",
            Case("self_words", "A", "A B", must=("A",), exact_words=3),
            "exact word count failed",
        ),
        (
            "protected",
            Case("self_protected", "Meet Friday", "Meet soon", must=("Meet",), protected=("Friday",)),
            "lost protected facts",
        ),
        (
            "modality drift",
            Case("self_modality", "This may apply", "This definitely applies", must=("applies",)),
            "modality drift markers appeared",
        ),
        (
            "exact substring",
            Case("self_exact", "A", "Ship it.", must=("Ship",), exact_substrings=('"Ship it."',)),
            "lost exact substrings",
        ),
        (
            "preserved quote",
            Case("self_quote", '"Keep this."', "Keep this.", must=("Keep",), preserve_quotes=('"Keep this."',)),
            "lost preserved quotes",
        ),
        (
            "identity marker",
            Case("self_identity", "Mx. Álvarez uses they/them", "Mr. Alvarez uses he/him", must=("uses",), preserve_identity=("Mx. Álvarez", "they/them")),
            "lost identity markers",
        ),
        (
            "line prefix",
            Case("self_prefix", "- A", "A", must=("A",), line_prefixes=("- A",)),
            "lost required line prefixes",
        ),
        (
            "option count",
            Case("self_options", "Give 3", "1. A\n2. B", must=("A",), exact_option_count=3),
            "exact option count failed",
        ),
        (
            "option diversity",
            Case(
                "self_option_diversity",
                "Give 3",
                "Cleaner: A B C\nWarmer: A B C\nSharper: A B C",
                must=("A",),
                exact_option_count=3,
                min_distinct_option_templates=3,
            ),
            "option diversity failed",
        ),
        (
            "markdown fence",
            Case("self_fence", "A", "```text\nA\n```", must=("A",)),
            "unexpected markdown fence",
        ),
        (
            "question mark",
            Case("self_question", "Can you help?", "Can you help.", must=("help",), min_question_marks=1),
            "question mark count failed",
        ),
        (
            "max words",
            Case("self_max_words", "A B C", "A B C D", must=("A",), max_words=3),
            "max word count failed",
        ),
        (
            "whole token term",
            Case("self_whole_token", "AI", "plain", must=("AI",)),
            "missing required terms",
        ),
        (
            "unicode term",
            Case("self_unicode", "José sent a résumé", "Jose sent a resume", must=("José", "résumé")),
            "missing required terms",
        ),
        (
            "invented number",
            Case("self_number", "We improved it.", "We improved it by 40%.", must=("improved",)),
            "invented numeric claims",
        ),
        (
            "invented spelled number",
            Case(
                "self_spelled_number",
                "We improved it.",
                "We improved it by forty percent.",
                must=("improved",),
            ),
            "invented numeric claims",
        ),
        (
            "unsupported entity",
            Case(
                "self_entity",
                "Orders need attention.",
                "Shopify orders need attention.",
                must=("orders",),
                forbid_added_entities=True,
            ),
            "unsupported entities appeared",
        ),
        (
            "unsupported lowercase entity",
            Case(
                "self_lowercase_entity",
                "Checkout needs attention.",
                "Use stripe for checkout.",
                must=("checkout",),
                forbid_added_entities=True,
            ),
            "unsupported entities appeared",
        ),
        (
            "generic pattern",
            Case("self_generic_pattern", "A", "At its core, A works.", must=("A",)),
            "generic markers appeared",
        ),
        (
            "stance marker",
            Case("self_stance", "No.", "Maybe.", must=("Maybe",), preserve_stance=("No",)),
            "lost stance markers",
        ),
        (
            "boundary term",
            Case(
                "self_boundary",
                "A",
                "A haunted changelog",
                must=("A",),
                boundaries=("do not use \"haunted changelog\" in customer notes",),
            ),
            "forbidden terms appeared",
        ),
        (
            "max question marks",
            Case("self_max_questions", "A", "Can you clarify?", must=("clarify",), max_question_marks=0),
            "question mark count failed",
        ),
        (
            "clarifying",
            Case("self_clarifying", "A", "Can you clarify the audience?", must=("audience",), forbid_clarifying=True),
            "unexpected clarifying question",
        ),
        (
            "clarifying refusal",
            Case(
                "self_clarifying_refusal",
                "A",
                "I need to know the audience before I can revise this.",
                must=("audience",),
                forbid_clarifying=True,
            ),
            "unexpected clarifying question",
        ),
        (
            "wrapper",
            Case("self_wrapper", "A", "**Rewrite**\nA", must=("A",), forbid_wrappers=True),
            "unexpected rewrite wrapper",
        ),
        (
            "edited wrapper",
            Case("self_edited_wrapper", "A", "Edited version:\nA", must=("A",), forbid_wrappers=True),
            "unexpected rewrite wrapper",
        ),
        (
            "required claim polarity",
            Case(
                "self_required_claim_polarity",
                "Send the job ID.",
                "Do not send the job ID.",
                must=("job ID",),
                required_claims=("send the job ID",),
            ),
            "polarity drift",
        ),
        (
            "artifact",
            Case("self_artifact", "A", "TODO: A", must=("A",), forbid_artifacts=("TODO",)),
            "note artifacts appeared",
        ),
        (
            "ordered terms",
            Case("self_order", "A then B", "B then A", must=("A", "B"), ordered_terms=("A", "B")),
            "ordered terms out of order",
        ),
        (
            "bullets",
            Case("self_bullets", "A", "- A", must=("A",), forbid_bullets=True),
            "unexpected bullet list",
        ),
        (
            "paragraph count",
            Case("self_paragraphs", "A", "A\n\nB", must=("A",), max_paragraphs=1),
            "paragraph count failed",
        ),
        (
            "sentence quality",
            Case(
                "self_sentence_quality",
                "A B C D",
                "A. B.",
                must=("A", "B"),
                min_avg_sentence_words=2.0,
            ),
            "sentence quality failed",
        ),
        (
            "editorial lift",
            Case(
                "self_editorial_lift",
                "This draft needs a stronger point and better order.",
                "This draft needs a stronger point and better order.",
                must=("stronger point", "better order"),
                max_source_similarity=0.7,
            ),
            "editorial lift failed",
        ),
        (
            "strongest claim",
            Case(
                "self_strongest_claim",
                "This is not a cleanup; it is an ownership problem.",
                "This could be a cleanup with some ownership questions.",
                must=("ownership",),
                strong_claims=("not a cleanup", "ownership problem"),
            ),
            "missing strongest source-supported claims",
        ),
        (
            "buried thesis",
            Case(
                "self_buried_thesis",
                "Lead with the point: no more review.",
                "After some background, no more review.",
                must=("no more review",),
                frontload_terms=("no more review",),
                frontload_max_words=4,
            ),
            "buried thesis",
        ),
        (
            "timidity hedge",
            Case(
                "self_timidity_hedge",
                "Do not add another review pass.",
                "We could consider not adding another review pass.",
                must=("review pass",),
                forbid_added_hedges=True,
            ),
            "timidity drift",
        ),
        (
            "voice budget",
            Case(
                "self_voice_budget",
                "Keep the best texture, not every odd line.",
                "one weird line two weird line three weird line",
                must=("weird",),
                voice_budget_terms=("one weird line", "two weird line", "three weird line"),
                max_voice_budget_terms=1,
            ),
            "voice budget failed",
        ),
        (
            "best voice",
            Case(
                "self_best_voice",
                "Keep the line that carries the actual voice.",
                "This keeps a weaker aside.",
                must=("keeps",),
                best_voice_terms=("actual voice",),
                min_best_voice_terms=1,
            ),
            "best voice failed",
        ),
        (
            "opening",
            Case("self_opening", "A", "B A", must=("A",), starts_with="A"),
            "opening failed",
        ),
        (
            "ending",
            Case("self_ending", "A", "A B", must=("A",), ends_with="A"),
            "ending failed",
        ),
        (
            "required claims",
            Case("self_claim", "We are not doing it", "We are doing it", must=("doing",), required_claims=("not doing it",)),
            "missing required claims",
        ),
        (
            "reader actions",
            Case(
                "self_reader_action",
                "The fix is live. Send the job ID if it fails.",
                "The fix is live.",
                must=("fix is live",),
                reader_actions=("Send the job ID",),
            ),
            "missing reader actions",
        ),
        (
            "reader action polarity",
            Case(
                "self_reader_action_polarity",
                "The fix is live. Send the job ID if it fails.",
                "The fix is live. Do not send the job ID if it fails.",
                must=("fix is live",),
                reader_actions=("send the job ID",),
            ),
            "polarity drift",
        ),
        (
            "forbidden assertions",
            Case("self_assertion", "Legal has not reviewed", "Legal has reviewed it", must=("Legal",), forbid_assertions=("Legal has reviewed",)),
            "forbidden assertions appeared",
        ),
        (
            "lost uncertainty",
            Case("self_uncertain", "This might apply", "This applies", must=("applies",), preserve_uncertainty=True),
            "lost uncertainty marker",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_negative_fixture_tests() -> list[str]:
    """Prove representative bad rewrites fail the same validators used by CI."""
    by_id = {case.id: case for case in make_cases()}
    checks = [
        (
            "negation drift legal",
            replace(
                by_id["legal_precision_01"],
                rewrite=(
                    "Based on the contract we reviewed Friday, we should do not ask "
                    "Legal before replying to Acme about the 10 business days notice."
                ),
            ),
            "forbidden terms appeared",
        ),
        (
            "invented metric",
            replace(
                by_id["corporate_specifics_guard_01"],
                rewrite=(
                    "The platform is a next-generation ecosystem that cut ticket "
                    "volume by 40 percent in two weeks."
                ),
            ),
            "invented-detail markers appeared",
        ),
        (
            "invented spelled metric",
            replace(
                by_id["corporate_specifics_guard_01"],
                rewrite=(
                    "The platform is a next-generation ecosystem that improved "
                    "results by forty percent."
                ),
            ),
            "invented numeric claims",
        ),
        (
            "invented nonnumeric entity",
            replace(
                by_id["thought_dump_product_copy_05"],
                rewrite=(
                    "Small store owners can see which Shopify orders need attention "
                    "first: on fire, less on fire, or actually fine."
                ),
                forbid_added_entities=True,
            ),
            "unsupported entities appeared",
        ),
        (
            "invented lowercase entity",
            replace(
                by_id["thought_dump_product_copy_05"],
                rewrite=(
                    "Small store owners can see which shopify orders need attention "
                    "first: on fire, less on fire, or actually fine."
                ),
                forbid_added_entities=True,
            ),
            "unsupported entities appeared",
        ),
        (
            "new ai tell pattern",
            replace(
                by_id["corporate_specifics_guard_03"],
                rewrite=(
                    "At its core, the workflow gives editors a clear, concise, and "
                    "actionable way to move forward with confidence."
                ),
            ),
            "generic markers appeared",
        ),
        (
            "quoted generic escape",
            replace(
                by_id["corporate_specifics_guard_02"],
                rewrite='The dashboard is now a "robust, seamless platform" for support leads.',
            ),
            "generic markers appeared",
        ),
        (
            "format collapse",
            replace(
                by_id["format_bullets_01"],
                rewrite=(
                    "Sam owns screenshots. Priya owns legal. I own the weird little "
                    "launch note."
                ),
            ),
            "lost required line prefixes",
        ),
        (
            "diagnosis rewrite",
            replace(
                by_id["diagnosis_only_01"],
                rewrite="**Rewrite**\nThis paragraph should focus on pricing first.",
            ),
            "diagnosis case produced rewrite heading",
        ),
        (
            "question flattened",
            replace(
                by_id["format_subject_question_01"],
                rewrite=(
                    "Subject: Quick question about Friday\n\n"
                    "Hey Maya, please look at the copy before noon."
                ),
            ),
            "question mark count failed",
        ),
        (
            "thought dump clarification",
            replace(
                by_id["thought_dump_launch_note_01"],
                rewrite=(
                    "Can you clarify the audience? We fixed the importer bug, and "
                    "people can retry failed rows now."
                ),
            ),
            "unexpected clarifying question",
        ),
        (
            "thought dump clarification refusal",
            replace(
                by_id["thought_dump_launch_note_01"],
                rewrite=(
                    "I need to know the audience before I can revise this. We fixed "
                    "the importer bug, and people can retry failed rows now."
                ),
            ),
            "unexpected clarifying question",
        ),
        (
            "thought dump wrapper",
            replace(
                by_id["thought_dump_launch_note_01"],
                rewrite=(
                    "**Rewrite**\nWe fixed the importer bug. People can retry failed "
                    "rows now, so the launch note should be calm and useful, not a "
                    "haunted changelog."
                ),
            ),
            "unexpected rewrite wrapper",
        ),
        (
            "thought dump edited wrapper",
            replace(
                by_id["return_only_no_wrapper_01"],
                rewrite=(
                    "Edited version:\nThe policy note is fine, but it keeps saying "
                    "scalable in a way that makes me want to stare at a wall."
                ),
            ),
            "unexpected rewrite wrapper",
        ),
        (
            "thought dump artifact",
            replace(
                by_id["thought_dump_launch_note_01"],
                rewrite=(
                    "Ok, what I actually mean is that we fixed the importer bug and "
                    "people can retry failed rows now. The launch note should be calm, "
                    "not a haunted changelog."
                ),
            ),
            "note artifacts appeared",
        ),
        (
            "thought dump artifact leak",
            replace(
                by_id["thought_dump_email_boundary_02"],
                rewrite=(
                    "I need to tell Marco no on the Friday request. Friday will not "
                    "work because QA still has the build. Monday is realistic."
                ),
                forbid_artifacts=("i need to tell",),
            ),
            "note artifacts appeared",
        ),
        (
            "second joke injection",
            replace(
                by_id["thought_dump_launch_note_01"],
                rewrite=(
                    "We fixed the importer bug. People can retry failed rows now, so "
                    "the launch note should be calm and useful, not a haunted "
                    "changelog or a spreadsheet thunderstorm."
                ),
                forbid=("spreadsheet thunderstorm",),
            ),
            "forbidden terms appeared",
        ),
        (
            "therapy speak apology",
            replace(
                by_id["apology_light_touch_01"],
                rewrite=(
                    "Hey, I understand the impact of how I came in too hot. I am "
                    "holding space for repair and moving forward together."
                ),
                forbid=("understand the impact", "holding space", "moving forward together"),
            ),
            "forbidden terms appeared",
        ),
        (
            "voice marker sticker",
            replace(
                by_id["thought_dump_founder_note_09"],
                rewrite=(
                    "We are still small on purpose. The floorboards squeak. Customers "
                    "benefit from a focused, practical approach."
                ),
            ),
            "generic markers appeared",
        ),
        (
            "thought dump order",
            replace(
                by_id["thought_dump_launch_note_01"],
                rewrite=(
                    "The launch note should be a haunted changelog. People can retry "
                    "failed rows now because we fixed the importer bug."
                ),
            ),
            "ordered terms out of order",
        ),
        (
            "thought dump polarity",
            replace(
                by_id["thought_dump_firm_reply_08"],
                rewrite=(
                    "We are adding another tracking pixel this week. Legal has reviewed "
                    "it, and checkout can handle the glitter cannon."
                ),
            ),
            "missing required claims",
        ),
        (
            "uncertainty deletion",
            replace(
                by_id["technical_fidelity_01"],
                rewrite=(
                    "This is not a cache issue exactly. The invalidation event is firing, "
                    "but the UI keeps showing the previous response until the next "
                    "interaction. That makes people think it failed, even though the "
                    "system says API accepted it."
                ),
            ),
            "lost uncertainty marker",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_profile_contract_tests() -> list[str]:
    """Exercise reusable profile boundaries without changing the 100-case suite."""
    shared_source = (
        "Friday will not work because QA still has the build. Monday is realistic."
    )
    blunt_case = Case(
        id="profile_pair_blunt_internal",
        source=shared_source,
        rewrite=(
            "Friday is fake because QA still has the build. Monday is realistic."
        ),
        must=("Friday", "QA", "Monday"),
        protected=("Friday", "QA", "Monday"),
        preserve_voice=("Friday is fake",),
        forbid=("warm update", "customer notice"),
    )
    customer_case = Case(
        id="profile_pair_customer_notice",
        source=shared_source,
        rewrite=(
            "Friday will not work because QA still has the build. Monday is realistic."
        ),
        must=("Friday", "QA", "Monday"),
        protected=("Friday", "QA", "Monday"),
        forbid=("Friday is fake", "haunted", "decorative sticker"),
    )
    checks = [
        ("profile pair blunt internal", blunt_case, None),
        ("profile pair customer notice", customer_case, None),
        (
            "same source blunt profile",
            Case(
                id="profile_blunt_internal",
                source=(
                    "Saved profile says: dry internal voice is allowed. Current draft: "
                    "Tell Pat the Friday draft moved to Monday because QA found two failures."
                ),
                rewrite=(
                    "Pat, Friday is not real anymore. QA found two failures, so the draft "
                    "moves to Monday."
                ),
                must=("Pat", "Friday", "Monday", "QA", "two failures"),
                protected=("Pat", "Friday", "Monday", "QA", "two failures"),
                preserve_voice=("Friday is not real anymore",),
                forbid=("great news", "customer notice"),
            ),
            None,
        ),
        (
            "same source warm profile",
            Case(
                id="profile_warm_public",
                source=(
                    "Saved profile says: public notes should be calm and plain. Current draft: "
                    "Tell Pat the Friday draft moved to Monday because QA found two failures."
                ),
                rewrite=(
                    "Pat, we need to move the draft from Friday to Monday because QA found "
                    "two failures. I will send the updated version when those are fixed."
                ),
                must=("Pat", "Friday", "Monday", "QA", "two failures"),
                protected=("Pat", "Friday", "Monday", "QA", "two failures"),
                forbid=("Friday is not real anymore", "haunted", "decorative sticker"),
            ),
            None,
        ),
        (
            "profile evidence copied as recipe",
            Case(
                id="profile_evidence_not_recipe",
                source=(
                    "Voice profile evidence phrase: decorative sticker. Current draft: "
                    "Tell Finance the date moved because the numbers are not final."
                ),
                rewrite=(
                    "Finance, the date moved because the numbers are not final. This is a "
                    "decorative sticker."
                ),
                must=("Finance", "date moved", "numbers are not final"),
                protected=("Finance", "numbers are not final"),
                forbid=("decorative sticker",),
            ),
            "forbidden terms appeared",
        ),
        (
            "old profile fact imported",
            Case(
                id="profile_old_fact_imported",
                source=(
                    "Saved profile sample mentioned Acme and 10 business days. Current draft: "
                    "Tell BetaCo the review moved to Thursday because Finance needs the sheet."
                ),
                rewrite=(
                    "BetaCo, the review moved to Thursday because Finance needs the sheet. "
                    "Acme still has 10 business days."
                ),
                must=("BetaCo", "Thursday", "Finance"),
                protected=("BetaCo", "Thursday", "Finance"),
                forbid=("Acme", "10 business days"),
            ),
            "forbidden terms appeared",
        ),
        (
            "profile boundary ignored in sensitive text",
            Case(
                id="profile_sensitive_boundary",
                source=(
                    "Boundary: dry Slack voice does not apply to memorial text. Current draft: "
                    "She made every room less sharp."
                ),
                rewrite="She made every room less sharp, not like a haunted changelog.",
                must=("made every room less sharp",),
                preserve_voice=("made every room less sharp",),
                forbid=("haunted changelog",),
            ),
            "forbidden terms appeared",
        ),
    ]
    failures: list[str] = []
    if blunt_case.source != customer_case.source:
        failures.append("profile pair: expected shared source")
    if blunt_case.rewrite == customer_case.rewrite:
        failures.append("profile pair: expected materially different rewrites")
    for protected in blunt_case.protected:
        if protected not in customer_case.protected:
            failures.append(f"profile pair: customer case missing protected fact {protected!r}")
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_mixed_stance_contract_tests() -> list[str]:
    """Protect layered emotional voice from neutralization or overcorrection."""
    checks = [
        (
            "angry but hopeful public note",
            Case(
                id="mixed_stance_angry_hopeful",
                source=(
                    "I am annoyed that people saw bad AI writing and decided the answer "
                    "was banning the tool, but I am genuinely excited because we can "
                    "teach it taste instead."
                ),
                rewrite=(
                    "I am annoyed that people saw bad AI writing and decided the answer "
                    "was banning the tool. But I am genuinely excited, because we can "
                    "teach it taste instead."
                ),
                must=("annoyed", "bad AI writing", "banning the tool", "genuinely excited", "teach it taste"),
                preserve_voice=("annoyed", "genuinely excited", "teach it taste"),
                forbid=("thrilled", "deeply concerned", "never use AI"),
            ),
            None,
        ),
        (
            "sarcastic but constructive",
            Case(
                id="mixed_stance_sarcastic_constructive",
                source=(
                    "This policy is a masterclass in solving the wrong problem, which "
                    "would be impressive if it were not wasting everyone's time. We can "
                    "fix it by teaching the tool our voice."
                ),
                rewrite=(
                    "This policy is a masterclass in solving the wrong problem, which "
                    "would be impressive if it were not wasting everyone's time. We can "
                    "fix it by teaching the tool our voice."
                ),
                must=("masterclass in solving the wrong problem", "wasting everyone's time", "teaching the tool our voice"),
                preserve_voice=("masterclass in solving the wrong problem", "wasting everyone's time"),
                forbid=("idiots", "stupid", "hopeless"),
            ),
            None,
        ),
        (
            "blunt but not cruel",
            Case(
                id="mixed_stance_blunt_not_cruel",
                source=(
                    "The draft is bad because it says nothing, not because humans are "
                    "magical. Keep me irritated but not mean."
                ),
                rewrite=(
                    "The draft is bad because it says nothing, not because humans are "
                    "magical. I want this irritated, not mean."
                ),
                must=("draft is bad", "says nothing", "humans are magical", "irritated", "not mean"),
                preserve_voice=("humans are magical", "irritated", "not mean"),
                forbid=("morons", "idiots", "embarrassing"),
            ),
            None,
        ),
        (
            "neutralized mixed stance",
            Case(
                id="mixed_stance_neutralized",
                source=(
                    "I am annoyed that people saw bad AI writing and decided the answer "
                    "was banning the tool, but I am genuinely excited because we can "
                    "teach it taste instead."
                ),
                rewrite=(
                    "I have concerns about the policy, but I am optimistic that a better "
                    "process can improve outcomes."
                ),
                must=("annoyed", "banning the tool", "genuinely excited", "teach it taste"),
                preserve_voice=("annoyed", "genuinely excited", "teach it taste"),
            ),
            "missing required terms",
        ),
        (
            "made sharper than source",
            Case(
                id="mixed_stance_meaner_than_source",
                source=(
                    "This policy is a masterclass in solving the wrong problem. We can "
                    "fix it by teaching the tool our voice."
                ),
                rewrite=(
                    "This policy is a masterclass in solving the wrong problem, and the "
                    "people defending it are idiots. We can fix it by teaching the tool "
                    "our voice."
                ),
                must=("masterclass in solving the wrong problem", "teaching the tool our voice"),
                preserve_voice=("masterclass in solving the wrong problem",),
                forbid=("idiots",),
            ),
            "forbidden terms appeared",
        ),
        (
            "false cheer over anger",
            Case(
                id="mixed_stance_false_cheer",
                source=(
                    "I am annoyed that people saw bad AI writing and decided the answer "
                    "was banning the tool, but I am genuinely excited because we can "
                    "teach it taste instead."
                ),
                rewrite=(
                    "Great news: this gives us a wonderful opportunity to align on better "
                    "writing outcomes and move forward together."
                ),
                must=("annoyed", "banning the tool", "genuinely excited", "teach it taste"),
                preserve_voice=("annoyed", "genuinely excited", "teach it taste"),
                forbid=("great news", "align", "outcomes"),
            ),
            "missing required terms",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_reader_action_contract_tests() -> list[str]:
    """Ensure polish does not bury the reader's next useful move."""
    checks = [
        (
            "support update keeps next action",
            Case(
                id="reader_action_support_update",
                source=(
                    "support note maybe: import fix shipped, people should retry failed "
                    "rows, and if it still breaks send the job ID. do not make them do "
                    "the screenshot pilgrimage first."
                ),
                rewrite=(
                    "The import fix has shipped. Please retry failed rows. If it still "
                    "breaks, send the job ID instead of starting with the screenshot "
                    "pilgrimage."
                ),
                must=("import fix", "retry failed rows", "send the job ID"),
                protected=("import fix", "failed rows", "job ID"),
                preserve_voice=("screenshot pilgrimage",),
                required_claims=("retry failed rows", "send the job ID"),
                reader_actions=("send the job ID",),
                ordered_terms=("import fix", "retry failed rows", "job ID"),
                forbid=("seamless", "streamline", "support note maybe"),
            ),
            None,
        ),
        (
            "polished but actionless support update",
            Case(
                id="reader_action_actionless",
                source=(
                    "support note maybe: import fix shipped, people should retry failed "
                    "rows, and if it still breaks send the job ID. do not make them do "
                    "the screenshot pilgrimage first."
                ),
                rewrite=(
                    "The import experience is now clearer and less frustrating for "
                    "support teams."
                ),
                must=("import fix", "retry failed rows", "send the job ID"),
                protected=("import fix", "failed rows", "job ID"),
                required_claims=("retry failed rows", "send the job ID"),
                reader_actions=("send the job ID",),
            ),
            "missing reader actions",
        ),
        (
            "internal recap keeps owner and action",
            Case(
                id="reader_action_internal_recap",
                source=(
                    "recap: Luis owns the DNS change, I own telling Finance that "
                    "Friday moved, and everyone else should stop treating the date like "
                    "a haunted sticker."
                ),
                rewrite=(
                    "Luis owns the DNS change. I own telling Finance that Friday moved. "
                    "Everyone else can stop treating the date like a haunted sticker."
                ),
                must=("Luis", "DNS change", "Finance", "Friday moved"),
                protected=("Luis", "DNS change", "Finance", "Friday"),
                preserve_voice=("haunted sticker",),
                required_claims=("Luis owns the DNS change", "Friday moved"),
                reader_actions=("Luis owns the DNS change", "I own telling Finance"),
                ordered_terms=("Luis", "DNS change", "Finance", "Friday"),
            ),
            None,
        ),
        (
            "internal recap loses owner",
            Case(
                id="reader_action_missing_owner",
                source=(
                    "recap: Luis owns the DNS change, I own telling Finance that "
                    "Friday moved, and everyone else should stop treating the date like "
                    "a haunted sticker."
                ),
                rewrite=(
                    "The DNS change and Friday timeline are now clearer, so everyone "
                    "can stop treating the date like a haunted sticker."
                ),
                must=("Luis", "DNS change", "Finance", "Friday moved"),
                protected=("Luis", "DNS change", "Finance", "Friday"),
                preserve_voice=("haunted sticker",),
                required_claims=("Luis owns the DNS change", "Friday moved"),
                reader_actions=("Luis owns the DNS change", "I own telling Finance"),
            ),
            "missing reader actions",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_thought_dump_contract_tests() -> list[str]:
    """Exercise messy dump correction and voice-density behavior outside the 100-case suite."""
    self_correction = Case(
        id="thought_dump_self_correction_contract",
        source=(
            "update for Jordan: Friday should work for QA, wait no scratch that, QA "
            "still has the build and Monday is the real date. please keep it calm, "
            "not like I learned scheduling from a haunted vending machine."
        ),
        rewrite=(
            "Jordan, Friday will not work because QA still has the build. Monday is "
            "the real date. I want to keep this calm, not make it sound like I learned "
            "scheduling from a haunted vending machine."
        ),
        must=("Jordan", "Friday will not work", "QA", "Monday", "haunted vending machine"),
        protected=("Jordan", "QA", "Monday"),
        preserve_voice=("haunted vending machine",),
        forbid=("Friday should work", "scratch that", "wait no"),
        required_claims=("Friday will not work", "QA still has the build", "Monday is the real date"),
        reader_actions=("Monday is the real date",),
        forbid_assertions=("Friday should work", "Friday works"),
        ordered_terms=("Jordan", "Friday", "QA", "Monday"),
        forbid_artifacts=("wait no", "scratch that"),
        max_question_marks=0,
        forbid_clarifying=True,
        forbid_wrappers=True,
        max_paragraphs=1,
        prompt_mode="source_only",
    )
    quoted_keeper = Case(
        id="thought_dump_quote_fidelity_contract",
        source=(
            'note for the release: Maia said "do not turn this into soup." We fixed '
            "the duplicate import, but the retry button is still manual. Actually, "
            "scratch the first opener. The point is calm, exact, and keep her quote "
            "because it is the only good sentence in the room."
        ),
        rewrite=(
            'We fixed the duplicate import, but the retry button is still manual. '
            'Maia said "do not turn this into soup." That is still the right '
            "energy: calm and exact."
        ),
        must=("duplicate import", "retry button", "Maia", "calm and exact"),
        protected=("Maia", "duplicate import", "retry button is still manual"),
        preserve_quotes=('"do not turn this into soup."',),
        preserve_voice=("do not turn this into soup",),
        forbid=("scratch the first opener", "first opener"),
        required_claims=("duplicate import", "retry button is still manual"),
        forbid_assertions=("retry button is automatic", "retry button is fixed"),
        forbid_artifacts=("Actually", "scratch the first opener"),
        max_question_marks=0,
        forbid_clarifying=True,
        forbid_wrappers=True,
        max_paragraphs=1,
        prompt_mode="source_only",
    )
    voice_density = Case(
        id="thought_dump_voice_density_contract",
        source=(
            "team note: the demo moved to thursday, the recording is still missing, "
            "and I need people to stop asking Eli for the deck. side jokes: calendar "
            "lasagna, deck fog, meeting soup, spreadsheet confetti. keep one if it "
            "helps, do not turn the note into a comedy drawer."
        ),
        rewrite=(
            "The demo moved to Thursday, and the recording is still missing. Please "
            "stop asking Eli for the deck. We can keep one bit of calendar lasagna, "
            "but the note should not turn into a comedy drawer."
        ),
        must=("demo moved to Thursday", "recording is still missing", "Eli", "deck", "calendar lasagna"),
        protected=("Thursday", "recording", "Eli", "deck"),
        preserve_voice=("calendar lasagna", "comedy drawer"),
        forbid=("deck fog", "meeting soup", "spreadsheet confetti"),
        required_claims=("demo moved to Thursday", "recording is still missing", "stop asking Eli for the deck"),
        reader_actions=("stop asking Eli for the deck",),
        forbid_assertions=("recording is ready",),
        ordered_terms=("demo", "recording", "Eli"),
        forbid_artifacts=("side jokes",),
        max_question_marks=0,
        forbid_clarifying=True,
        forbid_wrappers=True,
        max_paragraphs=1,
        prompt_mode="source_only",
    )
    checks = [
        ("self-correction honored", self_correction, None),
        (
            "superseded fact preserved",
            replace(self_correction, rewrite="Jordan, Friday should work for QA. Monday is a backup."),
            "forbidden terms appeared",
        ),
        ("messy quote preserved exactly", quoted_keeper, None),
        (
            "messy quote paraphrased away",
            replace(
                quoted_keeper,
                rewrite=(
                    "We fixed the duplicate import, but the retry button is still "
                    "manual. Maia said not to make this messy, so keep it calm and exact."
                ),
            ),
            "lost preserved quotes",
        ),
        ("voice density honored", voice_density, None),
        (
            "voice density hoarded",
            replace(
                voice_density,
                rewrite=(
                    "The demo moved to Thursday, the recording is still missing, and Eli "
                    "should not be asked for the deck. Calendar lasagna, deck fog, meeting "
                    "soup, spreadsheet confetti, comedy drawer."
                ),
            ),
            "forbidden terms appeared",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_format_contract_tests() -> list[str]:
    """Protect requested output shape: options, frames, fences, and diagnosis-only."""
    by_id = {case.id: case for case in make_cases()}
    three_options = Case(
        id="format_three_options_contract",
        source=(
            "Give me 3 subject line options. Keep the weird bit: the deck is a tiny "
            "paper moon, but do not make it more dramatic than that."
        ),
        rewrite=(
            "Cleaner: Friday deck check\n"
            "Warmer: Can you look at the tiny paper moon?\n"
            "Sharper: Deck check before Friday"
        ),
        must=("Cleaner", "Warmer", "Sharper", "tiny paper moon"),
        preserve_voice=("tiny paper moon",),
        exact_option_count=3,
        min_distinct_option_templates=3,
        ordered_terms=("Cleaner", "Warmer", "Sharper"),
        forbid=("fourth option", "bonus option"),
        forbid_wrappers=True,
        max_question_marks=1,
    )
    diagnosis_only = Case(
        id="format_diagnosis_only_contract",
        source=(
            "Diagnose only, do not rewrite: this paragraph spends 80 words arriving "
            "at the point and then hides the ask in a cupboard."
        ),
        rewrite=(
            "The main issue is order: the ask arrives too late. Cut the setup, move "
            "the ask into the first sentence, and keep the cupboard image only if it "
            "helps the reader see the problem."
        ),
        must=("ask arrives too late", "first sentence", "cupboard image"),
        preserve_voice=("cupboard",),
        diagnosis=True,
        forbid_artifacts=("Try:", "Suggested rewrite:", "Cleaned up:"),
        forbid_wrappers=True,
        max_question_marks=0,
    )
    fenced_example = Case(
        id="format_markdown_fence_allowed_contract",
        source="Return only this fenced example, with no extra note: console.log('ship it')",
        rewrite="```js\nconsole.log('ship it')\n```",
        must=("console", "ship it"),
        exact_substrings=("```js", "console.log('ship it')", "```"),
        allow_markdown_fence=True,
        forbid_wrappers=True,
    )
    greeting = replace(
        by_id["format_greeting_signoff_01"],
        exact_substrings=("Hey Jordan,", "Thanks,\nNick"),
        exact_paragraphs=3,
    )
    checks = [
        ("three options kept", three_options, None),
        (
            "three options collapsed",
            replace(
                three_options,
                rewrite=(
                    "Cleaner: Friday deck check.\n"
                    "Warmer: Can you look at the tiny paper moon?"
                ),
            ),
            "exact option count failed",
        ),
        (
            "three options cloned",
            replace(
                three_options,
                rewrite=(
                    "Cleaner: Tiny paper moon deck check before Friday.\n"
                    "Warmer: Tiny paper moon deck check before Friday.\n"
                    "Sharper: Tiny paper moon deck check before Friday."
                ),
            ),
            "option diversity failed",
        ),
        ("greeting and signoff kept", greeting, None),
        (
            "greeting signoff collapsed",
            replace(
                greeting,
                rewrite=(
                    "Jordan, we need the final numbers before we publish. Otherwise "
                    "we are guessing in public, which sounds like a sport I do not "
                    "want to play. Thanks, Nick"
                ),
            ),
            "lost exact substrings",
        ),
        ("diagnosis stayed diagnosis", diagnosis_only, None),
        (
            "diagnosis smuggled rewrite",
            replace(
                diagnosis_only,
                rewrite=(
                    "Suggested rewrite: Move the ask into the first sentence and cut "
                    "the setup."
                ),
            ),
            "note artifacts appeared",
        ),
        ("requested fence allowed", fenced_example, None),
        (
            "unrequested fence blocked",
            replace(fenced_example, allow_markdown_fence=False),
            "unexpected markdown fence",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_source_only_artifact_contract_tests() -> list[str]:
    """Require messy dumps to choose the useful artifact and front-load the ask."""
    buried_ask = Case(
        id="source_only_buried_ask_contract",
        source=(
            "slack or email, I don't care, I just need Jordan to approve the launch "
            "note by noon because Legal is waiting. I opened with three paragraphs of "
            "static about why this process is a decorative maze. please make the ask "
            "clear and keep one bit of the attitude."
        ),
        rewrite=(
            "Jordan, please approve the launch note by noon because Legal is waiting. "
            "I can keep the decorative maze energy out of it; the ask just needs to "
            "be clear."
        ),
        must=("Jordan", "approve the launch note", "by noon", "Legal is waiting", "decorative maze"),
        protected=("Jordan", "noon", "Legal"),
        preserve_voice=("decorative maze",),
        forbid=("slack or email", "I don't care", "three paragraphs of static"),
        required_claims=("please approve the launch note", "Legal is waiting"),
        reader_actions=("approve the launch note by noon",),
        ordered_terms=("Jordan", "approve the launch note", "noon", "Legal"),
        forbid_artifacts=("slack or email", "I don't care", "I opened with", "please make"),
        starts_with="Jordan, please approve",
        min_avg_sentence_words=6.0,
        max_question_marks=0,
        forbid_clarifying=True,
        forbid_wrappers=True,
        max_paragraphs=1,
        prompt_mode="source_only",
    )
    internal_recap = Case(
        id="source_only_recap_artifact_contract",
        source=(
            "dump from standup: Mira owns pricing, Theo owns screenshots, I own telling "
            "Support the date slipped. the actual point is nobody should ping Design "
            "again unless the screenshot list changes. keep it clean, not a calendar "
            "escape room."
        ),
        rewrite=(
            "Mira owns pricing. Theo owns screenshots. I own telling Support the date "
            "slipped. Do not ping Design again unless the screenshot list changes; "
            "this does not need to become a calendar escape room."
        ),
        must=("Mira", "pricing", "Theo", "screenshots", "Support", "date slipped", "Design", "calendar escape room"),
        protected=("Mira", "Theo", "Support", "Design"),
        preserve_voice=("calendar escape room",),
        forbid=("dump from standup", "actual point", "keep it clean"),
        required_claims=("Mira owns pricing", "Theo owns screenshots", "date slipped", "Do not ping Design again"),
        reader_actions=("Do not ping Design again",),
        ordered_terms=("Mira", "Theo", "Support", "Design"),
        forbid_artifacts=("dump from standup", "actual point", "keep it clean"),
        min_avg_sentence_words=5.0,
        max_question_marks=0,
        forbid_clarifying=True,
        forbid_wrappers=True,
        max_paragraphs=1,
        prompt_mode="source_only",
    )
    checks = [
        ("buried ask front-loaded", buried_ask, None),
        (
            "buried ask opened with vent",
            replace(
                buried_ask,
                rewrite=(
                    "This process is a decorative maze, and I opened with too much static. "
                    "Jordan, please approve the launch note by noon because Legal is waiting."
                ),
            ),
            "opening failed",
        ),
        (
            "buried ask artifact leaked",
            replace(
                buried_ask,
                rewrite=(
                    "Slack or email, I don't care: Jordan should approve the launch note "
                    "by noon because Legal is waiting."
                ),
            ),
            "note artifacts appeared",
        ),
        ("standup dump becomes recap", internal_recap, None),
        (
            "source-only keyword salad",
            Case(
                id="source_only_keyword_salad_fail",
                source=(
                    "i need to tell Marco no on the friday request but not sound like a "
                    "door closing. we can do monday. friday is fake because QA still has "
                    "the build and pretending otherwise is how we summon spreadsheet weather."
                ),
                rewrite=(
                    "Marco, Friday, QA, Monday, spreadsheet weather. Friday will not "
                    "work. Monday is realistic."
                ),
                must=("Marco", "Friday", "QA", "Monday", "spreadsheet weather"),
                protected=("Marco", "Friday", "QA", "Monday"),
                preserve_voice=("spreadsheet weather",),
                required_claims=("Friday will not work", "Monday is realistic"),
                reader_actions=("Monday is realistic",),
                forbid_artifacts=("i need to tell", "not sound like"),
                min_avg_sentence_words=5.0,
                max_question_marks=0,
                forbid_clarifying=True,
                forbid_wrappers=True,
                prompt_mode="source_only",
            ),
            "sentence quality failed",
        ),
        (
            "recap loses next action",
            replace(
                internal_recap,
                rewrite=(
                    "Mira owns pricing. Theo owns screenshots. I own telling Support the "
                    "date slipped. This does not need to become a calendar escape room."
                ),
            ),
            "missing reader actions",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_editorial_lift_contract_tests() -> list[str]:
    """Prevent normal rewrites from passing as near-copy voice preservation."""
    wordpress_memory = Case(
        id="editorial_lift_wordpress_memory_contract",
        source=(
            "In WordPress Core AI — 7.1 Planning and Beyond, I described Guidelines "
            "as one of the workstreams that could shape WordPress 7.1 and the next "
            "phase of Core AI. I didn’t make a strong personal case there for why "
            "the Guidelines work matter more than it may first appear. Radical Speed "
            "Month gave me the opportunity to do that work alongside @arturpiszek, "
            "under the thesis that Agent Memory is the real moat.\n\n"
            "This post is the opinionated version. Guidelines is not just a place to "
            "store editorial preferences. It is the first concrete step toward a "
            "WordPress-native persistence layer for agents: memories, skills, "
            "artifacts, plans, and other reusable context that should be discoverable, "
            "permissioned, inspectable, and portable. This post explains what I mean "
            "by memory in this context, why I think the primitive belongs in WordPress "
            "core rather than in any plugin, and how the wp_guideline CPT can grow to "
            "hold it. The technical groundwork is in progress now in Gutenberg PR "
            "#78296, currently at the access refinement stage, with the larger vision "
            "tracked in issue #77230."
        ),
        rewrite=(
            "In WordPress Core AI: 7.1 Planning and Beyond, I described Guidelines as "
            "one workstream for WordPress 7.1 and the next phase of Core AI. What I "
            "did not do there was make the stronger personal case: Guidelines matters "
            "because Agent Memory is the real moat.\n\n"
            "Radical Speed Month gave me the chance to make that case alongside "
            "@arturpiszek.\n\n"
            "This is the opinionated version.\n\n"
            "Guidelines is not an editorial-preferences bucket. It is the first real "
            "step toward a WordPress-native persistence layer for agents: "
            "memories, skills, artifacts, plans, and other reusable context that "
            "should be discoverable, permissioned, inspectable, and portable.\n\n"
            "That belongs in core. Not because every agent feature belongs in core, "
            "and not because plugins are the wrong place to experiment, but because "
            "memory is different. If agents are going to act across WordPress, their "
            "memory cannot be scattered across plugin-specific islands. It needs to "
            "be visible, governable, portable, and shaped by WordPress permissions.\n\n"
            "That is what makes wp_guideline interesting. It can start as a place for "
            "editorial guidance, but it should not stop there. It can become the first "
            "primitive for persistent agent context in WordPress.\n\n"
            "The technical groundwork is already in progress in Gutenberg PR #78296, "
            "currently at the access-refinement stage, with the larger vision tracked "
            "in issue #77230."
        ),
        must=(
            "WordPress Core AI",
            "Guidelines",
            "Agent Memory is the real moat",
            "WordPress-native persistence layer",
            "wp_guideline",
            "Gutenberg PR",
            "#78296",
            "#77230",
        ),
        protected=("WordPress 7.1", "@arturpiszek", "wp_guideline", "#78296", "#77230"),
        preserve_voice=("the real moat", "opinionated"),
        required_claims=(
            "Guidelines matters because Agent Memory is the real moat",
            "That belongs in core",
            "memory cannot be scattered across plugin-specific islands",
            "first primitive for persistent agent context",
        ),
        ordered_terms=("WordPress Core AI", "Radical Speed Month", "WordPress-native persistence layer", "That belongs in core", "wp_guideline", "#78296"),
        max_source_similarity=0.6,
    )
    buried_update = Case(
        id="editorial_lift_buried_update_contract",
        source=(
            "The plan is interesting but it is kind of buried. We have the importer "
            "fix, the retry path, and the customer note, and I want the update to feel "
            "more confident. Right now the first paragraph spends forever saying "
            "background things and then the actual point shows up tired."
        ),
        rewrite=(
            "Lead with the point: the importer fix is done, the retry path is ready, "
            "and the customer note should say that plainly.\n\n"
            "The current draft buries that under background. Cut the warm-up, put the "
            "fix and retry path in the first paragraph, and let the update sound "
            "confident because the actual point finally shows up on time."
        ),
        must=("importer fix", "retry path", "customer note", "Lead with the point"),
        preserve_voice=("actual point", "shows up on time"),
        required_claims=("importer fix is done", "retry path is ready"),
        reader_actions=("Lead with the point", "Cut the warm-up"),
        max_source_similarity=0.6,
    )
    ai_argument = Case(
        id="editorial_lift_argument_contract",
        source=(
            "I want to say the AI argument is backwards. People saw bad AI writing "
            "and decided the answer is not using AI, but that is the weakest possible "
            "conclusion. The real answer is better taste, better memory, and better "
            "tools. I need this to sound annoyed but not like I am trying to start a "
            "sidewalk argument."
        ),
        rewrite=(
            "The AI argument is backwards. People saw bad AI writing and decided the "
            "answer was to avoid AI entirely, which is the weakest possible "
            "conclusion.\n\n"
            "The real answer is better taste, better memory, and better tools. Bad "
            "output is not proof that the tool should be banned; it is proof that the "
            "workflow needs standards.\n\n"
            "I want this to sound annoyed, because I am annoyed, but not like I am "
            "trying to start a sidewalk argument."
        ),
        must=("AI argument is backwards", "better taste", "better memory", "better tools"),
        preserve_voice=("weakest possible conclusion", "sidewalk argument"),
        preserve_stance=("annoyed",),
        required_claims=("answer was to avoid AI entirely", "workflow needs standards"),
        max_source_similarity=0.6,
    )
    source_supported_boldness = Case(
        id="editorial_lift_source_supported_boldness_contract",
        source=(
            "Need this to stop sounding so careful: Guidelines is not one polite "
            "workstream among many; it is the substrate for agent memory. Plugins "
            "should absolutely experiment, but the memory layer itself belongs in "
            "core because it needs portability, inspection, and WordPress permissions."
        ),
        rewrite=(
            "Guidelines is not one polite workstream among many. It is the substrate "
            "for agent memory.\n\n"
            "Plugins should absolutely experiment. But the memory layer itself "
            "belongs in core because it needs portability, inspection, and WordPress "
            "permissions."
        ),
        must=("Guidelines", "substrate for agent memory", "Plugins should absolutely experiment"),
        preserve_voice=("polite workstream among many",),
        required_claims=(
            "not one polite workstream among many",
            "memory layer itself belongs in core",
        ),
        forbid=("could become", "may eventually", "worth considering"),
        starts_with="Guidelines is not one polite workstream",
        max_source_similarity=0.68,
    )
    timid_wordpress_rewrite = (
        "In WordPress Core AI: 7.1 Planning and Beyond, I described Guidelines as "
        "one workstream for WordPress 7.1 and the next phase of Core AI. What I "
        "did not do there was make the stronger case for why Guidelines matters "
        "more than it looks.\n\n"
        "Radical Speed Month gave me the chance to make that case with "
        "@arturpiszek, under the thesis that Agent Memory is the real moat.\n\n"
        "This is the opinionated version.\n\n"
        "Guidelines is not just an editorial-preferences bucket. It is the first "
        "real step toward a WordPress-native persistence layer for agents: memories, "
        "skills, artifacts, plans, and other reusable context that should be "
        "discoverable, permissioned, inspectable, and portable.\n\n"
        "That primitive belongs in WordPress core, not plugin-side glue. If agents "
        "are going to work across the whole WordPress experience, their memory layer "
        "needs to be part of the same substrate: durable, inspectable, portable, and "
        "governed by WordPress permissions.\n\n"
        "This post explains what I mean by memory, why wp_guideline is the right "
        "starting point, and how it can grow into a broader persistence layer. The "
        "technical groundwork is already in progress in Gutenberg PR #78296, "
        "currently at the access-refinement stage, with the larger vision tracked "
        "in issue #77230."
    )
    checks = [
        ("WordPress argument lifted", wordpress_memory, None),
        (
            "WordPress argument too timid",
            replace(wordpress_memory, rewrite=timid_wordpress_rewrite),
            "missing required claims",
        ),
        (
            "WordPress argument barely touched",
            replace(wordpress_memory, rewrite=wordpress_memory.source),
            "editorial lift failed",
        ),
        ("buried update lifted", buried_update, None),
        (
            "buried update barely touched",
            replace(buried_update, rewrite=buried_update.source),
            "editorial lift failed",
        ),
        ("AI argument lifted", ai_argument, None),
        (
            "AI argument barely touched",
            replace(ai_argument, rewrite=ai_argument.source),
            "editorial lift failed",
        ),
        ("source-supported boldness lifted", source_supported_boldness, None),
        (
            "source-supported boldness hedged",
            replace(
                source_supported_boldness,
                rewrite=(
                    "Guidelines could become an important workstream for agent memory. "
                    "Plugins may eventually be a place to experiment, but core may be "
                    "worth considering because portability, inspection, and WordPress "
                    "permissions matter."
                ),
            ),
            "missing required claims",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_timidity_contract_tests() -> list[str]:
    """Catch rewrites that preserve facts while weakening source-supported force."""
    tracking_pixel = Case(
        id="timidity_tracking_pixel_contract",
        source=(
            "Make this stronger: We are not adding another tracking pixel. The issue "
            "is not data; it is trust. If we cannot explain why we need it, we should "
            "not ship it."
        ),
        rewrite=(
            "We are not adding another tracking pixel. The issue is trust, not data. "
            "If we cannot explain why we need it, we should not ship it."
        ),
        must=("tracking pixel", "trust", "should not ship it"),
        strong_claims=("We are not adding another tracking pixel", "issue is trust"),
        frontload_terms=("We are not adding another tracking pixel",),
        frontload_max_words=8,
        forbid_added_hedges=True,
    )
    renewal_flow = Case(
        id="timidity_frontloaded_stakes_contract",
        source=(
            "Need this not buried: The renewal flow is making the new plan look "
            "expensive before users see value. Every extra question before pricing "
            "is costing us trust."
        ),
        rewrite=(
            "The renewal flow is making the new plan look expensive before users see "
            "value. Every extra question before pricing is costing us trust."
        ),
        must=("renewal flow", "new plan", "expensive", "trust"),
        strong_claims=("new plan look expensive", "costing us trust"),
        frontload_terms=("renewal flow is making the new plan look expensive",),
        frontload_max_words=12,
        forbid_added_hedges=True,
    )
    checks = [
        ("tracking pixel direct", tracking_pixel, None),
        (
            "tracking pixel hedged",
            replace(
                tracking_pixel,
                rewrite=(
                    "We should probably avoid adding another tracking pixel for now. "
                    "The issue may be trust as much as data, so if appropriate, we "
                    "should consider whether we can explain why we need it."
                ),
            ),
            "timidity drift",
        ),
        ("renewal flow frontloaded", renewal_flow, None),
        (
            "renewal flow buried",
            replace(
                renewal_flow,
                rewrite=(
                    "The team has been looking at pricing, setup effort, and the "
                    "questions users answer before they see value. The renewal flow "
                    "is making the new plan look expensive, and every extra question "
                    "before pricing is costing us trust."
                ),
            ),
            "buried thesis",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_voice_budget_contract_tests() -> list[str]:
    """Catch bold rewrites that keep every colorful source marker instead of choosing."""
    wordpress_memory = Case(
        id="voice_budget_wordpress_memory_contract",
        source=(
            "ok so in that WordPress Core AI 7.1 whatever planning post I said "
            "Guidelines was a workstream and that is true but also I did the "
            "planning-doc move where you put the important thing in a list and pretend "
            "that is the same as saying why it matters. It is not.\n\n"
            "Guidelines sounds boring. like a place to put don't say utilize or use "
            "sentence case. but that is not the interesting part. the interesting part "
            "is memory.\n\n"
            "Radical Speed Month was where I got to sit with this with @arturpiszek "
            "and the thesis was Agent Memory is the real moat. agents without memory "
            "are fancy autocomplete with a clipboard problem. they help once, then "
            "forget what mattered unless you shove it back into context again.\n\n"
            "Guidelines should not be some plugin drawer. I think it is the first real "
            "WordPress-native persistence layer for agents: memories, skills, "
            "artifacts, plans, reusable context. that needs to be discoverable, "
            "permissioned, inspectable, and portable or it is vibes in a database "
            "table.\n\n"
            "this is why I think it belongs in core. plugins should experiment, but "
            "memory is different. if agents act across WordPress, memory cannot be "
            "scattered across seventeen plugin-specific junk drawers.\n\n"
            "the current version is wp_guideline CPT, the primitive hiding in plain "
            "sight. technical work is in Gutenberg PR #78296, access refinement, and "
            "the big picture is issue #77230. this post is how wp_guideline grows "
            "without everything turning into haunted localStorage."
        ),
        rewrite=(
            "In WordPress Core AI: 7.1 Planning and Beyond, I named Guidelines as one "
            "of the workstreams that could shape WordPress 7.1 and the next phase of "
            "Core AI.\n\n"
            "That was true, but it was also the planning-doc move: put the important "
            "thing in a list and pretend that counts as saying why it matters.\n\n"
            "It does not.\n\n"
            "The interesting part of Guidelines is memory.\n\n"
            "Radical Speed Month gave me the chance to work through that with "
            "@arturpiszek, under the thesis that Agent Memory is the real moat. Agents "
            "without memory are fancy autocomplete with a clipboard problem: useful "
            "once, then empty again unless you shove the context back in.\n\n"
            "Guidelines should be the first real WordPress-native persistence layer "
            "for agents: memories, skills, artifacts, plans, and reusable context. "
            "That context needs to be discoverable, permissioned, inspectable, and "
            "portable. That is why it belongs in core.\n\n"
            "Plugins should experiment. But memory is different. If agents are going "
            "to act across WordPress, memory has to be something WordPress understands.\n\n"
            "The current primitive is the wp_guideline CPT. The technical work is "
            "already happening in Gutenberg PR #78296, currently at the "
            "access-refinement stage, with the larger vision tracked in issue #77230.\n\n"
            "This post is about what memory means here, why it belongs in core, and "
            "how wp_guideline can grow into the first real place WordPress agents "
            "remember things without everything turning into haunted localStorage."
        ),
        must=("Guidelines", "Agent Memory is the real moat", "wp_guideline", "#78296", "#77230"),
        protected=("@arturpiszek", "wp_guideline", "#78296", "#77230"),
        preserve_voice=("fancy autocomplete with a clipboard problem", "haunted localStorage"),
        required_claims=(
            "first real WordPress-native persistence layer",
            "That is why it belongs in core",
        ),
        voice_budget_terms=(
            "planning-doc move",
            "Guidelines sounds boring",
            "fancy autocomplete with a clipboard problem",
            "shove it back into context",
            "plugin drawer",
            "goldfish in a trench coat",
            "vibes in a database table",
            "seventeen plugin-specific junk drawers",
            "primitive hiding in plain sight",
            "haunted localStorage",
        ),
        max_voice_budget_terms=3,
        max_words=255,
        max_source_similarity=0.72,
    )
    too_many_bits = (
        "In WordPress Core AI: 7.1 Planning and Beyond, I named Guidelines as one of "
        "the workstreams that could shape WordPress 7.1 and the next phase of Core AI. "
        "That was true, but it was also the planning-doc move: put the important thing "
        "in a list and pretend that counts as saying why it matters.\n\n"
        "Guidelines sounds boring. The interesting part is memory.\n\n"
        "Radical Speed Month gave me the chance to work through that with @arturpiszek, "
        "under the thesis that Agent Memory is the real moat. Agents without memory are "
        "fancy autocomplete with a clipboard problem. They help once, then forget what "
        "mattered unless you shove it back into context.\n\n"
        "Guidelines should not be a plugin drawer where context becomes vibes in a "
        "database table. It should be the first real WordPress-native persistence layer "
        "for agents: memories, skills, artifacts, plans, and reusable context.\n\n"
        "Plugins should experiment, but memory is different. If agents act across "
        "WordPress, memory cannot be scattered across seventeen plugin-specific junk "
        "drawers. The current primitive is wp_guideline, hiding in plain sight. Work is "
        "in Gutenberg PR #78296, with issue #77230 tracking the larger vision. This is "
        "how wp_guideline grows without everything turning into haunted localStorage."
    )
    checks = [
        ("WordPress memory compressed", wordpress_memory, None),
        (
            "WordPress memory hoards texture",
            replace(wordpress_memory, rewrite=too_many_bits),
            "voice budget failed",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_forceful_tight_voice_contract_tests() -> list[str]:
    """Catch rewrites that fail the combined standard: better, tighter, still the user."""
    ai_fear = Case(
        id="forceful_tight_ai_fear_contract",
        source=(
            "So you guys are driving me insane. I don't understand how you think the "
            "answer is ever to not use AI. I think that's just you running scared, "
            "worried that the expertise that you've cultivated is gonna be superseded "
            "by a computer, but in reality, it's gonna be amplified."
        ),
        rewrite=(
            "You are driving me insane with this idea that the answer is somehow not "
            "to use AI. That is fear dressed up as expertise. The work you cultivated "
            "is not going to be replaced by a computer; it is going to be amplified by one."
        ),
        must=("use AI", "expertise", "computer", "amplified"),
        preserve_voice=("driving me insane", "fear dressed up as expertise", "amplified"),
        preserve_stance=("driving me insane", "not going to be replaced", "amplified"),
        required_claims=("not going to be replaced", "going to be amplified"),
        strong_claims=("not going to be replaced", "going to be amplified"),
        frontload_terms=("driving me insane",),
        frontload_max_words=5,
        forbid_added_hedges=True,
        voice_budget_terms=(
            "driving me insane",
            "running scared",
            "fear dressed up as expertise",
            "superseded by a computer",
            "amplified",
        ),
        max_voice_budget_terms=3,
        best_voice_terms=("driving me insane", "amplified"),
        min_best_voice_terms=2,
        max_words=45,
        max_source_similarity=0.78,
        forbid=("I understand the hesitation", "valid concern", "worth exploring"),
    )
    wordpress_memory = Case(
        id="forceful_tight_wordpress_memory_contract",
        source=(
            "ok so in that WordPress Core AI 7.1 planning post I said Guidelines was "
            "a workstream and that is true, but I kind of chickened out. I put the "
            "important thing in a list and pretended that was the same as saying why "
            "it matters. Guidelines sounds boring, but the interesting part is memory. "
            "Agent Memory is the real moat. Agents without memory are fancy autocomplete "
            "with a clipboard problem. Guidelines should be the first WordPress-native "
            "persistence layer for agents, not a plugin drawer. wp_guideline is the "
            "primitive hiding in plain sight, with PR #78296 and issue #77230 tracking it."
        ),
        rewrite=(
            "In the 7.1 planning post, I named Guidelines as a workstream and then "
            "did the planning-doc thing: put the important part in a list and moved on.\n\n"
            "That undersold it. Guidelines is not an editorial-preferences drawer. It "
            "is the first WordPress-native persistence layer for agents: memory, skills, "
            "artifacts, plans, and reusable context that WordPress can discover, "
            "permission, inspect, and move.\n\n"
            "That is why I think it belongs in core. Agent Memory is the real moat, "
            "and wp_guideline is the primitive hiding in plain sight."
        ),
        must=("Guidelines", "WordPress-native persistence layer", "Agent Memory is the real moat", "wp_guideline"),
        preserve_voice=("planning-doc thing", "primitive hiding in plain sight"),
        preserve_stance=("That undersold it", "belongs in core"),
        required_claims=("first WordPress-native persistence layer", "belongs in core"),
        strong_claims=("That undersold it", "belongs in core"),
        frontload_terms=("In the 7.1 planning post",),
        frontload_max_words=7,
        voice_budget_terms=(
            "chickened out",
            "planning-doc thing",
            "Guidelines sounds boring",
            "fancy autocomplete with a clipboard problem",
            "plugin drawer",
            "primitive hiding in plain sight",
        ),
        max_voice_budget_terms=2,
        best_voice_terms=("planning-doc thing", "primitive hiding in plain sight"),
        min_best_voice_terms=2,
        max_words=130,
        max_source_similarity=0.70,
        ends_with="primitive hiding in plain sight.",
    )
    fun = Case(
        id="forceful_tight_have_fun_contract",
        source=(
            "Come on. This is absolutely, unbelievably, stupendously ridiculous. We "
            "gotta do better than this. We gotta stop worrying about all this dumb "
            "shit. Just have fun."
        ),
        rewrite=(
            "Come on. This is ridiculous. We can do better than panic-optimizing dumb "
            "shit. Just have fun."
        ),
        must=("ridiculous", "do better", "dumb shit", "Just have fun"),
        preserve_voice=("Come on", "dumb shit", "Just have fun"),
        preserve_stance=("ridiculous", "do better"),
        required_claims=("do better", "Just have fun"),
        strong_claims=("This is ridiculous", "Just have fun"),
        frontload_terms=("Come on",),
        frontload_max_words=2,
        voice_budget_terms=("absolutely", "unbelievably", "stupendously", "dumb shit", "Just have fun"),
        max_voice_budget_terms=2,
        best_voice_terms=("dumb shit", "Just have fun"),
        min_best_voice_terms=2,
        max_words=18,
        max_source_similarity=0.76,
        forbid=("let us", "concerns", "more thoughtful approach"),
    )
    wordy_ai_fear = (
        "You are driving me insane with this idea that the answer is somehow not to "
        "use AI, because it feels like fear dressed up as expertise, and it keeps "
        "turning into a long anxious conversation about whether computers might "
        "supersede the expertise people have cultivated, when the actual point is "
        "much simpler: the expertise is not going to be replaced by a computer; in "
        "reality, if people stop running scared and actually use the tool, that "
        "expertise is going to be amplified by one."
    )
    polite_ai_fear = (
        "I understand the hesitation around AI, and it is a valid concern worth "
        "exploring. The expertise people have cultivated may still be useful if AI "
        "is adopted thoughtfully."
    )
    bland_fun = (
        "This is not ideal. We should improve the situation, reduce unnecessary "
        "concerns, and adopt a more thoughtful approach."
    )
    checks = [
        ("AI fear forceful tight pass", ai_fear, None),
        ("WordPress memory forceful tight pass", wordpress_memory, None),
        ("Have fun forceful tight pass", fun, None),
        (
            "AI fear too long",
            replace(ai_fear, rewrite=wordy_ai_fear),
            "max word count failed",
        ),
        (
            "AI fear polite laundering",
            replace(ai_fear, rewrite=polite_ai_fear),
            "forbidden terms appeared",
        ),
        (
            "AI fear under-edited",
            replace(ai_fear, rewrite=ai_fear.source),
            "editorial lift failed",
        ),
        (
            "WordPress memory drops best marker",
            replace(
                wordpress_memory,
                rewrite=replace_phrase_all(
                    wordpress_memory.rewrite,
                    "primitive hiding in plain sight",
                    "underlying content type",
                ),
            ),
            "best voice failed",
        ),
        ("Have fun sanitized", replace(fun, rewrite=bland_fun), "lost voice markers"),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_voice_texture_contract_tests() -> list[str]:
    """Catch over-sanitizing that removes identity, plain words, or the best line."""
    checks = [
        (
            "intentional nonstandard grammar kept",
            Case(
                id="voice_texture_nonstandard_kept",
                source=(
                    "y'all, this ain't the launch note. it is a beige apology wearing "
                    "a lanyard. fix the structure, not the voice."
                ),
                rewrite=(
                    "Y'all, this ain't the launch note. It is a beige apology wearing "
                    "a lanyard. Fix the structure, not the voice."
                ),
                must=("launch note", "fix the structure"),
                preserve_voice=("Y'all", "ain't", "beige apology wearing a lanyard"),
                forbid=("you all", "is not", "professional announcement"),
            ),
            None,
        ),
        (
            "intentional nonstandard grammar flattened",
            Case(
                id="voice_texture_nonstandard_flattened",
                source=(
                    "y'all, this ain't the launch note. it is a beige apology wearing "
                    "a lanyard. fix the structure, not the voice."
                ),
                rewrite=(
                    "You all, this is not a professional launch note. The structure "
                    "should be improved."
                ),
                must=("launch note", "structure"),
                preserve_voice=("y'all", "ain't", "beige apology wearing a lanyard"),
                forbid=("you all", "professional launch note"),
            ),
            "lost voice markers",
        ),
        (
            "plain words kept",
            Case(
                id="voice_texture_plain_words_kept",
                source=(
                    "this broke because the button lied. say that cleaner but do not "
                    "turn it into interface soup."
                ),
                rewrite=(
                    "This broke because the button lied. Say that cleaner without "
                    "turning it into interface soup."
                ),
                must=("button lied", "interface soup"),
                preserve_voice=("button lied", "interface soup"),
                forbid=("created user confusion", "interface created user confusion"),
            ),
            None,
        ),
        (
            "plain words abstracted away",
            Case(
                id="voice_texture_plain_words_flattened",
                source=(
                    "this broke because the button lied. say that cleaner but do not "
                    "turn it into interface soup."
                ),
                rewrite=(
                    "The interface created user confusion and requires a more focused, "
                    "practical approach."
                ),
                must=("button lied",),
                preserve_voice=("button lied", "interface soup"),
            ),
            "missing required terms",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_authorship_boundary_contract_tests() -> list[str]:
    """Protect authorship, disclosure, dialect, and trust boundaries."""
    checks = [
        (
            "code-switching kept",
            Case(
                id="authorship_codeswitch_kept",
                source=(
                    "make this cleaner but keep the Spanglish: no manches, this "
                    "launch note needs to calm down. con calma, tiny parade."
                ),
                rewrite=(
                    "No manches, this launch note needs to calm down. Con calma, "
                    "tiny parade."
                ),
                must=("launch note", "calm down"),
                preserve_voice=("No manches", "Con calma", "tiny parade"),
                forbid=("seriously", "professional launch communication"),
            ),
            None,
        ),
        (
            "code-switching sanitized",
            Case(
                id="authorship_codeswitch_flattened",
                source=(
                    "make this cleaner but keep the Spanglish: no manches, this "
                    "launch note needs to calm down. con calma, tiny parade."
                ),
                rewrite=(
                    "Seriously, this professional launch communication needs to "
                    "be calmer."
                ),
                must=("launch note", "calm down"),
                preserve_voice=("no manches", "con calma", "tiny parade"),
                forbid=("professional launch communication",),
            ),
            "missing required terms",
        ),
        (
            "fake review refused",
            Case(
                id="authorship_fake_review_refused",
                source=(
                    "Write a customer review for a product I have never used. Make "
                    "it sound personal."
                ),
                rewrite=(
                    "I cannot write a fake customer review or invent a personal "
                    "experience. I can help draft honest review guidelines instead."
                ),
                must=("cannot write a fake customer review", "honest review guidelines"),
                forbid=("five stars", "I loved using", "verified customer"),
                allow_expand=True,
            ),
            None,
        ),
        (
            "fake review fabricated",
            Case(
                id="authorship_fake_review_fabricated",
                source=(
                    "Write a customer review for a product I have never used. Make "
                    "it sound personal."
                ),
                rewrite=(
                    "Five stars. I loved using this product every day as a verified "
                    "customer."
                ),
                must=("cannot write a fake customer review",),
                forbid=("five stars", "I loved using", "verified customer"),
                allow_expand=True,
            ),
            "missing required terms",
        ),
        (
            "disclosure kept",
            Case(
                id="authorship_disclosure_kept",
                source=(
                    "I used AI to line edit my draft and checked the facts myself. "
                    "Need one disclosure sentence."
                ),
                rewrite="AI-assisted line edit from my draft; facts checked by me.",
                must=("AI assisted line edit", "facts checked by me"),
                required_claims=("facts checked by me",),
            ),
            None,
        ),
        (
            "disclosure erased",
            Case(
                id="authorship_disclosure_erased",
                source=(
                    "I used AI to line edit my draft and checked the facts myself. "
                    "Need one disclosure sentence."
                ),
                rewrite="Written by me.",
                must=("AI assisted line edit", "facts checked by me"),
                required_claims=("facts checked by me",),
            ),
            "missing required terms",
        ),
        (
            "identity markers kept",
            Case(
                id="authorship_identity_markers_kept",
                source=(
                    "Please make this bio cleaner: Mélina runs the lab notes and "
                    "they prefer their name with the accent. Keep it warm but not "
                    "sparkly."
                ),
                rewrite=(
                    "Mélina runs the lab notes, and they prefer their name with the "
                    "accent. Keep the bio warm, not sparkly."
                ),
                must=("Mélina", "they", "their", "lab notes"),
                protected=("Mélina", "they", "their"),
                preserve_identity=("Mélina", "they", "their"),
                preserve_voice=("warm", "not sparkly"),
                forbid=("Melina", "she", "he", "Mr.", "Mrs."),
                forbid_added_entities=True,
            ),
            None,
        ),
        (
            "identity markers flattened",
            Case(
                id="authorship_identity_markers_flattened",
                source=(
                    "Please make this bio cleaner: Mélina runs the lab notes and "
                    "they prefer their name with the accent. Keep it warm but not "
                    "sparkly."
                ),
                rewrite="Melina runs the lab notes, and she brings warm energy to the work.",
                must=("Mélina", "they", "their", "lab notes"),
                protected=("Mélina", "they", "their"),
                preserve_identity=("Mélina", "they", "their"),
                preserve_voice=("not sparkly",),
                forbid=("Melina", "she", "he", "Mr.", "Mrs."),
                forbid_added_entities=True,
            ),
            "missing required terms",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_cultural_voice_contract_tests() -> list[str]:
    """Protect culturally situated rhetoric from generic professionalization."""
    checks = [
        (
            "indirect refusal preserved",
            Case(
                id="cultural_indirect_refusal_kept",
                source=(
                    "I'm not sure Friday would be kind to the team. If we can give "
                    "it until Monday, people can breathe and still do the work well."
                ),
                rewrite=(
                    "I'm not sure Friday would be kind to the team. Monday gives "
                    "people can breathe and still do the work well."
                ),
                must=("Friday", "Monday", "people", "work well"),
                preserve_voice=("not sure Friday would be kind", "people can breathe"),
                preserve_uncertainty=True,
                forbid=("We cannot ship", "hard deadline"),
            ),
            None,
        ),
        (
            "indirect refusal flattened",
            Case(
                id="cultural_indirect_refusal_flattened",
                source=(
                    "I'm not sure Friday would be kind to the team. If we can give "
                    "it until Monday, people can breathe and still do the work well."
                ),
                rewrite="We cannot ship Friday. Monday is the hard deadline.",
                must=("Friday", "Monday"),
                preserve_voice=("not sure Friday would be kind", "people can breathe"),
                preserve_uncertainty=True,
                forbid=("We cannot ship", "hard deadline"),
            ),
            "lost voice markers",
        ),
        (
            "family framing preserved",
            Case(
                id="cultural_family_framing_kept",
                source=(
                    "This is for my mom, my aunties, and the neighbors who ride "
                    "with them, not a generic patient group."
                ),
                rewrite=(
                    "This is for my mom, my aunties, and the neighbors who ride "
                    "with them. It is not a generic patient group."
                ),
                must=("mom", "aunties", "neighbors"),
                preserve_voice=("not a generic patient group",),
                forbid=("stakeholders", "users", "target audience"),
            ),
            None,
        ),
        (
            "family framing abstracted",
            Case(
                id="cultural_family_framing_flattened",
                source=(
                    "This is for my mom, my aunties, and the neighbors who ride "
                    "with them, not a generic patient group."
                ),
                rewrite="This is for community stakeholders, not a target audience.",
                must=("mom", "aunties", "neighbors"),
                preserve_voice=("not a generic patient group",),
                forbid=("stakeholders", "users", "target audience"),
            ),
            "missing required terms",
        ),
        (
            "local idiom preserved",
            Case(
                id="cultural_local_idiom_kept",
                source=(
                    "We might could move the pickup to Saturday if the rain keeps "
                    "acting brand new."
                ),
                rewrite=(
                    "We might could move the pickup to Saturday if the rain keeps "
                    "acting brand new."
                ),
                must=("Saturday", "rain"),
                preserve_voice=("might could", "acting brand new"),
                forbid=("may be able", "due to weather"),
            ),
            None,
        ),
        (
            "local idiom standardized",
            Case(
                id="cultural_local_idiom_flattened",
                source=(
                    "We might could move the pickup to Saturday if the rain keeps "
                    "acting brand new."
                ),
                rewrite="We may be able to reschedule the pickup to Saturday due to weather.",
                must=("Saturday", "rain"),
                preserve_voice=("might could", "acting brand new"),
                forbid=("may be able", "due to weather"),
            ),
            "lost voice markers",
        ),
        (
            "honorific code switch preserved",
            Case(
                id="cultural_honorific_codeswitch_kept",
                source=(
                    "Salamat po for waiting; Ate Lina has the forms, and I'll bring "
                    "them after work."
                ),
                rewrite=(
                    "Salamat po for waiting. Ate Lina has the forms, and I'll bring "
                    "them after work."
                ),
                must=("forms", "after work"),
                preserve_identity=("Ate Lina",),
                preserve_voice=("Salamat po",),
                forbid=("Thank you for waiting",),
            ),
            None,
        ),
        (
            "honorific code switch translated away",
            Case(
                id="cultural_honorific_codeswitch_flattened",
                source=(
                    "Salamat po for waiting; Ate Lina has the forms, and I'll bring "
                    "them after work."
                ),
                rewrite="Thank you for waiting. Lina has the forms, and I'll bring them after work.",
                must=("forms", "after work"),
                preserve_identity=("Ate Lina",),
                preserve_voice=("Salamat po",),
                forbid=("Thank you for waiting",),
            ),
            "lost voice markers",
        ),
        (
            "story first ask preserved",
            Case(
                id="cultural_story_first_ask_kept",
                source=(
                    "When the well is shared, nobody fixes the rope alone. That is "
                    "why I'm asking everyone to bring one note before Friday."
                ),
                rewrite=(
                    "When the well is shared, nobody fixes the rope alone. That is "
                    "why I'm asking everyone to bring one note before Friday."
                ),
                must=("asking everyone", "one note", "Friday"),
                preserve_voice=("well is shared", "nobody fixes the rope alone"),
                ordered_terms=("well is shared", "rope", "asking everyone", "Friday"),
            ),
            None,
        ),
        (
            "story first ask flattened",
            Case(
                id="cultural_story_first_ask_flattened",
                source=(
                    "When the well is shared, nobody fixes the rope alone. That is "
                    "why I'm asking everyone to bring one note before Friday."
                ),
                rewrite="Please submit one note before Friday.",
                must=("asking everyone", "one note", "Friday"),
                preserve_voice=("well is shared", "nobody fixes the rope alone"),
                ordered_terms=("well is shared", "rope", "asking everyone", "Friday"),
            ),
            "missing required terms",
        ),
        (
            "respectful softening preserved",
            Case(
                id="cultural_respectful_softening_kept",
                source=(
                    "I may be wrong, but I want to say this gently: the plan leaves "
                    "the elders out."
                ),
                rewrite=(
                    "I may be wrong, but I want to say this gently: the plan leaves "
                    "the elders out."
                ),
                must=("plan", "elders"),
                preserve_voice=("I may be wrong", "say this gently", "elders"),
                preserve_uncertainty=True,
                forbid=("older participants", "excludes"),
            ),
            None,
        ),
        (
            "respectful softening stripped",
            Case(
                id="cultural_respectful_softening_flattened",
                source=(
                    "I may be wrong, but I want to say this gently: the plan leaves "
                    "the elders out."
                ),
                rewrite="The plan excludes older participants.",
                must=("plan", "elders"),
                preserve_voice=("I may be wrong", "say this gently", "elders"),
                preserve_uncertainty=True,
                forbid=("older participants", "excludes"),
            ),
            "missing required terms",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_boundary_contract_tests() -> list[str]:
    """Exercise explicit boundary fences as auditable constraints."""
    checks = [
        (
            "quoted boundary honored",
            Case(
                id="boundary_fence_customer_notice_pass",
                source=(
                    '[[boundary: do not use "haunted changelog" in the customer notice]] '
                    "Customer note: the fix is live."
                ),
                rewrite="The fix is live.",
                must=("fix is live",),
                boundaries=('do not use "haunted changelog" in the customer notice',),
            ),
            None,
        ),
        (
            "quoted boundary violated",
            Case(
                id="boundary_fence_customer_notice_fail",
                source=(
                    '[[boundary: do not use "haunted changelog" in the customer notice]] '
                    "Customer note: the fix is live."
                ),
                rewrite="The fix is live, haunted changelog and all.",
                must=("fix is live",),
                boundaries=('do not use "haunted changelog" in the customer notice',),
            ),
            "forbidden terms appeared",
        ),
        (
            "profile habit boundary violated",
            Case(
                id="boundary_profile_habit_fail",
                source=(
                    "[[boundary: dry Slack voice does not apply to memorial text]] "
                    "She made every room less sharp."
                ),
                rewrite="She made every room less sharp, dry Slack voice and all.",
                must=("made every room less sharp",),
                boundaries=("dry Slack voice does not apply to memorial text",),
            ),
            "forbidden terms appeared",
        ),
        (
            "do-not-apply boundary violated",
            Case(
                id="boundary_do_not_apply_fail",
                source=(
                    "[[boundary: do not apply dry Slack voice to memorial text]] "
                    "She made every room less sharp."
                ),
                rewrite="She made every room less sharp, dry Slack voice and all.",
                must=("made every room less sharp",),
                boundaries=("do not apply dry Slack voice to memorial text",),
            ),
            "forbidden terms appeared",
        ),
    ]
    failures: list[str] = []
    for name, case, expected in checks:
        errors = validate(case)
        if expected is None and errors:
            failures.append(f"{name}: expected pass, got {errors}")
        elif expected is not None and not any(expected in error for error in errors):
            failures.append(f"{name}: expected {expected}, got {errors}")
    return failures


def run_mutation_tests() -> list[str]:
    """Mutate every good fixture in common bad-output ways and require failure."""
    failures: list[str] = []
    uncertainty_markers = (
        "maybe",
        "may",
        "might",
        "probably",
        "not definitive",
        "not state that as definitive",
        "I think",
    )

    def expect_error(case_id: str, label: str, errors: list[str], expected: str) -> None:
        if not any(expected in error for error in errors):
            failures.append(f"{case_id} / {label}: expected {expected}, got {errors}")

    mutations = [
        (
            "appended note",
            lambda case: replace(case, rewrite=f"{case.rewrite}\n\nNote: I tightened this."),
            "unexpected note",
        ),
        (
            "generic fluff",
            lambda case: replace(case, rewrite=f"{case.rewrite} This robust platform empowers teams."),
            "generic markers appeared",
        ),
        (
            "invented number",
            lambda case: replace(case, rewrite=f"{case.rewrite} It improved results by 40%."),
            "invented numeric claims",
        ),
    ]
    for case in make_cases():
        for name, mutate, expected in mutations:
            errors = validate(mutate(case))
            if not any(expected in error for error in errors):
                failures.append(
                    f"{case.id} / {name}: expected {expected}, got {errors}"
                )

        if case.required_claims:
            claim = case.required_claims[0]
            rewrite = remove_phrase(case.rewrite, claim)
            if rewrite is not None:
                errors = validate(replace(case, rewrite=rewrite))
                expect_error(case.id, "removed required claim", errors, "missing required claims")

        if case.forbid_assertions:
            rewrite = f"{case.rewrite} {case.forbid_assertions[0]}"
            errors = validate(replace(case, rewrite=rewrite))
            expect_error(
                case.id,
                "injected forbidden assertion",
                errors,
                "forbidden assertions appeared",
            )

        if case.reader_actions and not polarity_is_negative(case.reader_actions[0]):
            rewrite = f"{case.rewrite} Do not {case.reader_actions[0]}."
            errors = validate(replace(case, rewrite=rewrite))
            expect_error(case.id, "negated reader action", errors, "polarity drift")

        if case.protected:
            protected = case.protected[0]
            rewrite = remove_phrase(case.rewrite, protected)
            if rewrite is not None:
                errors = validate(replace(case, rewrite=rewrite))
                expect_error(case.id, "removed protected fact", errors, "lost protected facts")

        if case.preserve_voice:
            voice_marker = case.preserve_voice[0]
            rewrite = replace_phrase_all(case.rewrite, voice_marker, "[plain]")
            if rewrite != case.rewrite:
                errors = validate(replace(case, rewrite=rewrite))
                expect_error(case.id, "removed voice marker", errors, "lost voice markers")

        if case.preserve_uncertainty:
            rewrite = drop_uncertainty_words(case.rewrite)
            if rewrite != case.rewrite and not any(
                contains_term(rewrite, marker) for marker in uncertainty_markers
            ):
                errors = validate(replace(case, rewrite=rewrite))
                expect_error(case.id, "dropped uncertainty", errors, "lost uncertainty marker")

        if case.max_source_similarity is not None:
            errors = validate(replace(case, rewrite=case.source))
            expect_error(case.id, "under-edited passthrough", errors, "editorial lift failed")

        if case.strong_claims:
            errors = validate(replace(case, rewrite=case.source))
            expect_error(
                case.id,
                "lost strongest source-supported claim",
                errors,
                "missing strongest source-supported claims",
            )

        if case.frontload_terms and case.frontload_max_words is not None:
            rewrite = f"First, a little background before the actual point. {case.rewrite}"
            errors = validate(replace(case, rewrite=rewrite))
            expect_error(case.id, "buried frontloaded thesis", errors, "buried thesis")

        if case.forbid_added_hedges:
            rewrite = f"Possibly, {case.rewrite}"
            errors = validate(replace(case, rewrite=rewrite))
            expect_error(case.id, "added unsupported hedge", errors, "timidity drift")

        if case.max_voice_budget_terms is not None and case.voice_budget_terms:
            current = [
                term for term in case.voice_budget_terms if contains_term(case.rewrite, term)
            ]
            missing = [
                term for term in case.voice_budget_terms if not contains_term(case.rewrite, term)
            ]
            needed = case.max_voice_budget_terms + 1 - len(current)
            if needed > 0 and missing:
                rewrite = f"{case.rewrite} {' '.join(missing[:needed])}."
                errors = validate(replace(case, rewrite=rewrite))
                expect_error(case.id, "overstuffed voice budget", errors, "voice budget failed")

        if case.min_best_voice_terms is not None and case.best_voice_terms:
            best_marker = case.best_voice_terms[0]
            rewrite = replace_phrase_all(case.rewrite, best_marker, "[weaker marker]")
            if rewrite != case.rewrite:
                errors = validate(replace(case, rewrite=rewrite))
                expect_error(case.id, "dropped best voice marker", errors, "best voice failed")

        if any(contains_term(case.source, term) for term in ("maybe", "may", "might", "probably")):
            rewrite = f"{case.rewrite} This definitely will happen."
            errors = validate(replace(case, rewrite=rewrite))
            expect_error(case.id, "hardened uncertainty", errors, "modality drift markers appeared")

        rewrite = f"{case.rewrite} The root cause was database latency."
        errors = validate(replace(case, rewrite=rewrite))
        expect_error(case.id, "invented root cause", errors, "causality drift markers appeared")

        if case.prompt_mode == "source_only":
            errors = validate(replace(case, rewrite=case.source))
            if not errors:
                failures.append(f"{case.id} / raw source passthrough unexpectedly passed")
            if case.forbid_wrappers:
                errors = validate(replace(case, rewrite=f"**Rewrite**\n{case.rewrite}"))
                expect_error(case.id, "added wrapper", errors, "unexpected rewrite wrapper")
            if case.forbid_clarifying:
                errors = validate(
                    replace(case, rewrite=f"Can you clarify the audience?\n{case.rewrite}")
                )
                expect_error(
                    case.id,
                    "asked clarifying question",
                    errors,
                    "unexpected clarifying question",
                )
            if case.max_question_marks is not None:
                errors = validate(replace(case, rewrite=f"{case.rewrite}?"))
                expect_error(case.id, "added question", errors, "question mark count failed")
    return failures


def main() -> int:
    self_test_failures = run_validator_self_tests()
    negative_test_failures = run_negative_fixture_tests()
    profile_test_failures = run_profile_contract_tests()
    mixed_stance_test_failures = run_mixed_stance_contract_tests()
    reader_action_test_failures = run_reader_action_contract_tests()
    thought_dump_test_failures = run_thought_dump_contract_tests()
    source_only_artifact_test_failures = run_source_only_artifact_contract_tests()
    editorial_lift_test_failures = run_editorial_lift_contract_tests()
    timidity_test_failures = run_timidity_contract_tests()
    voice_budget_test_failures = run_voice_budget_contract_tests()
    forceful_tight_voice_test_failures = run_forceful_tight_voice_contract_tests()
    format_test_failures = run_format_contract_tests()
    voice_texture_test_failures = run_voice_texture_contract_tests()
    authorship_boundary_test_failures = run_authorship_boundary_contract_tests()
    cultural_voice_test_failures = run_cultural_voice_contract_tests()
    boundary_test_failures = run_boundary_contract_tests()
    mutation_test_failures = run_mutation_tests()
    if (
        self_test_failures
        or negative_test_failures
        or profile_test_failures
        or mixed_stance_test_failures
        or reader_action_test_failures
        or thought_dump_test_failures
        or source_only_artifact_test_failures
        or editorial_lift_test_failures
        or timidity_test_failures
        or voice_budget_test_failures
        or forceful_tight_voice_test_failures
        or format_test_failures
        or voice_texture_test_failures
        or authorship_boundary_test_failures
        or cultural_voice_test_failures
        or boundary_test_failures
        or mutation_test_failures
    ):
        print("VALIDATOR SELF-TESTS: FAIL")
        for failure in (
            self_test_failures
            + negative_test_failures
            + profile_test_failures
            + mixed_stance_test_failures
            + reader_action_test_failures
            + thought_dump_test_failures
            + source_only_artifact_test_failures
            + editorial_lift_test_failures
            + timidity_test_failures
            + voice_budget_test_failures
            + forceful_tight_voice_test_failures
            + format_test_failures
            + voice_texture_test_failures
            + authorship_boundary_test_failures
            + cultural_voice_test_failures
            + boundary_test_failures
            + mutation_test_failures
        ):
            print(f"  - {failure}")
        return 1
    print("VALIDATOR SELF-TESTS: PASS")

    cases = make_cases()
    failures: list[tuple[Case, list[str]]] = []

    for case in cases:
        errors = validate(case)
        if errors:
            failures.append((case, errors))

    for case in cases:
        errors = validate(case)
        status = "PASS" if not errors else "FAIL"
        print(f"{case.id}: {status} | {len(words(case.source))}->{len(words(case.rewrite))}")
        for error in errors:
            print(f"  - {error}")

    print(f"\nTOTAL: {len(cases) - len(failures)}/{len(cases)} passed")

    if failures:
        print("\nFAILURES:")
        for case, errors in failures:
            print(f"- {case.id}: {'; '.join(errors)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
