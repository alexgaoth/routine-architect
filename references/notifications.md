# Notification channels

How a routine's output reaches the user. Pick per routine during the
interview; record the choice in the manifest's artifact contract.

## Contents
- Decision guide
- Email drafts (default)
- Sent email
- Push notification (ntfy)
- SMS
- Calendar events
- Chat webhooks

## Decision guide

| need | channel |
|---|---|
| daily reading material (digests, reports) | Gmail **draft** |
| must reach them even if they don't open drafts | sent email or push |
| urgent, interrupt-worthy (repeat failures) | push notification or SMS |
| time-anchored reminder | calendar event |
| team visibility | chat webhook |

Default to Gmail drafts. Escalate a channel only when the user has seen the
routine behave and asks for it.

## Email drafts (default)

Requires the Gmail MCP connector. The routine creates a draft addressed to
the user; nothing is sent, so a misbehaving routine cannot spam anyone —
worst case is clutter in their own drafts folder. Machine-checkable
(`gmail_draft` contract). Date-stamp the subject and instruct the routine to
check for an existing draft with today's subject before creating (retry
protection).

## Sent email

Same connector, `send` instead of draft. Use only after the user explicitly
promotes a routine, and only for routines with a WARN/FAIL-style trigger —
never for daily digests (inbox fatigue kills the fleet's credibility). When
sending, the watchdog contract should switch to searching the Sent folder.

## Push notification (ntfy)

For true "tap my shoulder" alerts without any account setup:
[ntfy.sh](https://ntfy.sh) — the user installs the app and subscribes to a
topic; the routine publishes with a plain HTTP POST (needs `Bash` and
network access in the cloud environment):

```bash
curl -s -H "Title: Watchdog ALERT" -d "2 routines failing since yesterday" \
  https://ntfy.sh/<topic>
```

The topic name is effectively a password — generate something long and
random, and treat the routine prompt as semi-public (anyone who can read it
can post to the topic). For higher stakes, self-host ntfy or use an
access-token setup. Not directly machine-checkable by the watchdog — pair it
with a draft artifact (post AND draft) so auditability is preserved.

## SMS

No first-class channel. Two workable paths, both with caveats:

- **Carrier email-to-SMS gateways** (e.g. `<number>@txt.att.net`): requires
  *sent* email and the carrier gateway to still exist — several US carriers
  have retired theirs. Verify with the user's carrier before promising this.
- **Twilio or similar API**: needs an auth token, and routines have no secret
  store — a token in a prompt or committed to the ops repo is exposed. Only
  acceptable with a deliberately scoped, revocable token the user accepts
  exposing, or a user-hosted relay (webhook that holds the secret). When in
  doubt, recommend ntfy push instead — it covers the same "buzz my phone"
  need without credentials.

## Calendar events

Requires the Google Calendar connector. Best for one-shot reminders and
deadline watchers ("grant closes Friday" lands as an event with the details
in the description). Machine-checkable (`calendar_event` contract). Have the
routine search for an existing event before creating (idempotency).

## Chat webhooks (Slack/Discord)

A plain POST to an incoming-webhook URL. Same secret caveat as Twilio: the
URL itself is the credential and will be visible in the prompt/manifest —
acceptable for a private/low-stakes channel the user designates, not for
anything sensitive. Pair with a draft artifact for auditability.
