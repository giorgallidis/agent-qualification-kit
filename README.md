# Agent Qualification Kit

A blind-test method for deciding whether an AI agent is ready to run unattended — before
you let it, not after it breaks something. Open source, MIT licensed, forkable.

## What it is

A small protocol plus a provider-agnostic harness that qualifies one agent (or one model,
or one prompt) on real tasks, scored blind, against a plain-model baseline, with a human
as the final gate. It does not care which model or framework runs your agent — the
harness talks to models through a pluggable adapter, so you can point it at any
OpenAI-compatible endpoint, or try the whole thing offline with the built-in stub.

## Why

Agents that look good in a demo fail in production. A demo is one cherry-picked run, seen
by the person who wrote the prompt, who already knows what "good" looks like. That is the
least reliable way to decide whether to trust an agent with real work. Measure before you
trust it — on tasks that look like the job, scored by someone (or something) that does not
know which answer came from the agent.

## The method, in 6 steps

1. **Write task cards from real work.** Not toy prompts — the actual thing the agent will
   be asked to do, with the real constraints (length limits, required sections, things it
   must never claim). See `templates/task-card-template.md`.
2. **Run the tasks twice.** Once through the agent (its real persona/instructions), once
   through the same underlying model with only the task card and sources — no persona, no
   skills. This is the baseline every agent has to beat.
3. **Blind the outputs.** Shuffle the order, strip anything that reveals which arm wrote
   which answer (agent name, product name, anything self-identifying), and lay both arms
   out for judging without labels.
4. **Score blind with a rubric judge.** A model — ideally a different, stronger model than
   the one that wrote the answers — scores each output 1–5 against a fixed rubric (accuracy
   to sources, voice, specificity, actionability, policy compliance), with hard-fail rules
   for the things that are never acceptable regardless of score. See
   `templates/rubric-template.md`.
5. **Judge pairwise, both orders.** The same judge is asked "which would you ship, after the
   fewest edits" for the agent's answer vs. the baseline's, once with the agent first and
   once with the baseline first. A win only counts if both orders agree — otherwise it's a
   tie. This catches a judge that just prefers whichever answer appears first.
6. **A human approves at least 4 of 5 samples.** No agent goes live on rubric score alone.
   A person reads the blinded outputs and decides, per sample: approve / edit minor / edit
   material / reject. See `templates/human-approval-sheet-template.md`.

An agent "passes" when: rubric mean ≥ 4.0/5 across all criteria, zero hard fails, **and** a
human approves (or accepts with a minor edit) at least 80% of the samples (4 of 5, or the
equivalent at whatever sample size you use).

## Quick start (no API key needed — under a minute)

```bash
python3 -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt                       # only needed for the OpenAI-compatible adapter

cd examples/lead-research-agent
python3 ../../harness/run_tasks.py . --role agent    --dry-run
python3 ../../harness/run_tasks.py . --role baseline --dry-run
python3 ../../harness/blind.py      . --redact "Lead Research Agent"
python3 ../../harness/judge.py      . --dry-run
python3 ../../harness/pairwise.py   . --dry-run
python3 ../../harness/report.py     . --approvals approvals.csv
cat judging/RESULT.md
```

`--dry-run` forces the offline stub adapter — no network, no API key, deterministic output —
so you can see the whole pipeline (task → run → blind → judge → pairwise → report) end to
end before spending a cent. `examples/lead-research-agent/` has this already run and
committed, so you can read the result without running anything.

To qualify your own agent: copy `examples/lead-research-agent/` as a starting layout, replace
`tasks.md`, `facts.md`, `agent.md` and `rubric.md` with your own (start from `templates/`),
and swap `--dry-run` for `--adapter openai --model <your model>` once you're ready to spend
real tokens. Keys are read from environment variables only — never pass one on the command
line.

## The headline metric: cost per accepted output

```
cost per accepted output = (total generation cost + total judging cost) / number of accepted outputs
```

An output is **accepted** only if it clears both gates: the rubric bar (mean ≥ 4.0, no hard
fail) *and* a human approved it (or accepted it with a minor edit). This is the number that
actually matters for deciding whether to run an agent unattended — not "how cheap is one
API call," but "how much does it cost me, all in, including judging, for every output I'd
actually be willing to ship." A cheap agent that needs a rewrite every time is not cheap.
`report.py` computes this automatically and writes it into `judging/RESULT.md`.

## Repo layout

```
templates/    task-card, rubric, facts-sheet and human-approval-sheet templates — start here
harness/      the CLI: run_tasks.py, blind.py, judge.py, pairwise.py, report.py, adapters.py
examples/     one fully worked fictional example, dry-run outputs committed
```

## Hard-fail rules (summary — customize in your own rubric.md)

A hard fail means the output is disqualified regardless of its numeric score: inventing a
fact, number, quote, client or result and presenting it as real; stating something was sent,
posted or booked when it was not; breaking a policy rule you've marked as non-negotiable
(e.g. naming a client without consent, quoting a price that should stay private). Hard fails
are binary and are reported separately from the mean score — a high mean does not offset one.

## Contributing

See `CONTRIBUTING.md` — new rubric criteria, new adapters, and new worked examples are all
welcome as PRs/discussions. See `CHANGELOG.md` for version history. Licensed MIT —
see `LICENSE`.
