# Todo-list onboarding

The best fleet design input isn't an interview — it's the list the user
already keeps. When a user shares a todo list, notes file, or project
board, derive the fleet from it. This grounds every routine in something
they actually want done, which is the difference between automation that
gets kept and automation that gets abandoned.

## Invitation

At the start of B1 (both express and full paths), offer once:

> "If you have a todo list, notes doc, or project board, share it (paste
> it, point me at the file, or a doc I can read) — I'll propose routines
> from what's actually on your plate. Or we can just talk."

Never require it. Never pressure a second time.

## Mapping heuristics

| todo item pattern | proposed archetype |
|---|---|
| "check X regularly", "keep an eye on", "monitor" | digest-notifier or research-watcher |
| "fix X when it breaks", error/alert emails piling up | alert-responder |
| "clean up", "add tests", "update deps", "improve docs" — recurring, never urgent | quiet-run-maintainer |
| "apply by <date>", "waiting on", "don't forget", "follow up" | one-shot reminder or research-watcher (deadline mode) |
| "post more", "write about", "publish changelog" | content-drafter |
| "stay on top of email/calendar" | digest-notifier (briefing variant) |

**Explicitly NOT automatable — say so, respectfully.** Deep work ("design
the new architecture"), one-time builds ("make the game"), decisions
("choose a direction"), learning ("study Rust"), relationships, and
anything the user clearly wants to do themselves. List these back under a
heading like "stays yours — no routine proposed", one line each. A tool
that claims it can automate thinking loses the user's trust for the items
it genuinely can automate.

## Rules (all mandatory)

1. **Quote, never invent.** Every proposed routine cites its source item
   verbatim in the proposal table. No routine may be proposed that doesn't
   trace to something the user wrote or said. If the list is thin, ask —
   don't pad.
2. **Ask about ambiguity.** "Website" alone could mean SEO watching,
   uptime checking, or content drafting. One clarifying question beats a
   wrong routine.
3. **Cap the first fleet.** From a todo list, propose at most 3 routines
   plus the watchdog, choosing the items with the clearest recurring shape.
   List the runners-up as "next candidates — add later with
   `/routine-architect add <archetype>`". An over-eager first fleet is the
   fastest route to notification fatigue and abandonment.
4. **Private things stay private.** Todo lists contain personal material.
   Use items only to propose routines; never copy list contents into
   manifest files, prompt files, or commit messages beyond what a routine
   genuinely needs (a routine watching "grant deadline March 3" needs that
   deadline; it does not need the rest of the list).
5. **Proposal format.** A table: quoted item → archetype → cadence →
   artifact, followed by the "stays yours" list, followed by the
   runners-up. Then proceed to the normal B3 agreement gate — the todo
   list feeds the design; it never skips the user's yes.

## After the first fleet

On reconcile runs, if the user shares an updated list, diff against the
manifest's purposes: propose additions for new recurring items, and flag
routines whose source item is gone ("this was for X, which is off your
list — keep, pause, or retire?"). The fleet should track the user's life,
not fossilize its first week.
