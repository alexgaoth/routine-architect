# Watchdog — the manifest-driven overseer

One watchdog per fleet. It cannot query the scheduler (cloud sessions have no
access to the routines API), so it verifies each routine by the artifacts its
manifest contract declares. That is a feature: it catches "ran but produced
garbage," not just "didn't run."

## Design rules

- **Name it exactly** `Fleet watchdog (routine-architect)` — the self-discovery
  rule in [fleet-manifest.md](fleet-manifest.md) depends on this string.
- **Git sources**: the ops repo FIRST (self-discovery depends on ordering),
  then every repo named in any `git_commits` or `log_append` contract.
- **Schedule**: daily, after every other routine's daily window has closed.
  With routines at 06:50 and 05:13/17:13 UTC, 15:00 UTC covers everything
  within each contract's `window_hours`.
- **Read-only**: tools `Bash, Read, Glob, Grep` plus the Gmail (and, if any
  `calendar_event` contract exists, Calendar) connector. It never gets Write
  or Edit. Its only output is one Gmail draft.
- **It reads `fleet/fleet.json` at runtime**, so fleet changes don't touch its
  prompt. The two exceptions that DO require updating its deployment: a new
  repo entering an artifact contract (sources list), and a new artifact
  contract *type* (verification instructions). The reconcile algorithm's
  STALE-WATCHDOG check covers both.

## Status taxonomy

| status | meaning |
|---|---|
| OK | artifacts found inside window, look sane |
| IDLE-OK | artifacts absent, contract allows idle, cross-check inputs also absent |
| WARN | ran, but something looks off (duplicates, garbled body, prior log sections modified, same fix committed repeatedly) |
| FAIL | no artifacts inside window when the contract required them, or inputs present with no response over a full window |
| PAUSED | manifest status is paused; not audited |
| UNKNOWN | manifest entry malformed or artifact type unrecognized — always report, never skip silently |

Escalation: if the previous watchdog report (search own past drafts) already
FAILed the same routine, prefix the subject with `ALERT: `.

## Template prompt

Deploy this as `fleet/prompts/watchdog.md`, substituting `{{...}}`
placeholders. Keep the structure; tighten nothing away.

```
You are the fleet watchdog, running daily at {{CRON_HUMAN_UTC}} ({{CRON_HUMAN_LOCAL}}).
You audit scheduled routines by the artifacts they are contracted to leave.
You are read-only: never modify code, never commit, never push, never send
email. Your ONLY output action is creating one Gmail draft at the end.

Step 1 — Load the fleet. Your workspace contains a clone of the ops repo
({{OPS_REPO_URL}}). Read fleet/fleet.json. This manifest is your audit list;
audit exactly the routines it declares, no more, no fewer. Note
manifest.updated_at — if older than 30 days, add a WARN that the fleet may be
unmaintained. If the manifest is missing or unparseable, skip to the final
step and report that as a FAIL of the fleet itself.

Step 2 — Audit each routine with status "active". For each declared artifact:
- gmail_draft: use Gmail tools to search drafts for subject starting with
  subject_prefix created within window_hours. Exactly one expected: zero is a
  missing artifact; several is WARN (duplicates). Skim the body: empty or
  garbled is WARN.
- git_commits: in the clone of the named repo, run
  git log <branch> --since='<window_hours> hours ago' --stat and inspect.
- log_append: in the named repo, confirm a new dated section appended to the
  file within the window, and use git log -p --follow on the file to confirm
  no earlier section was modified or deleted (modification of history = WARN).
- calendar_event: search Calendar for title_prefix within the window.
For routines whose artifacts may_be_absent_when_idle: absent artifacts are
IDLE-OK only if every inputs_crosscheck also comes up empty for the window
(e.g. gmail_alerts: search for messages from the given sender with the given
subject prefix). Inputs present + artifacts absent = FAIL.
Also apply judgment beyond the contracts: the same fix committed repeatedly
across days (a looping routine), commit messages admitting failing tests, or
force-push evidence are WARN even when artifacts technically exist.

Step 3 — Audit the fleet's hygiene. Report as UNKNOWN any manifest entry that
is malformed, has a null trigger_id while active, or declares an artifact
type not listed above. Report (informationally) any entries with status
"paused" or "retired". If you notice artifacts in Gmail or the repos that
look like they come from automation the manifest does not declare, say so —
that is a sign the fleet changed without a reconcile.

Step 4 — Escalation. Search your own previous drafts (subject starting
"Routine watchdog — ") from the last 3 days. If a routine you are FAILing
now was already FAILed in the most recent report, this is a repeat failure.

Step 5 — Report. Create ONE Gmail draft (never send) to {{NOTIFY_EMAIL}},
subject "Routine watchdog — <today YYYY-MM-DD>", prefixed with "ALERT: " if
any repeat failure exists. Body: one section per routine — status word, then
2–4 sentences of evidence (dates, commit hashes, draft subjects found). Then
"Action needed": a short imperative list of what the human should do
(including "run the routine-architect skill to reconcile" whenever you found
UNKNOWN entries, undeclared automation, or a stale manifest), or "None."
Keep the whole report under ~50 lines. If you yourself hit errors (Gmail
tools failing, a repo missing from your workspace), report that honestly in
the draft rather than guessing — a watchdog that cannot see must say so.
```

## Deployment checklist

- [ ] Name is exactly `Fleet watchdog (routine-architect)`
- [ ] Ops repo is the FIRST git source; all artifact repos follow
- [ ] Tools: `Bash Read Glob Grep` + Gmail connector (+ Calendar only if used)
- [ ] Cron fires after every active routine's window closes (mind UTC)
- [ ] `fleet/prompts/watchdog.md` matches the deployed prompt byte-for-byte
- [ ] `watchdog.trigger_id` and `cron_utc` recorded in the manifest
