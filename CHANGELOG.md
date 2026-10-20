# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - 2026-10-20

### Added
- Initial public release: the blind qualification method (task cards → run agent + baseline
  → blind → rubric judge → blind pairwise vs. baseline, both orders → human approval →
  report) extracted and generalized from an internal agent-fleet qualification process.
- `harness/`: provider-agnostic Python CLI (`run_tasks.py`, `blind.py`, `judge.py`,
  `pairwise.py`, `report.py`) with a stub adapter (offline, deterministic, for `--dry-run`)
  and an OpenAI-compatible adapter (keys from environment variables only).
- `templates/`: task-card, rubric, facts-sheet and human-approval-sheet templates.
- `examples/lead-research-agent/`: one fully worked fictional example with committed
  dry-run output, demonstrating the full pipeline including the cost-per-accepted-output
  metric.
- `CONTRIBUTING.md`, `LICENSE` (MIT).
