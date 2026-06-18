"""Shared service for Austrian municipalities running the RiSKommunal (RIS) CMS.

Many small Austrian municipalities publish their waste-collection calendar on the
RiSKommunal platform. They all expose the same building blocks:

* an HTML calendar page at ``/system/web/kalender.aspx`` which renders either as a
  table (``ris_table`` / ``td_kal`` cells) or as a list (``list_style`` div with
  ``h2`` dates), and
* an ICS feed at ``/system/web/CalendarService.ashx`` (used by a few sources that
  rely on hard-coded or scraped calendar IDs).

This module provides a single base class, :class:`RiSKommunalSource`, so that an
individual municipality source shrinks to a declaration of ``BASE_URL``,
``ICON_MAP`` and (where the calendar needs them) a few query parameters. The base
class auto-detects the table vs. list rendering, handles pagination with loop
detection, resolves address-based ``typids`` from the embedded ``strassenArr``
JavaScript array, and offers helpers for the ICS feed.
"""

from __future__ import annotations

import ast
import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS  # type: ignore[attr-defined]

# Assembly-qualified name token required by every RiSKommunal CalendarService.ashx
# endpoint. It is a platform constant (base64 of
# "RiSKommunal.Objects.Kalender, RISComponents, Version=1.0.0.0, Culture=neutral,
# PublicKeyToken=null") and is therefore shared here rather than in each source.
ICS_AQN = (
    "UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4w"
    "LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw="
)

CALENDAR_PATH = "/system/web/kalender.aspx"
ICS_PATH = "/system/web/CalendarService.ashx"

_DATE_RE = re.compile(r"(\d{2}\.\d{2}\.\d{4})")
_LIST_DIV_ID = "ctl00_ctl00_ctl00_cph_col_a_cph_content_cph_content_list_style"

HEADERS = {"User-Agent": "Mozilla/5.0"}


class RiSKommunalSource:
    """Base class for RiSKommunal-based waste-collection sources.

    Subclasses set class attributes:

    * ``BASE_URL`` (required): municipality root URL, e.g. ``https://www.koppl.at``.
    * ``ICON_MAP``: mapping of waste-type string -> ``Icons`` member.
    * ``QUERY_PARAMS``: extra query parameters for ``kalender.aspx`` (dict).
    * ``VDATUM_TODAY``: if True, add ``vdatum`` = today to the request.
    * ``MAX_PAGES``: pagination upper bound (default 50).
    * ``SELECTION_URL``: page carrying the street dropdown + ``strassenArr`` array
      (only needed for address-based sources).

    Address-/zone-based sources override ``__init__`` to expose their config-flow
    parameters and pass them to :meth:`__init__` of this class.
    """

    BASE_URL: str = ""
    ICON_MAP: dict = {}
    QUERY_PARAMS: dict = {}
    VDATUM_TODAY: bool = False
    MAX_PAGES: int = 50
    SELECTION_URL: str | None = None
    RAISE_ON_EMPTY: bool = False
    LOOKAHEAD_DAYS: int | None = None

    def __init__(
        self,
        strasse: str | None = None,
        hausnummer: str | int | None = None,
        zone: str | None = None,
    ):
        self._strasse = str(strasse).strip() if strasse is not None else None
        self._hausnummer = str(hausnummer).strip() if hausnummer is not None else None
        self._zone = str(zone).strip() if zone is not None else None

    # ------------------------------------------------------------------ #
    # Public fetch (HTML path)
    # ------------------------------------------------------------------ #
    def fetch(self) -> list[Collection]:
        session = requests.Session()

        typids = None
        if self._strasse is not None:
            typids = self._resolve_typids(session)

        entries = self._fetch_html(session, typids)
        if not entries and self.RAISE_ON_EMPTY:
            raise ValueError("Could not find any collection events.")
        return entries

    # ------------------------------------------------------------------ #
    # HTML calendar
    # ------------------------------------------------------------------ #
    def _calendar_url(self) -> str:
        return self.BASE_URL.rstrip("/") + CALENDAR_PATH

    def _get_page(
        self, session: requests.Session, page: int, typids: str | None
    ) -> BeautifulSoup:
        params = dict(self.QUERY_PARAMS)
        if self.VDATUM_TODAY or self.LOOKAHEAD_DAYS is not None:
            params["vdatum"] = date.today().strftime("%d.%m.%Y")
        if self.LOOKAHEAD_DAYS is not None:
            params["bdatum"] = self._end_date().strftime("%d.%m.%Y")
        if typids is not None:
            params["typids"] = typids
        params["page"] = page

        r = session.get(
            self._calendar_url(), params=params, headers=HEADERS, timeout=30
        )
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return BeautifulSoup(r.text, "html.parser")

    def _end_date(self) -> date:
        from datetime import timedelta

        return date.today() + timedelta(days=self.LOOKAHEAD_DAYS or 0)

    def _fetch_html(
        self, session: requests.Session, typids: str | None
    ) -> list[Collection]:
        entries: list[Collection] = []
        seen: set[tuple[str, str]] = set()
        seen_first: set[tuple[str, str]] = set()
        end_date = self._end_date() if self.LOOKAHEAD_DAYS is not None else None

        for page in range(self.MAX_PAGES):
            soup = self._get_page(session, page, typids)

            rows = self._parse_table(soup)
            list_mode = rows is None
            if list_mode:
                rows = self._parse_list(soup)

            if not rows:
                break

            first_key = (rows[0][0].isoformat(), rows[0][1])
            if first_key in seen_first:
                break
            seen_first.add(first_key)

            for collection_date, waste_type in rows:
                if end_date is not None and collection_date > end_date:
                    continue
                key = (collection_date.isoformat(), waste_type)
                if key in seen:
                    continue
                seen.add(key)
                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=self._icon(waste_type),
                    )
                )

            # The list rendering is never paginated.
            if list_mode:
                break
            # Stop once the page has run past the requested look-ahead window.
            if end_date is not None and rows[-1][0] > end_date:
                break

        return sorted(entries, key=lambda c: c.date)

    def _parse_table(self, soup: BeautifulSoup) -> list[tuple[date, str]] | None:
        """Parse the table rendering.

        Prefers the ``ris_table`` calendar; on installs that render a plain table
        it falls back to the first table that yields date rows. Returns ``None``
        when no data table is present so the caller can fall back to the list
        parser.
        """
        table = soup.find("table", class_="ris_table")
        if table is not None:
            return self._extract_table_rows(table)

        for table in soup.find_all("table"):
            rows = self._extract_table_rows(table)
            if rows:
                return rows
        return None

    def _extract_table_rows(self, table) -> list[tuple[date, str]]:
        out: list[tuple[date, str]] = []
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 2:
                continue

            m = _DATE_RE.match(tds[0].get_text(" ", strip=True))
            if not m:
                continue
            collection_date = datetime.strptime(m.group(1), "%d.%m.%Y").date()

            # Optional zone filter (third column, e.g. Eggelsberg).
            if self._zone is not None and len(tds) >= 3:
                row_zone = tds[2].get_text(strip=True)
                if row_zone not in ("Gemeinde Alle", self._zone):
                    continue

            anchor = tds[1].find("a")
            raw = (
                anchor.get_text(strip=True)
                if anchor
                else tds[1].get_text(" ", strip=True)
            )
            waste_type = re.sub(r"\s*\(.*\)\s*$", "", raw).strip()
            if not waste_type:
                continue

            out.append((collection_date, waste_type))

        return out

    def _parse_list(self, soup: BeautifulSoup) -> list[tuple[date, str]]:
        """Parse the ``list_style`` rendering.

        The list view groups collections under an ``<h2>`` date heading; the waste
        types follow either as ``<li>`` items in the next ``<ul>`` (each item
        carries a short ``<span>`` category and/or a descriptive ``<a>`` link) or,
        on older installs, as a single ``<span>`` after the heading. The short
        ``<span>`` category is preferred because it matches the ``ICON_MAP`` keys.
        """
        div = soup.find(id=_LIST_DIV_ID)
        if div is None:
            return []

        out: list[tuple[date, str]] = []
        for heading in div.find_all("h2"):
            m = _DATE_RE.match(heading.get_text(" ", strip=True))
            if not m:
                continue
            collection_date = datetime.strptime(m.group(1), "%d.%m.%Y").date()

            ul = heading.find_next_sibling("ul")
            items = ul.find_all("li") if ul else []
            if items:
                for li in items:
                    out.append((collection_date, self._list_item_type(li)))
            else:
                span = heading.find_next_sibling("span")
                if span is not None:
                    waste_type = re.sub(
                        r"^\((.*)\)$", r"\1", span.get_text(strip=True)
                    ).strip()
                    if waste_type:
                        out.append((collection_date, waste_type))

        return [(d, t) for d, t in out if t]

    @staticmethod
    def _list_item_type(li) -> str:
        span = li.find("span")
        if span is not None and span.get_text(strip=True):
            return re.sub(r"^\((.*)\)$", r"\1", span.get_text(strip=True)).strip()
        anchor = li.find("a")
        if anchor is not None:
            return anchor.get_text(strip=True)
        return li.get_text(" ", strip=True)

    # ------------------------------------------------------------------ #
    # Address resolution (strassenArr -> typids)
    # ------------------------------------------------------------------ #
    def _resolve_typids(self, session: requests.Session) -> str:
        url = self.SELECTION_URL or self._calendar_url()
        r = session.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        html = r.text

        street_map = self._parse_street_dropdown(html)
        street_id = None
        target = (self._strasse or "").casefold().replace(" ", "")
        for name, sid in street_map.items():
            if name.casefold().replace(" ", "") == target:
                street_id = sid
                break
        if street_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "strasse", self._strasse, sorted(street_map)
            )

        house = (self._hausnummer or "").casefold()
        labels: list[str] = []
        for entry in self._parse_strassen_arr(html):
            if entry[0] != street_id:
                continue
            for hnr in entry[1]:
                label = str(hnr[1])
                labels.append(label)
                if label.casefold() == house:
                    return hnr[2]
            break

        raise SourceArgumentNotFoundWithSuggestions(
            "hausnummer", self._hausnummer, labels
        )

    @staticmethod
    def _parse_street_dropdown(html: str) -> dict[str, int]:
        soup = BeautifulSoup(html, "html.parser")
        select = soup.find(
            "select",
            attrs={"name": re.compile(r"boxmuellkalenderstrassedd$")},
        )
        if select is None:
            select = soup.find(
                "select",
                attrs={"id": re.compile(r"boxmuellkalenderstrassedd$")},
            )
        if select is None:
            raise ValueError("Could not locate street selector on RiSKommunal page")

        result: dict[str, int] = {}
        for opt in select.find_all("option"):
            value = (opt.get("value") or "").strip()
            text = opt.get_text(strip=True)
            if value and text:
                result[text] = int(value)
        return result

    @staticmethod
    def _parse_strassen_arr(html: str) -> list:
        match = re.search(r"strassenArr\s*=\s*", html)
        if not match:
            raise ValueError("Could not locate strassenArr in page")

        start = html.find("[", match.end())
        depth = 0
        end = start
        for idx in range(start, len(html)):
            ch = html[idx]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break
        if depth != 0:
            raise ValueError("Could not parse strassenArr (unbalanced brackets)")

        return ast.literal_eval(html[start:end])

    # ------------------------------------------------------------------ #
    # ICS feed helpers
    # ------------------------------------------------------------------ #
    def _ics_url(self, gnr: str, do: str, sprache: str = "1") -> str:
        params = {"aqn": ICS_AQN, "sprache": sprache, "gnr": gnr, "do": do}
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return self.BASE_URL.rstrip("/") + ICS_PATH + "?" + query

    def parse_ics_url(self, url: str, cookies=None) -> list[tuple[date, str]]:
        """Fetch one ICS URL and return its ``(date, title)`` entries.

        Optional ``cookies`` are passed per request (no session persistence) for
        installs that gate the iCal download behind a selection cookie.
        """
        r = requests.get(url, headers=HEADERS, cookies=cookies, timeout=60)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return ICS().convert(r.text)

    def parse_ics_urls(self, urls: list[str], cookies=None) -> list[Collection]:
        """Fetch several ICS URLs, using each event's own title as the waste type."""
        entries: list[Collection] = []
        for url in urls:
            for d, title in self.parse_ics_url(url, cookies=cookies):
                waste_type = title.strip()
                entries.append(
                    Collection(date=d, t=waste_type, icon=self._icon(waste_type))
                )
        return entries

    def fetch_ics(self, gnr: str, do_ids: list[str]) -> list[Collection]:
        """Fetch ICS feeds for the given ``do`` ids; waste type from the event."""
        return self.parse_ics_urls([self._ics_url(gnr, do) for do in do_ids])

    def fetch_ics_by_label(
        self, gnr: str, calendars: dict[str, str]
    ) -> list[Collection]:
        """Fetch ICS feeds for ``{waste_type: do}``; label by the dict key."""
        entries: list[Collection] = []
        for waste_type, do in calendars.items():
            for d, _title in self.parse_ics_url(self._ics_url(gnr, do)):
                entries.append(
                    Collection(date=d, t=waste_type, icon=self._icon(waste_type))
                )
        return entries

    # ------------------------------------------------------------------ #
    # Icons
    # ------------------------------------------------------------------ #
    def _icon(self, waste_type: str):
        icon = self.ICON_MAP.get(waste_type)
        if icon is not None:
            return icon
        lowered = waste_type.casefold()
        for key, value in self.ICON_MAP.items():
            if key.casefold() in lowered:
                return value
        return None
