---
name: routine-architect
description: Designs, deploys, and maintains a complete fleet of scheduled cloud agents (routines) — notification digests, code maintainers, alert responders, research watchers — governed by a committed fleet manifest and audited by a watchdog routine that reads that manifest at runtime. Use when the user wants to set up routines, automate code monitoring or maintenance on a schedule, get emailed/notified about their repos, audit or fix an existing routine fleet, or build automation beyond what plain cron jobs can do.
---

# Routine Architect

Take a user from "I want automation" to a running, self-monitoring,
re-runnable fleet of cloud routines. A routine is a scheduled, fully isolated
cloud Claude session: unlike a cron job it can read code, exercise judgment,
fix bugs, run tests, search email, and write reports — but it starts with
**zero context** every run, so everything it needs must be in its prompt or in
a repo it clones.

This skill is **convergent**: the first run bootstraps the whole system; every
later run reconciles reality against the manifest and repairs drift. Never
treat a rerun as a fresh install.

## The four laws

1. **The manifest is the source of truth.** One designated git repo (the
   "ops repo") holds `fleet/fleet.json` and `fleet/prompts/*.md` describing
   every routine: schedule, prompt file, artifact contract, status. Routines
   are created *from* the manifest and changes are committed *to* it in the
   same sitting. A routine that isn't in the manifest is an orphan; a manifest
   entry that isn't deployed is a gap. Both are defects the reconcile step
   must surface. Schema and algorithm:
   [references/fleet-manifest.md](references/fleet-manifest.md).
2. **Every routine leaves an artifact.** A Gmail draft, pushed commits, an
   appended log section — declared in the manifest as a machine-checkable
   contract. If a run can legitimately do nothing, the contract says so
   (`may_be_absent_when_idle`) and names the input to cross-check. A routine
   whose liveness cannot be verified from artifacts must not be created.
3. **Notify, don't act, at the boundary.** Default outbound communication to
   drafts and dry-runs. The user promotes a routine to sending/publishing only
   after watching it behave.
4. **The watchdog reads the manifest at runtime.** It clones the ops repo each
   run and audits whatever `fleet.json` says — so the audit list can never go
   stale. The only watchdog config changes a fleet change can require are
   mechanical (adding a new repo to its git sources); the reconcile algorithm
   checks for this.

## Workflow

First, determine the mode — do not ask the user, detect it:
list deployed routines (in Claude Code: the bundled `schedule` skill /
`RemoteTrigger` tool, `action: "list"`). If a routine named
`Fleet watchdog (routine-architect)` exists, this is a managed fleet →
**Reconcile mode**. Otherwise → **Bootstrap mode**. (Existing unmanaged
routines in bootstrap mode get adopted in step B4.)

If the skill was invoked with arguments, they select a fast path (mode
detection still runs first, and a fast path on an unmanaged fleet falls
back to bootstrap):

- `quickstart` — express bootstrap: the starter fleet (digest + watchdog)
  with every choice defaulted per
  [references/defaults.md](references/defaults.md), asking only the four
  questions listed there
- `reconcile` — run the full reconcile, no other changes requested
- `audit` — reconcile steps R1–R3 only: report the diff and health history,
  change nothing
- `add <archetype>` — bootstrap steps B3–B7 for one new routine on the
  existing fleet (design, author from the template, validate, deploy,
  reconcile watchdog sources)

### Bootstrap mode — first run

```
Bootstrap Progress:
- [ ] B1. Interview the user
- [ ] B2. Choose the ops repo
- [ ] B3. Design the fleet on paper; get agreement
- [ ] B4. Write manifest + prompt files; adopt any pre-existing routines
- [ ] B5. Commit and push the ops repo
- [ ] B6. Deploy routines from the manifest, one at a time
- [ ] B7. Deploy the watchdog LAST
- [ ] B8. Hand off
```

**B1 Interview.** First decide the depth. **Express** (default for
newcomers, vague requests like "set me up", or the `quickstart` argument):
ask only the four questions in
[references/defaults.md](references/defaults.md) and default everything
else from its table. Express still runs B2–B4, just collapsed: B2 is
answered by question two; B3 is presenting the starter composition for a
yes/no; B4 adapts `examples/starter-fleet/` instead of blank templates —
and its validator run is never skipped. B5 onward is identical in both
paths. **Full** (the user names
specific alerts to act on, wants write-access routines, or has detailed
requirements): establish which repos matter and what "wrong" looks like for
each; how they want to be reached
([references/notifications.md](references/notifications.md)); what an agent
may do unattended vs. what needs review; their timezone and when reports
should arrive. In both paths, verify which MCP connectors are connected
before designing (a routine can only use connectors the user has).

**B2 Ops repo.** Pick with the user one git repo the routines can push to —
an existing infra repo or a new dedicated one. The manifest, prompt files,
and append-only logs live here. It must be reachable from cloud sessions.

**B3 Design.** Pick 2–5 archetypes from
[references/routine-catalog.md](references/routine-catalog.md). One routine,
one job. For each, one line: *name — cadence — inputs — artifact contract*.
Stagger schedules so the watchdog runs after everything else's daily window.
Show the table; get agreement before writing prompts.

**B4 Author.** Write `fleet/fleet.json` and one `fleet/prompts/<slug>.md` per
routine per [references/fleet-manifest.md](references/fleet-manifest.md).
Start each prompt from its archetype's fill-in template in `templates/`
(placeholders in `{{...}}`), tightening per
[references/prompt-patterns.md](references/prompt-patterns.md). If unmanaged
routines already exist, ask which to adopt (add manifest entries mirroring
their live config) and record the rest under `unmanaged_acknowledged` so the
watchdog doesn't flag them. Then run `python3 scripts/validate_fleet.py
fleet/fleet.json` (from the skill directory, against the ops repo checkout)
and fix every error before proceeding.

**B5 Commit.** Copy `scripts/validate_fleet.py` into the ops repo as
`fleet/validate_fleet.py` so the fleet stays self-checking without this
skill installed. Commit and push the ops repo *before* deploying — the
watchdog clones it fresh and must see the manifest.

**B6 Deploy.** Create each routine from its manifest entry
([references/api-reference.md](references/api-reference.md) for body shape,
cron rules, connector wiring, least-privilege tools). After each create,
write the returned `trigger_id` back into the manifest. Confirm each parsed
next-run time with the user in their timezone.

**B7 Watchdog.** Deploy from the template in
[references/watchdog.md](references/watchdog.md), with the ops repo plus
every repo named in any artifact contract as git sources. Record its
`trigger_id` in the manifest's `watchdog` block. Commit and push the
manifest update (it now contains all trigger_ids).

**B8 Hand off.** Summary table: every routine, schedule in the user's
timezone, artifact, management URL, plus the validator's usage estimate
(runs/month per routine and fleet total) so the user understands what the
cadence costs before living with it. State plainly: rerun this skill to
add, change, pause, or audit routines — never hand-edit a deployed routine
without also updating the manifest; deletion is manual on the routines page.

### Reconcile mode — every later run

```
Reconcile Progress:
- [ ] R1. Locate ops repo via the watchdog's config; read manifest
- [ ] R2. Read recent watchdog reports (fleet health history)
- [ ] R3. Diff manifest vs deployed: gaps, orphans, drift, retired
- [ ] R4. Apply the user's intent (add/change/pause/retire routines)
- [ ] R5. Converge: fix diffs, update watchdog sources if repos changed
- [ ] R6. Commit and push manifest; verify trigger_ids all recorded
- [ ] R7. Report fleet state
```

The full diff algorithm, each category's remedy, and the self-discovery rule
(watchdog config → ops repo → manifest) are specified rigorously in
[references/fleet-manifest.md](references/fleet-manifest.md). Follow it
exactly; do not improvise a partial reconcile. Even when the user asked only
for one small change, run the full diff first — the change lands on top of a
verified-consistent fleet, and drift gets caught while someone is watching.

## Reference files

- [references/fleet-manifest.md](references/fleet-manifest.md) — manifest
  schema, artifact-contract types, reconcile algorithm, lifecycle rules
- [references/routine-catalog.md](references/routine-catalog.md) — seven
  routine archetypes with cadences, tool lists, artifact contracts
- [references/prompt-patterns.md](references/prompt-patterns.md) — writing
  zero-context cloud-agent prompts, with an annotated example
- [references/watchdog.md](references/watchdog.md) — the manifest-driven
  overseer: design rules and fill-in template
- [references/notifications.md](references/notifications.md) — email, SMS,
  push, and calendar delivery channels and when to use each
- [references/defaults.md](references/defaults.md) — the express bootstrap:
  four questions, everything else defaulted
- [references/api-reference.md](references/api-reference.md) — routine API
  body shape, cron rules, connectors, environments, models

Also bundled: `examples/starter-fleet/` — a complete validator-passing ops
repo `fleet/` to adapt (express path starts here); `templates/` — fill-in
prompt templates, one per archetype (the watchdog's template is in its
reference file); `scripts/validate_fleet.py` — deterministic manifest
validator, run at B4/R1/R6; `evals/` — test scenarios for maintainers of
this skill (not used at runtime).

## Scope notes

- Routines run in the cloud: no local files, no local env vars, no gitignored
  `.env`. A routine can *detect* a missing production credential but only a
  human can supply it. Never let a routine fabricate or guess credentials.
- Sub-hourly polling or reacting to local machine state needs a local
  scheduled task or in-session loop, not a routine — say so rather than
  forcing a routine.
- If the user's platform has no routine/scheduler mechanism at all, stop and
  tell them; this skill designs fleets, it does not emulate a scheduler.
