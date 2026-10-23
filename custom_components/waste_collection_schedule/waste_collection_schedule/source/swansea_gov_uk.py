import base64
import json
import re
from datetime import date

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Swansea Council"
DESCRIPTION = "Source script for swansea.gov.uk"
URL = "https://swansea.gov.uk"
COUNTRY = "uk"
TEST_CASES = {
    "Cwmdonkin Drive": {"street_name": "cwmdonkin", "post_code": "SA20RA"},
    "Cwmdonkin Drive (UPRN)": {"post_code": "SA2 0RA", "uprn": "100100351698"},
    "Postcode only": {"post_code": "sa2 0ra"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "post_code": "Full postcode of the property",
        "street_name": "Any part of the address (e.g. street name), used to pick an address in the postcode",
        "uprn": "Unique Property Reference Number (UPRN) of the property",
    }
}
PARAM_TRANSLATIONS = {
    "en": {
        "post_code": "Postcode",
        "street_name": "Street name",
        "uprn": "UPRN",
    }
}

FORM_URL = "https://www.swansea.gov.uk/recyclingsearch"
POSTCODE_URL = "https://www.swansea.gov.uk/apiserver/postcode"
FORM_NAME = "RECYCLINGSEARCHMYACCOUNT"

ICON_MAP = {
    "Pink": Icons.GENERAL_WASTE,
    "Green": Icons.RECYCLING,
}

CLASS_MAP = {
    "calendar-pink": ["Pink"],
    "calendar-green": ["Green"],
    "calendar-both": ["Pink", "Green"],
}

MONTHS = {
    m: i + 1
    for i, m in enumerate(
        [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]
    )
}


def _normalise(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def _parse_caption(caption: str) -> tuple[int, int] | None:
    """Parse 'October 2026' or 'i18n{sc.commercialwaste.month10} 2026'."""
    year_match = re.search(r"(\d{4})\s*$", caption)
    if not year_match:
        return None
    year = int(year_match.group(1))
    month_match = re.search(r"month(\d{1,2})\}", caption)
    if month_match:
        return year, int(month_match.group(1))
    word = caption[: year_match.start()].strip().lower()
    if word in MONTHS:
        return year, MONTHS[word]
    return None


def _address_desc(address: dict) -> str:
    parts = [address.get(f"line{i}", "") for i in range(1, 6)]
    parts += [address.get("town", ""), address.get("postcode", "")]
    return ", ".join(p for p in parts if p)


class Source:
    def __init__(
        self,
        post_code: str,
        street_name: str | None = None,
        uprn: str | int | None = None,
    ):
        self._post_code = post_code
        self._street_name = street_name
        self._uprn = str(uprn) if uprn else None

    def _get_address(self, session) -> dict:
        jsonrpc = {
            "id": 1,
            "method": "postcodeSearch",
            "params": {"provider": "", "postcode": self._post_code},
        }
        r = session.get(
            POSTCODE_URL,
            params={"callback": "cb", "jsonrpc": json.dumps(jsonrpc)},
            timeout=30,
        )
        r.raise_for_status()
        # Response is JSONP: cb({...})
        payload = json.loads(r.text[r.text.index("(") + 1 : r.text.rindex(")")])
        addresses = [a for a in payload.get("result") or [] if "udprn" in a]
        if not addresses:
            raise SourceArgumentNotFound("post_code", self._post_code)

        if self._uprn:
            for address in addresses:
                if address["udprn"].lstrip("0") == self._uprn.lstrip("0"):
                    return address
            raise SourceArgumentNotFoundWithSuggestions(
                "uprn", self._uprn, [a["udprn"] for a in addresses]
            )

        if self._street_name:
            needle = _normalise(self._street_name)
            for address in addresses:
                if needle in _normalise(_address_desc(address)):
                    return address
            raise SourceArgumentNotFoundWithSuggestions(
                "street_name",
                self._street_name,
                sorted({_address_desc(a) for a in addresses}),
            )

        # Collections are scheduled per street, so any address in the postcode will do
        return addresses[0]

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        address = self._get_address(session)

        r = session.get(FORM_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form", id=f"{FORM_NAME}_FORM")
        if not form:
            raise Exception("Could not find recycling search form")

        def _val(name: str) -> str:
            el = form.find("input", attrs={"name": f"{FORM_NAME}_{name}"})
            return el.get("value", "") if el else ""

        data = {
            f"{FORM_NAME}_PAGESESSIONID": _val("PAGESESSIONID"),
            f"{FORM_NAME}_SESSIONID": _val("SESSIONID"),
            f"{FORM_NAME}_NONCE": _val("NONCE"),
            f"{FORM_NAME}_VARIABLES": "e30=",
            f"{FORM_NAME}_PAGENAME": "POSTCODEINPUT",
            f"{FORM_NAME}_PAGEINSTANCE": "0",
            f"{FORM_NAME}_ADDRESSLOOKUPPOSTCODE": address.get("postcode", ""),
            f"{FORM_NAME}_ADDRESSLINE1": address.get("line1", ""),
            f"{FORM_NAME}_ADDRESSLINE2": address.get("line2", ""),
            f"{FORM_NAME}_ADDRESSLINE3": address.get("line3", ""),
            f"{FORM_NAME}_TOWN": address.get("town", ""),
            f"{FORM_NAME}_POSTCODE": address.get("postcode", ""),
            f"{FORM_NAME}_UPRN": address["udprn"],
            f"{FORM_NAME}_FORMACTION_NEXT": f"{FORM_NAME}_NEXTBUTTON",
        }
        r = session.post(
            form["action"],
            data=data,
            headers={"Origin": "https://www.swansea.gov.uk", "Referer": FORM_URL},
            timeout=30,
        )
        r.raise_for_status()

        return self._parse_calendar(self._get_bin_info_html(r.text))

    @staticmethod
    def _get_bin_info_html(page: str) -> str:
        # The results are held in the base64-encoded form data of the page
        match = re.search(rf'{FORM_NAME}FormData\s*=\s*"([^"]+)"', page)
        if match:
            form_data = json.loads(base64.b64decode(match.group(1)).decode("utf-8"))
            for page_data in form_data.values():
                if isinstance(page_data, dict) and page_data.get("DISPLAYBININFO"):
                    return page_data["DISPLAYBININFO"]
        # Fall back to the rendered results block
        soup = BeautifulSoup(page, "html.parser")
        div = soup.find("div", id=f"{FORM_NAME}_DISPLAYBININFO")
        if div:
            return str(div)
        raise Exception("No collection data found in response")

    @staticmethod
    def _parse_calendar(html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        entries = []
        for table in soup.select("table.bin-calendar"):
            caption = table.find("caption")
            year_month = (
                _parse_caption(caption.get_text(strip=True)) if caption else None
            )
            if not year_month:
                continue
            year, month = year_month
            for td in table.find_all("td"):
                types = next(
                    (CLASS_MAP[c] for c in td.get("class") or [] if c in CLASS_MAP),
                    None,
                )
                day = td.get_text(strip=True)
                if not types or not day.isdigit():
                    continue
                for t in types:
                    entries.append(
                        Collection(
                            date=date(year, month, int(day)),
                            t=t,
                            icon=ICON_MAP.get(t),
                        )
                    )

        if not entries:
            raise Exception("No collection dates found in calendar")
        return entries
