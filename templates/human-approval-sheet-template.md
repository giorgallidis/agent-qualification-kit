# Human approval sheet (template)

The rubric and pairwise steps are diagnostic. Nothing goes live on their score alone — a
person has to read the actual blinded outputs and decide.

## How to review (about 15 minutes for 5 samples)
1. Open `samples/S1.md` ... `samples/Sn.md`. Each one starts with what was asked, then the
   output exactly as written. The order is shuffled and scores are hidden so they don't
   anchor your read.
2. Decide each one as if you were about to send/post/use it as is.
3. Record one decision per sample, in a CSV (`sample,decision`) that `harness/report.py
   --approvals` reads:
   - `approve` — ship as is.
   - `edit_minor` — a small fix you'd make yourself; counts as an approval.
   - `edit_material` — needs a real rewrite; does NOT count as an approval.
   - `reject` — not usable.

   ```csv
   sample,decision
   S1,approve
   S2,edit_minor
   S3,approve
   S4,reject
   S5,approve
   ```

## The gate
A process/agent qualifies when **all** of:
- rubric mean >= 4.0/5 (from `judging/scores.json` via `report.py`);
- zero hard fails;
- a human approved (`approve` or `edit_minor`) at least 80% of the samples (4 of 5, or the
  equivalent proportion at whatever sample size you used).

Until all three are true, the role stays on "draft only" — it does not get to send, post,
or act without review. `report.py` also uses your approval decisions to compute the
headline metric, cost per accepted output: only a sample that clears *both* the rubric bar
and your approval counts as "accepted."
