"""Work out the next/current legal advice line from data/hours.json.

No scraping happens here, so this is safe to run as often as you like.
"""
import json
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HOURS_FILE = Path(__file__).parent / "data" / "hours.json"
DAYS_AHEAD = 7  # today plus the next 7 days


def load_hours(path=HOURS_FILE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _to_time(hhmm):
    hour, minute = hhmm.split(":")
    return time(int(hour), int(minute))


def _fmt(dt):
    # 9:30am, 1:00pm
    return dt.strftime("%I:%M%p").lstrip("0").lower()


def next_slot(org, now):
    """Return the next slot that hasn't ended yet, or None."""
    tz = now.tzinfo
    window = org.get("call_window_minutes")

    for offset in range(DAYS_AHEAD + 1):
        day = now.date() + timedelta(days=offset)
        weekday = day.strftime("%A")
        slots = sorted(org["schedule"].get(weekday, []), key=lambda s: s["start"])

        for slot in slots:
            start = datetime.combine(day, _to_time(slot["start"]), tzinfo=tz)
            end = datetime.combine(day, _to_time(slot["end"]), tzinfo=tz)
            if window:
                # Lines that fill up fast: only count the first N minutes.
                end = min(end, start + timedelta(minutes=window))

            if now < end:
                return {
                    "org": org["name"],
                    "phone": org["phone"],
                    "start": start,
                    "end": end,
                    "is_now": start <= now < end,
                    "day": "today" if offset == 0 else weekday,
                    "type": slot.get("type", "general"),
                    "label": slot.get("label"),
                }
    return None


def _line(rec):
    if rec["label"]:
        when = f"{rec['label']} {rec['day']}" if rec["day"] == "today" else f"{rec['label']} on {rec['day']}"
    elif rec["is_now"]:
        when = f"Now until {_fmt(rec['end'])}"
    elif rec["day"] == "today":
        when = f"{_fmt(rec['start'])} today"
    else:
        when = f"{_fmt(rec['start'])} on {rec['day']}"

    note = {"phone": " (phone only)", "walk-in": " (walk-in)"}.get(rec["type"], "")
    return f"{when}, {rec['org']}, {rec['phone']}{note}"


def generate_recommendations(hours, now=None):
    tz = ZoneInfo(hours.get("timezone", "America/Los_Angeles"))
    now = now or datetime.now(tz)

    recs = []
    for org in hours["organizations"]:
        if not org.get("recommend", True):
            continue
        if rec := next_slot(org, now):
            recs.append(rec)

    if not recs:
        return "No available services found. Please check back during business hours."

    recs.sort(key=lambda r: r["start"])
    header = ("Unless you are eligible for SALA (age 60+), here are the "
              "next/current available legal advice line(s):")
    return header + "\n" + "\n".join(_line(r) for r in recs)


def cron_lines(hours):
    """Cron schedule lines that run update_sheet.py just after every moment
    the message can change (a slot opening or closing).

    GitHub cron is in UTC, so each time is listed for both PST (UTC-8) and
    PDT (UTC-7). Runs are 1 minute after the change because GitHub often
    starts scheduled jobs a little late, and :00 is the busiest minute.
    """
    local_minutes = set()
    for org in hours["organizations"]:
        if not org.get("recommend", True):
            continue
        window = org.get("call_window_minutes")
        for slots in org["schedule"].values():
            for slot in slots:
                h, m = map(int, slot["start"].split(":"))
                start = h * 60 + m
                h, m = map(int, slot["end"].split(":"))
                end = h * 60 + m
                if window:
                    end = min(end, start + window)
                local_minutes.update({start, end})

    by_minute = {}
    for minutes in local_minutes:
        for utc_offset in (8, 7):
            utc = minutes + utc_offset * 60 + 1
            if utc >= 24 * 60:
                raise ValueError("A run would fall on the next UTC day; adjust the weekday field by hand.")
            by_minute.setdefault(utc % 60, set()).add(utc // 60)

    return [f'- cron: "{minute} {",".join(map(str, sorted(hrs)))} * * 1-5"'
            for minute, hrs in sorted(by_minute.items())]


if __name__ == "__main__":
    import sys
    if "--cron" in sys.argv:
        print("\n".join(cron_lines(load_hours())))
    else:
        print(generate_recommendations(load_hours()))
