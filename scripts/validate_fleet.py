#!/usr/bin/env python3
"""Validate a routine-architect fleet manifest (fleet/fleet.json).

Usage:
    python3 scripts/validate_fleet.py [path/to/fleet.json]

Path defaults to fleet/fleet.json relative to the current directory.
Exits 0 on pass (warnings allowed), 1 on any error. Every finding names the
routine and the fix, so an agent (or human) can repair the manifest without
re-deriving the rules. Stdlib only.
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone as dt_timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # < 3.9
    ZoneInfo = None

STATUSES = {"active", "paused", "retired"}
ARCHETYPES = {
    "digest-notifier", "alert-responder", "quiet-run-maintainer",
    "research-watcher", "content-drafter", "one-shot-reminder", "watchdog",
}
ARTIFACT_FIELDS = {
    "gmail_draft": {"subject_prefix", "window_hours"},
    "git_commits": {"repo", "branch", "window_hours"},
    "log_append": {"repo", "path", "window_hours"},
    "calendar_event": {"title_prefix", "window_hours"},
}
CROSSCHECK_FIELDS = {"gmail_alerts": {"from", "subject_prefix", "window_hours"}}
NAME_SUFFIX = " (routine-architect)"
WATCHDOG_NAME = "Fleet watchdog (routine-architect)"
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

errors, warnings, infos = [], [], []


def err(code, msg):
    errors.append(f"[E{code}] {msg}")


def warn(code, msg):
    warnings.append(f"[W{code}] {msg}")


def parse_cron_field(field, lo, hi):
    """Return the set of matching ints, or None if invalid."""
    vals = set()
    for part in field.split(","):
        step = 1
        if "/" in part:
            part, step_s = part.split("/", 1)
            if not step_s.isdigit() or int(step_s) < 1:
                return None
            step = int(step_s)
        if part == "*":
            rng = range(lo, hi + 1)
        elif "-" in part:
            a, _, b = part.partition("-")
            if not (a.isdigit() and b.isdigit()):
                return None
            rng = range(int(a), int(b) + 1)
        elif part.isdigit():
            rng = range(int(part), int(part) + 1)
        else:
            return None
        vals.update(v for i, v in enumerate(rng) if i % step == 0)
    if not vals or min(vals) < lo or max(vals) > hi:
        return None
    return vals


def parse_cron(expr):
    """Parse a 5-field cron. Returns dict of field sets, or None."""
    parts = expr.split()
    if len(parts) != 5:
        return None
    minute = parse_cron_field(parts[0], 0, 59)
    hour = parse_cron_field(parts[1], 0, 23)
    dom = parse_cron_field(parts[2], 1, 31)
    month = parse_cron_field(parts[3], 1, 12)
    dow = parse_cron_field(parts[4], 0, 7)
    if None in (minute, hour, dom, month, dow):
        return None
    if 7 in dow:  # cron allows 7 == Sunday == 0
        dow = (dow - {7}) | {0}
    return {
        "minute": minute, "hour": hour, "dom": dom, "month": month,
        "dow": dow,
        "dom_restricted": parts[2] != "*",
        "dow_restricted": parts[4] != "*",
        "month_restricted": parts[3] != "*",
    }


def weekly_fires(cron):
    """Minutes-of-week (0..10079, Monday 00:00 = 0) when the cron fires.

    Only meaningful when dom and month are unrestricted (checked by caller).
    """
    fires = []
    for dow in range(7):  # Monday=0 here; cron Sunday=0 -> convert
        cron_dow = (dow + 1) % 7
        if cron_dow not in cron["dow"]:
            continue
        for h in sorted(cron["hour"]):
            for m in sorted(cron["minute"]):
                fires.append(dow * 1440 + h * 60 + m)
    return sorted(fires)


def max_gap_hours(fires):
    if len(fires) < 2:
        return 168.0
    gaps = [b - a for a, b in zip(fires, fires[1:])]
    gaps.append(10080 - fires[-1] + fires[0])  # wraparound
    return max(gaps) / 60.0


def check_hourly_min(owner, cron):
    if cron and len(cron["minute"]) > 1:
        err(303, f"{owner}: cron fires more than once per hour — the platform "
                 "rejects sub-hourly schedules (minimum interval 1 hour).")


def check_window(owner, cron, window, label):
    if cron["month_restricted"] or cron["dom_restricted"]:
        warn(301, f"{owner}: {label} uses day-of-month/month scheduling; "
                  "cadence-vs-window check skipped — verify window_hours by hand.")
        return
    gap = max_gap_hours(weekly_fires(cron))
    if window < gap + 1:
        err(302, f"{owner}: {label} window_hours={window} but the schedule's "
                 f"largest gap is {gap:.1f}h — runs can fall between audit "
                 f"windows. Set window_hours >= {int(gap) + 2}.")


def check_dst(routine, cron_utc, tz_name):
    cl = routine.get("cadence_local")
    if not cl or not ZoneInfo or not tz_name:
        return
    local = parse_cron(cl.get("cron_local", ""))
    if not local:
        err(401, f"{routine['slug']}: cadence_local.cron_local is not valid cron.")
        return
    if len(local["hour"]) != len(cron_utc["hour"]):
        err(402, f"{routine['slug']}: cadence_local declares "
                 f"{len(local['hour'])} firing hour(s) but cron_utc has "
                 f"{len(cron_utc['hour'])}.")
        return
    tz = ZoneInfo(tz_name)
    today = datetime.now(tz).date()
    expected = set()
    for h in local["hour"]:
        for m in local["minute"]:
            lt = datetime(today.year, today.month, today.day, h, m, tzinfo=tz)
            expected.add(lt.astimezone(dt_timezone.utc).hour)
    if expected != cron_utc["hour"]:
        err(403, f"{routine['slug']}: DST drift — local schedule "
                 f"{sorted(local['hour'])}:xx {tz_name} maps to UTC hours "
                 f"{sorted(expected)} today, but cron_utc fires at "
                 f"{sorted(cron_utc['hour'])}. Re-derive cron_utc and update "
                 "the deployment.")


def runs_per_month(cron):
    if cron["month_restricted"]:
        return None
    if cron["dom_restricted"]:
        return len(cron["dom"]) * len(cron["hour"]) * len(cron["minute"])
    return round(len(weekly_fires(cron)) * (365.25 / 7 / 12), 1)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "fleet/fleet.json"
    try:
        with open(path) as f:
            m = json.load(f)
    except FileNotFoundError:
        print(f"FAIL: manifest not found at {path}")
        return 1
    except json.JSONDecodeError as e:
        print(f"FAIL: manifest is not valid JSON: {e}")
        return 1

    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(path)))

    for field in ("manifest_version", "timezone", "notify_email", "ops_repo",
                  "watchdog", "routines", "updated_at"):
        if field not in m:
            err(101, f"top-level field '{field}' is missing.")
    tz_name = m.get("timezone")
    if tz_name and ZoneInfo:
        try:
            ZoneInfo(tz_name)
        except Exception:
            err(102, f"timezone '{tz_name}' is not a valid IANA zone.")

    wd = m.get("watchdog", {})
    if not wd.get("trigger_id"):
        warn(103, "watchdog.trigger_id is empty — watchdog not yet deployed "
                  "(expected only mid-bootstrap).")
    wd_cron = parse_cron(wd.get("cron_utc", ""))
    if not wd_cron:
        err(104, "watchdog.cron_utc is missing or not valid 5-field cron.")
    check_hourly_min("watchdog", wd_cron)
    wd_prompt = wd.get("prompt_file", "fleet/prompts/watchdog.md")
    if not os.path.isfile(os.path.join(root, wd_prompt)):
        err(105, f"watchdog prompt file '{wd_prompt}' does not exist.")

    slugs = set()
    total_runs = 0.0
    artifact_repos = set()
    for r in m.get("routines", []):
        slug = r.get("slug", "<missing slug>")
        for field in ("slug", "name", "archetype", "status", "cron_utc",
                      "prompt_file", "artifacts", "purpose"):
            if field not in r:
                err(201, f"{slug}: field '{field}' is missing.")
        if not SLUG_RE.match(r.get("slug", "")):
            err(202, f"{slug}: slug must be lowercase-hyphen "
                     "([a-z0-9]+(-[a-z0-9]+)*).")
        if slug in slugs:
            err(203, f"{slug}: duplicate slug — slugs must be unique forever.")
        slugs.add(slug)
        if not r.get("name", "").endswith(NAME_SUFFIX):
            err(204, f"{slug}: name must end with '{NAME_SUFFIX}' so reconcile "
                     "can distinguish managed routines.")
        if r.get("name") == WATCHDOG_NAME:
            err(205, f"{slug}: the watchdog belongs in the 'watchdog' block, "
                     "not in 'routines'.")
        if r.get("status") not in STATUSES:
            err(206, f"{slug}: status '{r.get('status')}' invalid — use "
                     f"{sorted(STATUSES)}.")
        if r.get("archetype") not in ARCHETYPES:
            warn(207, f"{slug}: archetype '{r.get('archetype')}' is not in the "
                      f"catalog ({sorted(ARCHETYPES)}).")
        cron = parse_cron(r.get("cron_utc", ""))
        if not cron:
            err(208, f"{slug}: cron_utc '{r.get('cron_utc')}' is not valid "
                     "5-field cron.")
        check_hourly_min(slug, cron)
        if r.get("status") == "active" and not r.get("trigger_id"):
            warn(209, f"{slug}: active but trigger_id is null — a GAP; deploy "
                      "and write the id back.")
        pf = r.get("prompt_file", "")
        full = os.path.join(root, pf)
        if not pf or not os.path.isfile(full):
            err(210, f"{slug}: prompt_file '{pf}' does not exist.")
        elif os.path.getsize(full) < 200:
            warn(211, f"{slug}: prompt_file '{pf}' is under 200 bytes — almost "
                      "certainly missing required prompt elements.")

        arts = r.get("artifacts", [])
        if r.get("status") == "active" and not arts:
            err(212, f"{slug}: active routine with no artifact contract is "
                     "unauditable — declare at least one artifact.")
        idle_ok = False
        for a in arts:
            t = a.get("type")
            if t not in ARTIFACT_FIELDS:
                err(213, f"{slug}: unknown artifact type '{t}' — watchdog "
                         f"only verifies {sorted(ARTIFACT_FIELDS)}.")
                continue
            missing = ARTIFACT_FIELDS[t] - set(a)
            if missing:
                err(214, f"{slug}: artifact '{t}' missing fields "
                         f"{sorted(missing)}.")
            if a.get("may_be_absent_when_idle"):
                idle_ok = True
            if t in ("git_commits", "log_append") and a.get("repo"):
                artifact_repos.add(a["repo"])
            if cron and isinstance(a.get("window_hours"), (int, float)):
                check_window(slug, cron, a["window_hours"],
                             f"artifact '{t}'")
        if idle_ok and not r.get("inputs_crosscheck"):
            warn(215, f"{slug}: artifacts may_be_absent_when_idle but no "
                      "inputs_crosscheck — watchdog cannot tell idle from "
                      "broken.")
        for c in r.get("inputs_crosscheck", []):
            t = c.get("type")
            if t not in CROSSCHECK_FIELDS:
                err(216, f"{slug}: unknown inputs_crosscheck type '{t}'.")
            elif CROSSCHECK_FIELDS[t] - set(c):
                err(217, f"{slug}: crosscheck '{t}' missing fields "
                         f"{sorted(CROSSCHECK_FIELDS[t] - set(c))}.")
        if cron:
            check_dst(r, cron, tz_name)
            rpm = runs_per_month(cron)
            if rpm and r.get("status") == "active":
                total_runs += rpm
                infos.append(f"{slug}: ~{rpm} runs/month")

    if wd_cron:
        total_runs += runs_per_month(wd_cron) or 0

    print(f"Checked {len(m.get('routines', []))} routines + watchdog.")
    if artifact_repos:
        print("Repos the watchdog's git sources must include (plus the ops "
              f"repo, listed first): {sorted(artifact_repos)}")
    if infos:
        print("Usage estimate: " + "; ".join(infos) +
              f"; fleet total ~{round(total_runs)} runs/month.")
    for w in warnings:
        print("WARN " + w)
    for e in errors:
        print("ERROR " + e)
    print(f"{'FAIL' if errors else 'PASS'}: {len(errors)} errors, "
          f"{len(warnings)} warnings.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
