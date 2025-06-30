import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ALIAS_MAP = {
    # US timezones
    "utc": "UTC",
    "est": "America/New_York",
    "edt": "America/New_York",
    "eastern": "America/New_York",
    "et": "America/New_York",
    "cst": "America/Chicago",
    "cdt": "America/Chicago",
    "central": "America/Chicago",
    "ct": "America/Chicago",
    "mst": "America/Denver",
    "mdt": "America/Denver",
    "mountain": "America/Denver",
    "mt": "America/Denver",
    "pst": "America/Los_Angeles",
    "pdt": "America/Los_Angeles",
    "pacific": "America/Los_Angeles",
    "pt": "America/Los_Angeles",

    # Canada
    "canada/pacific": "America/Vancouver",
    "canada/eastern": "America/Toronto",
    "canada/atlantic": "America/Halifax",

    # UK / Europe
    "bst": "Europe/London",
    "gmt": "Europe/London",
    "uk": "Europe/London",
    "west": "Europe/Lisbon",
    "cet": "Europe/Paris",
    "cest": "Europe/Paris",
    "eet": "Europe/Bucharest",
    "eest": "Europe/Bucharest",

    # Australia / NZ
    "aest": "Australia/Sydney",
    "aedt": "Australia/Sydney",
    "aus": "Australia/Sydney",
    "australia": "Australia/Sydney",
    "acst": "Australia/Adelaide",
    "acdt": "Australia/Adelaide",
    "awst": "Australia/Perth",
    "nzst": "Pacific/Auckland",
    "nzdt": "Pacific/Auckland",
    "nz": "Pacific/Auckland",

    # Asia
    "ist": "Asia/Kolkata",
    "india": "Asia/Kolkata",
    "china": "Asia/Shanghai",
    "cst-asia": "Asia/Shanghai",
    "kst": "Asia/Seoul",
    "kr": "Asia/Seoul",
    "jst": "Asia/Tokyo",
    "jp": "Asia/Tokyo",
    "sgt": "Asia/Singapore",
    "hkt": "Asia/Hong_Kong",
    "thai": "Asia/Bangkok",

    # Middle East
    "gst": "Asia/Dubai",
    "iran": "Asia/Tehran",
    "israel": "Asia/Jerusalem",

    # South America
    "brt": "America/Sao_Paulo",
    "arg": "America/Argentina/Buenos_Aires",

    # Africa
    "sast": "Africa/Johannesburg",
    "egypt": "Africa/Cairo",
}

def normalize_timezone(tz_input: str) -> str:
    key = tz_input.strip().lower()
    canonical = ALIAS_MAP.get(key, key)

    # Try ZoneInfo validation first
    try:
        ZoneInfo(canonical)
        return canonical
    except ZoneInfoNotFoundError:
        pass

    # Try to clean up malformed custom formats like 'europe/paris'
    if "/" in key:
        parts = key.split("/", 1)
        region = parts[0].title()
        city = parts[1].replace("_", " ").title().replace(" ", "_")
        fixed = f"{region}/{city}"
        try:
            ZoneInfo(fixed)
            return fixed
        except ZoneInfoNotFoundError:
            pass

    raise ValueError(f"Invalid timezone: '{tz_input}'")

def parse_time_string(raw: str) -> tuple[int, int]:
    """Support smart formats like '4pm', '04:00', '16', '4:30', '430'"""
    raw = raw.strip().lower().replace(" ", "")
    if raw.endswith("am") or raw.endswith("pm"):
        is_pm = "pm" in raw
        raw = raw.replace("am", "").replace("pm", "")
        if ":" in raw:
            hour, minute = map(int, raw.split(":"))
        elif len(raw) in [3, 4]:
            hour = int(raw[:-2])
            minute = int(raw[-2:])
        else:
            hour = int(raw)
            minute = 0
        if is_pm and hour < 12:
            hour += 12
        if not is_pm and hour == 12:
            hour = 0
    elif ":" in raw:
        hour, minute = map(int, raw.split(":"))
    elif len(raw) in [3, 4]:
        hour = int(raw[:-2])
        minute = int(raw[-2:])
    else:
        hour = int(raw)
        minute = 0

    if not (0 <= hour <= 23):
        raise ValueError("Hour must be between 0–23")
    if not (0 <= minute <= 59):
        raise ValueError("Minute must be between 0–59")

    return hour, minute

def local_to_utc(raw_time: str, tz_str: str) -> datetime.datetime:
    """Convert a smart time string in local timezone to UTC datetime."""
    try:
        tz_str = normalize_timezone(tz_str)
        tz = ZoneInfo(tz_str)
        now = datetime.datetime.now(tz)
        hour, minute = parse_time_string(raw_time)
        local_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return local_dt.astimezone(ZoneInfo("UTC"))
    except Exception as e:
        raise ValueError(f"Failed to convert to UTC: {e}")

def utc_to_local(utc_dt: datetime.datetime, tz_str: str) -> str:
    """Convert UTC datetime to HH:MM string in given timezone."""
    try:
        tz_str = normalize_timezone(tz_str)
        local_dt = utc_dt.astimezone(ZoneInfo(tz_str))
        return local_dt.strftime("%H:%M")
    except Exception as e:
        raise ValueError(f"Failed to convert to local time: {e}")

def get_2hr_blocks(start_hour: int, end_hour: int) -> list[str]:
    blocks = []
    for h in range(start_hour, end_hour):
        h1 = h % 24
        h2 = (h + 2) % 24
        blocks.append(f"{h1:02d}:00–{h2:02d}:00")
    return blocks
