import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = (
    "Fleurieu Regional Waste Authority"  # Title will show up in README.md and info.md
)
DESCRIPTION = (
    "Source script for fleurieuregionalwasteauthority.com.au"  # Describe your source
)
URL = "https://fleurieuregionalwasteauthority.com.au"  # Insert url to service homepage. URL will show up in README.md and info.md

TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Victor Harbor": {
        "name_or_number": "42",
        "street": "WISHART CRESCENT",
        "district": "ENCOUNTER BAY",
    },
    "Yankalilla": {
        "name_or_number": "12",
        "street": "Wallman Street",
        "district": "Yankalilla",
    },
    "Kangaroo Island": {
        "name_or_number": "3",
        "street": "Flinders Grove",
        "district": "Island Beach",
    },
    "Alexandrina": {
        "name_or_number": "10",
        "street": "Jacobs Street",
        "district": "Goolwa South",
    },
}

API_URLS = {
    "HOME": "https://fleurieuregionalwasteauthority.com.au/collection-calendar-downloads",
    "SEARCH": "https://fleurieuregionalwasteauthority.com.au/wp-admin/admin-ajax.php",
}
ICON_MAP = {
    "Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
}
HEADERS = {"user-agent": "Mozilla/5.0"}
EXTRA_INFO = [
    {"title": "Kangaroo Island Council", "url": "https://www.kangarooisland.sa.gov.au"},
    {
        "title": "District Council of Yankalilla",
        "url": "https://www.yankalilla.sa.gov.au",
    },
    {"title": "City of Victor Harbor", "url": "https://www.victor.sa.gov.au"},
    {"title": "Alexandrina Council", "url": "https://www.alexandrina.sa.gov.au"},
]
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Visit https://fleurieuregionalwasteauthority.com.au/collection-calendar-downloads and search for your street. Use the name/number, street name and district name as they appear when your collection schedule in being displayed.",
}
PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "name_or_number": "The number or name of the property, as displayed on the FRWA web site.",
        "street": "The street name of the property, as displayed on the FRWA web site.",
        "district": "The district name of the property, as displayed on the FRWA web site.",
    },
}
PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "name_or_number": "The number or name of the property, as displayed on the FRWA web site.",
        "street": "The street name of the property, as displayed on the FRWA web site.",
        "district": "The district name of the property, as displayed on the FRWA web site.",
    },
}


class Source:
    def __init__(
        self, name_or_number=int | str, street=str, district=str
    ):  # argX correspond to the args dict in the source configuration
        self._name_or_number = str(name_or_number).upper()
        self._street = street.upper()
        self._district = district.upper()
        self._id: str = None

    def fetch(self):

        s = requests.Session()

        # get security token
        r = s.get(API_URLS["HOME"], headers=HEADERS)
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
        script_text = soup.find("script", {"id": "autocomplete-search-js-extra"}).string
        json_text = script_text.split("=", 1)[1].rsplit(";", 1)[0].strip()
        data = json.loads(json_text)
        token = data["ajax_nonce"]

        # get unique ID from street search
        params = {
            "term": f"{self._name_or_number} {self._street}",
            "action": "autocomplete_search",
            "security": token,
        }
        street_json = s.get(API_URLS["SEARCH"], params=params, headers=HEADERS).json()
        for item in street_json:
            if (
                self._name_or_number == item["street_no"]
                and self._street in item["label"]
                and self._district in item["label"]
            ):
                self._id = item["id"]
        if self._id is None:
            raise Exception(
                f"Unable to find an street match for {self._name_or_number} {self._street} in {self._district}"
            )

        # retrieve schedule
        params = {
            "id": self._id,
            "action": "fetch_bin_collection",
        }
        r = s.post(API_URLS["SEARCH"], params=params, headers=HEADERS)
        soup = BeautifulSoup(r.content, "html.parser")

        # extract collections
        entries = []
        for block in soup.select("div.coll-main-wrap"):
            waste_type = block.find("h6").get_text(strip=True).split(" Collection")[0]
            next_date = None
            for row in block.select("table tr"):
                label = row.find_all("td")[0].get_text(strip=True)
                if label == "Next Collection Date:":
                    next_date = row.find_all("td")[1].get_text(strip=True)
            entries.append(
                Collection(
                    date=datetime.strptime(next_date, "%d %B %Y").date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
