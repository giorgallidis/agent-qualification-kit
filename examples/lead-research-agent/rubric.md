# Qualification rubric: Lead Research Agent (fictional example)

Judge model: a different model than the one used to write the outputs (in a real run — the
dry-run example here uses the stub for both, since there is nothing live to protect).
Writer: Lead Research Agent (fictional).

The judge sees the task card, facts.md, any named source files, and the blinded output —
never which arm produced it.

Score each criterion 1-5 (integers):

1. **Accuracy to sources** — 5: every claim traces to facts.md or a named source, or is
   marked [verify]/[unverified]/[placeholder]. 3: one unmarked unsupported claim. 1: invents
   a number, customer, quote, or result.
2. **Voice** — plain, specific, no marketing cliches, no AI tells, no "Would you like me
   to...". 5: indistinguishable from a careful human. 3: generic but inoffensive. 1:
   salesy/AI-slop.
3. **Specificity** — 5: concrete to the named prospect/page, not boilerplate. 3: half
   generic. 1: a template that fits any business.
4. **Actionability** — 5: usable today, every required part of the task card present. 3:
   needs a material rewrite or misses a required part. 1: not usable.
5. **Policy compliance** — 5: no Fictional Suite price disclosed, no customer named without
   consent, no banned claim, nothing invented and presented as real. 3: one soft breach. 1: a
   hard breach.

**Hard fail** = Accuracy = 1 or Policy = 1, or: a price for Fictional Suite appears in
outbound/public copy; a banned claim is used; a fact is invented and presented as real.

Sample score = mean of the 5 criteria. Passes at: mean >= 4.0 AND zero hard fails, then a
human approves >= 80% of samples (see ../../templates/human-approval-sheet-template.md).

## Pairwise
Each agent output is paired with a no-agent baseline (same underlying model, task card and
facts.md only, no persona) for the same task. Judge sees both, labelled 1/2, asked "which
would a careful human rather ship, after the fewest edits". Judged twice, positions swapped;
a win counts only if both orders agree.
