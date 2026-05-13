import datetime
import json
from urllib.parse import quote

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Campbelltown City Council (NSW)"
DESCRIPTION = "Source for Campbelltown City Council rubbish collection."
URL = "https://www.campbelltown.nsw.gov.au/"
TEST_CASES = {
    "Minto Mall": {
        "post_code": "2566",
        "suburb": "Minto",
        "street_name": "Brookfield Road",
        "street_number": "10",
    },
    "Campbelltown Catholic Club": {
        "post_code": "2560",
        "suburb": "Campbelltown",
        "street_name": "Camden Road",
        "street_number": "20-22",
    },
    "Australia Post Ingleburn": {
        "post_code": "2565",
        "suburb": "INGLEBURN",
        "street_name": "Oxford Road",
        "street_number": "34",
    },
}

API_URLS = {
    "address_search": "https://www.campbelltown.nsw.gov.au/api/v1/myarea/search?keywords={}",
    "collection": "https://www.campbelltown.nsw.gov.au/ocapi/Public/myarea/wasteservices?geolocationid={}&ocsvclang=en-AU",
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
}


class Source:
    def __init__(
        self, post_code: str, suburb: str, street_name: str, street_number: str
    ):
        self.post_code = post_code
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number

    def fetch(self):
        locationId = ""

        address = "{} {} {} NSW {}".format(
            self.street_number, self.street_name, self.suburb, self.post_code
        )

        session = requests.Session(impersonate="chrome")

        q = str(API_URLS["address_search"]).format(quote(address))
        r = session.get(q)
        r.raise_for_status()

        data = None
        try:
            data = json.loads(r.text)
        except Exception:
            soup = BeautifulSoup(r.text, "xml")
            address_results = soup.find_all("PhysicalAddressSearchResult")
            for result in address_results:
                id_element = result.find("Id")
                if id_element:
                    locationId = id_element.text.strip()
                    break
        else:
            for item in data.get("Items", []):
                locationId = item.get("Id", "")
                break

        if not locationId:
            return []

        q = str(API_URLS["collection"]).format(locationId)
        r = session.get(q)
        r.raise_for_status()

        try:
            data = json.loads(r.text)
        except Exception:
            return []

        responseContent = data.get("responseContent", "")
        if not responseContent:
            return []

        soup = BeautifulSoup(responseContent, "html.parser")
        services = soup.find_all("div", attrs={"class": "waste-services-result"})

        entries = []

        for item in services:
            date_text = item.find("div", attrs={"class": "next-service"})
            waste_type = item.find("h3")
            if not date_text or not waste_type:
                continue
            date_format = "%a %d/%m/%Y"
            try:
                cleaned_date_text = (
                    date_text.text.replace("\r", "").replace("\n", "").strip()
                )
                date = datetime.datetime.strptime(cleaned_date_text, date_format).date()
                waste_type_text = waste_type.text.strip()
                entries.append(
                    Collection(
                        date=date,
                        t=waste_type_text,
                        icon=ICON_MAP.get(waste_type_text, "mdi:trash-can"),
                    )
                )
            except Exception:
                continue

        return entries
