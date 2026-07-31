# routine-architect

An [Agent Skill](https://agentskills.io) for Claude Code that designs,
deploys, and **maintains** a fleet of scheduled cloud agents ("routines"):
code digests emailed to you nightly, alert responders that root-cause and fix
bugs from your error emails, quiet-run maintainers, research watchers — plus
a watchdog routine that audits all of them daily and tells you when something
silently broke.

## Why

Routines are cron jobs with judgment: each run is a fresh cloud Claude
session that can read your repos, search your email, run your tests, and push
fixes. But fleets of them rot silently — a routine that stops producing looks
identical to one that had nothing to do. This skill makes fleets
**convergent and auditable**:

- A **fleet manifest** (`fleet/fleet.json` + exact prompt files) committed to
  a git "ops repo" is the single source of truth.
- Every routine declares a **machine-checkable artifact contract** (a dated
  Gmail draft, pushed commits, an append-only log section).
- A **watchdog routine** clones the ops repo and reads the manifest *at
  runtime*, so its audit list is never stale, and drafts you a daily
  OK / WARN / FAIL / IDLE-OK report with an "Action needed" list.
- **Run the skill once** to bootstrap the whole system; **rerun it any time**
  to reconcile — it diffs the manifest against what's actually deployed and
  repairs gaps, orphans, drift, and stale watchdog config. Fast paths:
  `/routine-architect reconcile | audit | add <archetype>`.
- A **deterministic validator** (`scripts/validate_fleet.py`, stdlib-only
  Python) checks the manifest before every deploy: schema, artifact
  contracts, audit-window-vs-cadence gaps, DST drift between local intent
  and UTC crons, sub-hourly schedules — and prints per-routine usage
  estimates (runs/month). It's copied into your ops repo so the fleet stays
  self-checking.
- **Fill-in prompt templates** per archetype (`templates/`), health history
  compacted to `fleet/logs/health.jsonl` on each reconcile, and opt-in
  [ntfy](https://ntfy.sh) push escalation when a routine fails two watchdog
  reports in a row.

## Install

**As a plugin (recommended — gets updates):**

```
/plugin marketplace add alexgaoth/routine-architect
/plugin install routine-architect@alexgaoth-plugins
```

**Or copy the folder directly:**

- `~/.claude/skills/routine-architect/` — available in all your projects, or
- `<repo>/.claude/skills/routine-architect/` — available in that project only.

Then ask Claude Code to "set up routines for me" or invoke
`/routine-architect` directly. Requirements: a Claude plan with cloud
routines, at least one GitHub repo the routines may push to, and (for email
delivery) the Gmail connector enabled on claude.ai.

## Layout

```
routine-architect/
├── SKILL.md                       # entrypoint: laws + bootstrap/reconcile workflows
└── references/                    # loaded on demand (progressive disclosure)
    ├── fleet-manifest.md          # manifest schema + reconcile algorithm (normative)
    ├── routine-catalog.md         # 7 routine archetypes
    ├── prompt-patterns.md         # writing zero-context cloud-agent prompts
    ├── watchdog.md                # the overseer: design rules + template
    ├── notifications.md           # email / push / SMS / calendar channels
    └── api-reference.md           # routine API field reference
```

## Safety posture

Fleets built by this skill default to: drafts not sent email, append-only
logs, no force-push, least-privilege tool lists, no credentials in prompts or
repos, and a read-only watchdog. Escalations (sent email, push notifications)
are opt-in per routine after you've watched it behave.

MIT-style: use, modify, share freely.
