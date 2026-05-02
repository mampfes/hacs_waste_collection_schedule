import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Warrnambool City Council"
DESCRIPTION = "Source for Warrnambool City Council waste collection."
URL = "https://www.warrnambool.vic.gov.au"
TEST_CASES = {
    "Kiama Ave": {"street_address": "3 Kiama Ave WARRNAMBOOL VIC 3280"},
    "Henna St": {"street_address": "13 Henna St WARRNAMBOOL VIC 3280"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Full street address including suburb and postcode, e.g. '3 Kiama Ave WARRNAMBOOL VIC 3280'",
    }
}

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://wcdm-public.warrnambool.vic.gov.au"

ICON_MAP = {
    "Landfill": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "FOGO": "mdi:leaf",
    "Glass": "mdi:glass-fragile",
}


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        # Step 1: Search for address to get the zone code
        r = session.get(
            f"{BASE_URL}/wc_te_combine_cust_datalist.php",
            params={
                "cmd": "search",
                "t": "wc_te_combine_cust_data",
                "z_FORMATTED_ADDRESS": "LIKE",
                "x_FORMATTED_ADDRESS": self._street_address,
            },
        )
        r.raise_for_status()

        zone_match = re.search(r"fk_zonecode=([^&\"]+)", r.text)
        if not zone_match:
            raise SourceArgumentNotFound(
                "street_address",
                self._street_address,
                "Check your address at https://www.warrnambool.vic.gov.au/kerbside-bin-collection",
            )

        zone_code = zone_match.group(1)
        _LOGGER.debug("Zone code for %s: %s", self._street_address, zone_code)

        # Step 2: Get collection dates for the zone
        r = session.get(
            f"{BASE_URL}/autodates.php",
            params={
                "showmaster": "wc_te_combine_cust_data",
                "fk_zonecode": zone_code,
            },
        )
        r.raise_for_status()

        # Step 3: Parse HTML for collection dates
        soup = BeautifulSoup(r.text, "html.parser")
        entries: list[Collection] = []

        for ul in soup.find_all("ul"):
            li_items = ul.find_all("li", recursive=False)
            if not li_items:
                continue

            date_text = li_items[0].get_text(strip=True)
            if not date_text:
                continue

            # Parse date like "Wednesday, 15 April, 2026"
            try:
                date = datetime.strptime(date_text, "%A, %d %B, %Y").date()
            except ValueError:
                continue

            # Get waste types from nested <ul>
            sub_ul = ul.find("ul")
            if not sub_ul:
                continue

            types_text = sub_ul.get_text(strip=True)
            if not types_text:
                continue

            # Split comma-separated types (e.g. "Landfill,FOGO")
            for waste_type in types_text.split(","):
                waste_type = waste_type.strip()
                if waste_type:
                    entries.append(
                        Collection(
                            date=date,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                        )
                    )

        return entries
