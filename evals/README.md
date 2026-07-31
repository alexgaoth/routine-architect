# Evals

Manual test scenarios for the skill, per Anthropic's skill-authoring best
practice (3+ scenarios, tested across models before sharing). There is no
built-in runner: give each scenario's `query` to a fresh Claude Code session
with the skill installed (mock or sandbox the routine API), and judge
against `expected_behavior`.

- `scenario-1-bootstrap.json` — cold start, no fleet exists
- `scenario-2-reconcile-drift.json` — fleet exists, drift injected
- `scenario-3-adopt-unmanaged.json` — pre-existing routines to adopt
- `fixtures/valid/`, `fixtures/broken/` — manifests for
  `scripts/validate_fleet.py` (the broken one must FAIL with ≥6 errors)

Also test the validator directly:

```bash
python3 scripts/validate_fleet.py evals/fixtures/valid/fleet/fleet.json   # PASS
python3 scripts/validate_fleet.py evals/fixtures/broken/fleet/fleet.json  # FAIL
```

Re-run scenarios when the manifest schema, reconcile algorithm, or watchdog
template changes — not only when SKILL.md wording changes.
