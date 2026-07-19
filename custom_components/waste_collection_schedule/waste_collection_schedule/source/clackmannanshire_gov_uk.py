import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Clackmannanshire Council"
DESCRIPTION = "Source for Clackmannanshire Council, UK waste collection."
URL = "https://www.clacks.gov.uk"
COUNTRY = "uk"
TEST_CASES = {
    "16 Crophill, Sauchie": {
        "postcode": "FK10 3EY",
        "address": "16 Crophill, Sauchie",
    },
    "Elim Pentecostal Church, Alloa": {
        "postcode": "FK10 1EB",
        "address": "Elim Pentecostal Church, Alloa",
    },
    "With garden waste permit": {
        "postcode": "FK10 3EY",
        "address": "16 Crophill, Sauchie",
        "garden_waste": True,
    },
}

ICON_MAP = {
    "food caddy": Icons.BIO_KITCHEN,
    "blue bin": Icons.RECYCLING,
    "green bin": Icons.GENERAL_WASTE,
    "grey bin": Icons.PAPER,
    "brown bin": Icons.GARDEN,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Postcode of the property, e.g. 'FK10 3EY'.",
        "address": (
            "Address exactly as shown in the search results on the council "
            "website, e.g. '16 Crophill, Sauchie'."
        ),
        "garden_waste": (
            "Set to true if you hold a paid garden waste (brown bin) permit, "
            "to include its collection dates (optional, default false)."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "address": "Address",
        "garden_waste": "Garden waste (brown bin) permit",
    },
}

BASE_URL = "https://www.clacks.gov.uk"
SEARCH_URL = f"{BASE_URL}/environment/wastecollection/"

_YEAR_SUFFIX_RE = re.compile(r"\s*\d{4}\s*$")


def _normalize(text: str) -> str:
    return " ".join(text.lower().replace(",", " ").split())


class Source:
    def __init__(self, postcode: str, address: str, garden_waste: bool = False) -> None:
        self._postcode = postcode.strip()
        self._address = address.strip()
        self._garden_waste = bool(garden_waste)

    def _find_property_url(self, session: requests.Session) -> str:
        r = session.get(SEARCH_URL, params={"pc": self._postcode})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        results_div = soup.find("div", {"class": "highlight"})
        links: list[Tag] = []
        if isinstance(results_div, Tag):
            links = [
                a
                for a in results_div.find_all("a")
                if isinstance(a, Tag)
                and str(a.get("href", "")).startswith(
                    "/environment/wastecollection/id/"
                )
            ]

        if not links:
            raise SourceArgumentNotFound(
                "postcode",
                self._postcode,
                "No properties were found for this postcode on the "
                "Clackmannanshire Council website, please check the "
                "spelling and try again.",
            )

        target_norm = _normalize(self._address)

        for a in links:
            if _normalize(a.get_text()) == target_norm:
                return urljoin(BASE_URL, str(a["href"]))

        for a in links:
            if target_norm in _normalize(a.get_text()):
                return urljoin(BASE_URL, str(a["href"]))

        available = [a.get_text(strip=True) for a in links]
        raise SourceArgumentNotFoundWithSuggestions("address", self._address, available)

    def _find_ics_links(
        self, session: requests.Session, property_url: str
    ) -> list[str]:
        r = session.get(property_url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        highlight = soup.find("div", {"class": "highlight"})
        if not isinstance(highlight, Tag):
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "Could not find the property details page content.",
            )

        ics_links = [
            urljoin(BASE_URL, str(a["href"]))
            for a in highlight.find_all("a")
            if isinstance(a, Tag) and str(a.get("href", "")).lower().endswith(".ics")
        ]
        if not ics_links:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "No calendar (.ics) links were found for this property.",
            )
        return ics_links

    def _get_icon(self, title: str) -> Icons | None:
        return ICON_MAP.get(title.lower())

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        property_url = self._find_property_url(session)
        ics_links = self._find_ics_links(session, property_url)

        entries: list[Collection] = []

        r = session.get(ics_links[0])
        r.raise_for_status()
        for date, title in ICS().convert(r.text):
            entries.append(Collection(date=date, t=title, icon=self._get_icon(title)))

        if self._garden_waste and len(ics_links) > 1:
            r = session.get(ics_links[1])
            r.raise_for_status()
            for date, title in ICS().convert(r.text):
                clean_title = _YEAR_SUFFIX_RE.sub("", title).strip()
                entries.append(
                    Collection(
                        date=date,
                        t=clean_title,
                        icon=self._get_icon(clean_title),
                    )
                )

        return entries
