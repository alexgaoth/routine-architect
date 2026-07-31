# Prompt patterns for zero-context cloud agents

A routine's prompt is its entire brain. The agent wakes in a fresh sandbox
with cloned repos, the declared tools, and this text — nothing else. It
cannot ask questions. Every ambiguity you leave becomes improvisation in
production, twice a day, unsupervised.

## Contents
- The seven required elements
- Loop guards
- Guardrails block
- Credential honesty
- Push discipline
- Annotated example

## The seven required elements

Every routine prompt must contain, in roughly this order:

1. **Role and schedule.** "You are X, running at HH:MM UTC (HH:MM local)."
   The agent has no other way to know when "the last 24 hours" is anchored
   or why it exists.
2. **Workspace orientation.** What repos are cloned, which directory is
   production-relevant, which is secondary. Name paths explicitly.
3. **Inputs, scoped tightly.** Exact Gmail sender + subject prefix + time
   window; exact git commands with `--since` windows. Windows slightly wider
   than the cadence gap (14h for a 12h cadence) so nothing falls between runs.
4. **Decision procedure.** Numbered steps with explicit conditionals,
   including the do-nothing branch: "If all alerts match documented patterns
   or there are no new alerts, skip to the report step and state 'no new
   action needed' — do not force a change." Without a sanctioned exit, agents
   invent work.
5. **Artifact contract.** Exactly what the run leaves behind, matching the
   manifest entry: draft subject format, log file and section format, commit
   expectations. Date-stamp everything (`YYYY-MM-DD`).
6. **Guardrails block.** See below. Last, so it's freshest in context.
7. **Honest failure clause.** "If tools fail or something is missing, report
   that plainly in your artifact rather than guessing." A run that reports
   its own failure is OK; a run that fabricates success poisons the fleet.

## Loop guards

Recurring agents re-solve solved problems unless told how to recognize prior
work. Require, before any change:

- Read the append-only log's recent dated sections — if the finding is
  already documented, do not act on it again.
- Search `git log` for related prior commits ("search for 'fail fast on
  missing credentials' before duplicating that work").
- Append-only discipline: new dated sections only; never edit or remove
  earlier sections. (The watchdog checks this with `git log -p`.)

## Guardrails block

Adapt per archetype; the spine is constant:

```
Never force-push. Never delete files or branches. Never rewrite or remove
earlier log sections. Never send email — only create drafts. Do not proceed
to commit if tests fail: fix the issue or don't commit. If git status shows
pre-existing modifications you didn't make, leave those files alone and
stage only your own changes.
```

For notifier/watcher archetypes, add "never modify anything; your only
output is the draft." For content drafters, add "never publish anywhere."

## Credential honesty

Gitignored files (`.env`, secrets) do not exist in the clone. Therefore:

- The agent must never assert a credential is or isn't configured in
  production — phrase findings as "if this is a missing-credential issue,
  X needs to be set in production."
- The agent must never fabricate, guess, or commit credentials.
- Point it at `.env.example` / settings files as the map of what *should*
  exist.

## Push discipline

For any routine that pushes:

```
Before pushing: git fetch origin && git rebase origin/<branch> (never
force-push) in case another commit landed since your clone; resolve
conflicts conservatively, keeping both sides' content when in doubt.
```

Commit messages must state root cause and fix, not just "update files" —
the digest notifier and the human read these.

## Annotated example

A 12-hourly alert responder, annotated with `◄` (do not include annotations
in a real prompt):

```
You are reviewing observability alert emails for the `webapp` repo
(github.com/org/webapp). `src/` is live production code; `experiments/` is
secondary.                                          ◄ role + orientation

Each run:
1. Search Gmail for alerts: sender alerts@example.com, subject starting
   '[ERROR]', received in the last 14 hours.        ◄ scoped input, 12h+2
2. Read docs/QUALITY_LOG.md's dated sections first. If all new alerts match
   already-documented patterns, or there are no new alerts, skip to step 6
   and report 'no new action needed' — do not force a change.
                                                    ◄ loop guard + exit
3. For each genuinely NEW pattern, read the relevant code and find root
   cause. Check .env.example for what env vars are expected — you cannot see
   production values, so never assert a credential is or isn't configured;
   phrase it as 'if this is a missing-credential issue, X needs setting in
   production.'                                     ◄ credential honesty
4. Apply a code fix ONLY for genuine, verifiable bugs. Run the test suite
   for anything you touch; add tests for new behavior. Do not commit if
   tests fail.                                      ◄ feedback loop
5. Append a new dated section (today, YYYY-MM-DD) to docs/QUALITY_LOG.md:
   which alerts fired, root cause, fix applied or exactly what blocks one.
   Only append — never edit earlier sections.       ◄ artifact contract
6. Commit with a message stating root cause and fix. Before pushing:
   git fetch origin && git rebase origin/main (never force-push). Push.
                                                    ◄ push discipline
7. End with a bullet summary: alerts found, fixes (file:line), what still
   needs a human and why, whether the push succeeded.

Never force-push, never delete files or branches, never rewrite prior log
sections. If Gmail tools fail or the repo looks wrong, say so plainly in
your summary instead of guessing.                   ◄ guardrails + honesty
```

Prompt length: 300–600 words is the healthy band. Shorter usually means
missing elements; much longer usually means the routine has two jobs — split
it.
