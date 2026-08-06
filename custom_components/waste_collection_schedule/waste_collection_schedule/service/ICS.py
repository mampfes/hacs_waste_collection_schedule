import datetime
import logging
import re
import unicodedata
from html.parser import HTMLParser
from os import getcwd
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple
from urllib.parse import urljoin

import jinja2
from bs4 import BeautifulSoup, Tag
from curl_cffi import requests
from icalevents import icalevents

from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.parsers import Parser
    from waste_collection_schedule.retrievers import (
        HeadersArgs,
        ParamsType,
        Response,
    )

    type UrlArgs = Callable[..., str] | str
    type QueryArgs = Callable[..., ParamsType] | ParamsType
    type IcsEntries = list[tuple[datetime.date, str]]

#: One preparatory request in an :class:`IcsSessionRetriever` chain. Keys:
#: ``url`` (required), ``method`` (default ``"GET"``), ``params`` / ``data`` /
#: ``json`` / ``headers``, ``encoding`` (forced on this step's response before
#: anything reads its text; ``None``, the default, leaves the transport's own
#: detection alone), ``select`` (``{<select> name: config parameter}``, resolved
#: against this step's own response, see :func:`resolve_select_option`),
#: ``extract`` (``callable(response, context) -> dict`` merged into the running
#: context) and ``cookies`` (``callable(**context) -> dict`` merged into the
#: running cookie jar, evaluated after ``extract``).
type IcsSessionStep = "dict[str, Any]"

_LOGGER = logging.getLogger(__name__)


class IcsEvent(NamedTuple):
    date: datetime.date
    title: str
    location: str | None = None
    description: str | None = None


# RFC 5545 allows only ALPHA, DIGIT and "-" in a property name.
_PROPERTY_NAME = re.compile(r"[A-Za-z0-9-]+")

# An RFC 5545 DATE value: eight digits and nothing else (a DATE-TIME carries a
# "T" and a time, and often a trailing "Z").
_DATE_VALUE = re.compile(r"\d{8}")

# An RFC 5545 DATE *or* DATE-TIME value, which is all a DTEND may legally carry.
_DATE_OR_DATETIME_VALUE = re.compile(r"\d{8}(?:T\d{6}Z?)?")

# A whole VTIMEZONE component, so an empty one can be recognised and dropped.
_VTIMEZONE_BLOCK = re.compile(r"BEGIN:VTIMEZONE\r?\n(.*?)END:VTIMEZONE\r?\n", re.DOTALL)

# An RRULE UNTIL carrying a bare DATE (no time component follows the digits).
_BARE_UNTIL = re.compile(r"(UNTIL=\d{8})(?=[;\r\n]|$)")

# A duration written without the "T" that must precede a time component, so
# "-P10H" where RFC 5545 requires "-PT10H". Only the H/M/S forms are wrong;
# "-P1D" and "-P1DT10H" are both valid and do not match.
_TIMELESS_DURATION = re.compile(r"(TRIGGER[^:\r\n]*:-?P)(\d+[HMS])")

# The few German letters NFKD does not decompose, so a folded UID stays legible
# rather than losing the character entirely.
_UID_TRANSLITERATIONS = str.maketrans(
    {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        "ß": "ss",
    }
)


def _drop_malformed_content_lines(ics_data: str) -> str:
    """Drop content lines whose property name is not a valid iCalendar name.

    A provider that emits something like ``X-WR-TIMEZONE','EUROPE/BERLIN:``
    makes icalendar abort the entire feed ("Content line could not be parsed
    into parts"), even though the offending property carries nothing the
    schedule needs. No valid property can have such a name, so dropping the
    line (together with any folded continuation lines) is lossless for
    scheduling and leaves well-formed feeds untouched.
    """
    kept: list[str] = []
    dropping = False
    for line in ics_data.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        if stripped[:1] in (" ", "\t"):
            # Folded continuation line: it belongs to the preceding property.
            if not dropping:
                kept.append(line)
            continue
        dropping = False
        positions = [i for i in (stripped.find(":"), stripped.find(";")) if i >= 0]
        if positions:
            separator = min(positions)
            if separator > 0 and not _PROPERTY_NAME.fullmatch(stripped[:separator]):
                dropping = True
                continue
        kept.append(line)
    return "".join(kept)


def _is_date_only(line: str) -> bool:
    """True if a DTSTART/DTEND content line carries a DATE (not DATE-TIME) value."""
    name, _, value = line.partition(":")
    if "VALUE=DATE-TIME" in name.upper():
        return False
    if "VALUE=DATE" in name.upper():
        return True
    return _DATE_VALUE.fullmatch(value.strip()) is not None


def _repair_event_block(block: list[str]) -> list[str]:
    """Drop a VEVENT's DTEND when its value type disagrees with DTSTART's."""
    date_only_start = any(
        line.upper().startswith("DTSTART") and _is_date_only(line) for line in block
    )
    if not date_only_start:
        return block
    kept: list[str] = []
    dropping = False
    for line in block:
        if line[:1] in (" ", "\t"):
            # Folded continuation line: it belongs to the preceding property.
            if not dropping:
                kept.append(line)
            continue
        dropping = line.upper().startswith("DTEND") and not _is_date_only(line)
        if not dropping:
            kept.append(line)
    return kept


def _map_event_blocks(ics_data: str, repair: "Callable[[list[str]], list[str]]") -> str:
    """Rebuild a feed with ``repair`` applied to each VEVENT's lines.

    Lines outside a VEVENT are passed through untouched, so a repair that needs
    to see a whole event (a property whose validity depends on that event's
    DTSTART) can be written as a function of the block alone.
    """
    out: list[str] = []
    block: list[str] | None = None
    for line in ics_data.splitlines(keepends=True):
        upper = line.upper()
        if upper.startswith("BEGIN:VEVENT"):
            if block is not None:
                out.extend(repair(block))
            block = [line]
            continue
        if block is None:
            out.append(line)
            continue
        block.append(line)
        if upper.startswith("END:VEVENT"):
            out.extend(repair(block))
            block = None
    if block is not None:
        out.extend(repair(block))
    return "".join(out)


def _drop_mismatched_dtend(ics_data: str) -> str:
    """Drop a DTEND whose value type disagrees with its VEVENT's DTSTART.

    RFC 5545 requires DTEND to use the same value type as DTSTART. A provider
    that pairs an all-day ``DTSTART;VALUE=DATE`` with a date-time ``DTEND``
    (``DTSTART;VALUE=DATE:20260709`` / ``DTEND:20260710T000000``) leaves
    dateutil comparing a date against a datetime, which aborts the feed.
    Nothing in the conversion reads DTEND — only DTSTART decides the collection
    day — so dropping the offending line is lossless, and a feed whose two
    properties agree is returned untouched.
    """
    if "DTEND" not in ics_data:
        return ics_data
    return _map_event_blocks(ics_data, _repair_event_block)


def _dtstart_line(block: "list[str]") -> "str | None":
    for line in block:
        if line.upper().startswith("DTSTART"):
            return line.rstrip("\r\n")
    return None


def _repair_until_block(block: "list[str]") -> "list[str]":
    """Give a bare-DATE RRULE UNTIL the time its DTSTART's value type requires."""
    dtstart = _dtstart_line(block)
    if dtstart is None or _is_date_only(dtstart):
        # A date-only DTSTART wants a date-only UNTIL, which is what it has.
        return block
    value = _content_line_value(dtstart)
    parameters = dtstart[: len(dtstart) - len(value)].upper()
    # RFC 5545: when DTSTART is timezone-aware, UNTIL must be a UTC date-time;
    # when it is floating, UNTIL is floating too.
    aware = value.strip().endswith("Z") or "TZID=" in parameters
    suffix = "T000000Z" if aware else "T000000"
    return [
        _BARE_UNTIL.sub(r"\g<1>" + suffix, line)
        if line.upper().startswith("RRULE")
        else line
        for line in block
    ]


def _match_until_to_dtstart(ics_data: str) -> str:
    """Expand an RRULE UNTIL that is a DATE where DTSTART is a DATE-TIME.

    RFC 5545 requires UNTIL to carry the same value type as its event's
    DTSTART. A provider that pairs a date-with-time ``DTSTART:20260729T070000``
    with a bare ``UNTIL=20310724`` gives icalendar a recurrence rule it cannot
    build, which aborts the whole feed. Expanding the date to a date-time on
    the same day keeps the recurrence ending where the provider meant it to,
    and an event whose two properties already agree is left untouched.
    """
    if "UNTIL=" not in ics_data:
        return ics_data
    return _map_event_blocks(ics_data, _repair_until_block)


def _drop_empty_vtimezones(ics_data: str) -> str:
    """Drop VTIMEZONE components that define nothing, and references to them.

    RFC 5545 requires a VTIMEZONE to carry at least one STANDARD or DAYLIGHT
    subcomponent. Some generators emit the shell on its own
    (``BEGIN:VTIMEZONE`` / ``TZID:W. Europe Standard Time`` /
    ``END:VTIMEZONE``), so every ``TZID=`` parameter naming it points at a
    timezone with no offset, and icalendar either rejects the feed or produces
    a naive datetime that cannot be compared against an aware one. A definition
    that carries no offset cannot move a collection day, so dropping it and the
    parameters referencing it leaves DTSTART's date exactly where it was. A
    feed with real VTIMEZONE definitions is returned untouched.
    """
    if "BEGIN:VTIMEZONE" not in ics_data:
        return ics_data
    empty: list[str] = []

    def drop(match: "re.Match[str]") -> str:
        body = match.group(1)
        if "BEGIN:STANDARD" in body.upper() or "BEGIN:DAYLIGHT" in body.upper():
            return match.group(0)
        tzid = re.search(r"^TZID:(.*?)\r?$", body, re.MULTILINE)
        if tzid:
            empty.append(tzid.group(1))
        return ""

    ics_data = _VTIMEZONE_BLOCK.sub(drop, ics_data)
    for tzid in empty:
        ics_data = re.sub(
            rf';TZID="?{re.escape(tzid)}"?(?=[;:])',
            "",
            ics_data,
        )
    return ics_data


def _content_line_value(line: str) -> str:
    """The value part of a content line: everything after the first bare colon.

    A parameter value may itself be quoted and contain a colon
    (``DTEND;TZID="Etc:GMT":...``), so quoted runs are skipped rather than the
    line simply being split on its first colon.
    """
    in_quotes = False
    for index, character in enumerate(line):
        if character == '"':
            in_quotes = not in_quotes
        elif character == ":" and not in_quotes:
            return line[index + 1 :]
    return ""


def _drop_malformed_dtend(ics_data: str) -> str:
    """Drop a DTEND whose value is neither a DATE nor a DATE-TIME.

    Providers that assemble the calendar by string concatenation sometimes emit
    a corrupted end time ("20260408T.300", "20260204T 1.000"), which stops
    icalendar reading the feed at all. Nothing in the conversion looks at DTEND
    (only DTSTART decides the collection day), so dropping the line is lossless,
    and a feed whose DTEND values are well formed is returned untouched.
    """
    if "DTEND" not in ics_data:
        return ics_data
    kept: list[str] = []
    dropping = False
    for line in ics_data.splitlines(keepends=True):
        if line[:1] in (" ", "\t"):
            # Folded continuation line: it belongs to the preceding property.
            if not dropping:
                kept.append(line)
            continue
        dropping = line.upper().startswith(
            "DTEND"
        ) and not _DATE_OR_DATETIME_VALUE.fullmatch(
            _content_line_value(line.rstrip("\r\n")).strip()
        )
        if not dropping:
            kept.append(line)
    return "".join(kept)


def _ascii_fold_uid_value(value: str) -> str:
    if value.isascii():
        return value
    folded = unicodedata.normalize("NFKD", value.translate(_UID_TRANSLITERATIONS))
    return folded.encode("ascii", "ignore").decode("ascii")


def _ascii_fold_uids(ics_data: str) -> str:
    """Replace non-ASCII characters in UID values.

    Some generators put the address (umlauts and all) into the UID, which older
    icalendar releases refuse to parse. The value is only ever compared against
    other UIDs (to inherit a summary onto a recurrence exception), so folding it
    to ASCII keeps that grouping intact while removing the characters that break
    the feed. ASCII UIDs, which is nearly all of them, are returned untouched.
    """
    if ics_data.isascii():
        return ics_data
    return re.sub(
        r"^(UID[^:\r\n]*:)([^\r\n]*)",
        lambda m: m.group(1) + _ascii_fold_uid_value(m.group(2)),
        ics_data,
        flags=re.MULTILINE,
    )


def _repair_ics_data(ics_data: str) -> str:
    """Repair common provider malformations before handing data to icalevents.

    Every fix here targets a value the schedule does not depend on, or a purely
    syntactic defect; DTSTART and SUMMARY, which are all the conversion reads,
    are never altered.
    """
    # Give bare EXDATE;VALUE=DATE lines a time component so dateutil can compare
    # them against timezone-aware recurrences.
    ics_data = re.sub(
        r"(EXDATE;VALUE=DATE:[0-9]+)\r?\n",
        lambda m: m.group(1) + "T010000\n",
        ics_data,
    )

    # Fix truncated DTSTART/DTEND values where the time portion is missing
    # after the 'T' separator (e.g. "DTSTART;TZID=Europe/Berlin:20260505T").
    ics_data = re.sub(
        r"(DT(?:START|END)[^:]*:\d{8})T(\r?\n)",
        r"\g<1>T000000\g<2>",
        ics_data,
    )

    # Strip TZID from all-day (VALUE=DATE) DTSTART/DTEND lines.
    # TZID is only valid on DATETIME values; combining it with VALUE=DATE is
    # malformed ICS. When present, icalendar creates timezone-aware datetime
    # objects for the recurrence rule while EXDATE lines (which lack TZID)
    # stay naive, causing a TypeError when dateutil compares them.
    ics_data = re.sub(
        r"(DT(?:START|END));TZID=[^;:]+;(VALUE=DATE:)",
        r"\1;\2",
        ics_data,
    )

    # Drop VTIMEZONE definitions that carry no offset, and the TZID parameters
    # that reference them; they name a timezone that does not exist.
    ics_data = _drop_empty_vtimezones(ics_data)

    # Give an RRULE UNTIL the value type its event's DTSTART requires; a bare
    # date against a date-time DTSTART is a rule icalendar cannot build.
    ics_data = _match_until_to_dtstart(ics_data)

    # Drop the CREATED / LAST-MODIFIED metadata timestamps.
    # icalevents dereferences their `.dt`, so a malformed value (e.g. RESO's
    # doubled "20260101T000000ZT000000Z") aborts parsing of the whole feed even
    # though these properties play no part in scheduling. Nothing in the
    # conversion reads them, so removing them keeps DTSTART/SUMMARY intact and
    # tolerates any corruption of these non-essential properties.
    ics_data = re.sub(
        r"^(?:CREATED|LAST-MODIFIED)[;:].*(?:\r?\n[ \t].*)*\r?\n",
        "",
        ics_data,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    # Give an alarm's duration the "T" that must precede its time component;
    # icalendar rejects the whole feed over a "-P10H" that means "-PT10H".
    # TRIGGER plays no part in scheduling, so the repair cannot move a date.
    ics_data = _TIMELESS_DURATION.sub(r"\1T\2", ics_data)

    # Drop property lines whose name is not valid iCalendar; icalendar aborts
    # the whole feed on one of them.
    ics_data = _drop_malformed_content_lines(ics_data)

    # Drop a DTEND whose value is corrupted; nothing in the conversion reads
    # DTEND, and the bad value aborts the feed.
    ics_data = _drop_malformed_dtend(ics_data)

    # Drop a DTEND that disagrees with its DTSTART's value type; nothing in the
    # conversion reads DTEND, and the mismatch aborts the feed.
    ics_data = _drop_mismatched_dtend(ics_data)

    # Fold non-ASCII UID values to ASCII; the schedule never reads a UID except
    # to match a recurrence exception to its parent.
    ics_data = _ascii_fold_uids(ics_data)

    return ics_data


def _event_location_description(e: Any) -> tuple[str | None, str | None]:
    raw_loc = getattr(e, "location", None)
    if isinstance(raw_loc, str):
        loc = raw_loc.strip() or None
    else:
        loc = None
    raw_desc = getattr(e, "description", None)
    if isinstance(raw_desc, str):
        desc = raw_desc.strip() or None
    else:
        desc = None
    return loc, desc


class ICS:
    def __init__(
        self,
        offset: int | None = None,
        regex: str | None = None,
        split_at: str | None = None,
        title_template: str = "{{date.summary}}",
    ):
        self._offset = offset
        self._regex = None
        self._split_at = None

        if regex is not None:
            self._regex = re.compile(regex)

        if split_at is not None:
            self._split_at = re.compile(split_at)

        self._title_template = title_template

    def convert(self, ics_data: str) -> list[tuple[datetime.date, str]]:
        # calculate start- and end-date for recurring events
        start_date = datetime.datetime.now(datetime.UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if self._offset is not None:
            start_date -= datetime.timedelta(days=self._offset)
        end_date = start_date + datetime.timedelta(days=365)

        ics_data = _repair_ics_data(ics_data)

        # parse ics data
        events: list[Any] = icalevents.events(
            start=start_date, end=end_date, string_content=ics_data.encode()
        )

        # Inherit summary for recurrence exceptions that lack one.
        # Some ICS generators omit SUMMARY on replacement VEVENTs
        # (those with RECURRENCE-ID), expecting clients to inherit
        # from the parent recurring event.
        uid_summaries: dict = {}
        for e in events:
            if e.summary and e.recurring:
                uid_summaries[e.uid] = e.summary
        for e in events:
            if not e.summary and hasattr(e, "recurrence_id") and e.recurrence_id:
                if e.uid in uid_summaries:
                    e.summary = uid_summaries[e.uid]

        entries: list[tuple[datetime.date, str]] = []

        for e in events:
            # calculate date
            dtstart: datetime.date | None = None

            if isinstance(e.start, datetime.datetime):
                dtstart = e.start.date()
            elif isinstance(e.start, datetime.date):
                dtstart = e.start

            # Only continue if a start date can be found in the entry
            if dtstart is not None:
                if self._offset is not None:
                    dtstart += datetime.timedelta(days=self._offset)

                environment = jinja2.Environment()
                title_template = environment.from_string(self._title_template)
                entry_title = title_template.render(date=e)

                if self._regex is not None:
                    match = self._regex.match(entry_title)
                    if match:
                        entry_title = match.group(1)

                if self._split_at is not None:
                    entry_title_list = re.split(self._split_at, entry_title)
                    entries.extend(
                        (dtstart, t.strip().title()) for t in entry_title_list
                    )
                else:
                    entries.append((dtstart, entry_title))

        return entries

    def convert_events(self, ics_data: str) -> list[IcsEvent]:
        # calculate start- and end-date for recurring events
        start_date = datetime.datetime.now(datetime.UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if self._offset is not None:
            start_date -= datetime.timedelta(days=self._offset)
        end_date = start_date + datetime.timedelta(days=365)

        ics_data = _repair_ics_data(ics_data)

        # parse ics data
        events: list[Any] = icalevents.events(
            start=start_date, end=end_date, string_content=ics_data.encode()
        )

        # Inherit summary for recurrence exceptions that lack one.
        # Some ICS generators omit SUMMARY on replacement VEVENTs
        # (those with RECURRENCE-ID), expecting clients to inherit
        # from the parent recurring event.
        uid_summaries: dict = {}
        for e in events:
            if e.summary and e.recurring:
                uid_summaries[e.uid] = e.summary
        for e in events:
            if not e.summary and hasattr(e, "recurrence_id") and e.recurrence_id:
                if e.uid in uid_summaries:
                    e.summary = uid_summaries[e.uid]

        entries: list[IcsEvent] = []

        for e in events:
            # calculate date
            dtstart: datetime.date | None = None

            if isinstance(e.start, datetime.datetime):
                dtstart = e.start.date()
            elif isinstance(e.start, datetime.date):
                dtstart = e.start

            # Only continue if a start date can be found in the entry
            if dtstart is not None:
                if self._offset is not None:
                    dtstart += datetime.timedelta(days=self._offset)

                environment = jinja2.Environment()
                title_template = environment.from_string(self._title_template)
                entry_title = title_template.render(date=e)

                if self._regex is not None:
                    match = self._regex.match(entry_title)
                    if match:
                        entry_title = match.group(1)

                loc, desc = _event_location_description(e)

                if self._split_at is not None:
                    entry_title_list = re.split(self._split_at, entry_title)
                    entries.extend(
                        IcsEvent(
                            dtstart,
                            t.strip().title(),
                            location=loc,
                            description=desc,
                        )
                        for t in entry_title_list
                    )
                else:
                    entries.append(
                        IcsEvent(
                            dtstart,
                            entry_title,
                            location=loc,
                            description=desc,
                        )
                    )

        return entries


def _resolve_arg(mapping: Any, source: "BaseSource", **extra: Any) -> Any:
    """Resolve a retriever constructor argument against the source's params.

    A literal is returned unchanged; a callable is invoked with ``**extra`` plus
    ``**source.params``, so a URL or query template can be written in terms of
    the user's arguments (and, for the per-year retriever, the ``year``).
    """
    if callable(mapping):
        return mapping(**extra, **source.params)
    return mapping


def _resolve_context(mapping: Any, context: "dict[str, Any]") -> Any:
    """Resolve a step argument against a running request context.

    The context is the source's params plus whatever the chain has established
    so far (``year``, ``variant``, and every value a step's ``extract``
    returned), so a later step's URL or query can be written in terms of an
    earlier step's answer.
    """
    if callable(mapping):
        return mapping(**context)
    return mapping


def _calendar_years(lookahead_month: "int | None") -> list[int]:
    """The calendar years a schedule can span as at today.

    Always the current year, plus next year from ``lookahead_month`` onwards,
    because providers on a per-year calendar publish the following year some
    weeks before it starts.

    ``None`` means the provider does not publish per year at all: its feed is a
    rolling window that already covers the year turning, so the chain runs once
    whatever today's date is. Fetching a second time would only duplicate every
    entry.
    """
    today = datetime.date.today()
    years = [today.year]
    if lookahead_month is not None and today.month >= lookahead_month:
        years.append(today.year + 1)
    return years


#: Default request headers for the configured (user-driven) ICS feed request.
#: Several providers 403 a bare client, so the generic engine has always sent a
#: browser user-agent; ``headers`` in the user's own configuration is merged on
#: top of this, key by key.
ICS_FEED_HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _coerce_int(value: Any) -> "int | None":
    """Coerce a PARAMS-supplied value to int, tolerating None/empty/str/float.

    NumberSelector/YAML/UI callers may hand back a str, float or int; the ICS
    service and the year-field arithmetic below both want a plain int.
    """
    if value is None or value == "":
        return None
    return int(value)


def _flatten_params(params: "dict | None") -> "list[tuple[str, Any]] | None":
    """Flatten a params dict to (key, value) pairs, repeating list-valued keys.

    curl_cffi stringifies list-valued params as Python repr instead of
    repeating the key like ``requests`` does; flatten explicitly so multi-value
    fields like ``types[]`` still round-trip as repeated query/form keys.
    """
    if not params:
        return None
    return [
        (k, item)
        for k, v in params.items()
        for item in (v if isinstance(v, list) else [v])
    ]


def _fetch_url(
    url: str,
    params: "dict | None",
    method: str,
    headers: dict,
    verify_ssl: bool,
    impersonate: Any,
) -> str:
    # impersonate is free-text (any curl_cffi-supported browser string, e.g.
    # "chrome124"); curl_cffi's own type is a closed Literal, which a
    # user-configured value can never statically satisfy, hence Any here.
    flat_params = _flatten_params(params)

    if method == "GET":
        r = requests.get(
            url,
            params=flat_params,
            headers=headers,
            verify=verify_ssl,
            impersonate=impersonate,
        )
    elif method == "POST":
        r = requests.post(
            url,
            data=flat_params,
            headers=headers,
            verify=verify_ssl,
            impersonate=impersonate,
        )
    else:
        raise SourceArgumentNotFoundWithSuggestions("method", method, ["GET", "POST"])

    r.raise_for_status()

    if r.content.startswith(b"\xef\xbb\xbf"):
        r.encoding = "UTF-8-SIG"
    else:
        r.encoding = "utf-8"

    return r.text


def _fetch_file(file: str) -> str:
    try:
        path = Path(file)
        with path.open() as f:
            return f.read()
    except FileNotFoundError as e:
        _LOGGER.error(f"Working directory: '{getcwd()}'")
        raise SourceArgumentException(
            "file", f"File '{path.resolve()}' not found"
        ) from e


class IcsConfiguredRetriever(RetrieverFunc):
    """Fetch the ICS feed the *user's own configuration* names.

    The ICS platform's own retriever, and the one shape on this platform where
    nothing is fixed by a provider module: the endpoint, the HTTP method, the
    query/form arguments, the headers and the TLS handling all come out of the
    source's ``PARAMS``. It is what the generic ``ics`` source and, through it,
    the ~178 ``doc/ics/yaml/*.yaml`` providers use, so a fix here reaches every
    one of them instead of one module.

    It reads these params off ``source.params``, all optional unless noted:

    * ``url`` / ``file`` — exactly one of them (declare them as an
      ``alternatives()`` pair). ``webcal://`` is rewritten to ``https://``. A
      ``{%Y}`` placeholder anywhere in the URL is replaced with the year.
    * ``method`` — ``"GET"`` (default) or ``"POST"``; anything else raises
      ``SourceArgumentNotFoundWithSuggestions``.
    * ``params`` — query arguments for a GET, form fields for a POST. A
      list-valued entry is sent as a repeated key rather than a Python repr.
    * ``year_field`` — the ``params`` key carrying the year, for a provider
      that takes it as a field rather than in the URL. Requires ``params``.
    * ``headers`` — merged over :data:`ICS_FEED_HEADERS`, key by key.
    * ``verify_ssl`` — default ``True``.
    * ``impersonate`` — a ``curl_cffi`` browser target (e.g. ``"chrome"``) for
      a provider behind TLS fingerprinting.
    * ``version`` — deprecated and ignored; setting it logs a warning, so an
      existing YAML config carrying it keeps working.

    Where the URL or ``year_field`` makes the feed year-specific, this fetches
    the current year and, in December, next year as well, best effort: a
    provider that has not published the following calendar yet must not break
    the current one. Note that branch cannot be observed by cassette replay for
    eleven months of the year.

    Returns the feed bodies as a list of ``str`` (not responses), because the
    ``file`` branch has no response to return. Pair it with
    :class:`IcsConfiguredParser`, which takes exactly that::

        retrieve = IcsConfiguredRetriever()
        parse = IcsConfiguredParser()
    """

    def __call__(self, source: "BaseSource") -> "list[str]":
        params = source.params
        if params.get("version") is not None:
            _LOGGER.warning(
                "The 'version' parameter is deprecated and has no effect anymore."
            )

        url = params.get("url")
        file = params.get("file")
        year_field = params.get("year_field")
        method = params.get("method") or "GET"
        verify_ssl = params.get("verify_ssl")
        if verify_ssl is None:
            verify_ssl = True
        impersonate = params.get("impersonate")
        request_params = params.get("params")

        headers = dict(ICS_FEED_HEADERS)
        headers.update(params.get("headers") or {})

        if url is not None:
            url = re.sub("^webcal", "https", url)

            if "{%Y}" in url or year_field is not None:
                # url contains wildcard or params contains year field
                now = datetime.datetime.now()

                this_year_params = dict(request_params) if request_params else None
                url_this_year = url.replace("{%Y}", str(now.year))
                if year_field is not None:
                    if request_params is None:
                        raise SourceArgumentExceptionMultiple(
                            ("params", "year_field"),
                            "year_field specified without params",
                        )
                    this_year_params = dict(request_params)
                    this_year_params[year_field] = str(now.year)

                texts = [
                    _fetch_url(
                        url_this_year,
                        this_year_params,
                        method,
                        headers,
                        verify_ssl,
                        impersonate,
                    )
                ]

                if now.month == 12:
                    # also get data for next year if we are already in december
                    url_next_year = url.replace("{%Y}", str(now.year + 1))
                    next_year_params = dict(request_params) if request_params else None
                    # year_field implies request_params (checked above for
                    # url_this_year; request_params is never reassigned in
                    # between), so next_year_params is never None here -- the
                    # `is not None` guard just keeps that provable locally
                    # instead of relying on the earlier raise.
                    if year_field is not None and next_year_params is not None:
                        next_year_params[year_field] = str(now.year + 1)

                    try:
                        texts.append(
                            _fetch_url(
                                url_next_year,
                                next_year_params,
                                method,
                                headers,
                                verify_ssl,
                                impersonate,
                            )
                        )
                    except Exception:
                        # ignore if fetch for next year fails
                        pass

                return texts

            return [
                _fetch_url(
                    url, request_params, method, headers, verify_ssl, impersonate
                )
            ]

        # alternatives() above guarantees exactly one of url/file is set.
        assert file is not None
        return [_fetch_file(file)]


class IcsConfiguredParser:
    """Convert the configured feed bodies, with the *user's own* ICS options.

    The matching ``parse`` for :class:`IcsConfiguredRetriever`: it takes the
    list of feed bodies that retriever returns and converts each one, merging
    the events. Where :class:`~waste_collection_schedule.parsers.IcsEventsParser`
    is configured by the source module, this one is configured by whoever set
    the source up, reading ``offset``, ``split_at``, ``regex`` and
    ``title_template`` off ``source.params`` at fetch time.

    Yields :class:`IcsEvent` records, so LOCATION and DESCRIPTION survive to the
    calendar entry.
    """

    def __call__(
        self, raw: "list[str]", source: "BaseSource | None" = None
    ) -> "list[IcsEvent]":
        params = source.params if source is not None else {}
        ics = ICS(
            offset=_coerce_int(params.get("offset")),
            split_at=params.get("split_at"),
            regex=params.get("regex"),
            title_template=params.get("title_template") or "{{date.summary}}",
        )
        events: list[IcsEvent] = []
        for text in raw:
            events.extend(ics.convert_events(text))
        return events


class IcsYearRetriever(RetrieverFunc):
    """GET one ICS feed per calendar year the schedule can span.

    For providers that publish a calendar per year instead of a rolling window,
    so a single GET goes blank the moment the year turns. This fetches the
    current year and, from ``lookahead_month`` onwards, next year as well, and
    returns the list of responses; :class:`IcsFeedsParser` merges them.

    Some of these providers also move the per-year path around (a new one every
    time they re-platform), or accept the street only in a particular casing.
    ``fallback_url`` / ``fallback_params`` describe a second request to try for
    any year whose first attempt fails or comes back with no dated entries.

    A year that yields nothing from both attempts raises, so a silently empty
    calendar is never mistaken for "no collections this year".

    Where one address's calendar is spread over several parallel feeds (a
    separate paper contractor per district, say), ``optional_urls`` names the
    extras: they are merged into the same year's result and each is best
    effort, because a contractor that does not serve the address publishes no
    feed for it.

    Args:
        url: the feed URL, as ``callable(year=..., **source.params) -> str``
            or a literal.
        params: optional query arguments, as
            ``callable(year=..., **source.params) -> dict`` or a literal.
        headers: optional headers, literal or ``callable(**source.params)``.
        timeout: per-request timeout in seconds (default 30).
        lookahead_month: from this month (1-12) onwards, also fetch year + 1.
            Default 12: in December, next year's calendar is pulled too.
            ``None`` for a rolling feed that is not published per year.
        fallback_url: optional alternative URL, same calling convention as
            ``url``, retried for a year the first attempt did not satisfy.
        fallback_params: optional alternative query arguments for that retry;
            ignored unless ``fallback_url`` is set.
        optional_urls: additional feeds merged into the same year's result, as
            ``callable(year=..., **source.params) -> list[str]`` or a literal
            list. Every one is fetched, and one that fails or comes back empty
            is simply left out. For a provider that splits an address's
            calendar across parallel per-contractor or per-waste-type feeds
            that exist for some districts and not others, where a missing feed
            means "that contractor does not serve this address", not an error.
        require_lookahead: whether a failure fetching a lookahead year is fatal.
            Default ``True``, which is this retriever's long-standing contract:
            a per-year provider that stops answering for a year it used to
            publish has usually moved its URLs, and that is worth surfacing.
            Set ``False`` for a provider that simply publishes next year late,
            so the current year still propagates on its own. (Note the sibling
            :class:`IcsSessionRetriever` defaults this the other way round.)

    Example::

        retrieve = IcsYearRetriever(
            url=lambda year, **_: f"{API}/{YEAR_PATHS.get(year, DEFAULT_PATH)}",
            params=lambda street, **_: {"street": street, "link": "ical"},
            fallback_url=API,
        )
    """

    def __init__(
        self,
        *,
        url: "UrlArgs",
        params: "QueryArgs" = None,
        headers: "HeadersArgs" = None,
        timeout: int = 30,
        lookahead_month: "int | None" = 12,
        fallback_url: "UrlArgs | None" = None,
        fallback_params: "QueryArgs" = None,
        optional_urls: "Callable[..., Sequence[str]] | Sequence[str] | None" = None,
        require_lookahead: bool = True,
    ):
        self.url = url
        self.params = params
        self.headers = headers
        self.timeout = timeout
        self.lookahead_month = lookahead_month
        self.fallback_url = fallback_url
        self.fallback_params = fallback_params
        self.optional_urls = optional_urls
        self.require_lookahead = require_lookahead

    def __call__(self, source: "BaseSource") -> "list[Response]":
        feeds: list[Response] = []
        for index, year in enumerate(_calendar_years(self.lookahead_month)):
            try:
                feeds.extend(self._fetch_year(source, year))
            except Exception:
                if index == 0 or self.require_lookahead:
                    raise
        return feeds

    def _fetch_year(self, source: "BaseSource", year: int) -> "list[Response]":
        response = self._attempt(source, year, self.url, self.params)
        if response is None and self.fallback_url is not None:
            response = self._attempt(
                source, year, self.fallback_url, self.fallback_params
            )
        if response is None:
            raise ValueError(f"No ICS entries found for {year}")
        return [response, *self._optional(source, year)]

    def _optional(self, source: "BaseSource", year: int) -> "list[Response]":
        """The extra feeds for a year, best effort: a missing one is skipped."""
        if self.optional_urls is None:
            return []
        urls = self._resolve(self.optional_urls, source, year=year) or ()
        feeds = [self._attempt(source, year, url, None) for url in urls]
        return [feed for feed in feeds if feed is not None]

    def _attempt(
        self,
        source: "BaseSource",
        year: int,
        url: "UrlArgs",
        params: "QueryArgs",
    ) -> "Response | None":
        """Request one year's feed; return it only if it holds dated entries.

        Returns ``None`` for a transport error or an empty calendar, which is
        what makes the caller move on to the fallback request. Reading the body
        is normally the parser's job, but "did this year's calendar come back
        populated?" is the only question that can drive the retry, and it is an
        ICS question, which is why this retriever lives beside the converter.
        """
        try:
            response = source.session.get(
                self._resolve(url, source, year=year),
                params=self._resolve(params, source, year=year),
                headers=self._resolve(self.headers, source),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception:
            # Any failure here just means "try the fallback request".
            return None
        return response if ICS().convert(response.text) else None

    @staticmethod
    def _resolve(mapping: Any, source: "BaseSource", **extra: Any) -> Any:
        """Resolve a constructor argument against the source's params.

        Callables also receive ``year``, so a URL or query template can select
        the right calendar without the source writing a ``retrieve`` of its own.
        """
        return _resolve_arg(mapping, source, **extra)


class _FormStateParser(HTMLParser):
    """Scrape every ``<select><option>`` pair keyed by the select's ``name``."""

    def __init__(self):
        super().__init__()
        self.select_options: dict[str, list[tuple[str, str]]] = {}
        self._current_select: str | None = None
        self._current_option_value: str | None = None
        self._current_option_text: list[str] = []

    def _finalize_option(self):
        if self._current_select is None or self._current_option_value is None:
            return
        text = " ".join(part.strip() for part in self._current_option_text).strip()
        self.select_options[self._current_select].append(
            (self._current_option_value or "", text)
        )
        self._current_option_value = None
        self._current_option_text = []

    def finalize(self):
        self._finalize_option()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "select" and "name" in attributes:
            name = attributes["name"]
            if name is None:
                return
            self._finalize_option()
            self._current_select = name
            self.select_options.setdefault(self._current_select, [])
        elif tag == "option" and self._current_select is not None:
            self._finalize_option()
            self._current_option_value = attributes.get("value", "")
            self._current_option_text = []

    def handle_data(self, data):
        if self._current_option_value is not None:
            self._current_option_text.append(data)

    def handle_endtag(self, tag):
        if tag == "option":
            self._finalize_option()
        elif tag == "select":
            self._finalize_option()
            self._current_select = None

    def get_options(self, field_name: str) -> list[str]:
        return [
            text or value
            for value, text in self.select_options.get(field_name, [])
            if (text or value)
        ]


def select_options(html: str, field_name: str) -> "list[str]":
    """The option labels of one ``<select>`` on a page, in document order.

    For the cascading form wizard whose every step answers with a fresh
    ``<select>`` of the values that are valid *given the previous choices* (a
    city, then its streets, then that street's house numbers), so the value the
    next request may submit can only be read off the response in hand. Falls
    back to an option's ``value`` attribute where it carries no text, and skips
    an option that has neither.
    """
    parser = _FormStateParser()
    parser.feed(html)
    parser.finalize()
    parser.close()
    return parser.get_options(field_name)


def _normalize(value: object) -> str:
    return " ".join(str(value).split()).casefold()


def resolve_select_option(field_name: str, value: str, options: "list[str]") -> str:
    """Match a configured value to one of a form's own options, or explain.

    An exact match wins; failing that the comparison ignores case and collapses
    runs of whitespace, because a user typing an address rarely reproduces a
    provider's own capitalisation and spacing. A miss raises against
    ``field_name`` (the *config parameter's* name, not the form field's) so the
    HA UI blames the field the user filled in, listing the options that do work.
    An empty option list means an earlier choice in the cascade cannot be
    combined with this one at all, which is what the second message says.
    """
    if value in options:
        return value
    normalized_options = {_normalize(option): option for option in options}
    normalized_value = _normalize(value)
    if normalized_value in normalized_options:
        return normalized_options[normalized_value]
    if options:
        raise SourceArgumentNotFoundWithSuggestions(field_name, value, options)
    raise SourceArgumentNotFound(
        field_name, value, "please check the other address arguments and try again."
    )


class IcsSessionRetriever(RetrieverFunc):
    """Establish the server's idea of "your address", then GET the ICS feed.

    The ICS counterpart to
    :class:`~waste_collection_schedule.retrievers.AthosWasteManagementRetriever`:
    a small, fixed chain of preparatory requests, expressed as data rather than
    per-source control flow, followed by the calendar download. It covers the
    two shapes a plain :class:`IcsYearRetriever` GET cannot reach:

    * **Stateful POST-then-GET.** Submitting the address stores it in a
      server-side session and the feed is then read back with a bare GET that
      carries no address at all. Both requests share ``source.session``, so the
      session cookie ties them together.
    * **Chained id lookups.** The feed needs ids the site only hands out one
      request at a time (city id, then street id), threaded forward through the
      query and a growing cookie jar.

    * **Cascading form selects.** The site will not accept a known-good address
      submitted outright: each step answers with a fresh ``<select>`` of the
      values valid *given the previous choices*, and the next request may only
      submit one of those. A step's ``select`` names which of them to read::

          {"url": API, "select": {"Ort": "city"}}

      That scrapes ``<select name="Ort">`` off this step's own response, matches
      the ``city`` parameter against its options (ignoring case and repeated
      whitespace, see :func:`resolve_select_option`), and replaces ``city`` in
      the context with the provider's own spelling, so a later step's ``data``
      submits the value the form will accept. A value the form does not offer
      raises against the config parameter, listing the ones it does.

    Each entry in ``steps`` runs in order and may contribute to a running
    ``context`` (the source's params, plus ``year``, ``variant``, and every key
    a step's ``extract`` returned) and to a running cookie jar. Every callable
    argument is called with ``**context``, so later steps and the feed request
    are written in terms of what the earlier ones found::

        retrieve = IcsSessionRetriever(
            steps=[
                {
                    "url": SEARCH_URL,
                    "params": lambda city, **_: {"term": city},
                    "extract": lambda r, ctx: {"city_id": r.json()[0]["id"]},
                    "cookies": lambda city_id, **_: {"stadt": str(city_id)},
                },
            ],
            feed_url=ICS_URL,
            feed_params=lambda city_id, year, **_: {"stadt": city_id, "jahr": year},
        )
        parse = IcsFeedsParser(parsers.IcsParser())

    The chain runs once per calendar year the schedule can span (see
    ``lookahead_month``) and, within a year, once per entry in ``variants``, so
    the whole thing returns a list of feed responses for :class:`IcsFeedsParser`
    to merge.

    Args:
        feed_url: the calendar URL (literal or ``callable(**context) -> str``).
            ``None`` (the default) means the last step's own response *is* the
            calendar, for a provider that answers the form submission with the
            feed rather than redirecting to a download URL; at least one step
            is then required.
        steps: ordered preparatory requests; see :data:`IcsSessionStep`. May be
            empty, which reduces this to a per-year GET.
        feed_params: query arguments for the feed request (literal or
            ``callable(**context)``).
        cookies: cookies seeded before the first step (literal or
            ``callable(**context)``); steps add to the same jar.
        variants: values the whole chain is repeated for, one feed each, bound
            in the context as ``variant``. For a provider that splits one
            address's calendar across parallel feeds (a separate contractor per
            waste stream). ``None`` runs the chain once with ``variant=None``.
        headers: default headers for every request; a step may override its own.
        timeout: per-request timeout in seconds (default 30).
        encoding: response encoding forced on the feed response before its text
            is read; ``None`` (default) leaves the transport's own detection
            alone. A *step* whose own response is read (by ``select`` or
            ``extract``) declares its own ``encoding`` key, because a provider
            that mis-declares the charset of its HTML pages does not necessarily
            mis-declare it on the calendar download.
        lookahead_month: from this month (1-12) onwards, also run for year + 1.
            Default 12: in December, next year's calendar is fetched too.
            ``None`` for a provider whose feed is a rolling window rather than
            a per-year calendar, so the chain runs exactly once.
        require_lookahead: by default a failure fetching a lookahead year is
            tolerated (the provider has simply not published it yet) while the
            current year still propagates. Set ``True`` to insist on both.
        require_entries: check each feed converts to at least one dated entry,
            and raise if not. Off by default; prefer the source's
            ``RAISE_ON_EMPTY``, and reach for this only when an empty *year*
            must fail even though a sibling year came back populated.
        empty_message: the message ``require_entries`` raises with, for a
            provider that can say something more useful than the default about
            why the address found nothing.
    """

    def __init__(
        self,
        *,
        feed_url: "UrlArgs | None" = None,
        steps: "Sequence[IcsSessionStep]" = (),
        feed_params: "QueryArgs" = None,
        cookies: "Callable[..., dict] | dict | None" = None,
        variants: "Sequence[Any] | None" = None,
        headers: "HeadersArgs" = None,
        timeout: int = 30,
        encoding: str | None = None,
        lookahead_month: "int | None" = 12,
        require_lookahead: bool = False,
        require_entries: bool = False,
        empty_message: str | None = None,
    ):
        if feed_url is None and not steps:
            raise ValueError(
                "IcsSessionRetriever: give a `feed_url`, or at least one step "
                "whose own response is the calendar"
            )
        self.feed_url = feed_url
        self.steps = list(steps)
        self.feed_params = feed_params
        self.cookies = cookies
        self.variants = variants
        self.headers = headers
        self.timeout = timeout
        self.encoding = encoding
        self.lookahead_month = lookahead_month
        self.require_lookahead = require_lookahead
        self.require_entries = require_entries
        self.empty_message = empty_message

    def __call__(self, source: "BaseSource") -> "list[Response]":
        feeds: list[Response] = []
        for index, year in enumerate(_calendar_years(self.lookahead_month)):
            try:
                # Built in full before it is kept, so a year that fails halfway
                # through its variants contributes nothing rather than half a
                # calendar.
                feeds.extend(self._fetch_year(source, year))
            except Exception:
                if index == 0 or self.require_lookahead:
                    raise
        return feeds

    def _fetch_year(self, source: "BaseSource", year: int) -> "list[Response]":
        variants: Sequence[Any] = (
            self.variants if self.variants is not None else (None,)
        )
        return [self._fetch(source, year, variant) for variant in variants]

    def _fetch(self, source: "BaseSource", year: int, variant: Any) -> "Response":
        context: dict[str, Any] = {**source.params, "year": year, "variant": variant}
        cookies: dict[str, str] = {}
        if self.cookies is not None:
            cookies.update(_resolve_context(self.cookies, context))

        last: Any = None
        for step in self.steps:
            response = source.session.request(
                step.get("method", "GET"),
                _resolve_context(step["url"], context),
                params=_resolve_context(step.get("params"), context),
                data=_resolve_context(step.get("data"), context),
                json=_resolve_context(step.get("json"), context),
                headers=_resolve_context(step.get("headers", self.headers), context),
                # Only pass a jar once there is something in it, so a provider
                # that relies purely on the session's own cookies is untouched.
                cookies=cookies or None,
                timeout=self.timeout,
            )
            response.raise_for_status()
            # Only when the step names one: the constructor's `encoding` is the
            # calendar's, and a provider can mis-declare one without the other.
            if step.get("encoding") is not None:
                response.encoding = step["encoding"]
            last = response
            for field_name, argument in step.get("select", {}).items():
                context[argument] = resolve_select_option(
                    argument,
                    str(context[argument]),
                    select_options(response.text, field_name),
                )
            if "extract" in step:
                context.update(step["extract"](response, context))
            if "cookies" in step:
                cookies.update(step["cookies"](**context))

        if self.feed_url is None:
            # The last step's own response is the calendar. The constructor
            # guarantees there is at least one step in that case.
            feed = last
        else:
            feed = source.session.get(
                _resolve_context(self.feed_url, context),
                params=_resolve_context(self.feed_params, context),
                headers=_resolve_context(self.headers, context),
                cookies=cookies or None,
                timeout=self.timeout,
            )
            feed.raise_for_status()
        if self.encoding is not None:
            feed.encoding = self.encoding
        if self.require_entries and not ICS().convert(feed.text):
            raise ValueError(self.empty_message or f"No ICS entries found for {year}")
        return feed


class IcsLookupRetriever(RetrieverFunc):
    """Read a key off a lookup page, then GET the ICS feed with it as a query.

    The address-to-id shape of
    :class:`~waste_collection_schedule.retrievers.TwoStepRetriever`, for the
    many ICS endpoints that take the resolved id (and a date window) as *query
    arguments* rather than in the path, which is what stops the schedule URL
    from being expressible as a single string::

        retrieve = IcsLookupRetriever(
            base_url="https://abfall.example.de",
            extract=_pick_location,
            feed_path="/ical",
            params=lambda key, **_: {"location": key, "startDate": ...},
        )
        parse = IcsFeedsParser(parsers.IcsParser())

    Both requests go through ``source.session``, and the result is a list of
    responses so :class:`IcsFeedsParser` handles it unchanged.

    Args:
        base_url: the site root both requests are built from (literal or
            ``callable(**source.params) -> str``).
        extract: ``callable(lookup_response, source) -> key``; pulls the id out
            of the lookup page and may raise ``SourceArgumentNotFound`` /
            ``SourceArgumentNotFoundWithSuggestions`` for an address the page
            does not list.
        lookup_path: appended to ``base_url`` for the lookup request (default
            ``""``: the site root is itself the page carrying the id list).
        feed_path: appended to ``base_url`` for the calendar request, as
            ``callable(key=..., variant=..., **source.params) -> str`` or a
            literal. Make it a callable for a provider that puts the resolved
            id in the *path* rather than the query.
        params: query arguments for the calendar request, as
            ``callable(key=..., variant=..., **source.params) -> dict`` or a
            literal.
        variants: values the calendar request is repeated for, one feed each,
            passed to ``feed_path`` / ``params`` as ``variant``. The lookup runs
            once and every variant reuses its key, which is the difference from
            :class:`IcsSessionRetriever`'s option of the same name (there the
            whole chain re-runs, because the steps themselves are what the
            variant changes). For a provider that splits one address's calendar
            across parallel feeds: a separate query flag per year, or per waste
            stream. ``None`` (default) fetches a single feed.
        headers: optional headers applied to both requests.
        timeout: per-request timeout in seconds (default 30).
        stale_year_base_url: optional alternate site root, as
            ``callable(year=..., **source.params) -> str``. Consulted only when
            the primary feed's earliest event falls outside the current year,
            which is how a provider that publishes each year on a year-suffixed
            host reads once the new year's calendar has taken over the primary
            one. Both requests are repeated there and the second feed is merged
            in. Best effort: an alternate host that does not exist yet leaves
            the primary schedule as it is.
    """

    def __init__(
        self,
        *,
        base_url: "UrlArgs",
        extract: "Callable[..., Any]",
        feed_path: "UrlArgs" = "",
        lookup_path: str = "",
        params: "QueryArgs" = None,
        variants: "Sequence[Any] | None" = None,
        headers: "HeadersArgs" = None,
        timeout: int = 30,
        stale_year_base_url: "UrlArgs | None" = None,
    ):
        self.base_url = base_url
        self.extract = extract
        self.feed_path = feed_path
        self.lookup_path = lookup_path
        self.params = params
        self.variants = variants
        self.headers = headers
        self.timeout = timeout
        self.stale_year_base_url = stale_year_base_url

    def __call__(self, source: "BaseSource") -> "list[Response]":
        feeds = self._fetch(source, _resolve_arg(self.base_url, source))
        feeds.extend(self._stale_year_feeds(source, feeds[0]))
        return feeds

    def _fetch(self, source: "BaseSource", base_url: str) -> "list[Response]":
        headers = _resolve_arg(self.headers, source)
        lookup = source.session.get(
            f"{base_url}{self.lookup_path}", headers=headers, timeout=self.timeout
        )
        lookup.raise_for_status()
        key = self.extract(lookup, source)

        variants: Sequence[Any] = (
            self.variants if self.variants is not None else (None,)
        )
        feeds: list[Response] = []
        for variant in variants:
            feed = source.session.get(
                f"{base_url}{_resolve_arg(self.feed_path, source, key=key, variant=variant)}",
                params=_resolve_arg(self.params, source, key=key, variant=variant),
                headers=headers,
                timeout=self.timeout,
            )
            feed.raise_for_status()
            feeds.append(feed)
        return feeds

    def _stale_year_feeds(
        self, source: "BaseSource", feed: "Response"
    ) -> "list[Response]":
        """Fetch the alternate host's feed, if the primary one has aged out.

        Reading the body is normally the parser's job, but "is this still the
        current year's calendar?" is the only question that can decide whether
        the alternate host is worth a request, and it is an ICS question.
        """
        if self.stale_year_base_url is None:
            return []
        try:
            year = datetime.date.today().year
            if min(date for date, _ in ICS().convert(feed.text)).year == year:
                return []
            return self._fetch(
                source, _resolve_arg(self.stale_year_base_url, source, year=year)
            )
        except Exception:
            # Best effort: the alternate host may not be published yet, and the
            # primary feed on its own is still a usable schedule.
            return []


class IcsIndexRetriever(RetrieverFunc):
    """Scrape an index page for ICS feed links, then GET every one.

    For a provider that publishes not one calendar but a small fixed set: one
    feed per waste type or per district, each linked from a stable index page.
    A WordPress events calendar's per-category ``?ical=download`` links and a
    council's list of ``.ics`` downloads are both this shape. There is no lookup
    key to submit, so :class:`~waste_collection_schedule.retrievers.TwoStepRetriever`
    does not fit: every listed feed is fetched and the results merged. Pair it
    with :class:`IcsFeedsParser`, which already accepts a list of responses::

        retrieve = IcsIndexRetriever(
            index_url="https://www.example.gv.at/kalender/",
            link_selector="i.fa-calendar-plus",
            pattern=r"abfalltyp",
        )
        parse = IcsFeedsParser(parsers.IcsParser())

    Links are kept in document order and de-duplicated, and each href is
    resolved against the index URL, so a relative link works.

    Where the listed feeds are *alternatives* rather than parts of one schedule
    (one per collection district, and the user belongs to some of them), name
    each link with ``label`` and the config parameter holding the wanted names
    with ``argument``. Only the labelled feeds the user asked for are fetched,
    in the order they asked for them, and an unknown name raises
    ``SourceArgumentNotFoundWithSuggestions`` listing the labels the page does
    offer::

        retrieve = IcsIndexRetriever(
            index_url=CALENDAR_PAGE,
            link_selector='a[data-extension="ICS"]',
            pattern=r"/downloads/datei/",
            label=_area_name,
            argument="areas",
        )

    Like :class:`~waste_collection_schedule.retrievers.PdfLinkRetriever` this
    reads the first response's body to find the links; that is the sanctioned
    exception to "a retriever only does HTTP".

    Args:
        index_url: the page listing the feeds (literal or
            ``callable(**source.params) -> str``).
        pattern: regex an ``<a href>`` must match to count as a feed link,
            searched case-insensitively. Default ``r"\\.ics(?:$|\\?)"`` matches
            a plain ``.ics`` download; override it for a provider whose export
            links are recognised by a path segment or query instead.
        link_selector: optional CSS selector narrowing which anchors count. A
            matching element that is not itself an ``<a href>`` resolves to its
            nearest enclosing one, so the selector may name the download icon
            rather than the link (e.g. ``"i.fa-calendar-plus"``). ``None``
            considers every anchor on the page.
        min_feeds: minimum number of feed links expected. Fewer raises rather
            than returning a silently short schedule (default 1). Counted
            against the links the page offers, before any ``argument``
            selection.
        label: optional ``callable(anchor) -> str | None`` naming each feed
            link (from its title, its text, its href). A link the callable
            returns ``None`` for is left unnamed and can never be selected.
            Required by ``argument``, and harmless without it.
        argument: optional name of the config parameter listing which labelled
            feeds to fetch. Its value may be a single name or a list of them,
            matched against the labels case-insensitively.
        headers: optional headers applied to every request.
        timeout: per-request timeout in seconds.
    """

    def __init__(
        self,
        *,
        index_url: "UrlArgs",
        pattern: str = r"\.ics(?:$|\?)",
        link_selector: "str | None" = None,
        min_feeds: int = 1,
        label: "Callable[[Tag], str | None] | None" = None,
        argument: str | None = None,
        headers: "HeadersArgs" = None,
        timeout: int = 30,
    ):
        if argument is not None and label is None:
            raise ValueError(
                "IcsIndexRetriever: `argument` needs `label`, the callable that "
                "names each feed link so the user's values can select one"
            )
        self.index_url = index_url
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.link_selector = link_selector
        self.min_feeds = min_feeds
        self.label = label
        self.argument = argument
        self.headers = headers
        self.timeout = timeout

    def _anchors(self, soup: BeautifulSoup) -> "list[Tag]":
        if self.link_selector is None:
            return list(soup.find_all("a", href=True))
        anchors: list[Tag] = []
        for element in soup.select(self.link_selector):
            anchor = (
                element
                if element.name == "a" and element.has_attr("href")
                else element.find_parent("a", href=True)
            )
            if isinstance(anchor, Tag):
                anchors.append(anchor)
        return anchors

    def _feed_urls(self, index_url: str, html: str) -> "list[tuple[str | None, str]]":
        soup = BeautifulSoup(html, "html.parser")
        found: list[tuple[str | None, str]] = []
        seen: set[str] = set()
        for anchor in self._anchors(soup):
            href = str(anchor["href"])
            if not self.pattern.search(href):
                continue
            url = urljoin(index_url, href)
            if url in seen:
                continue
            seen.add(url)
            found.append((self.label(anchor) if self.label else None, url))
        return found

    def _selected(
        self, found: "list[tuple[str | None, str]]", source: "BaseSource"
    ) -> list[str]:
        """The feed URLs the user's ``argument`` asked for, in their order."""
        # The constructor guarantees `label` is set whenever `argument` is.
        argument = str(self.argument)
        wanted = source.params.get(argument)
        if isinstance(wanted, str):
            wanted = [wanted]
        available = [(label, url) for label, url in found if label is not None]

        urls: list[str] = []
        for value in wanted or []:
            for label, url in available:
                if str(label).lower() == str(value).lower():
                    urls.append(url)
                    break
            else:
                raise SourceArgumentNotFoundWithSuggestions(
                    argument, value, [str(label) for label, _ in available]
                )
        return urls

    def __call__(self, source: "BaseSource") -> "list[Response]":
        headers = _resolve_arg(self.headers, source)
        index_url = _resolve_arg(self.index_url, source)

        index = source.session.get(index_url, headers=headers, timeout=self.timeout)
        index.raise_for_status()

        found = self._feed_urls(index_url, index.text)
        if len(found) < self.min_feeds:
            raise ValueError(
                f"found {len(found)} ICS feed link(s) matching "
                f"{self.pattern.pattern!r} on {index_url}, expected at least "
                f"{self.min_feeds}; the page layout may have changed."
            )

        urls = (
            self._selected(found, source)
            if self.argument is not None
            else [url for _, url in found]
        )

        feeds = []
        for url in urls:
            feed = source.session.get(url, headers=headers, timeout=self.timeout)
            feed.raise_for_status()
            feeds.append(feed)
        return feeds


class _UnwrappedFeed:
    """A response whose ``text`` is the iCalendar document inside its envelope.

    Everything else (status code, headers, ``json()``) is delegated to the real
    response, so a parser reading more than the body still behaves as it would
    on an unwrapped provider.
    """

    def __init__(self, feed: Any, text: str):
        self._feed = feed
        self.text = text

    def __getattr__(self, name: str) -> Any:
        return getattr(self._feed, name)


class IcsFeedsParser:
    """Apply an ICS parser to every feed the retriever returned, and merge.

    The multi-feed companion to ``parsers.IcsParser``, and the matching ``parse``
    for :class:`IcsYearRetriever`, whose ``retrieve`` hands over one response per
    calendar year. A single response is accepted too, so swapping between the
    two costs nothing.

    It composes rather than replaces: pass the configured ``parsers.IcsParser``
    that suits the provider, and every option that parser has (``offset``,
    ``regex``, ``split_at``, ``title_template``, ``min_events``) applies to each
    feed in turn::

        parse = IcsFeedsParser(parsers.IcsParser(split_at=" / "))

    ``min_events`` therefore reads as "every feed must have this many events",
    which is the useful reading for a per-year calendar: a year that came back
    all but empty is the failure worth catching, and it would otherwise hide
    behind a well-populated sibling year.

    The remaining options handle what merging several provider feeds tends to
    need on top of the per-feed parse:

    * ``clean`` — ``callable(title) -> title`` applied to every entry's title
      before ``exclude`` and ``dedupe`` see it. Use it for the label tidy-up
      that has to happen *before* de-duplication (two feeds spelling the same
      collection differently); a tidy-up that only affects the displayed label
      belongs on ``ICSTransformer(clean=...)`` instead.
    * ``exclude`` — regex; an entry whose title matches (case-insensitively,
      anywhere in the title) is dropped. For the housekeeping VEVENT a provider
      mixes into the schedule ("Abfallkalender endet bald"), which carries no
      waste type.
    * ``dedupe`` — drop repeated entries, keeping first-seen order. Several
      providers publish overlapping feeds (one per paper contractor, per
      district, per year) that repeat the shared collections in each.
    * ``unwrap`` — ``callable(body) -> ics_text`` applied to each feed's body
      before anything reads it. For a provider that does not serve the calendar
      as the response body but wraps it in an envelope, typically a JSON field
      holding the feed base64-encoded. Everything downstream (``require_calendar``
      included) then sees plain iCalendar text.

    A provider whose feed doubles as the address check is served by
    ``argument`` plus one or both of:

    * ``require_calendar`` — the endpoint answers 200 with an HTML page rather
      than an HTTP error when the id is unknown, so a body that is not an
      iCalendar document means "bad argument", not "provider broken".
    * ``suggestions`` — ``callable(source) -> list[str]`` consulted only when
      the merged result is empty, to turn "no collections" into
      ``SourceArgumentNotFoundWithSuggestions`` listing the values that do
      work. It runs on the error path only, which is why it belongs here and
      not in the retriever.

    Both name the offending config parameter through ``argument``, so the HA
    UI blames the field the user actually filled in.
    """

    def __init__(
        self,
        parser: "Parser[IcsEntries] | None" = None,
        *,
        clean: "Callable[[str], str] | None" = None,
        exclude: str | None = None,
        dedupe: bool = False,
        unwrap: "Callable[[str], str] | None" = None,
        argument: str | None = None,
        require_calendar: bool = False,
        suggestions: "Callable[[BaseSource], list[str]] | None" = None,
    ):
        if (require_calendar or suggestions is not None) and argument is None:
            raise ValueError(
                "IcsFeedsParser: require_calendar/suggestions need `argument`, "
                "the name of the config parameter to report the failure against"
            )
        self._parser = parser
        self._unwrap = unwrap
        self._clean = clean
        self._exclude = re.compile(exclude, re.IGNORECASE) if exclude else None
        self._dedupe = dedupe
        self._argument = argument
        self._require_calendar = require_calendar
        self._suggestions = suggestions

    def _unwrap_feed(self, feed: Any) -> Any:
        """Replace a feed's body with the iCalendar text inside its envelope."""
        if self._unwrap is None:
            return feed
        return _UnwrappedFeed(feed, self._unwrap(feed.text))

    def _check_calendar(self, feed: Any, source: "BaseSource | None") -> None:
        if not self._require_calendar or self._argument is None:
            return
        if feed.text.lstrip("\ufeff \t\r\n").startswith("BEGIN:VCALENDAR"):
            return
        value = source.params.get(self._argument) if source is not None else None
        raise SourceArgumentNotFound(
            self._argument,
            value,
            "no calendar found for this location, please check this value is correct.",
        )

    def _clean_entry(self, entry: Any) -> Any:
        """Apply ``clean`` to an entry's title, whichever record shape it is."""
        if self._clean is None:
            return entry
        if isinstance(entry, IcsEvent):
            return entry._replace(title=self._clean(entry.title))
        return (entry[0], self._clean(entry[1]))

    def _raise_unknown_argument(self, source: "BaseSource") -> None:
        # The constructor guarantees `argument` is set whenever `suggestions` is.
        argument = str(self._argument)
        value = source.params.get(argument)
        suggestions = self._suggestions(source) if self._suggestions else []
        if suggestions:
            raise SourceArgumentNotFoundWithSuggestions(argument, value, suggestions)
        raise SourceArgumentNotFound(argument, value)

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "IcsEntries":
        parser = self._parser
        if parser is None:
            # Imported here, not at module scope: parsers imports this module.
            from waste_collection_schedule import parsers

            parser = parsers.IcsParser()

        feeds = response if isinstance(response, (list, tuple)) else [response]
        entries: IcsEntries = []
        seen: set = set()
        for raw_feed in feeds:
            feed = self._unwrap_feed(raw_feed)
            self._check_calendar(feed, source)
            for parsed in parser(feed, source):
                entry = self._clean_entry(parsed)
                if self._exclude is not None and self._exclude.search(entry[1].strip()):
                    continue
                if self._dedupe:
                    if entry in seen:
                        continue
                    seen.add(entry)
                entries.append(entry)

        if not entries and self._suggestions is not None and source is not None:
            self._raise_unknown_argument(source)
        return entries
