import logging
import requests

from bs4 import BeautifulSoup
from dateutil.parser import parse
from waste_collection_schedule import Collection

TITLE = "Environment First"
URL = "https://environmentfirst.co.uk"
EXTRA_INFO = [
    {
       "title": "Eastbourne Borough Council",
       "url": "https://lewes-eastbourne.gov.uk"
    },
    {
       "title": "Lewes District Council",
       "url": "https://lewes-eastbourne.gov.uk"
    },
]
DESCRIPTION = (
    """Consolidated source for waste collection services from:
        Eastbourne Borough Council 
        Lewes District Council
        """
)
TEST_CASES = {
    "houseUPRN" : {"uprn": "100060063421"},
    "houseNumber": {"post_code": "BN228SG", "number": 3},
    "houseName": {"post_code": "BN73LG", "number": "Garden Cottage"},
}

ICON_MAP = {
    "RUBBISH": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN WASTE": "mdi:leaf",
}


_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, post_code=None, number=None, name=None, uprn=None):
        self._uprn = uprn
        self._post_code = post_code
        self._number = str(number)
        self._name = name

    def fetch(self):

        s = requests.Session()

        if self._uprn:
            # GET request returns schedule for matching uprn
            r = s.get(f"https://www.environmentfirst.co.uk/house.php?uprn={self._uprn}")
            responseContent = r.text

        elif (self._post_code and self._number):
            # POST request returns schedule for matching address
            payload = {
                "property_no": self._number,
                "property_name": "",
                "street": "",
                "postcode": self._post_code
            }
            r = s.post("https://www.environmentfirst.co.uk/results.php", data = payload)
            responseContent = r.text

        elif (self._post_code and self._name):
            # POST request returns list of postcode addresses
            payload = {
                "property_no": "",
                "property_name": self._name,
                "street": "",
                "postcode": self._post_code
            }
            r = s.post("https://www.environmentfirst.co.uk/results.php", data = payload)
            responseContent = r.text

            # Loop through postcode address list to find house name and uprn
            soup = BeautifulSoup(responseContent, "html.parser")
            table = soup.find('table')
            for row in table.find_all('tr')[1:]:
                if self._name in row.text:
                    for item in row('a', href=True):
                        self._uprn = str.split(item.get('href'), "=")[1]

            # GET request returns schedule for matching uprn
            r = s.get(f"https://www.environmentfirst.co.uk/house.php?uprn={self._uprn}")
            responseContent = r.text

        else:
            raise Exception("Address not found")        

        entries = []

        # Extract waste types and dates from responseContent
        soup = BeautifulSoup(responseContent, "html.parser")
        x = soup.findAll("p")
        for i in x[1:-1]: # ignores elements containing address and marketing message 
            if " day " in i.text:
                for round_type in ICON_MAP:
                    if round_type in i.text.upper():
                        entries.append(
                            Collection(
                                date = parse(str.split(i.text, ":")[1]).date(),
                                t = round_type,
                                icon = ICON_MAP.get(round_type),
                            )
                        )

        return entries
