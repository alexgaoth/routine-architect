# Fleet manifest — schema and reconcile algorithm

The manifest makes the fleet convergent: bootstrap creates it, every rerun
reconciles against it, and the watchdog reads it at runtime. This file is the
normative spec — when in doubt, this document wins over intuition.

## Contents
- Ops repo layout
- Self-discovery rule
- fleet.json schema
- Artifact contract types
- Prompt files
- Reconcile algorithm (R1–R7)
- Lifecycle rules
- Invariants checklist

## Ops repo layout

```
<ops-repo>/
└── fleet/
    ├── fleet.json          # the manifest (spec below)
    ├── prompts/
    │   ├── <slug>.md       # exact deployed prompt text, one per routine
    │   └── watchdog.md     # exact deployed watchdog prompt
    └── logs/               # optional: append-only logs routines write to
```

Paths are fixed by convention — do not let users relocate `fleet/` (the
watchdog template and the self-discovery rule depend on it).

## Self-discovery rule

A managed fleet must be findable with zero prior context, in this order:

1. List deployed routines. Find the one named exactly
   `Fleet watchdog (routine-architect)`.
2. Its first git source is the ops repo (the watchdog template guarantees
   this ordering).
3. Clone/read that repo; the manifest is at `fleet/fleet.json`.

If step 1 finds no watchdog but finds routines whose names match manifest
naming (or the user says a fleet exists), ask the user for the ops repo URL
and treat the run as a **repair** (reconcile with a missing-watchdog defect).

## fleet.json schema

```json
{
  "manifest_version": 1,
  "generated_by": "routine-architect",
  "updated_at": "2026-07-30T21:00:00Z",
  "timezone": "America/Los_Angeles",
  "notify_email": "user@example.com",
  "ops_repo": "https://github.com/org/ops-repo",
  "watchdog": {
    "trigger_id": "trig_...",
    "cron_utc": "0 15 * * *",
    "prompt_file": "fleet/prompts/watchdog.md"
  },
  "unmanaged_acknowledged": [
    {"trigger_id": "trig_...", "name": "...", "note": "user's pre-existing routine, left alone"}
  ],
  "routines": [
    {
      "slug": "code-digest",
      "name": "Code digest (routine-architect)",
      "trigger_id": "trig_...",
      "archetype": "digest-notifier",
      "status": "active",
      "cron_utc": "50 6 * * *",
      "cadence_human": "daily 11:50pm America/Los_Angeles",
      "prompt_file": "fleet/prompts/code-digest.md",
      "model": "claude-sonnet-5",
      "allowed_tools": ["Bash", "Read", "Glob", "Grep", "mcp__Gmail__*"],
      "sources": ["https://github.com/org/repo-a", "https://github.com/org/repo-b"],
      "connectors": ["Gmail"],
      "artifacts": [
        {
          "type": "gmail_draft",
          "subject_prefix": "Code digest — ",
          "window_hours": 26,
          "may_be_absent_when_idle": false
        }
      ],
      "inputs_crosscheck": [],
      "purpose": "One-line human description."
    }
  ]
}
```

Field rules:

- `slug`: lowercase-hyphen, unique, stable forever (it names the prompt file
  and log entries). Renaming a slug is a retire + add, never an edit.
- `name`: display name; MUST end with `(routine-architect)` so managed
  routines are distinguishable from unmanaged ones in a raw listing.
- `status`: `active` | `paused` | `retired`. Exactly these three.
- `trigger_id`: filled in after deployment. A manifest committed with a null
  trigger_id on an `active` routine is a defect the next reconcile must fix
  (deploy it, then write the id back).
- `window_hours`: slightly longer than the cadence gap (e.g. 26 for daily,
  14 for 12-hourly) so no run falls between audit windows.
- `sources` / `connectors` / `allowed_tools` / `model` / `cron_utc`: must
  mirror the deployed config exactly — these are the fields drift is
  detected on.

## Artifact contract types

The watchdog knows exactly these four types. Adding a new type means editing
the watchdog prompt template — that is the one case where a fleet change
touches the watchdog's prompt.

| type | fields | verified by |
|---|---|---|
| `gmail_draft` | `subject_prefix`, `window_hours` | Gmail draft search: exactly one draft whose subject starts with prefix, created inside window |
| `git_commits` | `repo`, `branch`, `window_hours`, `may_be_absent_when_idle` | `git log` on the cloned repo inside window |
| `log_append` | `repo`, `path`, `window_hours`, `may_be_absent_when_idle` | new dated section appended (and no earlier section modified — check with `git log -p`) |
| `calendar_event` | `title_prefix`, `window_hours` | Calendar search inside window |

`inputs_crosscheck` entries (currently one type, `gmail_alerts`: `from`,
`subject_prefix`, `window_hours`) let the watchdog distinguish IDLE-OK from
FAIL when artifacts `may_be_absent_when_idle`: inputs present + artifacts
absent across a full window ⇒ FAIL, not idle.

## Prompt files

`fleet/prompts/<slug>.md` contains the **exact** prompt text deployed —
byte-for-byte what goes in the create/update body. No frontmatter, no
commentary; commentary belongs in `purpose`. This is what makes prompt drift
detectable and prompts reviewable in version control.

## Reconcile algorithm

Run all steps in order, every rerun, even for a "small" requested change.

**R1 — Locate and load.** Apply the self-discovery rule. Read `fleet.json`
and every prompt file. Validate the manifest against the schema above;
schema violations are defects to fix this run (with the user's confirmation).

**R2 — Health history.** Search the user's Gmail drafts for recent
`Routine watchdog —` reports (last 7 days). Summarize any WARN/FAIL to the
user — reconciliation starts from known health, not assumptions.

**R3 — Diff.** List deployed routines. Match manifest entries to deployed
routines by `trigger_id` (fallback: exact `name`). Classify every mismatch:

| class | condition | remedy |
|---|---|---|
| GAP | manifest `active`, not deployed (or null trigger_id) | deploy from manifest, write back trigger_id |
| ORPHAN | deployed with `(routine-architect)` suffix, not in manifest | ask user: adopt (add entry mirroring live config) or retire (disable + record) |
| UNMANAGED | deployed without suffix, not in `unmanaged_acknowledged` | ask user: adopt, acknowledge, or leave (then acknowledge with note) |
| DRIFT | matched, but deployed cron/prompt/tools/sources/model/connectors ≠ manifest | show field-level diff; user picks direction; converge (update deployment or update manifest) |
| PAUSED-LIVE | manifest `paused`, deployed enabled | disable the deployment |
| RETIRED-LIVE | manifest `retired`, deployed enabled | disable; remind user deletion is manual |
| STALE-WATCHDOG | a repo in any artifact contract missing from watchdog's sources; or a contract type absent from its prompt | update the watchdog deployment and `fleet/prompts/watchdog.md` |

Present the full classification table to the user before applying anything.

**R4 — Intent.** Apply what the user actually asked for (new routine, cadence
change, pause, etc.) as manifest edits + prompt-file edits first. New
routines follow bootstrap steps B3–B4 in miniature.

**R5 — Converge.** Apply all remedies from R3 plus deployments for R4. One
routine at a time; confirm each parsed next-run time.

**R6 — Commit.** Update `updated_at`, commit ops repo, push. Verify: every
`active` entry has a trigger_id; every trigger_id in the manifest exists in
the deployment listing. If push fails, tell the user — an unpushed manifest
means the watchdog audits yesterday's fleet.

**R7 — Report.** Fleet table (name, schedule in user's timezone, status,
artifact, URL), what changed this run, and any defect the user chose to
leave open.

## Lifecycle rules

- **Add**: manifest entry + prompt file → commit+push → deploy → write back
  trigger_id → commit+push again. (Two commits; the second records the id.)
- **Change**: edit manifest/prompt file → commit+push → update deployment.
  Never the reverse order — the manifest leads, deployment follows.
- **Pause**: set `status: paused` → disable deployment. Watchdog skips paused
  entries (reports them as PAUSED, not FAIL).
- **Retire**: set `status: retired` → disable deployment → user deletes
  manually when ready. Keep the entry and prompt file for history; a retired
  slug is never reused.
- **New repo enters any artifact contract**: also update watchdog sources
  (see STALE-WATCHDOG remedy) in the same sitting.

## Invariants checklist

Before ending any bootstrap or reconcile, verify:

- [ ] Manifest validates against the schema; `updated_at` refreshed
- [ ] Every `active` routine deployed, enabled, trigger_id recorded
- [ ] Every deployed managed routine matches its manifest entry field-for-field
- [ ] Watchdog deployed, its sources ⊇ {ops repo} ∪ {all artifact repos},
      ops repo listed first
- [ ] Ops repo committed AND pushed
- [ ] No orphan or unmanaged routine left unclassified
