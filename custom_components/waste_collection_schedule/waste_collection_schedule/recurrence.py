"""Recurrence helpers: expand a recurring schedule into concrete dates.

Many providers publish a *recurring* schedule — a weekday, or a base/anchor date
plus a weekly or fortnightly cadence — rather than explicit collection dates.
Turning that into a list of dates is the same arithmetic for every such source,
so it lives here as a core utility that any source (or service) can reuse.

What stays in the source is only the provider-specific part: reading the data to
work out the start date and cadence. Once you have those, use these helpers::

    from waste_collection_schedule import recurrence

    # base date + cadence -> N dates
    dates = recurrence.recurring(base, recurrence.FORTNIGHTLY, 13)

    # a weekday -> the next occurrence, then weekly
    start = recurrence.next_weekday(recurrence.WEEKDAYS["friday"])
    dates = recurrence.recurring(start, recurrence.WEEKLY, 26)

    # a cycle pinned to a historical anchor date
    dates = recurrence.recurring_from_anchor(anchor, recurrence.FORTNIGHTLY, 13)
"""

import datetime

WEEKLY = datetime.timedelta(weeks=1)
FORTNIGHTLY = datetime.timedelta(days=14)


def _index(rows: list[list[str]], start: int) -> dict[str, int]:
    """Build a {normalised name -> number} map from per-item synonym rows."""
    index: dict[str, int] = {}
    for offset, names in enumerate(rows, start=start):
        for name in names:
            index[name] = offset
    return index


# Weekday name (any of en/de/fr/it, lower-case) -> Python weekday number
# (Monday=0 .. Sunday=6). Multilingual so sources don't each carry a local dict
# (e.g. shawinigan publishes French day names). Use ``weekday()`` for tolerant
# lookup; the dict itself is kept for direct ``WEEKDAYS["friday"]`` access.
WEEKDAYS = _index(
    [
        ["monday", "montag", "lundi", "lunedì", "lunedi"],
        ["tuesday", "dienstag", "mardi", "martedì", "martedi"],
        ["wednesday", "mittwoch", "mercredi", "mercoledì", "mercoledi"],
        ["thursday", "donnerstag", "jeudi", "giovedì", "giovedi"],
        ["friday", "freitag", "vendredi", "venerdì", "venerdi"],
        ["saturday", "samstag", "samedi", "sabato"],
        ["sunday", "sonntag", "dimanche", "domenica"],
    ],
    start=0,
)

# Month name (en/de/fr/it, lower-case) -> month number (January=1 .. December=12).
MONTHS = _index(
    [
        ["january", "januar", "janvier", "gennaio"],
        ["february", "februar", "février", "fevrier", "febbraio"],
        ["march", "märz", "maerz", "mars", "marzo"],
        ["april", "avril", "aprile"],
        ["may", "mai", "maggio"],
        ["june", "juni", "juin", "giugno"],
        ["july", "juli", "juillet", "luglio"],
        ["august", "août", "aout", "agosto"],
        ["september", "septembre", "settembre"],
        ["october", "oktober", "octobre", "ottobre"],
        ["november", "novembre", "novembre"],
        ["december", "dezember", "décembre", "decembre", "dicembre"],
    ],
    start=1,
)


def weekday(name: str) -> int | None:
    """Resolve a weekday name (any supported language) to 0=Mon..6=Sun, or None."""
    return WEEKDAYS.get(str(name).strip().lower())


def month(name: str) -> int | None:
    """Resolve a month name (any supported language) to 1=Jan..12=Dec, or None."""
    return MONTHS.get(str(name).strip().lower())


def recurring(
    start: datetime.date, step: datetime.timedelta, count: int
) -> list[datetime.date]:
    """Return ``count`` dates starting at ``start``, each ``step`` apart."""
    return [start + step * i for i in range(count)]


def recurring_from_anchor(
    anchor: datetime.date,
    step: datetime.timedelta,
    count: int,
    *,
    after: datetime.date | None = None,
) -> list[datetime.date]:
    """Roll ``anchor`` forward by ``step`` until it reaches ``after``, then recur.

    ``after`` defaults to today. Use for a cycle pinned to a historical anchor
    date (e.g. a fortnightly schedule that started months ago): the anchor is
    advanced to the first occurrence on/after ``after``, then ``count`` dates
    ``step`` apart are returned.
    """
    after = after or datetime.date.today()
    current = anchor
    while current < after:
        current += step
    return recurring(current, step, count)


def next_weekday(
    weekday: int, *, on_or_after: datetime.date | None = None
) -> datetime.date:
    """Return the first date on ``weekday`` (0=Mon .. 6=Sun) on/after a date.

    ``on_or_after`` defaults to today.
    """
    base = on_or_after or datetime.date.today()
    return base + datetime.timedelta(days=(weekday - base.weekday()) % 7)


def most_recent_weekday(
    weekday: int, *, on_or_before: datetime.date | None = None
) -> datetime.date:
    """Return the most recent date on ``weekday`` (0=Mon .. 6=Sun) on/before a date.

    ``on_or_before`` defaults to today.
    """
    base = on_or_before or datetime.date.today()
    return base - datetime.timedelta(days=(base.weekday() - weekday + 7) % 7)
