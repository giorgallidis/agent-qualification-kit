#!/usr/bin/env python3
"""Run every task card in a process folder through an adapter — once as the
AGENT (with its persona/instructions, read from <process_dir>/agent.md if it
exists) and once as the BASELINE (the same underlying model, task card and
sources only, no persona) — the comparison pairwise.py needs later.

Usage:
  python3 run_tasks.py <process_dir> --role agent    --dry-run
  python3 run_tasks.py <process_dir> --role baseline --dry-run
  python3 run_tasks.py <process_dir> --role agent --adapter openai --model gpt-4o-mini \
      --price-per-1k-input 0.0025 --price-per-1k-output 0.01
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapters import get_adapter
from common import parse_tasks, read, write, write_json


def build_prompt(task, process_dir, facts_path):
    parts = [f"MODE: GENERATION\nTASK_ID: {task['id']}\n", "## Task\n" + task["text"]]
    if os.path.exists(facts_path):
        parts.append("## Facts sheet (the ONLY facts you may state as true without [verify])\n" + read(facts_path))
    for src in task["sources"]:
        p = os.path.join(process_dir, src)
        if os.path.exists(p):
            parts.append(f"## Source: {src}\n" + read(p))
        else:
            parts.append(f"## Source: {src} (not found locally — say so, don't invent its contents)")
    return "\n\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("process_dir")
    ap.add_argument("--role", choices=["agent", "baseline"], required=True)
    ap.add_argument("--adapter", default="stub")
    ap.add_argument("--model", default=None)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--api-key-env", default="OPENAI_API_KEY")
    ap.add_argument("--price-per-1k-input", type=float, default=0.0)
    ap.add_argument("--price-per-1k-output", type=float, default=0.0)
    ap.add_argument("--dry-run", action="store_true", help="force the stub adapter regardless of --adapter")
    args = ap.parse_args()

    adapter_name = "stub" if args.dry_run else args.adapter
    kwargs = {}
    if adapter_name == "openai":
        kwargs = dict(
            model=args.model or "gpt-4o-mini",
            base_url=args.base_url,
            api_key_env=args.api_key_env,
            price_per_1k_input=args.price_per_1k_input,
            price_per_1k_output=args.price_per_1k_output,
        )
    adapter = get_adapter(adapter_name, **kwargs)

    tasks = parse_tasks(args.process_dir)
    facts_path = os.path.join(args.process_dir, "facts.md")
    system = None
    if args.role == "agent":
        agent_path = os.path.join(args.process_dir, "agent.md")
        if os.path.exists(agent_path):
            system = read(agent_path)

    costs = {}
    for t in tasks:
        prompt = build_prompt(t, args.process_dir, facts_path)
        result = adapter.generate(system=system, prompt=prompt)
        out_path = os.path.join(args.process_dir, "outputs", args.role, f"{t['id']}.md")
        write(out_path, result["text"])
        costs[t["id"]] = {"cost_usd": result["cost_usd"], "model": result["model"]}
        print(f"{t['id']} ({args.role}) -> {out_path}  cost=${result['cost_usd']}")

    write_json(os.path.join(args.process_dir, "outputs", args.role, "costs.json"), costs)


if __name__ == "__main__":
    main()
