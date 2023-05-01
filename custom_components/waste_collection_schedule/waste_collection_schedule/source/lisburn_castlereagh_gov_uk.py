import requests
import bs4
import difflib

from datetime import datetime

from waste_collection_schedule import Collection

# Title will show up in README.md and info.md
TITLE = "Lisburn and Castlereagh City Council"
# Describe your source
DESCRIPTION = "Source for the Lisburn and Castlereagh City Council"
# Insert url to service homepage. URL will show up in README.md and info.md
URL = "https://lisburncastlereagh.gov.uk/"
TEST_CASES = {
    "Test_001": {"postcode": "BT28 1AG", "house_number": "19A"},
    "Test_002": {"postcode": "BT26 6AB", "house_number": "31"},
    "Test_003": {"postcode": "BT26 6AB", "house_number": 15},
    "Test_004": {"property_id": "DYYSm8Ls8XxGi3Nq"},
    "Test_005": {"property_id": "ZJat6DWG1Lp95xp1"},
}

API_URL = "https://lisburn.isl-fusion.com"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "ResidualBin": "mdi:trash-can",
    "RecycleBin": "mdi:recycle",
    "BrownBin": "mdi:leaf",
}
NICE_NAMES = {
    "ResidualBin": "Refuse",
    "RecycleBin": "Recycling",
    "BrownBin": "Garden",
}


class Source:
    # argX correspond to the args dict in the source configuration
    def __init__(self, property_id=None, postcode=None, house_number=None):
        self._property_id = property_id
        self._postcode = postcode
        self._house_number = house_number

        if not any([self._property_id, self._postcode and self._house_number]):
            raise ValueError("Must provide either a property ID or both the Postcode and House Number")

    def fetch(self):
        session = requests.Session()

        if not self._property_id:
            search_url = f"{API_URL}/address/{self._postcode}"
            response = session.get(search_url)
            response.raise_for_status()
            try:
                address_list = response.json().get("html")
            except:
                raise ValueError(f"No data found for {self._postcode}")

            soup = bs4.BeautifulSoup(address_list, features="html.parser")

            address_by_id = {}
            for li in soup.findAll("li"):
                link = li.findAll("a")[0]
                property_id = link.attrs["href"].replace("/view", "").replace("/", "")
                address = link.text
                address_by_id[property_id] = address

            all_addresses = list(address_by_id.values())

            common = difflib.SequenceMatcher(a=all_addresses[0], b=all_addresses[1]).find_longest_match()
            to_be_removed = all_addresses[0][common.a:common.a+common.size]

            ids_by_house_number = {
                address.replace(to_be_removed, ""): property_id for property_id, address in address_by_id.items()
            }

            self._property_id = ids_by_house_number.get(str(self._house_number))

            if not self._property_id:
                raise ValueError(f"Property not found for house number {self._house_number}")

        today = datetime.today().date()
        calendar_url = f"{API_URL}/calendar/{self._property_id}/{today.strftime('%Y-%m-%d')}"
        response = session.get(calendar_url)
        response.raise_for_status()

        try:
            next_collections = response.json().get("nextCollections")
        except:
            raise ValueError("No collection data in response")

        entries = []  # List that holds collection schedule

        for collection in next_collections["collections"].values():
            collection_date = datetime.strptime(collection["date"], "%Y-%m-%d").date()

            for bin in collection["collections"].values():
                entries.append(
                    Collection(
                        date=collection_date,
                        t=NICE_NAMES.get(bin["name"]),
                        icon=ICON_MAP.get(bin["name"])
                    )
                )

        return entries
