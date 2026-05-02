import logging
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Bolton Council"
DESCRIPTION = "Source for Bolton Council, UK."
URL = "https://www.bolton.gov.uk"

AUTH_KEY = "Authorization"

API_NAME = "es_bin_collection_dates"
API_BASE = "https://bolton.form.uk.empro.verintcloudservices.com/"
API_URLS = {
    "authentication": "api/citizen?archived=Y&preview=false&locale=en",
    "postcode_lookup": "api/widget?action=propertysearch&actionedby=ps_address&loadform=true&access=citizen&locale=en",
    "set_object": "api/setobjectid?objecttype=property&objectid={uprn}&loaddata=true",
    "collection_dates": "api/custom?action=es_get_bin_collection_dates&actionedby=uprn_changed&loadform=true&access=citizen&locale=en",
}

ICON_MAP = {
    "Grey Bin": "mdi:trash-can",
    "Beige Bin": "mdi:newspaper-variant",
    "Burgundy Bin": "mdi:bottle-soda",
    "Green Bin": "mdi:leaf",
    "Food container": "mdi:food",
}

TEST_CASES = {
    "Test_Postcode_Without_Space": {
        "postcode": "BL52AX",
        "house_number": "13",
    },
    "Test_Postcode_With_Space": {
        "postcode": "BL1 5BQ",
        "house_number": "14",
    },
    "Test_House_With_Street_Before_Number": {
        "postcode": "BL1 5XR",
        "house_number": "WOODSLEIGH COPPICE 2",
    },
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, postcode: str, house_number: str):
        self._postcode = postcode
        self._house_number = str(house_number)

    @staticmethod
    def _get_headers(auth_token: str) -> dict:
        return {
            "referer": API_BASE,
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0",
            AUTH_KEY: auth_token,
        }

    @staticmethod
    def _create_payload(data: dict) -> dict:
        return {
            "name": API_NAME,
            "email": "",
            "caseid": "",
            "xref": "",
            "xref1": "",
            "xref2": "",
            "data": data,
        }

    @staticmethod
    def _parse_html(html_content: str) -> list[Collection]:
        entries = []
        soup = BeautifulSoup(html_content, "html.parser")

        bin_sections = soup.find_all(
            "div", style=lambda value: value and "overflow:auto" in value
        )

        for section in bin_sections:
            bin_type = (
                section.find("strong").get_text(strip=True).replace(":", "").strip()
            )
            if "caddy" in bin_type.lower():
                bin_type = "Food container"
            else:
                for colour in ["Grey", "Beige", "Burgundy", "Green", "Garden"]:
                    if colour.lower() in bin_type.lower():
                        bin_type = f"{colour} Bin"
                        break

            dates = section.find_all("li")

            for date_item in dates:
                try:
                    date_text = date_item.get_text(strip=True)
                    date_obj = datetime.strptime(date_text, "%A %d %B %Y").date()

                    entries.append(
                        Collection(
                            date=date_obj,
                            t=bin_type,
                            icon=ICON_MAP.get(bin_type),
                        )
                    )
                except ValueError as e:
                    _LOGGER.warning(f"Failed to parse date: {date_text}, error: {e}")
                    continue
        return entries

    def _find_uprn(self, auth_token: str) -> tuple[str, str]:
        data = {"postcode": self._postcode}
        addresses_response = self._session.post(
            url=API_BASE + API_URLS["postcode_lookup"],
            headers=self._get_headers(auth_token),
            json=self._create_payload(data),
        )
        addresses_response.raise_for_status()
        data = addresses_response.json()

        if not data["data"]:
            raise SourceArgumentNotFound("postcode", self._postcode)

        if AUTH_KEY in addresses_response.headers:
            auth_token = addresses_response.headers[AUTH_KEY]

        for address in data["data"]:
            label = address["label"]
            if (
                label == self._house_number
                or label.startswith(f"{self._house_number} ")
                or label.startswith(f"{self._house_number},")
            ):
                return address["value"], auth_token

        raise SourceArgumentNotFoundWithSuggestions(
            "house_number",
            self._house_number,
            [address["label"] for address in data["data"]],
        )

    def fetch(self):
        self._session = requests.session()

        token_response = self._session.get(API_BASE + API_URLS["authentication"])
        token_response.raise_for_status()
        auth_token = token_response.headers[AUTH_KEY]

        uprn, auth_token = self._find_uprn(auth_token=auth_token)

        set_object_url = (API_BASE + API_URLS["set_object"]).format(uprn=uprn)
        set_object_response = self._session.post(
            set_object_url, headers=self._get_headers(auth_token)
        )
        set_object_response.raise_for_status()

        set_object_data = set_object_response.json()
        canonical_uprn = set_object_data["profileData"]["property-UPRN"]

        if AUTH_KEY in set_object_response.headers:
            auth_token = set_object_response.headers[AUTH_KEY]

        post_data = self._create_payload(
            {
                "uprn": canonical_uprn,
                "start_date": (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y"),
                "end_date": (datetime.now() + timedelta(days=365)).strftime("%d/%m/%Y"),
            }
        )

        schedule = self._session.post(
            API_BASE + API_URLS["collection_dates"],
            json=post_data,
            headers=self._get_headers(auth_token=auth_token),
        )
        schedule.raise_for_status()

        result = schedule.json()

        return self._parse_html(result["data"]["collection_dates"])
