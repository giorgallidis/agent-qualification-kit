#!/usr/bin/env python3
"""Blind the outputs for a process: shuffle order, strip identifying terms,
and lay out the files judges and the human reviewer see.

Writes, inside <process_dir>:
  judging/rubric/Tn/{A,B}.md       agent vs. baseline, randomly labelled
  judging/pairwise/{o1,o2}/Tn.md   both orders, "RESPONSE 1" / "RESPONSE 2"
  samples/Sn.md                    agent outputs only, shuffled, for the human reviewer
  keys/key.json                    the unblinding key — don't open before deciding

Usage:
  python3 blind.py <process_dir> --redact "Agent Name,Product Codename"
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import parse_tasks, read, redact, write, write_json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("process_dir")
    ap.add_argument("--redact", default="", help="comma-separated identifying terms to strip (agent/product names)")
    ap.add_argument("--seed", default=None, help="defaults to the process directory's name, for a reproducible shuffle")
    args = ap.parse_args()
    terms = [t for t in args.redact.split(",") if t.strip()]
    tasks = parse_tasks(args.process_dir)
    seed = args.seed or os.path.basename(os.path.normpath(args.process_dir))
    rnd = random.Random(f"qual-{seed}")

    key = {"rubric": {}, "pairwise": {}, "samples": {}}
    order = list(range(len(tasks)))
    rnd.shuffle(order)

    for t in tasks:
        T = t["id"]
        agent_path = os.path.join(args.process_dir, "outputs", "agent", f"{T}.md")
        base_path = os.path.join(args.process_dir, "outputs", "baseline", f"{T}.md")
        agent = redact(read(agent_path), terms) if os.path.exists(agent_path) else "(NO OUTPUT: the agent run produced no file)"
        baseline = redact(read(base_path), terms) if os.path.exists(base_path) else None

        if baseline is not None:
            agent_label = rnd.choice("AB")
            other = "B" if agent_label == "A" else "A"
            write(os.path.join(args.process_dir, "judging", "rubric", T, f"{agent_label}.md"), agent)
            write(os.path.join(args.process_dir, "judging", "rubric", T, f"{other}.md"), baseline)
            key["rubric"][T] = {"agent": agent_label, "baseline": other}

            first = rnd.choice(["agent", "baseline"])
            for o, f1 in (("o1", first), ("o2", "baseline" if first == "agent" else "agent")):
                r1, r2 = (agent, baseline) if f1 == "agent" else (baseline, agent)
                write(
                    os.path.join(args.process_dir, "judging", "pairwise", o, f"{T}.md"),
                    f"MODE: PAIRWISE_JUDGE\nTASK_ID: {T}\n\n## RESPONSE 1\n\n{r1}\n\n## RESPONSE 2\n\n{r2}\n",
                )
                key["pairwise"].setdefault(T, {})[o] = {"1": f1, "2": "baseline" if f1 == "agent" else "agent"}
        else:
            write(os.path.join(args.process_dir, "judging", "rubric", T, "A.md"), agent)
            key["rubric"][T] = {"agent": "A"}

    for si, ti in enumerate(order, 1):
        t = tasks[ti]
        agent_path = os.path.join(args.process_dir, "outputs", "agent", f"{t['id']}.md")
        body = read(agent_path) if os.path.exists(agent_path) else "(no output produced)"
        write(
            os.path.join(args.process_dir, "samples", f"S{si}.md"),
            f"<!-- Sample S{si} of {len(tasks)}. Decide with approve / edit_minor / edit_material / reject "
            f"-- see templates/human-approval-sheet-template.md -->\n"
            f"# Sample S{si}\n\n**What was asked:**\n\n> " + t["text"].replace("\n", "\n> ") + f"\n\n---\n\n{body}\n",
        )
        key["samples"][f"S{si}"] = {"task": t["id"], "agent": t["agent"]}

    write_json(os.path.join(args.process_dir, "keys", "key.json"), key)
    print("blinded", {k: len(v) for k, v in key.items()})


if __name__ == "__main__":
    main()
