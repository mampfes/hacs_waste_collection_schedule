import datetime
import logging
import re
import unicodedata
from typing import TYPE_CHECKING, Any, NamedTuple

import jinja2
from icalevents import icalevents

from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from collections.abc import Callable

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

_LOGGER = logging.getLogger(__name__)


class IcsEvent(NamedTuple):
    date: datetime.date
    title: str
    location: str | None = None
    description: str | None = None


# RFC 5545 allows only ALPHA, DIGIT and "-" in a property name.
_PROPERTY_NAME = re.compile(r"[A-Za-z0-9-]+")

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
    syntactic defect; the essential DTSTART/DTEND/SUMMARY are never altered.
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

    # Drop property lines whose name is not valid iCalendar; icalendar aborts
    # the whole feed on one of them.
    ics_data = _drop_malformed_content_lines(ics_data)

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

    Args:
        url: the feed URL, as ``callable(year=..., **source.params) -> str``
            or a literal.
        params: optional query arguments, as
            ``callable(year=..., **source.params) -> dict`` or a literal.
        headers: optional headers, literal or ``callable(**source.params)``.
        timeout: per-request timeout in seconds (default 30).
        lookahead_month: from this month (1-12) onwards, also fetch year + 1.
            Default 12: in December, next year's calendar is pulled too.
        fallback_url: optional alternative URL, same calling convention as
            ``url``, retried for a year the first attempt did not satisfy.
        fallback_params: optional alternative query arguments for that retry;
            ignored unless ``fallback_url`` is set.

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
        lookahead_month: int = 12,
        fallback_url: "UrlArgs | None" = None,
        fallback_params: "QueryArgs" = None,
    ):
        self.url = url
        self.params = params
        self.headers = headers
        self.timeout = timeout
        self.lookahead_month = lookahead_month
        self.fallback_url = fallback_url
        self.fallback_params = fallback_params

    def __call__(self, source: "BaseSource") -> "list[Response]":
        today = datetime.date.today()
        years = [today.year]
        if today.month >= self.lookahead_month:
            years.append(today.year + 1)
        return [self._fetch_year(source, year) for year in years]

    def _fetch_year(self, source: "BaseSource", year: int) -> "Response":
        response = self._attempt(source, year, self.url, self.params)
        if response is None and self.fallback_url is not None:
            response = self._attempt(
                source, year, self.fallback_url, self.fallback_params
            )
        if response is None:
            raise ValueError(f"No ICS entries found for {year}")
        return response

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
        if callable(mapping):
            return mapping(**extra, **source.params)
        return mapping


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
    """

    def __init__(self, parser: "Parser[IcsEntries] | None" = None):
        self._parser = parser

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
        for feed in feeds:
            entries.extend(parser(feed, source))
        return entries
