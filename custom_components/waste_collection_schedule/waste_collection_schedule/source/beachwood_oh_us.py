import datetime
import logging
import re
from functools import lru_cache
from typing import ClassVar, final

from curl_cffi import requests as curl_requests
from waste_collection_schedule import field_terms, recurrence, response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import PdfTextParser
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import RowTransformer

# The city publishes a "Rubbish Pick Up Days" PDF mapping each street to one
# fixed collection day (Monday-Thursday); on that day both the rubbish and the
# recycling cart are emptied. Every page repeats a three-line header before its
# entries, and a street name may span several lines when it carries a "(...)"
# directional qualifier. The PDF is re-fetched and re-parsed on every run:
# CivicPlus DocumentCenter 404s HEAD requests and sends no ETag/Last-Modified,
# so a change cannot be detected without downloading the file (~12 KB), and a
# cache could only ever be validated against the full body anyway. Plain
# `requests` is 404-blocked; the curl_cffi session BaseSource provides is not.

_TITLE = "City of Beachwood, OH"
_DESCRIPTION = (
    "Source for City of Beachwood (OH, USA) residential rubbish and recycling."
)
_URL = "https://www.beachwoodohio.com/226/Rubbish-Recycling-More"
_PDF_URL = (
    "https://www.beachwoodohio.com/DocumentCenter/View/"
    "4553/Rubbish-Pick-Up-Days--By-Street"
)

_LOGGER = logging.getLogger(__name__)

_HEADER_LINES = frozenset({"City of Beachwood", "Rubbish Pick Up Days"})
_DATE_LINE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")

_RUBBISH = "Rubbish"
_RECYCLING = "Recycling"

# datetime.date.weekday() convention: Monday is 0.
_THURSDAY = recurrence.weekday("Thursday")

# Holiday-name stems. The `holidays` library localises full names, so every rule
# matches on the stem as a substring — a rename to "Thanksgiving Day" once
# disabled the Thanksgiving shift entirely. test_beachwood_oh_us.py pins these
# against the live calendar.
_THANKSGIVING = "Thanksgiving"
_COLUMBUS_DAY = "Columbus Day"
_VETERANS_DAY = "Veterans Day"
# In the shared Ohio calendar but not observed by Beachwood Public Works.
_EXCLUDED_HOLIDAYS = (_COLUMBUS_DAY, _VETERANS_DAY)

# The published PDF prints this Cedar Road section without its opening
# parenthesis and the city will not fix it. Left alone it becomes a bogus
# top-level street; repaired on read it joins the normal cascade.
_PDF_FIXUPS = {
    "Cedar Road East bound from Fenway to Community)": (
        "Cedar Road (East bound from Fenway to Community)"
    ),
}


def _normalize(name: str) -> str:
    return " ".join(name.split())


def _split_street(street: str) -> tuple[str, str]:
    """Split a street into ``(base, qualifier)``.

    The qualifier is a parenthetical suffix such as ``(North of Timberlane)``;
    a street without one has an empty qualifier.
    """
    idx = street.find("(")
    if idx == -1:
        return street, ""
    return street[:idx].rstrip(), street[idx:]


def _join_street(base: str, qualifier: str) -> str:
    return f"{base} {qualifier}".strip() if qualifier else base.strip()


def _parse_street_table(
    pdf_text: str, source: "BaseSource | None" = None
) -> dict[str, str]:
    """Map every street to its weekday from the PDF's text layer.

    Each entry is one or more street-name lines followed by a single
    day-of-week line. The repeated page header (two fixed lines plus a date)
    is filtered wherever it appears, so pages can be processed as one stream.
    """
    name = response_shape.source_name(source)
    street_day: dict[str, str] = {}
    parts: list[str] = []
    for raw in pdf_text.splitlines():
        line = raw.strip()
        if not line or line in _HEADER_LINES or _DATE_LINE_RE.match(line):
            continue
        if recurrence.weekday(line) is not None:
            street = _normalize(" ".join(parts))
            response_shape.expect(
                bool(street),
                source_name=name,
                detail=f"day line {line!r} is not preceded by a street name",
            )
            street = _PDF_FIXUPS.get(street, street)
            if street.count("(") != street.count(")"):
                _LOGGER.warning(
                    "Beachwood PDF entry %r has unbalanced parentheses — likely "
                    "a new typo in the source; add it to _PDF_FIXUPS.",
                    street,
                )
            if street in street_day and street_day[street] != line:
                _LOGGER.warning(
                    "Beachwood PDF lists %r twice with different days (%s, %s); "
                    "using the last one.",
                    street,
                    street_day[street],
                    line,
                )
            street_day[street] = line
            parts = []
        else:
            parts.append(line)

    response_shape.expect(
        not parts,
        source_name=name,
        detail=f"trailing lines with no day of week: {parts!r}",
    )
    response_shape.expect(
        bool(street_day),
        source_name=name,
        detail="no street/day entries found — the PDF layout may have changed",
    )
    return street_day


def _resolve_street(records: str, source: "BaseSource | None" = None) -> list[str]:
    """Resolve the selected street to its collection weekday.

    ``records`` is the PDF text from ``parse``. Returns a single-item list — the
    weekday name — for the recurrence expander.
    """
    table = _parse_street_table(records, source)
    params = source.params if source is not None else {}
    base = params.get("street_base") or ""
    qualifier = params.get("street_qualifier") or ""

    day = table.get(_join_street(base, qualifier))
    if day is None:
        matches = {
            name: value
            for name, value in table.items()
            if _split_street(name)[0] == base
        }
        if not matches:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_base", base, sorted({_split_street(s)[0] for s in table})
            )
        if len(matches) > 1:
            raise SourceArgumentRequiredWithSuggestions(
                "street_qualifier",
                f"{base} is split into sections with different collection days — "
                "choose the section that matches your address.",
                sorted(_split_street(name)[1] for name in matches),
            )
        if qualifier:
            raise SourceArgumentNotFound(
                "street_qualifier",
                qualifier,
                f"{base} is not split into sections; leave the section field blank.",
            )
        (day,) = matches.values()
    return [day]


def _describe(weekday_name: str, source: "BaseSource | None"):
    """Weekly Rubbish + Recycling on the street's published weekday.

    From the next occurrence of that weekday on/after today through
    31 December of the current calendar year.
    """
    weekday = recurrence.weekday(weekday_name)
    if weekday is None:
        raise ValueError(f"unknown weekday: {weekday_name!r}")
    today = datetime.date.today()
    start = recurrence.next_weekday(weekday, on_or_after=today)
    year_end = datetime.date(today.year, 12, 31)
    for key in (_RUBBISH, _RECYCLING):
        yield Schedule(key, start, until=year_end)


@lru_cache(maxsize=4)
def _observed_holidays(year: int) -> dict[datetime.date, str]:
    """Beachwood-observed public holidays for ``year`` ± 1 as ``{date: name}``.

    The shared US federal calendar for Ohio (already OPM-shifted), minus
    Columbus Day and Veterans Day, which Public Works does not close for.
    Keyed by year so a long-running Home Assistant process still gets the right
    calendar after a New Year rather than the one it started with.
    """
    return {
        day: holiday_name
        for day, holiday_name in recurrence.us_federal_holidays(
            range(year - 1, year + 2), subdiv="OH", observed=True
        ).items()
        if not any(excluded in holiday_name for excluded in _EXCLUDED_HOLIDAYS)
    }


def _adjust(
    collection_date: datetime.date, key: str, source: "BaseSource | None"
) -> datetime.date:
    """Apply Beachwood's holiday shifting rules to one collection date.

    - Thanksgiving: only the Thursday collection moves, to the Wednesday before
      Thanksgiving; every other day that week is unaffected.
    - Every other observed holiday: a collection on or after the holiday, within
      the same Monday-Sunday week, is delayed by one day.
    """
    holidays = _observed_holidays(collection_date.year)
    monday = collection_date - datetime.timedelta(days=collection_date.weekday())
    for offset in range(7):
        day = monday + datetime.timedelta(days=offset)
        holiday_name = holidays.get(day)
        if holiday_name is None:
            continue
        if _THANKSGIVING in holiday_name:
            if collection_date.weekday() == _THURSDAY:
                return day - datetime.timedelta(days=1)
        elif collection_date >= day:
            return collection_date + datetime.timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = _TITLE
    DESCRIPTION = _DESCRIPTION
    URL = _URL
    COUNTRY = "us"
    API_URL = _PDF_URL
    RAISE_ON_EMPTY = True

    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@GreenDavidA"]

    TEST_CASES: ClassVar[dict] = {
        "Beacon Drive": {"street_base": "Beacon Drive", "street_qualifier": ""},
        "East Silsby Road": {
            "street_base": "East Silsby Road",
            "street_qualifier": "",
        },
        "Fairmount Boulevard (East bound from Sulgrave, and West bound to Richmond)": {
            "street_base": "Fairmount Boulevard",
            "street_qualifier": (
                "(East bound from Sulgrave, and West bound to Richmond)"
            ),
        },
        "Fairmount Boulevard (West bound from 24471)": {
            "street_base": "Fairmount Boulevard",
            "street_qualifier": "(West bound from 24471)",
        },
        # The section whose PDF entry is missing its opening parenthesis; only
        # resolvable once _PDF_FIXUPS has repaired it.
        "Cedar Road (East bound from Fenway to Community)": {
            "street_base": "Cedar Road",
            "street_qualifier": "(East bound from Fenway to Community)",
        },
        "Fernwood Road": {"street_base": "Fernwood Road", "street_qualifier": ""},
        "Halworth Road": {"street_base": "Halworth Road", "street_qualifier": ""},
        "Woodside Lane": {"street_base": "Woodside Lane", "street_qualifier": ""},
    }

    PARAMS = (
        cascading_select(
            ("street_base", field_terms.STREET),
            ("street_qualifier", "Section of street"),
        ),
    )

    WASTE_TYPES: ClassVar[list[wt.WasteType]] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            'Check your collection day in the <a href="'
            "https://www.beachwoodohio.com/DocumentCenter/View/"
            '4553/Rubbish-Pick-Up-Days--By-Street" target="_blank">'
            "Rubbish Pick Up Days (PDF)</a> published by the City of Beachwood. "
            "Select your street and submit. Most streets need nothing more; a "
            "few are split into sections with different days, and for those a "
            "second dropdown then asks which section matches your address."
        ),
    }

    @classmethod
    def get_choices(cls, field: str, selections: dict[str, str]) -> list[str]:
        # Runs at config-flow time, before a Source (and its session) exists,
        # so the PDF is fetched with a standalone browser-impersonating session.
        session = curl_requests.Session(impersonate="chrome")
        resp = session.get(_PDF_URL, timeout=30)
        resp.raise_for_status()
        table = _parse_street_table(PdfTextParser()(resp))

        if field == "street_base":
            return sorted({_split_street(street)[0] for street in table})

        if field == "street_qualifier":
            base = selections.get("street_base")
            if not base:
                return []
            matches = [s for s in table if _split_street(s)[0] == base]
            if len(matches) <= 1:
                return []  # single-section street — no qualifier to pick
            return sorted(_split_street(street)[1] for street in matches)

        return []

    parse = PdfTextParser(min_chars=500)
    preprocess = Compose(
        _resolve_street,
        RecurrenceExpander(_describe),
        HolidayShift(_adjust),
    )
    transform = RowTransformer(
        type_value_map={
            _RUBBISH: wt.GENERAL_WASTE,
            _RECYCLING: wt.RECYCLABLES,
        }
    )
