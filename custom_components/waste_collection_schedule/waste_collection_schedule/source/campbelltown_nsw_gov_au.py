import datetime
import json

import requests
from bs4 import BeautifulSoup
from requests.utils import requote_uri
from waste_collection_schedule import Collection

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

ICON_MAP = {
    "General Waste": "trash-can",
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

        q = requote_uri(str(API_URLS["address_search"]).format(address))
        r = requests.get(q, headers=HEADERS)
        r.raise_for_status()

        # Try JSON first, fallback to XML if needed
        data = None
        try:
            data = json.loads(r.text)
        except Exception:
            # Try XML
            soup = BeautifulSoup(r.text, 'xml')
            address_results = soup.find_all('PhysicalAddressSearchResult')
            for result in address_results:
                id_element = result.find('Id')
                if id_element:
                    locationId = id_element.text.strip()
                    break
        else:
            # JSON path
            for item in data.get("Items", []):
                locationId = item.get("Id", "")
                break

        if not locationId:
            return []

        # Retrieve the upcoming collections for our property
        q = requote_uri(str(API_URLS["collection"]).format(locationId))
        r = requests.get(q, headers=HEADERS)
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
            date_format = '%a %d/%m/%Y'
            try:
                cleaned_date_text = date_text.text.replace('\r','').replace('\n','').strip()
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
