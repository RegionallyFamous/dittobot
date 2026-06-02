#!/usr/bin/env python3
"""Optional live model smoke test for Dittobot.

This script sends a small sample of regression cases to the OpenAI Responses
API and validates the model output with regression_100.py's deterministic
checks. It is intentionally opt-in: no API key, no network call, no failure.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from regression_100 import Case, make_cases, validate, words


DEFAULT_MODEL = "gpt-5.2"
DEFAULT_API_URL = "https://api.openai.com/v1/responses"


def redact_secrets(text: str) -> str:
    return re.sub(r"sk-[A-Za-z0-9_*.-]+", "sk-...REDACTED", text)


def output_text(response: dict) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"].strip()

    parts: list[str] = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and "text" in content:
                parts.append(content["text"])
    return "\n".join(parts).strip()


def user_prompt(case: Case) -> str:
    lines = [
        "Use Dittobot to revise this source text.",
        f"Case: {case.id}",
        "Return only the rewritten text unless a note is explicitly allowed.",
        "",
        "Requirements:",
    ]
    if case.must:
        lines.append(f"- Preserve these required terms or ideas: {', '.join(case.must)}")
    if case.protected:
        lines.append(f"- Do not change these protected facts: {', '.join(case.protected)}")
    if case.forbid:
        lines.append(f"- Avoid these forbidden terms: {', '.join(case.forbid)}")
    if case.preserve_voice:
        lines.append(f"- Preserve these voice markers: {', '.join(case.preserve_voice)}")
    if case.exact_words is not None:
        lines.append(f"- Use exactly {case.exact_words} words.")
    if case.no_dash:
        lines.append("- Use no dashes of any kind.")
    if not case.allow_note:
        lines.append("- Do not include notes, preambles, or rationale.")

    lines.extend(["", "Source:", case.source])
    return "\n".join(lines)


def call_responses_api(
    *,
    api_key: str,
    api_url: str,
    model: str,
    skill_text: str,
    prompt: str,
    timeout: int,
    max_output_tokens: int,
) -> str:
    payload = {
        "model": model,
        "max_output_tokens": max_output_tokens,
        "input": [
            {"role": "developer", "content": skill_text},
            {"role": "user", "content": prompt},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    text = output_text(body)
    if not text:
        raise RuntimeError(f"Response did not include output text: {body}")
    return text


def selected_cases(case_ids: list[str], limit: int) -> list[Case]:
    cases = make_cases()
    if case_ids:
        by_id = {case.id: case for case in cases}
        missing = [case_id for case_id in case_ids if case_id not in by_id]
        if missing:
            raise SystemExit(f"Unknown case id(s): {', '.join(missing)}")
        return [by_id[case_id] for case_id in case_ids]
    return cases[:limit]


def validate_api_url(api_url: str, allow_custom: bool) -> None:
    if api_url == DEFAULT_API_URL:
        return
    parsed = urlparse(api_url)
    if parsed.scheme != "https":
        raise SystemExit("Custom API URLs must use https.")
    if not allow_custom:
        raise SystemExit(
            "Refusing to send OPENAI_API_KEY to a custom API URL. "
            "Pass --allow-custom-api-url if you trust this endpoint."
        )


def validate_save_path(path: str | None) -> None:
    if not path:
        return
    if not path.endswith(".local.jsonl"):
        raise SystemExit("--save-jsonl path must end with .local.jsonl so git ignores it.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10, help="Number of cases to run.")
    parser.add_argument("--case", action="append", default=[], help="Specific case id to run.")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--api-url", default=os.environ.get("OPENAI_API_URL", DEFAULT_API_URL))
    parser.add_argument(
        "--allow-custom-api-url",
        action="store_true",
        help="Allow sending the bearer token to --api-url / OPENAI_API_URL.",
    )
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--max-output-tokens", type=int, default=500)
    parser.add_argument("--save-jsonl", help="Optional local transcript path. Do not commit it.")
    parser.add_argument(
        "--require-key",
        action="store_true",
        help="Exit nonzero instead of skipping when OPENAI_API_KEY is missing.",
    )
    args = parser.parse_args()

    validate_api_url(args.api_url, args.allow_custom_api_url)
    validate_save_path(args.save_jsonl)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("SKIP: OPENAI_API_KEY is not set; live eval is optional.")
        return 1 if args.require_key else 0

    repo = Path(__file__).resolve().parents[1]
    skill_text = (repo / "SKILL.md").read_text(encoding="utf-8")
    cases = selected_cases(args.case, args.limit)

    save_file = None
    if args.save_jsonl:
        save_file = Path(args.save_jsonl).open("a", encoding="utf-8")

    failures: list[tuple[str, list[str]]] = []
    try:
        for case in cases:
            try:
                text = call_responses_api(
                    api_key=api_key,
                    api_url=args.api_url,
                    model=args.model,
                    skill_text=skill_text,
                    prompt=user_prompt(case),
                    timeout=args.timeout,
                    max_output_tokens=args.max_output_tokens,
                )
            except urllib.error.HTTPError as exc:
                detail = redact_secrets(exc.read().decode("utf-8", errors="replace"))
                message = f"HTTP {exc.code}: {detail or exc.reason}"
                failures.append((case.id, [f"API error: {message}"]))
                print(f"{case.id}: FAIL | API error: {message}")
                continue
            except (urllib.error.URLError, RuntimeError) as exc:
                failures.append((case.id, [f"API error: {exc}"]))
                print(f"{case.id}: FAIL | API error: {exc}")
                continue

            live_case = dataclasses.replace(case, rewrite=text)
            errors = validate(live_case)
            status = "PASS" if not errors else "FAIL"
            print(f"{case.id}: {status} | live words={len(words(text))}")
            for error in errors:
                print(f"  - {error}")
            if save_file:
                save_file.write(
                    json.dumps(
                        {
                            "case": case.id,
                            "model": args.model,
                            "source": case.source,
                            "output": text,
                            "errors": errors,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            if errors:
                failures.append((case.id, errors))
    finally:
        if save_file:
            save_file.close()

    print(f"\nLIVE TOTAL: {len(cases) - len(failures)}/{len(cases)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
