"""Die NÖ Umweltverbände (``<district>.umweltverbaende.at``).

The Lower Austrian waste associations each run a WordPress site on the
``umweltverbaende.at`` platform, and the sites do not all publish their schedule
the same way. Which way a district uses is only known by asking the site, so
:class:`UmweltverbaendeRetriever` probes it and follows what it finds:

1. **Old site** (light blue header, green buttons): ``/?kat=32&jahr=<year>`` lists the
   municipalities as ``a.weblink`` links, each leading to a page whose rows
   (``div.tunterlegt``) read ``<weekday>  <dd.mm.yyyy>  <type>``. A municipality with
   several calendars (streets, "Rayons") lists them all, so ``calendar`` filters them.
2. **New site** (dark blue header): one of a few known paths (``abholtermine/`` ...)
   that holds either

   * direct ``.ics`` links, flat or grouped per municipality in an accordion
     (``div.el-item`` with an ``a.el-title``): the chosen calendar is downloaded; or
   * a form whose ``select#gemeinde`` and a WordPress ``admin-ajax.php`` endpoint
     (protected by a nonce embedded in the page) resolve municipality, town, postal
     code, street, house number and addition one level at a time and answer with
     the ``zones`` (waste type and dates) of the household, optionally asking for
     the ``fraktionen`` (waste fractions) first.

A district that answers the new-site probe but yields nothing is read as an old site.
The result is always a list of ``(date, label)`` rows that the shared ICS transformer
turns into collections, so a source is the district it serves and its type map.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, NamedTuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

#: district id (the subdomain) -> title. Districts that left the platform or only
#: publish PDFs are not listed; see ``UNSUPPORTED``.
DISTRICTS: dict[str, str] = {
    "baden": "GVA Baden",
    "gmuend": "GV Gmünd",
    "gaenserndorf": "GVU Bezirk Gänserndorf",
    "hollabrunn": "Abfallverband Hollabrunn",
    "horn": "Gemeindeverband Horn",
    "korneuburg": "Abfallverband Korneuburg",
    "krems": "GV Krems",
    "lilienfeld": "GVA Lilienfeld",
    "laa": "GAUL Laa an der Thaya",
    "moedling": "GVA Mödling",
    "melk": "GVU Melk",
    "mistelbach": "GAUM Mistelbach",
    "stpoeltenland": "GVU St. Pölten",
    "waidhofen": "GVA Waidhofen/Thaya",
    "zwettl": "GV Zwettl",
}

#: Districts a configuration may still name, with why they are not served here.
UNSUPPORTED: dict[str, str] = {
    "kremsstadt": (
        "kremsstadt is not supported by this source, follow the documentation of "
        "the City of Krems ICS source"
    ),
    "scheibbs": (
        "scheibbs only publishes its schedule as PDF files and is not supported"
    ),
    "bruck": "bruck only publishes PDF files and is not supported",
    "neunkirchen": "neunkirchen lists no schedules and is not supported",
    "tulln": "tulln offers neither an API nor an ICS file and is not supported",
    "schwechat": "schwechat moved to the Infeo platform: use the infeo_at source",
    "klosterneuburg": "klosterneuburg publishes its schedule on its own site",
}

_COLLECTION_PATHS = (
    "muellabfuhrkalender/",  # Mödling
    "abholtermine-preview/",  # Hollabrunn
    "fuer-die-bevoelkerung/abholtermine/",
    "abfall-entsorgung/abfuhrtermine/",
    "fuer-die-bevoelkerung/abfuhrterminkalender/",
    "entsorgung-und-termine/abholtermine/",
)

_LOCATION_KEYS = (
    "search[ort]",
    "search[postleitzahl]",
    "search[strasse]",
    "search[hausnummer]",
    "search[zusatz]",
)

_NONCE = re.compile(r'"nonce":"([a-zA-Z0-9]+)"')


class Schedule(NamedTuple):
    """What the retriever found: ``(date, label)`` rows."""

    rows: list[tuple[date, str]]

    @property
    def text(self) -> str:  # for the shape checks that want a body to log
        return "\n".join(f"{d} {t}" for d, t in self.rows)


def same(first: str, second: str) -> bool:
    """Whether two names are the same, case, spaces and commas aside."""

    def norm(text: str) -> str:
        return text.strip().lower().replace(" ", "").replace(",", "").casefold()

    return norm(first) == norm(second)


def bounded_substring(needle: str, haystack: str) -> bool:
    """Substring match with non-word boundaries, so "Abfuhrbereich II" does not
    match "Abfuhrbereich III" (issue #4675). Unicode-aware like :func:`same`."""
    pattern = r"(?<!\w)" + re.escape(needle.casefold()) + r"(?!\w)"
    return re.search(pattern, haystack.casefold()) is not None


def old_rows(
    html: str,
    calendars: list[str] | None,
    title_separator: str,
    splitter: str | None,
) -> list[tuple[date, str]]:
    """The rows of an old-site municipality page, filtered by ``calendars``."""
    rows: list[tuple[date, str]] = []
    for day in BeautifulSoup(html, "html.parser").select("div.tunterlegt"):
        # A run of 2+ whitespace characters (spaces and/or non-breaking spaces)
        # separates the columns, in both the old and the newer markup.
        txt = re.split(r"[  ]{2,}", day.text.strip())
        if len(txt) == 1:
            words = day.text.strip().split(" ")
            txt = [
                words[0].strip(","),
                words[1].strip(","),
                " ".join(w.strip() for w in words[2:]).strip(","),
            ]
        if calendars:
            if not any(c.upper() in txt[2].upper() for c in calendars):
                continue
            for part in [txt[2]] if splitter is None else txt[2].split(splitter):
                rows.append(
                    (_old_date(txt[1]), part.split(title_separator)[-1].strip())
                )
        else:
            rows.append((_old_date(txt[1]), txt[2].strip()))
    return rows


def _old_date(text: str) -> date:
    return datetime.strptime(text.strip().strip(",:"), "%d.%m.%Y").date()


def ics_links(scope: Any, base: str) -> dict[str, str]:
    """The ``.ics`` links (by link text) inside a soup scope."""
    links: dict[str, str] = {}
    for a in scope.find_all("a", href=True):
        href = a["href"]
        if not href.endswith(".ics"):
            continue
        if href.startswith("http"):
            url = href
        elif href.startswith("/"):
            url = base.rstrip("/") + href
        else:
            url = base.rstrip("/") + "/" + href
        links[a.text.strip()] = url
    return links


def choose_ics_links(
    soup: Any, base: str, municipal: str | None, calendars: list[str] | None
) -> list[str]:
    """The ICS links of the configured municipal and calendar(s).

    Raises ``LookupError`` when the page carries no ICS link at all, so the caller
    can read the page as the form variant instead.
    """
    sections = [
        item for item in soup.select("div.el-item") if item.select_one("a.el-title")
    ]
    if sections and municipal:
        matched = [
            item
            for item in sections
            if same(municipal, item.select_one("a.el-title").get_text())
        ]
        if not matched:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipal",
                municipal,
                [s.select_one("a.el-title").get_text().strip() for s in sections],
            )
        links: dict[str, str] = {}
        for section in matched:
            links.update(ics_links(section, base))
    else:
        links = ics_links(soup, base)
        if municipal:
            # Some districts list every municipality's calendars in one flat
            # list: narrow down to the municipal where its name appears (#7428).
            scoped = {n: u for n, u in links.items() if bounded_substring(municipal, n)}
            if scoped:
                links = scoped

    if not links:
        raise LookupError("no ics links")

    chosen: list[str] = []
    if calendars:
        for cal in calendars:
            chosen += [u for n, u in links.items() if same(cal, n)]
        if not chosen:
            for cal in calendars:
                chosen += [u for n, u in links.items() if bounded_substring(cal, n)]
        if not chosen and len(links) == 1:
            chosen = list(links.values())
    elif len(links) == 1:
        chosen = list(links.values())
    else:
        raise SourceArgumentRequiredWithSuggestions("calendar", None, list(links))

    if not chosen:
        raise SourceArgumentNotFoundWithSuggestions("calendar", calendars, list(links))
    return chosen


class UmweltverbaendeRetriever(RetrieverFunc):
    """Probe the district's site and read the schedule from whichever variant it is.

    Args:
        district: name of the ``source.params`` field holding the district id, or
            a literal district id when ``fixed_district`` is set.
        municipal: field holding the municipality (``None``: not used).
        fixed_district: serve this district whatever the params say.
        optional: names of the other, optional fields: ``town``, ``plz``,
            ``street``, ``hnr``, ``addition``, ``calendar``,
            ``calendar_title_separator`` and ``calendar_splitter``.
    """

    def __init__(
        self,
        *,
        district: str = "district",
        municipal: str = "municipal",
        fixed_district: str | None = None,
        town: str = "town",
        plz: str = "plz",
        street: str = "street",
        hnr: str = "hnr",
        addition: str = "addition",
        calendar: str = "calendar",
        calendar_title_separator: str = "calendar_title_separator",
        calendar_splitter: str = "calendar_splitter",
    ):
        self.district = district
        self.municipal = municipal
        self.fixed_district = fixed_district
        self.fields = {
            "town": town,
            "plz": plz,
            "street": street,
            "hnr": hnr,
            "addition": addition,
        }
        self.calendar = calendar
        self.title_separator = calendar_title_separator
        self.splitter = calendar_splitter

    def __call__(self, source: BaseSource) -> Schedule:
        params = source.params
        district = str(self.fixed_district or params[self.district]).lower()
        if district in UNSUPPORTED:
            raise SourceArgumentException(self.district, UNSUPPORTED[district])
        if district not in DISTRICTS:
            raise SourceArgumentNotFoundWithSuggestions(
                self.district, district, list(DISTRICTS)
            )
        self._session = source.session
        self._district = district
        self._home = f"https://{district}.umweltverbaende.at/"
        self._municipal = params.get(self.municipal)
        self._args = {k: params.get(v) for k, v in self.fields.items()}
        cal = params.get(self.calendar)
        self._calendars = (
            [c.lower() for c in cal]
            if isinstance(cal, list)
            else [cal.lower()]
            if cal
            else None
        )
        self._sep = params.get(self.title_separator) or ":"
        self._split = params.get(self.splitter)

        page = self._find_collection_page()
        now = datetime.now()
        years = [now.year] + ([now.year + 1] if now.month == 12 else [])
        if page is None:
            return Schedule(self._old(years))
        try:
            rows = self._new(page, years)
        except SourceArgumentException:
            raise
        except Exception as error:
            try:
                return Schedule(self._old(years))
            except Exception:
                raise error from None
        return Schedule(rows or self._old(years))

    # -- discovery -----------------------------------------------------------

    def _find_collection_page(self) -> str | None:
        year = datetime.now().year
        paths = (
            *_COLLECTION_PATHS,
            f"fuer-die-bevoelkerung/abholtermine-{year + 1}/",  # Zwettl
            f"fuer-die-bevoelkerung/abholtermine-{year}/",
        )
        for path in paths:
            response = self._session.get(f"{self._home}{path}")
            if response.status_code == 200:
                parsed = urlparse(str(response.url))
                self._home = f"{parsed.scheme}://{parsed.netloc}/"
                return str(response.url)
        return None

    # -- old site ------------------------------------------------------------

    def _old(self, years: list[int]) -> list[tuple[date, str]]:
        rows = self._old_year(years[0])
        for year in years[1:]:
            try:
                rows += self._old_year(year)
            except Exception:
                pass
        return rows

    def _old_year(self, year: int) -> list[tuple[date, str]]:
        base = f"https://{self._district}.umweltverbaende.at/"
        listing = self._session.get(f"{base}?kat=32&jahr={year}")
        html = listing.text
        if self._municipal:
            soup = BeautifulSoup(listing.text, "html.parser")
            for col in soup.select("div.col-sm-9"):
                for link in col.select("a.weblink"):
                    if self._municipal in link.text:
                        html = self._session.get(f"{base}{link['href']}").text
        return old_rows(html, self._calendars, self._sep, self._split)

    # -- new site ------------------------------------------------------------

    def _new(self, url: str, years: list[int]) -> list[tuple[date, str]]:
        rows = self._new_year(url, years[0])
        for year in years[1:]:
            try:
                rows += self._new_year(url, year)
            except Exception:
                pass
        return rows

    def _new_year(self, url: str, year: int) -> list[tuple[date, str]]:
        page = self._session.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        try:
            links = choose_ics_links(soup, self._home, self._municipal, self._calendars)
        except LookupError:
            pass
        else:
            from waste_collection_schedule.service.ICS import ICS

            rows: list[tuple[date, str]] = []
            for link in links:
                rows += ICS().convert(self._session.get(link).text)
            return rows
        return self._ajax(page.text, soup, year)

    def _post(self, data: Any) -> Any:
        response = self._session.post(f"{self._home}wp-admin/admin-ajax.php", data=data)
        response.raise_for_status()
        return response.json()

    def _level(
        self,
        data: dict[str, str],
        argument: str,
        value: str | None,
        element: str,
        following: Any,
    ) -> dict[str, str]:
        """Resolve one dropdown level, then the levels below it."""
        data["element"] = element
        options = BeautifulSoup(
            (self._post(data)["options"] or "").strip(), "html.parser"
        ).select("option")
        if not options:
            return data
        if len(options) == 1:
            data[f"search[{element}]"] = options[0]["value"]
            return following(data)
        names = [o.text.strip() for o in options]
        if not value:
            raise SourceArgumentRequiredWithSuggestions(argument, value, names)
        match = next((o for o in options if same(value, o.text)), None)
        if match is None:
            raise SourceArgumentNotFoundWithSuggestions(argument, value, names)
        data[f"search[{element}]"] = match["value"]
        return following(data)

    def _ajax(self, text: str, soup: Any, year: int) -> list[tuple[date, str]]:
        nonce_match = _NONCE.search(text)
        if not nonce_match:
            raise ValueError("Could not find the nonce on the collection page")
        nonce = nonce_match.group(1)

        select = soup.select_one("select#gemeinde")
        if not select:
            raise ValueError("Could not find the list of municipalities")
        options = [o for o in select.select("option") if o["value"]]
        match = next(
            (o for o in options if self._municipal and same(self._municipal, o.text)),
            None,
        )
        if match is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipal", self._municipal, [o.text.strip() for o in options]
            )
        municipal = match["value"]

        data: dict[str, str] = {
            "action": "get_zone_and_abfuhrtermine",
            "nonce": nonce,
            "element": "",
            "jahr": str(year),
            "search[gemeinde]": municipal,
        }
        args = self._args

        def addition(d: dict[str, str]) -> dict[str, str]:
            return self._level(d, "addition", args["addition"], "zusatz", lambda x: x)

        def number(d: dict[str, str]) -> dict[str, str]:
            return self._level(d, "hnr", args["hnr"], "hausnummer", addition)

        def street(d: dict[str, str]) -> dict[str, str]:
            return self._level(d, "street", args["street"], "strasse", number)

        def plz(d: dict[str, str]) -> dict[str, str]:
            return self._level(d, "plz", args["plz"], "postleitzahl", street)

        try:
            located = self._level(
                {
                    "action": "get_dropdown_data",
                    "nonce": nonce,
                    "element": "ort",
                    "search[gemeinde]": municipal,
                    "jahr": str(year),
                },
                "town",
                args["town"],
                "ort",
                plz,
            )
            # Keep every filter from the dropdown chain so the household's own
            # schedule is returned, not a broad default.
            for key in _LOCATION_KEYS:
                if key in located:
                    data[key] = located[key]
        except Exception:
            # Continue with just the municipality: the household filter is a
            # refinement, and the municipality's own zones are still a schedule.
            pass

        answer = self._post(data)
        zones = answer.get("zones", []) if answer.get("success") else []
        if not isinstance(zones, list):
            zones = []

        if not zones:
            zones = self._zones_by_fraction(nonce, year, municipal, data)

        rows: list[tuple[date, str]] = []
        for zone in zones:
            fraction = zone.get("fraktion")
            # Some zones come back with a fraction but no (or empty) "dates".
            if not fraction or not zone.get("dates"):
                continue
            for entry in zone["dates"]:
                rows.append(
                    (datetime.strptime(entry["date"], "%Y-%m-%d").date(), fraction)
                )
        return rows

    def _zones_by_fraction(
        self, nonce: str, year: int, municipal: str, data: dict[str, str]
    ) -> list[Any]:
        """Older districts: ask for the checked fractions, then for their zones."""
        fractions = {
            "action": "get_fraktionen",
            "nonce": nonce,
            "element": "",
            "jahr": str(year),
            "search[gemeinde]": municipal,
            **{k: data[k] for k in _LOCATION_KEYS if k in data},
        }
        answer = self._post(fractions)
        if not answer.get("html"):
            return []
        boxes = BeautifulSoup(answer["html"], "html.parser").select(
            "input[type=checkbox][name='fraktionen[]']"
        )
        checked = [b["value"] for b in boxes if b.has_attr("checked")]
        if not checked:
            return []
        body: list[tuple[str, str]] = [
            ("action", "get_zone_and_abfuhrtermine"),
            ("nonce", nonce),
            ("element", ""),
            ("jahr", str(year)),
            ("search[gemeinde]", municipal),
            *[(k, data[k]) for k in _LOCATION_KEYS if k in data],
            *[("fraktionen[]", c) for c in checked],
        ]
        answer = self._post(body)
        zones = answer.get("zones", []) if answer.get("success") else []
        return zones if isinstance(zones, list) else []


class UmweltverbaendeParser(Parser["list[tuple[date, str]]"]):
    """The ``(date, label)`` rows the retriever found."""

    def __call__(
        self, response: Schedule, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        return response.rows
