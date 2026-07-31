# Starter fleet example

A complete, validator-passing ops-repo `fleet/` directory for the express
bootstrap: one nightly **code digest** (Gmail draft summarizing commits
across your repos) plus the **watchdog** that audits it every morning.
Read-only everywhere; the only thing it ever produces is drafts in your own
Gmail.

This is what the skill adapts during an express bootstrap — but you can
also copy it by hand into your own ops repo and edit:

1. Replace every `YOURNAME`, `your-repo`, and `you@example.com`.
2. Set `timezone` to your IANA zone and recompute BOTH UTC crons for your
   local times (digest 11:50pm local, watchdog 8:00am local). Keep the
   `cadence_local` fields updated to your local times too — the validator
   checks them against the UTC crons (routine and watchdog alike) and
   catches conversion mistakes and later DST drift. This example uses
   America/Phoenix, which has no DST, so it validates on any date.
3. Check yourself: `python3 fleet/validate_fleet.py fleet/fleet.json`
   (copy the validator in from `scripts/validate_fleet.py`).
4. The empty `trigger_id` fields are correct at this stage — they get
   filled in as each routine is deployed.

To grow beyond the starter: `templates/` has fill-in prompts for the other
archetypes (alert responder, maintainer, watcher, drafter, reminder), and
`references/routine-catalog.md` explains when each is worth having.
