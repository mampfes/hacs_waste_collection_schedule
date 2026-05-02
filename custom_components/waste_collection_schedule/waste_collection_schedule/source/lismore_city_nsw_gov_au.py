import json
import re
from datetime import date as dt_date
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)

TITLE = "Lismore City Council"
DESCRIPTION = "Source for Lismore City Council, NSW, Australia."
URL = "https://www.lismore.nsw.gov.au/Households/Waste-and-recycling/Whats-My-Bin-Day1"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the full service address used by Lismore City Council, for example "
        "'1 Rosella Chase, Goonellabah NSW 2480'."
    )
}
TEST_CASES = {
    "1 Rosella Chase, Goonellabah NSW 2480": {
        "address": "1 Rosella Chase, Goonellabah NSW 2480"
    }
}

SEARCH_URL = "https://api.whatbinday.com/api/search"

HEADERS = {
    "accept": "text/html, */*; q=0.01",
    "origin": "https://www.lismore.nsw.gov.au",
    "referer": URL,
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
}

ICON_MAP = {
    "waste bin": "mdi:trash-can",
    "general waste": "mdi:trash-can",
    "red bin": "mdi:trash-can",
    "recycle bin": "mdi:recycle",
    "recycling": "mdi:recycle",
    "yellow bin": "mdi:recycle",
    "green bin": "mdi:leaf",
    "green waste": "mdi:leaf",
    "garden organics": "mdi:leaf",
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


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())
        self._session = requests.Session(impersonate="chrome124")
        self._session.headers.update(HEADERS)
        self._page_html: str | None = None

    def fetch(self) -> list[Collection]:
        html = self._search()
        entries = self._parse_entries(html)
        if not entries:
            raise SourceArgumentNotFound("address", self._address)
        return entries

    def _search(self) -> str:
        api_key = self._get_api_key()
        parsed_address = self._split_address(self._address)
        response = self._session.post(
            SEARCH_URL,
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
                "agendaResultLimit": "3",
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
        return response.text

    def _get_api_key(self) -> str:
        page_html = self._get_page_html()
        api_key = self._extract_api_key(page_html)
        if api_key:
            return api_key

        soup = BeautifulSoup(page_html, "html.parser")
        base_origin = urlparse(URL).netloc.lower()
        for script in soup.select("script[src]"):
            src = script.get("src", "").strip()
            if not src:
                continue

            script_url = urljoin(URL, src)
            parsed_script_url = urlparse(script_url)
            if parsed_script_url.netloc.lower() != base_origin:
                continue

            script_path = parsed_script_url.path.lower()
            if not script_path.endswith(".js"):
                continue
            if "whatbinday" not in script_url.lower():
                continue

            script_response = self._session.get(script_url, timeout=30)
            if not script_response.ok:
                continue
            api_key = self._extract_api_key(script_response.text)
            if api_key:
                return api_key

        raise SourceArgumentException(
            "address",
            "Unable to load the Lismore City Council widget configuration needed to look up collection dates.",
        )

    def _get_page_html(self) -> str:
        if self._page_html is None:
            response = self._session.get(URL, timeout=30)
            response.raise_for_status()
            self._page_html = response.text
        return self._page_html

    def _extract_api_key(self, text: str) -> str | None:
        patterns = [
            r'apiKey["\']?\s*[:=]\s*["\']([0-9a-fA-F-]{36})["\']',
            r'["\']apiKey["\']\s*,\s*["\']([0-9a-fA-F-]{36})["\']',
            r'whatbinday[^"\']*["\']([0-9a-fA-F-]{36})["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _parse_entries(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("li.WBD-result-item")
        if not items:
            return []

        entries: list[Collection] = []
        seen: set[tuple[dt_date, str]] = set()

        for item in items:
            date_el = item.select_one(".WBD-event-date")
            if not date_el:
                continue

            date_text = " ".join(date_el.get_text(" ", strip=True).split())
            try:
                collection_date = datetime.strptime(date_text, "%A %d %b %Y").date()
            except ValueError:
                continue

            detail_els = item.select(".WBD-event-detail")
            for detail in detail_els:
                type_el = detail.select_one(".WBD-bin-text")
                if not type_el:
                    continue

                waste_type = self._normalize_type(
                    " ".join(type_el.get_text(" ", strip=True).split())
                )
                image_el = detail.select_one(".WBD-bin-image")
                picture = None
                if image_el is not None:
                    src = image_el.get("src", "").strip()
                    if src:
                        picture = urljoin(URL, src)
                key = (collection_date, waste_type)
                if key in seen:
                    continue
                seen.add(key)

                entry = Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=self._guess_icon(waste_type),
                )
                if picture:
                    entry.set_picture(picture)
                entries.append(entry)

        return sorted(entries, key=lambda x: x.date)

    def _guess_icon(self, name: str) -> str | None:
        lower = name.lower()
        for key, icon in ICON_MAP.items():
            if key in lower:
                return icon
        return None

    def _normalize_type(self, name: str) -> str:
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
