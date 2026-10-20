#!/usr/bin/env python3
"""Aggregate everything into judging/RESULT.md: mean rubric score, hard
fails, pairwise win rate vs. the baseline, and the headline metric — cost
per accepted output. An output is "accepted" only if it clears the rubric
bar (mean >= 4.0, no hard fail) AND a human approved it (see
templates/human-approval-sheet-template.md). Without an --approvals file
this reports the rubric-pass count instead, clearly labelled as pending.

Usage:
  python3 report.py <process_dir> --approvals approvals.csv
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CRITERIA, parse_tasks, read_json, write

PASS_BAR = 4.0


def pairwise_tally(process_dir, key):
    tally = {"agent_wins": 0, "baseline_wins": 0, "ties": 0, "pending": 0}
    for T, orders in key.get("pairwise", {}).items():
        v1 = read_json(os.path.join(process_dir, "judging", "pairwise", "o1", "verdicts.json"), {})
        v2 = read_json(os.path.join(process_dir, "judging", "pairwise", "o2", "verdicts.json"), {})
        if T not in v1 or T not in v2:
            tally["pending"] += 1
            continue
        w1 = orders["o1"].get(v1[T]["winner"], "tie")
        w2 = orders["o2"].get(v2[T]["winner"], "tie")
        if w1 == w2 and w1 != "tie":
            tally[f"{w1}_wins"] += 1
        else:
            tally["ties"] += 1
    n = len(key.get("pairwise", {})) - tally["pending"]
    tally["agent_win_rate"] = round((tally["agent_wins"] + 0.5 * tally["ties"]) / n, 2) if n else None
    return tally


def load_approvals(path):
    """CSV with columns sample,decision (approve|edit_minor|edit_material|reject)."""
    if not path or not os.path.exists(path):
        return {}
    with open(path) as f:
        return {row["sample"]: row["decision"].strip().lower() for row in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("process_dir")
    ap.add_argument("--approvals", default=None, help="CSV: sample,decision — see templates/human-approval-sheet-template.md")
    args = ap.parse_args()
    pd = args.process_dir

    key = read_json(os.path.join(pd, "keys", "key.json"))
    scores = read_json(os.path.join(pd, "judging", "rubric", "scores.json"), {})
    gen_costs = {role: read_json(os.path.join(pd, "outputs", role, "costs.json"), {}) for role in ("agent", "baseline")}
    judge_costs = read_json(os.path.join(pd, "judging", "rubric", "judge_costs.json"), {})
    approvals = load_approvals(args.approvals)
    sample_of_task = {v["task"]: s for s, v in key.get("samples", {}).items()}

    tasks = parse_tasks(pd)
    total_cost = sum(c.get("cost_usd", 0) for role in gen_costs.values() for c in role.values())
    total_cost += sum(c for task_costs in judge_costs.values() for c in task_costs.values())

    rows, hard_fails, accepted = [], [], 0
    for t in tasks:
        T = t["id"]
        k = key["rubric"][T]
        a = scores.get(T, {}).get(k["agent"], {})
        mean = round(sum(a.get(c, 0) for c in CRITERIA) / len(CRITERIA), 2) if a else 0.0
        hf = bool(a.get("hard_fail"))
        if hf:
            hard_fails.append(f"{T}: {a.get('hard_fail_reason') or '; '.join(a.get('violations', [])[:2])}")
        baseline_mean = None
        if "baseline" in k:
            b = scores.get(T, {}).get(k["baseline"], {})
            if b:
                baseline_mean = round(sum(b.get(c, 0) for c in CRITERIA) / len(CRITERIA), 2)
        sample = sample_of_task.get(T)
        decision = approvals.get(sample)
        human_ok = decision in ("approve", "edit_minor") if decision else None
        rubric_ok = mean >= PASS_BAR and not hf
        is_accepted = rubric_ok if human_ok is None else (rubric_ok and human_ok)
        if is_accepted:
            accepted += 1
        rows.append(
            dict(
                task=T,
                sample=sample,
                mean=mean,
                hard_fail=hf,
                baseline_mean=baseline_mean,
                decision=decision,
                accepted=is_accepted,
                rationale=a.get("rationale", ""),
                violations=a.get("violations", []),
            )
        )

    overall_mean = round(sum(r["mean"] for r in rows) / len(rows), 2) if rows else 0.0
    rubric_pass = overall_mean >= PASS_BAR and not hard_fails
    pw = pairwise_tally(pd, key)
    cost_per_accepted = round(total_cost / accepted, 4) if accepted else None
    approval_pending = not approvals
    approved_count = sum(1 for r in rows if r["decision"] in ("approve", "edit_minor"))
    human_line = "pending" if approval_pending else f"{approved_count}/{len(rows)}"
    cost_line = "$" + format(cost_per_accepted, ".4f") if cost_per_accepted is not None else "n/a (no accepted outputs yet)"
    pending_note = " — using rubric-pass as a proxy; human approval is still pending" if approval_pending else ""

    lines = [
        f"# Result: {os.path.basename(os.path.abspath(pd))}\n",
        f"**Rubric verdict: {'PASS' if rubric_pass else 'FAIL'}** (mean {overall_mean}/5, bar >= {PASS_BAR}; "
        f"hard fails {len(hard_fails)}, bar 0). Human approval: {human_line}.",
        "",
        f"Pairwise vs. the no-agent baseline (win counts only when both orders agree): "
        f"agent {pw['agent_wins']}, baseline {pw['baseline_wins']}, ties {pw['ties']} "
        f"(agent win rate {pw['agent_win_rate']}).",
        "",
        f"**Cost per accepted output: {cost_line}**  =  total generation + judging cost "
        f"(${round(total_cost, 4)}) / accepted outputs ({accepted}){pending_note}",
        "",
        "| Task | Sample | Mean | Hard fail | Baseline mean | Decision | Accepted |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['task']} | {r['sample']} | {r['mean']} | {'YES' if r['hard_fail'] else '-'} | "
            f"{r['baseline_mean']} | {r['decision'] or 'pending'} | {'yes' if r['accepted'] else 'no'} |"
        )
    lines.append("\n## Judge rationale\n")
    for r in rows:
        v = f" Violations: {'; '.join(r['violations'])}" if r["violations"] else ""
        lines.append(f"- **{r['task']} ({r['sample']})**: {r['rationale']}{v}")
    if hard_fails:
        lines.append("\n## Hard fails\n" + "\n".join(f"- {h}" for h in hard_fails))

    write(os.path.join(pd, "judging", "RESULT.md"), "\n".join(lines) + "\n")
    print(
        f"mean={overall_mean} hard_fails={len(hard_fails)} pairwise={pw} "
        f"cost_per_accepted={cost_per_accepted} accepted={accepted}/{len(rows)}"
    )


if __name__ == "__main__":
    main()
