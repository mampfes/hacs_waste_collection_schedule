import json
import urllib.parse
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from ..collection import Collection
from ..exceptions import SourceArgumentNotFound
from ..icons import Icons

TITLE = "Lismore City Council (NSW)"
DESCRIPTION = "Source for Lismore City Council waste collection, NSW, Australia."
URL = "https://www.lismore.nsw.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "71 Tuntable Falls Rd, NIMBIN NSW 2480": {
        "address": "71 Tuntable Falls Rd, NIMBIN NSW 2480",
    },
    "10 Sibley St, NIMBIN NSW 2480": {
        "address": "10 Sibley St, NIMBIN NSW 2480",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your full street address as you would write it on an envelope, "
        "e.g. '71 Tuntable Falls Rd, NIMBIN NSW 2480'. "
        "Abbreviations like 'Rd', 'St', 'Ave' are fine — the address will be "
        "resolved automatically."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including suburb and postcode.",
    }
}

_EXPERIAN_SEARCH_URL = "https://api.experianaperture.io/address/search/v1"
# Auth-Token sourced from the Lismore Council WhatBinDay widget configuration
# at https://www.lismore.nsw.gov.au/Households/Waste-and-recycling/Whats-My-Bin-Day1
_EXPERIAN_AUTH_TOKEN = "f003c9aa-c3ba-4a6c-8a36-ba5199c13a76"

_WHATBINDAY_URL = "https://api.whatbinday.com/api/search"
_WHATBINDAY_API_KEY = "fef3003f-1321-4de3-ae49-392e22458fb4"

_DATE_FORMAT = "%A %d %b %Y"  # e.g. "Thursday 02 Jul 2026"

# Street-type abbreviation expansion (mirrors WhatBinDay's experinalShimStreetType JS)
_STREET_TYPE_MAP: dict[str, str] = {
    "Rd": "Road",
    "St": "Street",
    "Ave": "Avenue",
    "Av": "Avenue",
    "Dr": "Drive",
    "Ct": "Court",
    "Crt": "Court",
    "Pl": "Place",
    "Cres": "Crescent",
    "Cr": "Crescent",
    "Tce": "Terrace",
    "Pde": "Parade",
    "Hwy": "Highway",
    "Blvd": "Boulevard",
    "Bvd": "Boulevard",
    "Ln": "Lane",
    "Cl": "Close",
    "Gr": "Grove",
    "Esp": "Esplanade",
    "Pwy": "Parkway",
    "Pkwy": "Parkway",
    "Sq": "Square",
    "Cct": "Circuit",
    "Bnd": "Bend",
    "Trk": "Track",
}

ICON_MAP: dict[str, str] = {
    "recycle": Icons.RECYCLING,
    "recycling": Icons.RECYCLING,
    "waste": Icons.GENERAL_WASTE,
    "general": Icons.GENERAL_WASTE,
    "garden": Icons.GARDEN,
    "green": Icons.ORGANIC,
    "organic": Icons.ORGANIC,
    "glass": Icons.GLASS,
    "paper": Icons.PAPER,
    "hazardous": Icons.HAZARDOUS,
    "bulky": Icons.BULKY,
}


def _icon_for_bin(bin_text: str, css_classes: str) -> str | None:
    combined = (bin_text + " " + css_classes).lower()
    for keyword, icon in ICON_MAP.items():
        if keyword in combined:
            return icon
    return None


def _expand_street_type(abbrev: str) -> str:
    """Expand a street-type abbreviation to its full name, e.g. 'Rd' → 'Road'."""
    return _STREET_TYPE_MAP.get(abbrev, abbrev)


class Source:
    def __init__(self, address: str):
        self._address = address

    def _experian_search(self, session: requests.Session) -> str:
        """POST free-text address to Experian; return the format URL of the best match."""
        payload = {
            "country_iso": "AUS",
            "components": {"unspecified": [self._address]},
            "dataset": "",
            "take": 1,
        }
        r = session.post(_EXPERIAN_SEARCH_URL, json=payload, timeout=30)
        r.raise_for_status()

        suggestions = r.json().get("result", {}).get("suggestions", [])
        if not suggestions:
            raise SourceArgumentNotFound(
                "address",
                f"No address found for '{self._address}'. "
                "Check the address is within the Lismore LGA.",
            )
        return suggestions[0]["format"]

    def _experian_format(self, session: requests.Session, format_url: str) -> dict:
        """GET the format URL to retrieve structured address components."""
        r = session.get(format_url, timeout=30)
        r.raise_for_status()
        return r.json().get("result", {})

    @staticmethod
    def _build_wbd_address(result: dict) -> dict:
        components = result.get("components", {})

        building = components.get("building", {})
        street = components.get("street", {})
        locality = components.get("locality", {})
        postal = components.get("postal_code", {})

        street_number = building.get("building_number", "")
        street_type_abbrev = street.get("type", "")
        street_type_long = _expand_street_type(street_type_abbrev)
        street_full = street.get("full_name", "")
        # Replace abbreviated type with full type in street name
        if street_type_abbrev and street_type_abbrev in street_full:
            street_name = street_full.replace(street_type_abbrev, street_type_long, 1)
        else:
            street_name = street_full

        suburb = locality.get("town", {}).get("name", "")
        state = locality.get("region", {}).get("name", "")
        postcode = postal.get("full_name", "")

        formatted = result.get("address", {}).get("address_line_1", "")
        if suburb:
            formatted = f"{formatted}, {suburb} {postcode}"

        return {
            "address": {
                "street_number": street_number,
                "route": street_name,
                "locality": suburb,
                "administrative_area_level_1": state,
                "postal_code": postcode,
                "part": "",
                "subpremise": "",
                "formatted_address": formatted,
            },
            "geometry": {"location": {"lat": 0, "lng": 0}},
        }

    @staticmethod
    def _fetch_bin_days(
        session: requests.Session, wbd_address: dict
    ) -> list[Collection]:
        params = {
            "apiKey": _WHATBINDAY_API_KEY,
            "address": json.dumps(wbd_address),
            "agendaResultLimit": 30,
            "dateFormat": "EEEE dd MMM yyyy",
            "displayFormat": "agenda",
            "calendarStart": "",
            "calendarFutureMonths": 3,
            "calendarPrintBannerImgUrl": "",
            "calendarPrintAdditionalCss": "",
            "regionDisplay": "false",
            "notes": "",
        }
        r = session.post(
            _WHATBINDAY_URL,
            data=urllib.parse.urlencode(params),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        r.raise_for_status()
        return Source._parse_html(r.text)

    @staticmethod
    def _parse_html(html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        entries: list[Collection] = []

        for item in soup.select("li.WBD-result-item"):
            date_tag = item.select_one("span.WBD-event-date")
            if not date_tag:
                continue
            try:
                collection_date = datetime.strptime(
                    date_tag.get_text(strip=True), _DATE_FORMAT
                ).date()
            except ValueError:
                continue

            for detail in item.select("span.WBD-event-detail"):
                img = detail.select_one("img")
                css_classes = " ".join(img.get("class", [])) if img else ""
                text_tag = detail.select_one("span.WBD-bin-text")
                bin_name = (
                    text_tag.get_text(strip=True)
                    if text_tag
                    else (img.get("alt") or img.get("title") or "" if img else "")
                )
                if not bin_name:
                    continue

                entries.append(
                    Collection(
                        collection_date,
                        bin_name,
                        icon=_icon_for_bin(bin_name, css_classes),
                        picture=img.get("src") if img else None,
                    )
                )

        return entries

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/json",
                "Auth-Token": _EXPERIAN_AUTH_TOKEN,
                "Add-Components": "true",
            }
        )

        format_url = self._experian_search(session)
        result = self._experian_format(session, format_url)
        wbd_address = self._build_wbd_address(result)
        return self._fetch_bin_days(session, wbd_address)
