#!/usr/bin/env python3
"""Blind pairwise judging: agent vs. a no-agent baseline, in both orders,
same judge model, asked "which would you ship, after the fewest edits". A
win counts only when both orders agree — otherwise it's a tie. This catches
a judge that just prefers whichever response comes first.

Writes judging/pairwise/{o1,o2}/verdicts.json.

Usage:
  python3 pairwise.py <process_dir> --dry-run
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapters import get_adapter
from common import parse_tasks, read, write_json

QUESTION = (
    "Which response would a careful human rather ship, after the fewest edits, respecting "
    'every rule in the rubric and facts sheet? Return ONLY a JSON object '
    '{"winner": "1" or "2", "reason": "one sentence"}.'
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("process_dir")
    ap.add_argument("--rubric", default=None)
    ap.add_argument("--adapter", default="stub")
    ap.add_argument("--model", default=None)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--api-key-env", default="OPENAI_API_KEY")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    adapter_name = "stub" if args.dry_run else args.adapter
    kwargs = (
        dict(model=args.model or "gpt-4o-mini", base_url=args.base_url, api_key_env=args.api_key_env)
        if adapter_name == "openai"
        else {}
    )
    adapter = get_adapter(adapter_name, **kwargs)

    rubric_path = args.rubric or os.path.join(args.process_dir, "rubric.md")
    rubric_text = read(rubric_path)
    tasks = {t["id"]: t for t in parse_tasks(args.process_dir)}

    for o in ("o1", "o2"):
        d = os.path.join(args.process_dir, "judging", "pairwise", o)
        if not os.path.isdir(d):
            continue
        verdicts = {}
        for fn in sorted(f for f in os.listdir(d) if f.endswith(".md")):
            T = fn[:-3]
            pair_text = read(os.path.join(d, fn))
            prompt = f"{pair_text}\n\n## Rubric and facts\n{rubric_text}\n\n## Task card\n{tasks[T]['text']}\n\n{QUESTION}"
            result = adapter.generate(system=None, prompt=prompt)
            try:
                parsed = json.loads(result["text"])
            except json.JSONDecodeError:
                parsed = {"winner": "tie", "reason": "judge did not return valid JSON"}
            verdicts[T] = parsed
        write_json(os.path.join(d, "verdicts.json"), verdicts)
        print(o, "judged", len(verdicts), "pairs")


if __name__ == "__main__":
    main()
