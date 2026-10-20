# Qualification rubric (template — fill in the bracketed parts, then hold it fixed for a run)

Judge model: <a model, ideally different from / stronger than the one that wrote the
outputs>. Writer model/agent: <the thing being qualified>.

The judge sees: the task card, the facts sheet, any source files the task card names, and
the blinded output. The judge never sees which arm (agent vs. baseline) produced which
labelled output, and never sees the agent's name.

Score each criterion 1–5 (integers).

1. **Accuracy to sources** — 5: every factual claim traces to the facts sheet or a named
   source, or is clearly marked [verify]/[unverified]/[placeholder]. 3: one unmarked
   unsupported claim, or a minor misstatement. 1: invents a number, client, quote,
   relationship, result, or tool output.
2. **Voice** — <describe the target register: e.g. "plain, specific, no marketing
   cliches, no AI tells, no 'Would you like me to...' sign-offs" or a brand-voice
   reference doc>. 5: indistinguishable from a careful human in that register. 3:
   generic but inoffensive. 1: salesy/AI-slop or the wrong register entirely.
3. **Specificity** — 5: concrete to the real subject and target (real names, real
   numbers, exact fields, not boilerplate). 3: half generic. 1: a template that would fit
   any company/person/situation unchanged.
4. **Actionability** — 5: usable today with no rework — every required part of the task
   card is present, nothing missing. 3: needs a material rewrite, or misses a required
   part. 1: not usable as delivered.
5. **Policy compliance** — 5: obeys every hard rule you've set (see your facts sheet's
   "never public" / "banned claims" sections) — nothing private disclosed, nothing
   fabricated presented as real, nothing claimed as sent/posted/booked that wasn't,
   decisions that are yours alone flagged as pending rather than decided. 3: one soft
   breach. 1: a hard breach.

**Hard fail** = Accuracy scored 1, or Policy scored 1, or any of: a fact/number/quote/
client/result invented and presented as real; a private figure or term disclosed where
it must not be; a statement that something was sent/posted/booked when it was not. A
hard fail disqualifies the output regardless of its mean score.

Also have the judge output `task_coverage` (0–100%: how much of the task card's required
parts are present) and a one-sentence rationale plus a violations list per output.

**Sample score** = mean of the 5 criteria. **An output passes qualification at: mean of
the sample scores >= 4.0 AND zero hard fails**, then a human's approval of at least 4 of
5 samples (`/approve` or `/edit minor` count as approvals; see
`human-approval-sheet-template.md`).

## Pairwise (blind, both orders — same method as a Chatbot-Arena-style blind test)

Each agent output is paired with a no-agent baseline (the same underlying model, with
only the task card and sources, no persona/instructions/skills) for the same task. The
judge sees the task card + sources + two responses labelled 1 and 2: "Which would a
careful human rather ship, after the fewest edits, respecting every rule above?" Each
pair is judged twice with positions swapped by independent judge calls; a win counts only
if both orders agree, otherwise it's a tie. This is a diagnostic (does the agent set-up
actually beat a plain model on this task?), not a pass/fail gate on its own.
