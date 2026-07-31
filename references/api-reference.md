# Routine API reference

Mechanics for deploying what the manifest describes. In Claude Code, the
bundled `schedule` skill loads the `RemoteTrigger` tool with the user's live
connector list and environment ids — invoke it rather than reconstructing
that context by hand; this file is the condensed field reference for when
you're already in flight.

## Contents
- Actions
- Create body shape
- Cron and run_once_at rules
- MCP connections
- Tools, model, environment
- Managed-name convention
- Verification after create/update

## Actions

`RemoteTrigger` with `action`: `list` | `get` | `create` | `update` | `run`
(`trigger_id` required for get/update/run; `body` for create/update; update
is partial). **Deletion is not available via API** — users delete at
`https://claude.ai/code/routines`. Management link for any routine:
`https://claude.ai/code/routines/<trigger_id>`.

## Create body shape

```json
{
  "name": "Code digest (routine-architect)",
  "cron_expression": "50 6 * * *",
  "enabled": true,
  "mcp_connections": [
    {"connector_uuid": "<from the schedule skill's connector list>",
     "name": "Gmail",
     "url": "https://gmailmcp.googleapis.com/mcp/v1"}
  ],
  "job_config": {
    "ccr": {
      "environment_id": "<env id from the schedule skill>",
      "session_context": {
        "model": "claude-sonnet-5",
        "sources": [
          {"git_repository": {"url": "https://github.com/org/ops-repo"}},
          {"git_repository": {"url": "https://github.com/org/webapp"}}
        ],
        "allowed_tools": ["Bash", "Read", "Glob", "Grep", "mcp__Gmail__*"]
      },
      "events": [
        {"data": {
          "uuid": "<fresh lowercase v4 uuid — generate per routine>",
          "session_id": "",
          "type": "user",
          "parent_tool_use_id": null,
          "message": {"content": "<exact contents of fleet/prompts/<slug>.md>",
                      "role": "user"}
        }}
      ]
    }
  }
}
```

The prompt goes in `events[0].data.message.content` and must be byte-for-byte
the manifest's prompt file.

## Cron and run_once_at rules

- 5-field cron, **UTC only**. Minimum interval 1 hour (`*/30 * * * *` is
  rejected).
- Convert from the user's timezone and confirm the conversion out loud
  ("11:50pm PT = 06:50 UTC → `50 6 * * *`"). Remember DST changes the
  offset; a fleet tuned in winter drifts an hour in summer — note this in
  the hand-off.
- One-shot: replace `cron_expression` with `"run_once_at":
  "YYYY-MM-DDTHH:MM:SSZ"` (RFC3339 UTC, future). Fires once, auto-disables
  (`ended_reason: "run_once_fired"`); re-arm by updating with a new
  `run_once_at`. Check the actual current time (`date -u`) before computing —
  never infer it from conversation context.
- Stagger the fleet: no two routines on the same minute, watchdog after all
  windows close.

## MCP connections

Only connectors the *user* has connected on claude.ai are available; the
`schedule` skill lists them with their `connector_uuid`s. The `name` field
allows only `[a-zA-Z0-9_-]`. If a design needs a connector the user lacks,
send them to `https://claude.ai/customize/connectors` before deploying that
routine. Granting a connector grants its full tool surface — scope behavior
in the prompt ("only create drafts") and keep `allowed_tools` minimal.

## Tools, model, environment

- `allowed_tools`: least privilege per archetype. Notifiers/watchers/watchdog:
  `Bash, Read, Glob, Grep` (+ connector tools like `mcp__Gmail__*`).
  Responders/maintainers add `Write, Edit`. Nothing gets tools its job
  doesn't need — a notifier with Edit is a defect.
- `model`: `claude-sonnet-5` is the right default (routines run often; cost
  scales with cadence). Escalate a specific routine to a more capable model
  only when its runs demonstrably fail from reasoning, not from prompt gaps.
- `environment_id`: from the schedule skill's environment list; required.

## Managed-name convention

Every routine this skill deploys is named `<Human name> (routine-architect)`,
and the watchdog exactly `Fleet watchdog (routine-architect)`. This is what
lets reconcile distinguish ORPHAN (managed suffix, no manifest entry) from
UNMANAGED (no suffix) in a raw listing. Do not deploy without the suffix.

## Verification after create/update

The create/update response echoes the parsed config and next-run time:

1. Confirm `next_run_at` matches intent; translate to the user's timezone
   and show them.
2. Record the returned `id` (trigger_id) in the manifest immediately.
3. Give the user the management link.
4. Optionally `action: "run"` for a smoke test of a newly created routine —
   with the user's consent, since a real run costs usage and produces a real
   artifact.
