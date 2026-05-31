"""Source for Rochford District Council, UK."""

from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Rochford District Council"
DESCRIPTION = "Source for Rochford District Council, UK."
URL = "https://www.rochford.gov.uk"
COUNTRY = "uk"

API_URL = "https://www.rochford.gov.uk/bins-and-collections"
FORM_ID = "waste_collection_block_ajax_form"

TEST_CASES = {
    "Station View, Rochford": {"postcode": "SS4 1AS", "uprn": "E05010853-10014203194"},
    "Windermere Ave, Hullbridge": {
        "postcode": "SS5 6JT",
        "uprn": "E05010850-100090575867",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Go to https://www.rochford.gov.uk/bins-and-collections and enter your "
        "postcode, then press 'Find'. Open the address dropdown that appears and "
        "select your address. The 'uprn' is the value of the selected option in "
        "that dropdown: a composite of the ward code and UPRN separated by a "
        "hyphen, e.g. 'E05010853-10014203194'. You can read it from the page's "
        "HTML source (the <option value> attribute)."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "uprn": "UPRN",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "The postcode of the property.",
        "uprn": (
            "The composite ward code and UPRN of the property "
            "(e.g. 'E05010853-10014203194')."
        ),
    },
}

ICON_MAP = {
    "Compost": Icons.GARDEN,
    "Recyclables": Icons.RECYCLING,
    "Non-recyclables": Icons.GENERAL_WASTE,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": API_URL,
}

AJAX_URL = f"{API_URL}?_wrapper_format=drupal_ajax&ajax_form=1"


class Source:
    def __init__(self, postcode: str, uprn: str):
        self._postcode = postcode.upper()
        self._uprn = uprn

    @staticmethod
    def _get_form_build_id(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        inp = soup.find("input", {"name": "form_build_id"})
        return inp.get("value")

    @staticmethod
    def _get_insert_html(commands: list) -> str:
        for command in commands:
            if command.get("command") == "insert":
                return command.get("data", "")
        return ""

    def fetch(self) -> List[Collection]:
        s = requests.Session()

        # Step 0 - load page and scrape the initial form_build_id
        r = s.get(API_URL, headers=HEADERS)
        r.raise_for_status()
        form_build_id = self._get_form_build_id(r.text)

        # Step 1 - submit postcode to obtain the address dropdown
        payload = {
            "postcode": self._postcode,
            "op": "Find",
            "form_build_id": form_build_id,
            "form_id": FORM_ID,
            "_triggering_element_name": "op",
            "_triggering_element_value": "Find",
            "_drupal_ajax": "1",
        }
        r = s.post(AJAX_URL, headers=HEADERS, data=payload)
        r.raise_for_status()
        insert_html = self._get_insert_html(r.json())
        soup = BeautifulSoup(insert_html, "html.parser")

        select = soup.find("select", {"name": "uprn"})
        options = []
        if select is not None:
            for option in select.find_all("option"):
                value = option.get("value")
                if value:  # skip the empty "- Select -" option
                    options.append(value)

        if not options:
            raise SourceArgumentNotFoundWithSuggestions("postcode", self._postcode, [])

        if self._uprn not in options:
            raise SourceArgumentNotFoundWithSuggestions("uprn", self._uprn, options)

        # form_build_id rotates - re-scrape it from the step 1 response
        rotated_build_id = self._get_form_build_id(insert_html)

        # Step 2 - submit the chosen uprn to get the collection days
        payload = {
            "postcode": self._postcode,
            "uprn": self._uprn,
            "op": "View collection days",
            "form_build_id": rotated_build_id,
            "form_id": FORM_ID,
            "_triggering_element_name": "op",
            "_triggering_element_value": "View collection days",
            "_drupal_ajax": "1",
        }
        r = s.post(AJAX_URL, headers=HEADERS, data=payload)
        r.raise_for_status()
        insert_html = self._get_insert_html(r.json())
        soup = BeautifulSoup(insert_html, "html.parser")

        entries: List[Collection] = []
        for row in soup.find_all("tr", {"class": "waste-collection__day"}):
            time_tag = row.find("time")
            type_cell = row.find("td", {"class": "waste-collection__day--type"})
            if time_tag is None or type_cell is None:
                continue
            date_str = time_tag.get("datetime")
            waste_type = type_cell.get_text(strip=True)
            entries.append(
                Collection(
                    date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
