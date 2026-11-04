import re
from typing import TYPE_CHECKING, Any, NamedTuple

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    OTHER,
    PAPER,
    PLASTIC,
    RECYCLABLES,
)

# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# a-region.ch / citymobile.ch is a Swiss municipal waste-widget platform that
# powers several unrelated providers (A-Region, Köniz, ZAB Bazenheid,
# Winterthur) from the same "apid"/"apparentid" HTML structure:
#
#   region page -> one link per waste-type/tour -> (optionally) one link per
#   district within that tour -> a single "webcal://...ical.php" calendar.
#
# Resolving a region is provider-specific (a static municipality -> href table
# for A-Region/Köniz/ZAB, a street-name search for Winterthur), but the walk
# from a resolved region down to each tour's ICS calendar is identical across
# all four, so it lives once in ARegionRetriever. The label on each returned
# Collection comes from the ICS feed's own SUMMARY, not from the tour/waste
# type name used only for site navigation, so ARegionRetriever returns the raw
# ICS text of every calendar it finds and ARegionIcsParser (no I/O) decodes
# them into (date, label) rows for ICSTransformer.
# --------------------------------------------------------------------------- #

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

SERVICES = {
    "winterthur": "https://m.winterthur.ch",
    "a_region": "https://www.a-region.ch",
    "koeniz": "https://koeniz.citymobile.ch",
    "zab": "https://zab.citymobile.ch",
}

# The raw ICS SUMMARY labels the shared multilingual vocabulary
# (waste_types.resolve) does not already recognise verbatim (Swiss German
# spellings, or a canonical bucket the catalogue has no dedicated type for).
# Anything not listed here and not resolved falls back to
# waste_types.preserved(), so an unrecognised label is still shown (never
# silently dropped to OTHER). Consistent with the mapping already used for the
# same Swiss German labels in muttenz_ch.py.
TYPE_VALUE_MAP = {
    "Kehricht": GENERAL_WASTE,
    "Grünabfuhr": GARDEN_WASTE,
    "Grüngut": GARDEN_WASTE,
    "Papier/Karton": PAPER,
    "Metall": RECYCLABLES,
    "Altmetall": RECYCLABLES,
    "Schredderdienst": GARDEN_WASTE,
    "Häckseldienst": GARDEN_WASTE,
    "Christbaum": GARDEN_WASTE,
    "Christbäume": GARDEN_WASTE,
    "Sperrgut": RECYCLABLES,
    # Tour titles (ZAB, Köniz): a multi-district tour's events are labelled by
    # their tour, see _tour_label().
    "Kehrichtsammlung": GENERAL_WASTE,
    "Papier und Karton": PAPER,
    "Bioabfuhr": ORGANIC,
    # The KUH-Bag: mixed household plastics.
    "Kunststoffsammlung": PLASTIC,
    # A swap day for reusable items at the collection point, not a pickup.
    "Bring- und Holtag": OTHER,
    # A-Region and Winterthur tour titles.
    "Hauskehricht, Sperrgut": GENERAL_WASTE,
    "Hauskehricht / Sperrgut": GENERAL_WASTE,
    "Kehricht und Sperrgut": GENERAL_WASTE,
    "Papier, Karton": PAPER,
    "Altpapier und Karton": PAPER,
    "Grünabfälle": GARDEN_WASTE,
    "Grüntour": GARDEN_WASTE,
    "Eisen-und Metallware": RECYCLABLES,
    "Grobmetall": RECYCLABLES,
}


class ARegionRetriever(RetrieverFunc):
    """Resolve a region, then walk its tour/district links down to raw ICS text.

    Region resolution is one of two shapes, selected by which arguments are
    set:

    * ``municipalities``: a static municipality-name -> href table (A-Region,
      Köniz, ZAB). ``municipality`` names the ``source.params`` field holding
      the chosen municipality.
    * ``search_url``: a live street-name search endpoint (Winterthur, which has
      no municipality table). ``street`` names the ``source.params`` field
      holding the street name.

    Once the region page is resolved, every tour link on it is followed; a
    tour whose page lists several districts is followed further using the
    ``district`` field in ``source.params`` (required only when more than one
    district is found and there is no single-district shortcut). Returns the
    raw ICS text of every calendar found (one per tour).
    """

    def __init__(
        self,
        service: str,
        municipalities: "dict[str, str] | None" = None,
        municipality: str = "municipality",
        search_url: "str | None" = None,
        street: str = "street",
        district: str = "district",
    ):
        self.service = service
        self.municipalities = municipalities
        self.municipality_field = municipality
        self.search_url = search_url
        self.street_field = street
        self.district_field = district

    def __call__(self, source: "BaseSource") -> "list[TourCalendar]":
        base_url = SERVICES[self.service]
        session = source.session
        params = source.params

        if self.search_url is not None:
            region_url = self._region_url_by_street(session, params[self.street_field])
        else:
            municipalities = self.municipalities or {}
            municipality_value = params[self.municipality_field]
            if municipality_value not in municipalities:
                raise SourceArgumentNotFoundWithSuggestions(
                    self.municipality_field,
                    municipality_value,
                    municipalities.keys(),
                )
            region_url = municipalities[municipality_value]

        requested = _requested_districts(params.get(self.district_field))
        waste_type_links = self._get_waste_types(session, base_url, region_url)

        # Walk every tour first and only then download calendars, so a wrong or
        # missing district is reported with the districts of *all* tours (a
        # household picks one per tour, e.g. Wil: "Kehrichtsammlung Wil Nord;
        # Papier und Karton Wil Nord-West") before any ICS is fetched.
        all_districts: list[str] = []
        matched: set[str] = set()
        needs_district = False
        calendar_pages: list[tuple[str, str]] = []
        tour_pages: list[tuple[str, Any]] = []
        for tour, link in waste_type_links.items():
            soup = self._get_page(session, base_url, link)
            districts = _districts(soup)
            if not districts:
                tour_pages.append((tour, soup))
                continue
            if len(districts) == 1:
                # only one district found -> use it
                calendar_pages.append((tour, next(iter(districts.values()))))
                continue
            all_districts += [d for d in districts if d not in all_districts]
            if requested is None:
                needs_district = True
                continue
            # A tour none of whose districts was requested is left out: the
            # household chose districts for the tours it uses.
            for name in requested:
                if name in districts:
                    matched.add(name)
                    calendar_pages.append((tour, districts[name]))

        if needs_district:
            raise SourceArgumentRequiredWithSuggestions(
                self.district_field,
                "Multiple districts found; specify which one to use.",
                all_districts,
            )
        unmatched = [name for name in requested or () if name not in matched]
        if unmatched and all_districts:
            raise SourceArgumentNotFoundWithSuggestions(
                self.district_field,
                "; ".join(unmatched),
                all_districts,
            )

        calendars: list[TourCalendar] = []
        for tour, soup in tour_pages:
            calendars += [
                TourCalendar(tour, text)
                for text in self._calendar_texts(session, base_url, soup, requested)
            ]
        for tour, link in calendar_pages:
            calendars += [
                TourCalendar(tour, text)
                for text in self._get_ics_texts(session, base_url, link, requested)
            ]
        return calendars

    def _region_url_by_street(self, session: Any, street: str) -> str:
        r = session.get(self.search_url, params={"q": street})
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        anchors = soup.select("a")
        if not anchors:
            raise SourceArgumentException(self.street_field, "No streets found")

        streets = []
        for a in anchors:
            href = a.get("href")
            if not isinstance(href, str):
                continue
            text = a.get_text(strip=True)
            streets.append(text)
            if text.lower().replace(" ", "") == street.lower().replace(" ", ""):
                return href

        raise SourceArgumentNotFoundWithSuggestions(self.street_field, street, streets)

    def _get_waste_types(
        self, session: Any, base_url: str, link: str
    ) -> "dict[str, str]":
        if not link.startswith("http"):
            link = f"{base_url}{link}"
        r = session.get(link)
        r.raise_for_status()

        waste_types: dict[str, str] = {}
        soup = BeautifulSoup(r.text, features="html.parser")
        for download in soup.find_all("a", href=True):
            href = download.get("href")
            if href and "download.php" in href:
                # Skip PDF/attachment downloads (e.g. "Abfall-Info" leaflets)
                # outright: they are not calendar pages, can be several MB in
                # size, and the title-text PDF check below doesn't catch every
                # leaflet (some don't say "PDF" in their visible title).
                # Repeatedly fetching a several-MB PDF on every poll can also
                # trip the provider's own anti-bot rate limiting (#7310).
                continue
            if (
                download.find("div", class_="badgeIcon")
                or download.find("img", class_="rowImg")
                or download.find("img", class_="svgIconImg")
            ):
                titles = download.find_all("div", class_="title")
                title_strings = [title.string for title in titles]
                # Skip PDF download tiles: they are not ICS-backed waste types,
                # and following one feeds a PDF's bytes into the HTML parser
                # (crashing on some municipalities, e.g. Wolfhalden). The legacy
                # check `if "PDF" in titles` compared the string against a list
                # of Tag objects, so it never matched.
                if any(s and "PDF" in s for s in title_strings):
                    continue
                if not title_strings:
                    title_strings = [download.get_text(strip=True)]
                for title in title_strings:
                    if title:
                        waste_types[title] = href
        return waste_types

    def _get_page(self, session: Any, base_url: str, link: str) -> Any:
        if not link.startswith("http"):
            link = f"{base_url}{link}"
        r = session.get(link)
        r.raise_for_status()
        return BeautifulSoup(r.text, features="html.parser")

    def _get_ics_texts(
        self,
        session: Any,
        base_url: str,
        link: str,
        requested: "list[str] | None",
    ) -> "list[str]":
        """The calendar of one tour or district page.

        A district page may list districts itself; one is followed directly,
        several by the requested names (ignored when none of them is there).
        """
        soup = self._get_page(session, base_url, link)
        return self._calendar_texts(session, base_url, soup, requested)

    def _calendar_texts(
        self,
        session: Any,
        base_url: str,
        soup: Any,
        requested: "list[str] | None",
    ) -> "list[str]":
        districts = _districts(soup)
        if len(districts) == 1:
            return self._get_ics_texts(
                session, base_url, next(iter(districts.values())), requested
            )
        if districts:
            texts: list[str] = []
            for name in requested or ():
                if name in districts:
                    texts += self._get_ics_texts(
                        session, base_url, districts[name], requested
                    )
            return texts

        for download in soup.find_all("a", href=True):
            # href ::= "webcal://.../appl/ics.php?apid=12731252&from=..."
            href = download.get("href")
            if href.startswith("webcal") and "ical.php" in href:
                ics_url = re.sub("^webcal", "https", href)
                ics_response = session.get(ics_url)
                ics_response.raise_for_status()
                return [ics_response.text]

        return []


def _districts(soup: Any) -> "dict[str, str]":
    """District name -> link of the districts a tour page lists, if any."""
    districts: dict[str, str] = {}
    for download in soup.find_all("a", href=True):
        href = download.get("href")
        if "apparentid" in href:
            title = download.find("div", class_="title")
            if title is not None and title.string:
                district_name_split = title.string.split(": ")
                districts[
                    district_name_split[1 if len(district_name_split) > 1 else 0]
                ] = href
    return districts


def _requested_districts(value: Any) -> "list[str] | None":
    """The configured district(s): one name, "A; B", or a YAML list.

    Semicolons separate names because district names contain commas
    ("Papier und Karton Bronschhofen, Maugwil").
    """
    if value is None:
        return None
    items = value if isinstance(value, (list, tuple)) else str(value).split(";")
    names = [str(item).strip() for item in items]
    return [name for name in names if name] or None


class TourCalendar(NamedTuple):
    """The raw ICS text of one calendar and the title of the tour it belongs to."""

    tour: str
    ics: str


def _tour_label(label: str, tour: str) -> str:
    """Classify an event by its tour when its SUMMARY is the tour plus an area.

    Applied before the type map, so the tour title is what gets mapped.

    Tours with several districts title each calendar's events after the
    district: "Kehrichtsammlung Wil Nord", "Papier und Karton Bronschhofen,
    Maugwil" in the tour "Kehrichtsammlung" / "Papier und Karton". The tour
    title is the waste type; the rest only names the area.
    """
    tour = " ".join(tour.split())
    if not tour or label == tour:
        return label
    if label.startswith(tour):
        return tour
    # A-Region names the district after a colon, shortening the tour:
    # "Hauskehricht: Unteres Stadtgebiet" in the tour "Hauskehricht, Sperrgut".
    head, colon, _ = label.partition(": ")
    if colon and head.strip() and tour.startswith(head.strip()):
        return tour
    return label


class ARegionIcsParser(Parser["list[tuple[Any, str]]"]):
    """Decode every raw ICS calendar returned by ARegionRetriever.

    Does no I/O: it only runs the (pure text) ICS conversion over each raw
    calendar and concatenates the resulting (date, label) rows, so it can be
    exercised standalone against cached ICS fixtures.
    """

    def __init__(self, regex: "str | None" = None, min_events: "int | None" = None):
        self.regex = regex
        self.min_events = min_events

    def __call__(
        self, raw: "list[TourCalendar | str]", source: "BaseSource | None" = None
    ) -> "list[tuple[Any, str]]":
        from waste_collection_schedule import response_shape
        from waste_collection_schedule.service.ICS import ICS

        ics = ICS(regex=self.regex)
        rows: list[tuple[Any, str]] = []
        for calendar in raw:
            if isinstance(calendar, TourCalendar):
                rows += [
                    (date, _tour_label(label, calendar.tour))
                    for date, label in ics.convert(calendar.ics)
                ]
            else:
                rows += ics.convert(calendar)

        if self.min_events is not None:
            response_shape.expect(
                len(rows) >= self.min_events,
                source_name=response_shape.source_name(source),
                detail=f"expected at least {self.min_events} ICS events across "
                f"{len(raw)} calendar(s), got {len(rows)}",
                raw="\n---\n".join(
                    c.ics if isinstance(c, TourCalendar) else c for c in raw
                )[:2000],
            )
        return rows
