# Contributing

This kit is a method first, code second. The most useful contributions are often a
rubric criterion, a worked example, or an adapter — not necessarily a big PR.

## Propose a rubric criterion

Open a discussion or PR against `templates/rubric-template.md` with:
- the criterion name and what it catches that the existing five (accuracy, voice,
  specificity, actionability, policy) don't;
- 1–5 anchors written the same way the others are (what a 5 looks like, what a 1 looks
  like, what counts as a hard fail if anything does);
- one real (or realistic) example output at each end of the scale.

Keep criteria orthogonal — if two criteria usually move together, they're probably one
criterion wearing two names.

## Propose an adapter

`harness/adapters.py` has one job per adapter: turn `(system, prompt)` into
`{"text", "cost_usd", "model"}`. To add one:
- subclass `Adapter` and implement `generate()`;
- read any credentials from an environment variable the caller names (never hard-code a
  key, never accept one as a CLI argument);
- compute `cost_usd` from the provider's own published pricing, passed in as an argument
  — don't guess a number and hard-code it;
- register it in `get_adapter()`;
- a PR with a new adapter should also include a short note on how you tested it (a
  `--dry-run` style smoke test is fine if you can't share real API output).

## Propose an example

A new worked example under `examples/` is welcome, especially for a different kind of
task (classification, coding, voice support, research) than `lead-research-agent`. It
should be fully fictional or fully anonymized — no real company facts, client names, or
prices, per the sanitization rule this kit itself was built under. Commit the dry-run
output so a reader can see the result without running anything.

## Discussions welcome

Questions about how to adapt the method to a different domain, disagreements with a
rubric anchor, or "does this hard-fail rule make sense" are all good discussion topics,
not just issues. Open one before a big PR if you're not sure the approach fits.
