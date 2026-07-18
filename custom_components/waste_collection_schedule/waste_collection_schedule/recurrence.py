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

    # "the 2nd Tuesday of the month" -> the next occurrence, or a run of them
    second_tuesday = recurrence.monthly_nth_weekday(1, 2)
    next_year = recurrence.monthly_nth_weekdays(1, 2, 12)

    # US federal holidays (for a HolidayShift preprocess), for one state's rules
    tn_holidays = recurrence.us_federal_holidays(range(2026, 2028), subdiv="TN")
"""

import datetime
import unicodedata
from collections.abc import Iterable

import holidays as _holidays
from babel import Locale

WEEKLY = datetime.timedelta(weeks=1)
FORTNIGHTLY = datetime.timedelta(days=14)


# Languages we source month/weekday names for, via Babel's CLDR data. Adding a
# language is just adding its code here: the names (in every grammatical form
# CLDR carries) come from Babel, so sources never hand-roll a weekday/month dict.
# Covers the regions the project's sources span.
_LOCALES = (
    "en",
    "de",
    "fr",
    "it",
    "pl",
    "nl",
    "es",
    "pt",
    "sv",
    "da",
    "nb",
    "nn",
    "fi",
    "is",
    "cs",
    "sk",
    "sl",
    "hr",
    "hu",
    "ro",
    "et",
    "lv",
    "lt",
    "ga",
)


def _strip_accents(text: str) -> str:
    """Drop combining marks: 'février' -> 'fevrier', 'lunedì' -> 'lunedi'."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def _german_expand(text: str) -> str:
    """German umlaut/eszett spelling: 'märz' -> 'maerz', 'straße' -> 'strasse'."""
    return (
        text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    )


def _register(index: dict[str, int], name: str, number: int) -> None:
    """Register a name and its accent-stripped / umlaut-expanded variants."""
    key = name.strip().lower()
    if not key:
        return
    for variant in (key, _strip_accents(key), _german_expand(key)):
        index.setdefault(variant, number)


def _build_index(attr: str) -> dict[str, int]:
    """Build a {name -> number} map from Babel for every language in _LOCALES.

    ``attr`` is ``"days"`` (keyed 0=Mon..6=Sun) or ``"months"`` (1=Jan..12=Dec);
    both Babel orderings already match our convention. Both the ``format`` and
    ``stand-alone`` CLDR contexts are included, so grammatically inflected names
    (e.g. Polish genitive "stycznia" vs nominative "styczeń") all resolve.
    """
    index: dict[str, int] = {}
    for code in _LOCALES:
        try:
            locale = Locale.parse(code)
        except Exception:
            continue
        table = getattr(locale, attr)
        for context in ("format", "stand-alone"):
            for number, name in table.get(context, {}).get("wide", {}).items():
                _register(index, name, number)
    return index


# Weekday name (any supported language, lower-case) -> Python weekday number
# (Monday=0 .. Sunday=6). Use ``weekday()`` for tolerant lookup; the dict is also
# kept for direct ``WEEKDAYS["friday"]`` access.
WEEKDAYS = _build_index("days")

# Month name (any supported language, lower-case) -> month number (1..12).
MONTHS = _build_index("months")


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


def recurring_within(
    start: datetime.date,
    step: datetime.timedelta,
    *,
    not_before: datetime.date,
    until: datetime.date,
) -> list[datetime.date]:
    """Phase-aligned occurrences within an inclusive ``[not_before, until]`` window.

    ``start`` fixes the cadence *phase* (which day the cycle lands on); it need
    not itself be inside the window. The cycle is advanced or retreated to the
    first occurrence on/after ``not_before``, then every occurrence up to and
    including ``until`` is returned. Returns ``[]`` if the window is empty.

    Use for seasonal schedules where a cadence only applies within part of the
    year (e.g. garden waste collected weekly in April but fortnightly May-Sep),
    by issuing one windowed :class:`Schedule` per season segment.
    """
    if step <= datetime.timedelta(0):
        raise ValueError("step must be positive")

    current = start
    if current < not_before:
        current += step * ((not_before - current) // step)
        while current < not_before:
            current += step
    else:
        while current - step >= not_before:
            current -= step

    dates: list[datetime.date] = []
    while current <= until:
        dates.append(current)
        current += step
    return dates


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


def _nth_weekday_of_month(
    year: int, month: int, weekday: int, n: int
) -> datetime.date | None:
    """Date of the n-th (``n == -1``: last) ``weekday`` in a given month.

    Returns ``None`` when that month has no n-th occurrence (e.g. a 5th
    Monday in a month with only four).
    """
    first = datetime.date(year, month, 1)
    next_month = (
        datetime.date(year + 1, 1, 1)
        if month == 12
        else datetime.date(year, month + 1, 1)
    )
    if n == -1:
        last_day = next_month - datetime.timedelta(days=1)
        return last_day - datetime.timedelta(days=(last_day.weekday() - weekday) % 7)
    if n < 1:
        raise ValueError("n must be 1-5 (the n-th occurrence), or -1 for the last")
    candidate = first + datetime.timedelta(
        days=(weekday - first.weekday()) % 7 + 7 * (n - 1)
    )
    return candidate if candidate.month == month else None


def monthly_nth_weekday(
    weekday: int, n: int, *, on_or_after: datetime.date | None = None
) -> datetime.date:
    """Return the first "n-th weekday of a month" on/after a date.

    ``weekday`` is 0=Mon .. 6=Sun; ``n`` is 1-5 for the n-th occurrence within
    the month, or -1 for the last occurrence (which may be a 4th or 5th,
    depending on the month/year — e.g. "last Monday of May"). ``on_or_after``
    defaults to today.

    The reusable building block for a "2nd Tuesday of the month" style
    cadence, and for a US-federal-holiday rule such as "3rd Monday in
    January" (Martin Luther King Jr. Day) or "4th Thursday in November"
    (Thanksgiving) — though :func:`us_federal_holidays` already computes
    those for you via the ``holidays`` library.
    """
    base = on_or_after or datetime.date.today()
    year, month = base.year, base.month
    for _ in range(24):  # at most two years ahead
        candidate = _nth_weekday_of_month(year, month, weekday, n)
        if candidate is not None and candidate >= base:
            return candidate
        month += 1
        if month > 12:
            month = 1
            year += 1
    raise ValueError(
        f"no {n!r}-th weekday {weekday!r} found within 24 months of {base}"
    )


def monthly_nth_weekdays(
    weekday: int,
    n: int,
    count: int,
    *,
    on_or_after: datetime.date | None = None,
) -> list[datetime.date]:
    """Return ``count`` consecutive monthly occurrences of the n-th weekday.

    Each occurrence anchors the search for the next, so this returns one date
    per month (in order) rather than every "n-th weekday" that happens to
    fall within a fixed window (months are not a fixed-length step, so this
    is not expressible via :func:`recurring`).
    """
    base = on_or_after or datetime.date.today()
    dates: list[datetime.date] = []
    for _ in range(count):
        found = monthly_nth_weekday(weekday, n, on_or_after=base)
        dates.append(found)
        base = found + datetime.timedelta(days=1)
    return dates


def us_federal_holidays(
    years: Iterable[int] | int,
    *,
    subdiv: str | None = None,
    observed: bool = True,
) -> set[datetime.date]:
    """US federal holiday dates for the given year(s), via the ``holidays`` library.

    A thin, shared wrapper so sources compute the same calendar rather than
    each hand-rolling "n-th weekday of the month" arithmetic for Martin
    Luther King Jr. Day, Presidents'/Washington's Birthday, Memorial Day,
    Labor Day, Columbus Day and Thanksgiving (plus the fixed-date holidays'
    weekend-observed shift).

    ``subdiv`` selects a state/territory subdivision, which can change the
    set (e.g. Tennessee's calendar adds Good Friday and drops Columbus Day).
    ``observed`` mirrors the ``holidays`` library's own flag: when True
    (the default) a fixed-date holiday landing on a weekend also yields its
    shifted weekday as a second entry; pass ``observed=False`` for the raw
    calendar dates only.
    """
    year_list = [years] if isinstance(years, int) else list(years)
    return set(_holidays.US(years=year_list, subdiv=subdiv, observed=observed).keys())
