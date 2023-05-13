import datetime
import json
import requests

from bs4 import BeautifulSoup
from requests.utils import requote_uri
from waste_collection_schedule import Collection

TITLE = "City of Kingston"
DESCRIPTION = "Source for City of Kingston (VIC) waste collection."
URL = "https://www.kingston.vic.gov.au"
TEST_CASES = {
    "randomHouse": {
        "post_code": "3169",
        "suburb": "CLAYTON SOUTH",
        "street_name": "Oakes Avenue",
        "street_number": "30C",
    },
    "randomAppartment": {
        "post_code": "3197",
        "suburb": "CARRUM",
        "street_name": "Whatley Street",
        "street_number": "1/51",
    },
    "randomMultiunit": {
        "post_code": "3189",
        "suburb": "MOORABBIN",
        "street_name": "Station Street",
        "street_number": "1/1-5",
    },
    "stringCheck": {
        "post_code": 3195,
        "suburb": "mordialloc",
        "street_name": "albert street",
        "street_number": 117,
    },
}
API_URLS = {
    "session":"https://www.kingston.vic.gov.au",
    "search": "https://www.kingston.vic.gov.au/api/v1/myarea/search?keywords={}",
    "schedule": "https://www.kingston.vic.gov.au/ocapi/Public/myarea/wasteservices?geolocationid={}&ocsvclang=en-AU",
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "General waste (landfill)": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food and garden waste": "mdi:leaf",
}

# _LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self, post_code: str, suburb: str, street_name: str, street_number: str
    ):
        self.post_code = str(post_code).upper()
        self.suburb = suburb.upper()
        self.street_name = street_name.upper()
        self.street_number = str(street_number).upper()

    def fetch(self):

        # 'collection' api call seems to require an ASP.Net_sessionID, so obtain the relevant cookie
        s = requests.Session()
        q = requote_uri(str(API_URLS["session"]))
        r0 = s.get(q, headers = HEADERS)

        # Do initial address search
        address = "{} {} {} {}".format(self.street_number, self.street_name, self.suburb, self.post_code)
        q = requote_uri(str(API_URLS["search"]).format(address))
        r1 = s.get(q, headers = HEADERS)
        data = json.loads(r1.text)["Items"]

        # Find the geolocation for the address
        locationId = ""
        for item in data:
            if address in item['AddressSingleLine']:
                locationId = item["Id"]

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
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
