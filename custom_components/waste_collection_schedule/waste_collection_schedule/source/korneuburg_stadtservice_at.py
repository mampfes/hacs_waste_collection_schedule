from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

# Demonstrates: a RiSKommunal municipality whose calendar is not exposed
# through the platform's usual kalender.aspx table/list rendering at all.
# Korneuburg instead resolves a "Teilgebiet" (subarea, 1-4) from the address
# via the same street-dropdown + strassenArr address picker every RiSKommunal
# install exposes (so RiSKommunalSource's parsing of those is reused rather
# than re-implemented), then scrapes four fixed per-subarea pages for a
# piwik_download_tracker iCal link each, and finally downloads those iCal
# feeds. No configured retriever expresses "resolve an id, then scrape N
# unrelated pages for a download link each, then fetch every one of those" --
# hence a source-defined retrieve()/parse() pair.

_BASE_URL = "https://www.korneuburg.gv.at"
_ADDRESS_URL = urljoin(_BASE_URL, "Rathaus/Buergerservice/Muellabfuhr")
_CALENDAR_URL = urljoin(_BASE_URL, "system/web/kalender.aspx")
_MENUONR = "225991280"

# Per-Teilgebiet (subarea) waste-type pages; each carries one
# piwik_download_tracker iCal link for that round.
_WASTE_TYPE_PATHS: dict[str, tuple[str, ...]] = {
    "1": ("Biomuell_3", "Restmuell_3", "Papier_2", "Gelber_Sack_4"),
    "2": ("Biomuell_4", "Restmuell_2", "Papier_3", "Gelber_Sack_1"),
    "3": ("Biomuell_1", "Restmuell_1", "Papier_1", "Gelber_Sack_2"),
    "4": ("Biomuell_2", "Restmuell", "Papier", "Gelber_Sack_3"),
}

# Accepts the cookie-consent banner; required before the RIS CMS serves the
# address-picker page.
_BASE_COOKIES: dict[str, str] = {"ris_cookie_setting": "g7750"}


def _valid_teilgebiet(value: object) -> str | None:
    """Return the Teilgebiet number as a string if it's a direct 1-4 override."""
    try:
        number = int(str(value))
    except (TypeError, ValueError):
        return None
    return str(number) if 0 < number <= 4 else None


def _extract_teilgebiet(soup: BeautifulSoup) -> str | None:
    """Read the "Teilgebiet N" label off the resolved-address overview page."""
    for span in soup.find_all("span"):
        if (
            span.parent is not None
            and span.parent.name == "td"
            and span.string
            and "teilgebiet" in span.string.lower()
        ):
            return span.string.split(" ")[1]
    return None


def _resolve_teilgebiet(
    source: BaseSource, session, cookies: dict[str, str]
) -> tuple[str, dict[str, str]]:
    """Resolve the Teilgebiet for the configured street/house number.

    Reuses RiSKommunalSource's street-dropdown and strassenArr parsing (the
    same address picker every RiSKommunal install exposes) to turn the
    street/house number into a "typids" value and a selection cookie, then
    scrapes the resulting overview page for its Teilgebiet label. Returns the
    Teilgebiet plus the cookies to keep using for every later request (the
    selection cookie the CMS expects to see from here on).
    """
    street_name = source.params["street_name"]
    street_number = str(source.params["street_number"])

    page = session.get(_ADDRESS_URL, cookies=cookies, timeout=source.TIMEOUT)
    page.raise_for_status()
    html = page.text

    street_map = RiSKommunalSource._parse_street_dropdown(html)
    street_id = street_map.get(street_name)
    if street_id is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "street_name", street_name, sorted(street_map)
        )

    number_id = None
    typids = None
    labels: list[str] = []
    for entry in RiSKommunalSource._parse_strassen_arr(html):
        if entry[0] != street_id:
            continue
        for hnr in entry[1]:
            label = str(hnr[1])
            labels.append(label)
            if label == street_number:
                number_id, typids = hnr[0], hnr[2]
        break

    if typids is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "street_number", street_number, labels
        )

    cookies = dict(cookies, riscms_muellkalender=f"{street_id}_{number_id}")
    overview = session.get(
        _CALENDAR_URL,
        cookies=cookies,
        params={"sprache": "1", "menuonr": _MENUONR, "typids": typids},
        timeout=source.TIMEOUT,
    )
    overview.raise_for_status()

    teilgebiet = _extract_teilgebiet(BeautifulSoup(overview.text, "html.parser"))
    if teilgebiet is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "street_number", street_number, labels
        )
    return teilgebiet, cookies


def _region_ical_urls(session, teilgebiet: str, cookies: dict[str, str]) -> list[str]:
    """Scrape each of a Teilgebiet's waste-type pages for its iCal link."""
    urls = []
    for path in _WASTE_TYPE_PATHS[teilgebiet]:
        page = session.get(urljoin(_BASE_URL, path), cookies=cookies, timeout=30)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        link = soup.find(
            "a",
            {"class": "piwik_download_tracker", "data-trackingtyp": "iCal/Kalender"},
        )
        if isinstance(link, Tag):
            href = link.get("href")
            if isinstance(href, str):
                urls.append(urljoin(_BASE_URL, href))
    return urls


@final
class Source(BaseSource):
    TITLE = "Stadtservice Korneuburg"
    DESCRIPTION = "Source for Stadtservice Korneuburg, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Rathaus": {"street_name": "Hauptplatz", "street_number": 39},  # Teilgebiet 4
        "Rathaus using Teilgebiet": {
            "street_name": "SomeStreet",
            "street_number": "1A",
            "teilgebiet": "4",
        },  # Teilgebiet 4
        "Werft": {"street_name": "Am Hafen", "street_number": 6},  # Teilgebiet 2
    }

    PARAMS = (
        street(field="street_name"),
        house_number(field="street_number"),
        text_field("teilgebiet", "Subarea", optional=True),
    )

    transform = ICSTransformer()

    def __init__(
        self,
        street_name: str,
        street_number: "str | int",
        teilgebiet: "str | int | None" = None,
    ):
        super().__init__(
            street_name=street_name,
            street_number=street_number,
            teilgebiet=teilgebiet,
        )

    def retrieve(self, source):
        session = source.session
        cookies = dict(_BASE_COOKIES)

        teilgebiet = _valid_teilgebiet(source.params.get("teilgebiet"))
        if teilgebiet is None:
            teilgebiet, cookies = _resolve_teilgebiet(source, session, cookies)

        return [
            session.get(url, cookies=cookies, timeout=source.TIMEOUT)
            for url in _region_ical_urls(session, teilgebiet, cookies)
        ]

    def parse(self, raw, source):
        ics_parser = IcsParser()
        for response in raw:
            yield from ics_parser(response, source)
