import datetime
import json
import requests

from bs4 import BeautifulSoup
from requests.utils import requote_uri
from waste_collection_schedule import Collection

TITLE = "Horowhenua District Council"
DESCRIPTION = "Source for Horowhenua District Council Rubbish & Recycling collection."
URL = "https://www.horowhenua.govt.nz/"
TEST_CASES = {
    "House-Shannon": {
        "post_code": "4821",
        "town": "Shannon",
        "street_name": "Bryce Street",
        "street_number": "55",
    },
    "House-Levin": {
        "post_code": "5510",
        "town": "Levin",
        "street_name": "McKenzie Street",
        "street_number": "15",
    },
    "Commercial-Foxton": {
        "post_code": "4814",
        "town": "Foxton",
        "street_name": "State Highway 1",
        "street_number": "18",
    },
}

API_URLS = {
    "session":"https://www.horowhenua.govt.nz" ,
    "search": "https://www.horowhenua.govt.nz/api/v1/myarea/search?keywords={}",
    "schedule": "https://www.horowhenua.govt.nz/ocapi/Public/myarea/wasteservices?geolocationid={}&ocsvclang=en-AU",
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

# _LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self, post_code: str, town: str, street_name: str, street_number: str
    ):
        self.post_code = post_code
        self.town = town.upper()
        self.street_name = street_name
        self.street_number = street_number

    def fetch(self):

        locationId = 0

        # 'collection' api call seems to require an ASP.Net_sessionID, so obtain the relevant cookie
        s = requests.Session()
        q = requote_uri(str(API_URLS["session"]))
        r0 = s.get(q, headers = HEADERS)

        # Do initial address search
        address = "{} {} {} {}".format(self.street_number, self.street_name, self.town, self.post_code)
        q = requote_uri(str(API_URLS["search"]).format(address))
        r1 = s.get(q, headers = HEADERS)
        data = json.loads(r1.text)

        # Find the geolocation for the address
        for item in data["Items"]:
            normalized_input = Source.normalize_address(address)
            normalized_response = Source.normalize_address(item['AddressSingleLine'])
            if normalized_input in normalized_response:
                locationId = item["Id"]
            break

        if locationId == 0:
            return []

        # Retrieve the upcoming collections for location
        q = requote_uri(str(API_URLS["schedule"]).format(locationId))
        r2 = s.get(q, headers = HEADERS)
        data = json.loads(r2.text)
        responseContent = data["responseContent"]

        soup = BeautifulSoup(responseContent, "html.parser")
        services = soup.find_all("article")

        entries = []

        for item in services:
            waste_type = item.find('h3').text
            date = datetime.datetime.strptime(item.find('div', {'class': 'next-service'}).text.strip(), "%a %d/%m/%Y").date()
            entries.append(
                Collection(
                    date = date,
                    t=waste_type,  # api returns Recycling, Rubbish
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries

    @staticmethod
    def normalize_address(address_str):
        # Remove leading/trailing whitespace, capitalize
        address_str = address_str.strip().upper()
        # Replace any multiplewhite space characters with a single space
        address_str = " ".join(address_str.split())

        return address_str

