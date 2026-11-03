"""Heuristic best-time-to-post computation (local hours per audience age)."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Ranked local posting hours; earlier = better.
PEAK_HOURS = {
    "13-17": [20, 16, 21, 12, 7, 18],
    "18-24": [21, 12, 19, 17, 9, 23],
    "25-34": [20, 12, 7, 18, 21, 9],
    "35+": [19, 8, 13, 20, 12, 17],
}


def get_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def best_hours(audience_age: str, count: int) -> list[int]:
    return sorted(PEAK_HOURS.get(audience_age, PEAK_HOURS["18-24"])[:count])


def upcoming_slots(tz: str, audience_age: str, per_day: int, n: int, now: datetime | None = None) -> list[datetime]:
    """Next `n` UTC datetimes that fall on the best local hours."""
    zone = get_zone(tz)
    now = now or datetime.now(timezone.utc)
    local_now = now.astimezone(zone)
    hours = best_hours(audience_age, per_day)
    slots: list[datetime] = []
    day = local_now.date()
    while len(slots) < n:
        for h in hours:
            slot = datetime(day.year, day.month, day.day, h, 0, tzinfo=zone)
            if slot > local_now:
                slots.append(slot.astimezone(timezone.utc))
                if len(slots) == n:
                    break
        day += timedelta(days=1)
    return slots
