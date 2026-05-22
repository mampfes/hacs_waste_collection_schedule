import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Cheltenham Borough Council"
DESCRIPTION = "Source for Cheltenham Borough Council waste collection schedule"
URL = "https://www.cheltenham.gov.uk"
COUNTRY = "uk"
TEST_CASES = {
    "282 Hatherley Road GL51 6HR": {"property_id": 56299},
}

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://cheltenham-host01.oncreate.app"
WEBPAGE_TOKEN = "3e546dda8816902a52a5e3f68096b16d45e279f1f634e9433b899675b5349448"
SUBPAGE_ID = "PAG0000686GBCNH1"
CELL_ID = "PCL0005127GBCNH1"
FRAGMENT_ID = "PCF0019732GBCNH1"
WIDGET_GROUP_ID = "PWG0002596GBCNH1"
SUBMIT_FRAGMENT_ID = "PCF0016614GBCNH1"

ICON_MAP = {
    "Refuse": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Food": Icons.BIO_KITCHEN,
    "Garden": Icons.GARDEN,
    "Paper": Icons.PAPER,
    "Card": Icons.PAPER,
}

PARAM_TRANSLATIONS = {
    "en": {
        "property_id": "Property ID",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "property_id": "Internal numeric property identifier from Cheltenham's bin checker (e.g. 56299)",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://cheltenham-host01.oncreate.app/w/webpage/collection-lookup, enter your postcode, select your address, then note the numeric property ID shown in the page.",
}


class Source:
    def __init__(self, property_id: int | str):
        self._property_id = str(property_id)

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

        page_url = f"{BASE_URL}/w/webpage/collection-lookup?webpage_subpage_id={SUBPAGE_ID}&webpage_token={WEBPAGE_TOKEN}"

        # Establish session cookie
        session.get(f"{BASE_URL}/w/webpage/collection-lookup")

        # Step 1: Retrieve form to get CSRF token and collection key
        r1 = session.post(
            page_url,
            data={
                "webpage_cell_id": CELL_ID,
                "webpage_fragment_id": FRAGMENT_ID,
                "webpage_widget_group_id": WIDGET_GROUP_ID,
            },
        )
        r1.raise_for_status()
        data1 = r1.json().get("data", "")

        form_check_match = re.search(r'name="form_check" value="([a-f0-9]+)"', data1)
        if not form_check_match:
            raise Exception("Could not extract CSRF token from form response")
        form_check = form_check_match.group(1)

        collection_key_match = re.search(r'data-unique_key="(C_[a-f0-9]+)"', data1)
        if not collection_key_match:
            raise Exception("Could not extract collection key from form response")
        collection_key = collection_key_match.group(1)

        # Step 2: Submit property_id to get bin schedule
        r2 = session.post(
            page_url,
            data={
                "form_check": form_check,
                "submitted_page_storage_key": "/w/webpage/collection-lookup",
                "submitted_page_id": SUBPAGE_ID,
                "submitted_widget_group_id": WIDGET_GROUP_ID,
                "submitted_widget_group_type": "search",
                f"payload[{SUBPAGE_ID}][{WIDGET_GROUP_ID}][{CELL_ID}][search][{collection_key}][{FRAGMENT_ID}]": self._property_id,
                f"payload[{SUBPAGE_ID}][{WIDGET_GROUP_ID}][{CELL_ID}][search][{collection_key}][{SUBMIT_FRAGMENT_ID}]": "Next",
            },
        )
        r2.raise_for_status()
        data2 = r2.json().get("data", "")

        return self._parse_schedule(data2)

    def _parse_schedule(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.find_all("tr", class_="page_fragment_collection")

        if not rows:
            raise SourceArgumentNotFound(
                "property_id",
                self._property_id,
                "no collection data found — please check your property_id is correct",
            )

        entries = []
        for row in rows:
            current_value = row.get("data-current_value", "")
            if not current_value:
                continue
            # Format: bin_size_detail|bin_type_name|id|last_date_dd/mm/yyyy|next_date_dd/mm/yyyy|schedule
            parts = current_value.split("|")
            if len(parts) < 5:
                continue
            bin_type = parts[1].strip()
            next_date_str = parts[4].strip()
            if not next_date_str or next_date_str == "N/A":
                continue
            try:
                next_date = datetime.strptime(next_date_str, "%d/%m/%Y").date()
            except ValueError:
                LOGGER.warning(
                    "Could not parse date %r for bin type %r", next_date_str, bin_type
                )
                continue

            icon = None
            for keyword, mapped_icon in ICON_MAP.items():
                if keyword.lower() in bin_type.lower():
                    icon = mapped_icon
                    break

            entries.append(Collection(date=next_date, t=bin_type, icon=icon))

        return entries
