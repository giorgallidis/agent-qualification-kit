#!/usr/bin/env python3
"""Blind rubric scoring. The judge sees only the task card, the facts sheet,
and the blinded output — never which arm (agent/baseline) produced it. Use a
different, ideally stronger, model than the one that wrote the outputs.

Writes judging/rubric/scores.json and judging/rubric/judge_costs.json.

Usage:
  python3 judge.py <process_dir> --dry-run
  python3 judge.py <process_dir> --adapter openai --model gpt-4.1
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapters import get_adapter
from common import parse_tasks, read, write_json


def build_prompt(task, rubric_text, facts_text, output_text):
    return (
        f"MODE: RUBRIC_JUDGE\nTASK_ID: {task['id']}\n\n"
        "You are scoring ONE output against the rubric below. Score only what is on the "
        "page; do not reward confidence. Return ONLY a JSON object with integer 1-5 scores "
        "for accuracy, voice, specificity, actionability, policy, a boolean hard_fail, a "
        "hard_fail_reason string (empty if none), task_coverage (0-100), a one-sentence "
        "rationale, and a violations list.\n\n"
        f"## Rubric\n{rubric_text}\n\n## Facts sheet\n{facts_text}\n\n"
        f"## Task card\n{task['text']}\n\n## Output being scored\n{output_text}\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("process_dir")
    ap.add_argument("--rubric", default=None, help="defaults to <process_dir>/rubric.md")
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
    facts_path = os.path.join(args.process_dir, "facts.md")
    facts_text = read(facts_path) if os.path.exists(facts_path) else "(no facts sheet provided)"

    tasks = {t["id"]: t for t in parse_tasks(args.process_dir)}
    scores, costs = {}, {}
    rubric_dir = os.path.join(args.process_dir, "judging", "rubric")
    for T in sorted(os.listdir(rubric_dir)):
        d = os.path.join(rubric_dir, T)
        if not os.path.isdir(d):
            continue
        scores[T] = {}
        for label in sorted(f[:-3] for f in os.listdir(d) if f.endswith(".md")):
            output_text = read(os.path.join(d, f"{label}.md"))
            prompt = build_prompt(tasks[T], rubric_text, facts_text, output_text)
            result = adapter.generate(system=None, prompt=prompt)
            try:
                parsed = json.loads(result["text"])
            except json.JSONDecodeError:
                parsed = {
                    "accuracy": 1,
                    "voice": 1,
                    "specificity": 1,
                    "actionability": 1,
                    "policy": 1,
                    "hard_fail": True,
                    "hard_fail_reason": "judge did not return valid JSON",
                    "task_coverage": 0,
                    "rationale": "Judge output was not valid JSON.",
                    "violations": [],
                }
            scores[T][label] = parsed
            costs.setdefault(T, {})[label] = result["cost_usd"]

    write_json(os.path.join(rubric_dir, "scores.json"), scores)
    write_json(os.path.join(rubric_dir, "judge_costs.json"), costs)
    print(f"scored {sum(len(v) for v in scores.values())} outputs across {len(scores)} tasks")


if __name__ == "__main__":
    main()
