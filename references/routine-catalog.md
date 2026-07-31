# Routine catalog

Seven archetypes. Pick per need; combine into a fleet; never merge two
archetypes into one routine. Format per entry: what it does, cadence, inputs,
tools, artifact contract, risks. Artifact contracts named below
(`gmail_draft`, `git_commits`, `log_append`, `calendar_event`) are the
machine-checkable types defined in [fleet-manifest.md](fleet-manifest.md) —
every routine's manifest entry declares its contracts in those terms.

## Contents
- 1. Digest notifier
- 2. Alert responder
- 3. Quiet-run maintainer
- 4. Research watcher
- 5. Content drafter
- 6. One-shot reminder
- 7. Watchdog (see watchdog.md)
- Fleet-shape examples

## 1. Digest notifier

Summarizes activity so the user never has to go looking: commits pushed across
repos, inbox themes, calendar for the day, metrics deltas.

- **Cadence:** daily; late night for code digests, early morning for briefings.
- **Inputs:** git history of cloned repos (`git log --all --since='24 hours ago' --stat`),
  Gmail search, Calendar list.
- **Tools:** `Bash, Read, Glob, Grep` + Gmail/Calendar connector. No Write/Edit —
  a notifier must not modify anything.
- **Artifact:** `gmail_draft` with a date-stamped subject
  (`"Code digest — YYYY-MM-DD"`), `may_be_absent_when_idle: false`. Idle
  state: draft still created, body says "No activity in the last 24 hours."
  — never skip the artifact, the watchdog reads absence as failure.
- **Risks:** duplicate drafts if the routine retries; instruct it to check for
  an existing draft with today's subject first.

## 2. Alert responder

Reads operational alerts (error emails, CI failures), root-causes them in the
repo, fixes genuine bugs, runs tests, documents, pushes. The highest-value and
highest-risk archetype.

- **Cadence:** every 12h typical; hourly only for genuinely hot systems.
- **Inputs:** Gmail search scoped tightly (exact sender + subject prefix +
  received-window slightly longer than the cadence, e.g. 14h for a 12h cadence,
  so nothing falls in the gap between runs).
- **Tools:** `Bash, Read, Write, Edit, Glob, Grep` + Gmail connector.
- **Artifact:** `git_commits` + `log_append` (a **dated, append-only section**
  in e.g. `docs/QUALITY_LOG.md`) per run that acted, both
  `may_be_absent_when_idle: true`, paired with a `gmail_alerts`
  inputs_crosscheck so the watchdog can tell idle from broken.
- **Risks:** the loop (re-fixing the same bug every run — require it to read
  the log doc and `git log` for prior fixes before changing anything); forcing
  a change when none is needed (state explicitly: "if all alerts match
  documented patterns, report 'no new action needed' and stop"); push races
  (require `git fetch && git rebase origin/main`, forbid force-push); credential
  theater (it cannot see production `.env` — it may say "X needs to be set in
  production", never "X is missing").

## 3. Quiet-run maintainer

Proactive upkeep when nothing is on fire: run the test suite, raise coverage on
the worst file, bump one minor dependency and verify, fix lints, improve docs.
Pairs well as the "else" branch of an alert responder, or standalone.

- **Cadence:** nightly or weekly.
- **Tools:** `Bash, Read, Write, Edit, Glob, Grep`.
- **Artifact:** one commit (or PR) per run with a conventional message, plus a
  line appended to a maintenance log. Cap the blast radius in the prompt: "one
  dependency per run", "only files under tests/", "never touch public API".
- **Risks:** scope creep into refactors nobody asked for — enumerate allowed
  change types explicitly and forbid the rest.

## 4. Research watcher

Watches the outside world: competitor pricing pages, new releases of key
dependencies, hackathon/grant deadlines, papers, job postings. Replaces the
"I should check X weekly" mental load.

- **Cadence:** weekly; daily only when timeliness genuinely matters.
- **Inputs:** web fetches/searches if the environment allows network access;
  otherwise repo-committed watchlist files updated by the user.
- **Tools:** `Bash, Read` + whatever fetch capability the environment provides
  + Gmail connector for delivery.
- **Artifact:** Gmail draft, date-stamped, diffed against the previous report —
  "changed since last week" is the value, so have it keep a state file in a
  repo (committed) or restate prior findings in the draft for comparison.
- **Risks:** hallucinated findings — require a source URL per claim, and
  "nothing changed" as an acceptable, reportable outcome.

## 5. Content drafter

Turns the user's activity (commits, notes, writing) into draft posts, changelog
entries, or newsletter sections.

- **Cadence:** daily or weekly.
- **Tools:** `Bash, Read, Glob, Grep` + Gmail connector.
- **Artifact:** Gmail draft containing the candidate posts. **Never** publishes
  anywhere directly — no exception; posting is the user's hand on the button.
- **Risks:** voice drift — include 2–3 verbatim examples of the user's real
  writing in the prompt as style anchors.

## 6. One-shot reminder

Not recurring: `run_once_at` a future timestamp. "Check the cert renewal on
the 1st", "revisit this PR in two weeks". Fires once, then auto-disables.

- **Artifact:** Gmail draft or calendar event carrying the reminder plus any
  context gathered at fire time (that's the advantage over a plain reminder:
  it can check the current state of the thing before reminding).
- **Risks:** timestamp must be future and UTC; confirm the local-time
  conversion with the user.

## 7. Watchdog

The overseer. Full pattern and template in [watchdog.md](watchdog.md). One per
fleet, scheduled last, audit list updated with every fleet change.

## Fleet-shape examples

**Solo dev, one product repo:** digest notifier (nightly) + alert responder
(12h) + quiet-run maintainer (weekly) + watchdog (daily, morning).

**Many small repos, no production alerts:** digest notifier across all repos
(nightly) + quiet-run maintainer rotating one repo per run (nightly) +
research watcher (weekly) + watchdog (daily).

**Non-coding user:** morning briefing notifier (daily) + research watcher
(weekly) + content drafter (weekly) + watchdog (daily).
