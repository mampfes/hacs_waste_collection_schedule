import re
from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Maitland City Council"
DESCRIPTION = "Source for Maitland City Council (NSW) waste collection."
URL = "https://www.maitland.nsw.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "1 High Street, Maitland": {"address": "1 High Street, Maitland"},
    "2 Acer Terrace, Thornton": {"address": "2 Acer Terrace, Thornton"},
    "1 Adele Crescent, Ashtonfield": {"address": "1 Adele Crescent, Ashtonfield"},
    "14 Mistfly Street Chisholm NSW 2322": {
        "address": "14 Mistfly Street Chisholm NSW 2322"
    },
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address within the Maitland City Council area",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit the Maitland City Council bin collection page, search for your address, and use the street address as shown.",
}

MAITLAND_API_BASE = "https://integration.maitland.nsw.gov.au/api"
HRR_SEARCH_URL = "https://www5.wastedge.com/publicaddresssearch_549/_search"
HRR_COLLECTION_URL = (
    "https://www5.wastedge.com/web/wsrms/we_resportal/HRRCollectionval.p"
)
HRR_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Basic YWRkcmVzc3NlYXJjaDphZGRyZXNzc2VhcmNo",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://hrr.com.au",
    "Referer": "https://hrr.com.au/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

DATE_FORMAT = "%A, %d %B %Y"


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        # Step 1: Search Maitland API for the property
        maitland_properties = self._search_maitland(self._address)
        if not maitland_properties:
            raise SourceArgumentNotFound("address", self._address)

        # Step 2: Select the best property (first result is usually best)
        property_data = maitland_properties[0]
        property_id = property_data.get("property_id")
        if not property_id:
            raise SourceArgumentNotFound(
                "address",
                self._address,
            )
        full_address = property_data.get("full_address", self._address)

        # Step 3: Get collection day from Maitland API
        collection_info = self._get_bin_collection(property_id)
        next_collection_str = collection_info.get("nextCollection", "")
        next_collection_date = datetime.strptime(
            next_collection_str, DATE_FORMAT
        ).date()

        # Step 4: Search HRR API for recycling schedule
        hrr_cust_number = self._search_hrr(full_address)
        if hrr_cust_number is None:
            raise SourceArgumentNotFound(
                "address",
                self._address,
            )

        # Step 5: Get next recycling date from HRR
        hrr_date = self._get_hrr_collection_date(hrr_cust_number)

        # Step 6: Generate entries
        entries: list[Collection] = []

        # Red bin (General Waste) - weekly
        entries.extend(self._generate_weekly(next_collection_date, "General Waste"))

        # Green bin (Organics) - weekly
        entries.extend(self._generate_weekly(next_collection_date, "Green Waste"))

        # Yellow bin (Recycling) - fortnightly from HRR anchor date
        entries.extend(self._generate_fortnightly(hrr_date, "Recycling"))

        return entries

    @staticmethod
    def _search_maitland(address: str) -> list[dict]:
        url = f"{MAITLAND_API_BASE}/wastetrack/search-bin"
        # The API rejects queries that include the state "NSW" (case-insensitive).
        # Strip it out so "14 Mistfly Street Chisholm NSW 2322"
        # becomes "14 Mistfly Street Chisholm 2322".
        cleaned = re.sub(r"\s+NSW", "", address, flags=re.IGNORECASE).strip()
        params = {"addressText": cleaned}
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []

    @staticmethod
    def _get_bin_collection(property_id: str) -> dict:
        url = f"{MAITLAND_API_BASE}/wastetrack/bin-collection"
        params = {"propertyId": property_id}
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _search_hrr(full_address: str) -> str | None:
        # HRR expects the address without the trailing 4-digit postcode.
        # Only strip the last token if it looks like a postcode.
        parts = full_address.rsplit(" ", 1)
        if len(parts) == 2 and re.fullmatch(r"\d{4}", parts[1]):
            query = parts[0].lower()
        else:
            query = full_address.lower()
        post_data = {
            "query": {
                "bool": {
                    "should": {"match_phrase_prefix": {"address": query}},
                    "must_not": {"match_phrase": {"st": "T"}},
                }
            }
        }
        response = requests.post(
            HRR_SEARCH_URL, json=post_data, headers=HRR_HEADERS, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            return None
        return str(hits[0]["_source"]["cust_number"])

    @staticmethod
    def _get_hrr_collection_date(cust_number: str) -> date:
        params = {
            "ID": "e347cd965f6a92ef2ccd61ded7c597b9",
            "custNo": cust_number,
        }
        response = requests.get(
            HRR_COLLECTION_URL, params=params, headers=HRR_HEADERS, timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if data.get("message") == "WARNING":
            raise SourceArgumentNotFound(
                "address",
                f"HRR returned no collection data for customer {cust_number}",
            )
        if data.get("message") == "ERROR":
            raise RuntimeError(f"HRR API returned an error for customer {cust_number}")

        records = data.get("records", [])
        if not records:
            raise SourceArgumentNotFound(
                "address",
                f"HRR returned no collection records for customer {cust_number}",
            )

        service_date = records[0].get("ServiceDate", "")
        return date.fromisoformat(service_date)

    @staticmethod
    def _generate_weekly(start_date: date, waste_type: str) -> list[Collection]:
        icon = ICON_MAP.get(waste_type)
        return [
            Collection(
                date=start_date + timedelta(weeks=i),
                t=waste_type,
                icon=icon,
            )
            for i in range(26)
        ]

    @staticmethod
    def _generate_fortnightly(start_date: date, waste_type: str) -> list[Collection]:
        icon = ICON_MAP.get(waste_type)
        today = date.today()
        # Ensure start_date is not in the past
        while start_date < today:
            start_date += timedelta(days=14)
        return [
            Collection(
                date=start_date + timedelta(days=i * 14),
                t=waste_type,
                icon=icon,
            )
            for i in range(13)
        ]
