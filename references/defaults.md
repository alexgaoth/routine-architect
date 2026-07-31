# Express defaults

The express bootstrap path exists so a newcomer reaches a working, watched
fleet by answering only the questions that cannot be defaulted. Everything
else comes from this table. Reconcile runs can change any of it later —
say that to the user so no default feels like a commitment.

## The four questions (ask nothing else in express mode)

Before asking, extend the todo-list invitation from
[todo-mapping.md](todo-mapping.md) — a shared list typically answers
questions 1 and 4 by itself, and may upgrade the starter composition to a
todo-derived fleet (still capped at 3 + watchdog).

1. **Which repos should be watched?** (GitHub URLs; also determines digest
   sources)
2. **Which repo may the fleet write to** as the ops repo? (offer: a new
   dedicated repo named `fleet-ops` is the cleanest answer)
3. **What email address** should reports go to, and **what timezone** are
   they in? (one question; infer timezone from their phrasing when possible
   and confirm)
4. **Anything an agent must never touch?** (free text → goes into prompts'
   guardrails; "nothing special" is a fine answer)

Connectors are checked, not asked: verify Gmail is connected; if not, point
to the connectors page and pause there.

## Default decisions

| decision | express default | why |
|---|---|---|
| starter fleet composition | digest-notifier + watchdog only | one visible artifact on day one; zero write-risk; archetypes with push access are opt-in upgrades |
| digest cadence | daily, 11:50pm user-local | end-of-day summary; stays clear of the watchdog |
| watchdog cadence | daily, 8:00am user-local | after the digest's window closes; report waiting at breakfast |
| notification channel | Gmail drafts | safe-by-default; see [notifications.md](notifications.md) to escalate |
| model | claude-sonnet-5 | cost scales with cadence |
| tools | per-archetype least privilege (catalog) | notifier and watchdog get no Write/Edit |
| escalation | none (no ntfy) | opt-in after the user has seen normal reports |
| naming | `Code digest (routine-architect)`, `Fleet watchdog (routine-architect)` | managed-name convention |
| prompt authoring | start from `examples/starter-fleet/`, swap the placeholders | adapting a validated example beats authoring from spec |

## Express flow

Express is bootstrap steps B1–B8 with B1 collapsed to the four questions,
B3 collapsed to presenting the starter composition table for a yes/no, and
B4 starting from `examples/starter-fleet/` (already validator-PASSing)
instead of blank templates. Everything from B5 on is identical — the
manifest, validator, commit-before-deploy, and watchdog-last rules never
relax.

After the first watchdog report lands, the natural upgrades (suggest, don't
push): add an alert-responder if they have error emails, a research-watcher
for deadlines, ntfy escalation, sent-email promotion. Each is a
`/routine-architect add <archetype>` or reconcile run away.

## When to leave express

Leave express and run the full interview (B1) when the user: names specific
alerts/errors they want acted on, wants any routine that writes to a repo,
has pre-existing routines to adopt, or asks for channels beyond email. A
user who answers the four questions with a paragraph of requirements is
telling you they want the full path — honor that.
