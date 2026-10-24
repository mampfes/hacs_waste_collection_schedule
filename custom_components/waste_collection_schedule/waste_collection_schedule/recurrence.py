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

    # Good Friday (the one movable feast sources defer collections around)
    no_collection = recurrence.good_friday(2026)

    # Abbreviations, scoped to one language so "mar" can't mean both
    # March and mardi; Roman numerals only when asked for
    recurrence.month("Mär", "de", abbreviated=True)  # 3
    recurrence.weekday("Mo", "de", abbreviated=True)  # 0
    recurrence.month("XII", roman=True)  # 12
    recurrence.roman("iv")  # 4
"""

import datetime
import functools
import re
import unicodedata
from collections.abc import Iterable

import holidays as _holidays
from babel import Locale
from dateutil.easter import easter as _easter

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
    "ja",
)

# Languages whose *abbreviated* weekday names are also registered. Most scripts
# abbreviate ambiguously ("mar" is Tuesday in Spanish but March elsewhere), so
# only the wide names are indexed by default. Japanese is the exception: the
# single-kanji form ("火" for 火曜日) is how providers actually write weekdays,
# often run together ("火金" = Tuesday and Friday), and it collides with nothing.
_ABBREVIATED_DAY_LOCALES = ("ja",)


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
        widths = ["wide"]
        if attr == "days" and code in _ABBREVIATED_DAY_LOCALES:
            widths.append("abbreviated")
        for context in ("format", "stand-alone"):
            for width in widths:
                for number, name in table.get(context, {}).get(width, {}).items():
                    _register(index, name, number)
    return index


# Weekday name (any supported language, lower-case) -> Python weekday number
# (Monday=0 .. Sunday=6). Use ``weekday()`` for tolerant lookup; the dict is also
# kept for direct ``WEEKDAYS["friday"]`` access.
WEEKDAYS = _build_index("days")

# Month name (any supported language, lower-case) -> month number (1..12).
MONTHS = _build_index("months")

# Inflected month forms CLDR does not carry, keyed by language: the Slovenian
# genitive, which providers print in dated notes ("2. januar se nadomešča 3.
# januarja"). Registered without overriding a form that already names a month.
_EXTRA_MONTH_FORMS = {
    "sl": (
        "januarja",
        "februarja",
        "marca",
        "aprila",
        "maja",
        "junija",
        "julija",
        "avgusta",
        "septembra",
        "oktobra",
        "novembra",
        "decembra",
    ),
}
for _forms in _EXTRA_MONTH_FORMS.values():
    for _number, _name in enumerate(_forms, start=1):
        _register(MONTHS, _name, _number)


@functools.cache
def _locale_index(attr: str, code: str, abbreviated: bool) -> dict[str, int]:
    """{name -> number} for one language: wide names, plus abbreviations if asked.

    Abbreviations are registered without their trailing period ("Jan." and
    "Jan" both become "jan"), in both CLDR contexts.
    """
    table = getattr(Locale.parse(code), attr)
    index: dict[str, int] = {}
    for width in ("wide", "abbreviated") if abbreviated else ("wide",):
        for context in ("format", "stand-alone"):
            for number, name in table.get(context, {}).get(width, {}).items():
                _register(index, name.strip().rstrip("."), number)
    if attr == "months":
        for number, name in enumerate(_EXTRA_MONTH_FORMS.get(code, ()), start=1):
            _register(index, name, number)
    return index


def _lookup(
    attr: str,
    global_index: dict[str, int],
    name: str,
    locale: str | None,
    abbreviated: bool,
) -> int | None:
    key = str(name).strip().lower()
    if locale is None:
        if abbreviated:
            raise ValueError(
                f"abbreviated {attr} names are ambiguous across languages; "
                "pass locale= as well"
            )
        return global_index.get(key)
    if abbreviated:
        key = key.rstrip(".")
    return _locale_index(attr, locale, abbreviated).get(key)


def _names(attr: str, locale: str, abbreviated: bool) -> tuple[str, ...]:
    table = getattr(Locale.parse(locale), attr)["stand-alone"]
    names = table["abbreviated" if abbreviated else "wide"]
    return tuple(names[number].rstrip(".") for number in sorted(names))


def weekday(
    name: str, locale: str | None = None, *, abbreviated: bool = False
) -> int | None:
    """Resolve a weekday name to 0=Mon..6=Sun, or None.

    Without ``locale`` any supported language's full name resolves. With a
    language code (``"de"``) only that language's names do, and
    ``abbreviated=True`` adds its abbreviations ("Mo", "Mo."). Abbreviations
    always need a locale: "mar" is Tuesday in French but March elsewhere.
    """
    return _lookup("days", WEEKDAYS, name, locale, abbreviated)


def month(
    name: str,
    locale: str | None = None,
    *,
    abbreviated: bool = False,
    roman: bool = False,
) -> int | None:
    """Resolve a month name to 1=Jan..12=Dec, or None.

    ``locale`` and ``abbreviated`` work as for :func:`weekday` ("Mär", "Okt."
    with ``locale="de", abbreviated=True``). ``roman=True`` also accepts the
    Roman numerals I..XII some calendars print as month headers; it is opt-in
    because "I" or "V" in running text is rarely a month.
    """
    number = _lookup("months", MONTHS, name, locale, abbreviated)
    if number is None and roman:
        numeral = _roman_number(name)
        number = numeral if numeral is not None and numeral <= 12 else None
    return number


def weekday_names(locale: str, *, abbreviated: bool = False) -> tuple[str, ...]:
    """One language's weekday names, Monday first, as CLDR prints them stand-alone.

    A trailing abbreviation period is dropped: ``weekday_names("de",
    abbreviated=True)`` is ``("Mo", "Di", ..., "So")``.
    """
    return _names("days", locale, abbreviated)


def month_names(locale: str, *, abbreviated: bool = False) -> tuple[str, ...]:
    """One language's month names, January first (see :func:`weekday_names`).

    ``month_names("de", abbreviated=True)`` is ``("Jan", "Feb", "Mär", ...)``.
    """
    return _names("months", locale, abbreviated)


_ROMAN_VALUES = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)
_ROMAN_RE = re.compile(r"M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})")


def roman(text: str) -> int | None:
    """A Roman numeral ("IV", "xii") as an int, or None if it is not one.

    Only well-formed numerals count ("IIII" and "IIV" are None), in either case.
    """
    return _roman_number(text)


def _roman_number(text: str) -> int | None:
    key = str(text).strip().upper()
    if not key or not _ROMAN_RE.fullmatch(key):
        return None
    total = 0
    for value, numeral in _ROMAN_VALUES:
        while key.startswith(numeral):
            total += value
            key = key[len(numeral) :]
    return total


def to_roman(number: int) -> str:
    """An int 1..3999 as an upper-case Roman numeral (4 -> "IV")."""
    if not 1 <= number <= 3999:
        raise ValueError(f"no Roman numeral for {number}")
    parts = []
    for value, numeral in _ROMAN_VALUES:
        count, number = divmod(number, value)
        parts.append(numeral * count)
    return "".join(parts)


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


def good_friday(year: int) -> datetime.date:
    """Return Good Friday (two days before Easter Sunday) for ``year``.

    Good Friday is the movable feast waste providers most often suspend or
    defer a collection on, in every country that observes it, so the Easter
    arithmetic lives here rather than being hand-rolled per source. Pair it
    with a :class:`~waste_collection_schedule.preprocessors.HolidayShift`
    adjust callable that encodes the provider's own deferral rule.
    """
    return _easter(year) - datetime.timedelta(days=2)


def us_federal_holidays(
    years: Iterable[int] | int,
    *,
    subdiv: str | None = None,
    observed: bool = True,
) -> dict[datetime.date, str]:
    """US federal holiday dates for the given year(s), via the ``holidays`` library.

    Returns a ``{date: holiday_name}`` dict so callers can inspect *which*
    holiday falls on a given date (useful for holiday-specific adjustment
    rules such as Thanksgiving's Wednesday shift).

    A thin, shared wrapper so sources compute the same calendar rather than
    each hand-rolling "n-th weekday of the month" arithmetic for Martin
    Luther King Jr. Day, Presidents'/Washington's Birthday, Memorial Day,
    Labor Day, Columbus Day and Thanksgiving (plus the fixed-date holidays'
    weekend-observed shift).

    ``subdiv`` selects a state/territory subdivision, which can change the
    set (e.g. Tennessee's calendar adds Good Friday and drops Columbus Day).
    ``observed`` mirrors the ``holidays`` library's own flag: when True
    (the default) a fixed-date holiday landing on a weekend also yields its
    shifted weekday as a second entry with the same name; pass
    ``observed=False`` for the raw calendar dates only.

    The returned dict is safe to use with ``in`` — ``date in holidays``
    checks keys, just like before.
    """
    year_list = [years] if isinstance(years, int) else list(years)
    return dict(_holidays.US(years=year_list, subdiv=subdiv, observed=observed))
