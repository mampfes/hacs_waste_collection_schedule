import json
import re
from datetime import date as dt_date
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)

TITLE = "Lismore City Council"
DESCRIPTION = (
    "Source for Lismore City Council waste collection services in NSW, Australia."
)
URL = "https://www.lismore.nsw.gov.au/Households/Waste-and-recycling/Whats-My-Bin-Day1"
COUNTRY = "au"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the full service address used by Lismore City Council, for example "
        "'1 Rosella Chase, Goonellabah NSW 2480'."
    )
}
PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full service address (e.g. '1 Rosella Chase, Goonellabah NSW 2480')"
    }
}
PARAM_TRANSLATIONS = {"en": {"address": "Address"}}
TEST_CASES = {
    "1 Rosella Chase, Goonellabah NSW 2480": {
        "address": "1 Rosella Chase, Goonellabah NSW 2480"
    },
    "10 Sibley St, NIMBIN NSW 2480": {"address": "10 Sibley St, NIMBIN NSW 2480"},
}

# The council embeds the WhatBinDay widget, which is configured with a
# council-specific API key. The shared WhatBinDay device API (V3) does not
# know about Lismore and answers with another region's roster (see issue
# #7623), so the widget endpoint with Lismore's own key must be used.
SEARCH_URL = "https://api.whatbinday.com/api/search"

HEADERS = {
    "accept": "text/html, */*; q=0.01",
    "origin": "https://www.lismore.nsw.gov.au",
    "referer": URL,
    "x-requested-with": "XMLHttpRequest",
}

STATE_MAP = {
    "NSW": "New South Wales",
    "VIC": "Victoria",
    "QLD": "Queensland",
    "SA": "South Australia",
    "WA": "Western Australia",
    "TAS": "Tasmania",
    "ACT": "Australian Capital Territory",
    "NT": "Northern Territory",
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green Waste": Icons.ORGANIC,
}

API_KEY_PATTERN = re.compile(
    r"""apiKey["']?\s*[:=]\s*["']([0-9a-fA-F-]{36})["']""", re.IGNORECASE
)


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome124")
        api_key = self._get_api_key(session)
        parsed_address = self._split_address(self._address)
        response = session.post(
            SEARCH_URL,
            headers=HEADERS,
            data={
                "apiKey": api_key,
                "address": json.dumps(
                    {
                        "address": {
                            "street_number": parsed_address["street_number"],
                            "route": parsed_address["route"],
                            "locality": parsed_address["locality"],
                            "administrative_area_level_1": STATE_MAP.get(
                                parsed_address["state"], parsed_address["state"]
                            ),
                            "postal_code": parsed_address["postal_code"],
                            "part": "",
                            "subpremise": parsed_address["subpremise"],
                            "formatted_address": parsed_address["formatted_address"],
                        },
                        "geometry": {"location": {"lat": 0, "lng": 0}},
                    }
                ),
                "agendaResultLimit": "5",
                "dateFormat": "EEEE dd MMM yyyy",
                "generalBinImage": "",
                "recycleBinImage": "",
                "greenBinImage": "",
                "glassBinImage": "",
                "paperBinImage": "",
                "displayFormat": "agenda",
                "calendarStart": "",
                "calendarFutureMonths": "2",
                "calendarPrintBannerImgUrl": "",
                "calendarPrintAdditionalCss": "",
                "regionDisplay": "false",
                "notes": "",
            },
            timeout=30,
        )
        response.raise_for_status()

        entries = self._parse_entries(response.text)
        if not entries:
            raise SourceArgumentNotFound("address", self._address)
        return entries

    def _get_api_key(self, session: requests.Session) -> str:
        response = session.get(URL, timeout=30)
        response.raise_for_status()
        match = API_KEY_PATTERN.search(response.text)
        if not match:
            raise SourceArgumentException(
                "address",
                "Unable to load the Lismore City Council widget configuration needed to look up collection dates.",
            )
        return match.group(1)

    def _parse_entries(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        entries: list[Collection] = []
        seen: set[tuple[dt_date, str]] = set()

        for item in soup.select("li.WBD-result-item"):
            date_el = item.select_one(".WBD-event-date")
            if not date_el:
                continue
            date_text = " ".join(date_el.get_text(" ", strip=True).split())
            try:
                collection_date = datetime.strptime(date_text, "%A %d %b %Y").date()
            except ValueError:
                continue

            for detail in item.select(".WBD-event-detail"):
                type_el = detail.select_one(".WBD-bin-text")
                if not type_el:
                    continue
                waste_type = self._normalize_type(
                    " ".join(type_el.get_text(" ", strip=True).split())
                )
                if (collection_date, waste_type) in seen:
                    continue
                seen.add((collection_date, waste_type))

                entry = Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
                image_el = detail.select_one(".WBD-bin-image")
                src = str(image_el.get("src", "")).strip() if image_el else ""
                if src:
                    entry.set_picture(urljoin(URL, src))
                entries.append(entry)

        return sorted(entries, key=lambda x: x.date)

    @staticmethod
    def _normalize_type(name: str) -> str:
        lower = name.lower()
        if "waste bin" in lower or "general waste" in lower or "red bin" in lower:
            return "General Waste"
        if "recycle bin" in lower or "recycling" in lower or "yellow bin" in lower:
            return "Recycling"
        if "green bin" in lower or "green waste" in lower:
            return "Green Waste"
        return name

    def _split_address(self, address: str) -> dict[str, str]:
        normalized = " ".join(address.replace(",", " , ").split())
        match = re.match(
            r"^(?:(?P<subpremise>(?:[A-Za-z]+\s+)?\d+[A-Za-z]?)\/)?"
            r"(?P<street_number>\d+[A-Za-z]?(?:-\d+[A-Za-z]?)?)\s+"
            r"(?P<route>.+?)\s*,?\s+"
            r"(?P<locality>[A-Za-z ]+?)\s+"
            r"(?P<state>NSW|VIC|QLD|SA|WA|TAS|ACT|NT)\s+"
            r"(?P<postal_code>\d{4})$",
            normalized,
            flags=re.IGNORECASE,
        )
        if not match:
            raise SourceArgumentNotFound("address", address)

        subpremise = (match.group("subpremise") or "").strip()
        street_number = match.group("street_number").strip()
        route = match.group("route").replace(" , ", " ").strip()
        locality = match.group("locality").strip().upper()
        state = match.group("state").strip().upper()
        postal_code = match.group("postal_code").strip()
        address_prefix = (
            f"{subpremise}/{street_number}" if subpremise else street_number
        )
        formatted_address = (
            f"{address_prefix} {route}, {locality} {state} {postal_code}"
        )

        return {
            "subpremise": subpremise,
            "street_number": street_number,
            "route": route,
            "locality": locality,
            "state": state,
            "postal_code": postal_code,
            "formatted_address": formatted_address,
        }
