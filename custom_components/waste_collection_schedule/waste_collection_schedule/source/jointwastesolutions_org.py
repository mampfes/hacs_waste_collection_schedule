# Credit where it's due:
# This is predominantly a refactoring of the Woking Borough Council script from the UKBinCollectionData repo
# https://github.com/robbrad/UKBinCollectionData

import re
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "Joint Waste Solutions"
URL = "https://www.jointwastesolutions.org/"
COUNTRY = "uk"
EXTRA_INFO = [
    {
        "title": "Woking Borough Council",
        "url": "https://www.woking.gov.uk",
        "country": "uk",
    },
]
DESCRIPTION = "Manages Waste and Recycling services for Elmbridge, Mole Valley, Surrey Heath & Woking"
TEST_CASES = {
    "Test Woking #1": {
        "house": "4",
        "postcode": "GU21 4PQ",
        "street": "",
    },
    # "Test Woking #2": {
    #     "postcode": "SO20 6EJ",
    #     "uprn": "100060583697", abbey road
    #     "council": "TEST_VALLEY",
    # },
    # "Test Woking #3": {
    #     "postcode": "SO51 5BE",
    #     "uprn": 100060571645,
    #     "council": "TEST_VALLEY",
    # },
    # "Test Woking #4": {
    #     "postcode": "SO51 5BE",
    #     "uprn": 100060571645,
    #     "council": "TEST_VALLEY",
    # },
}
ICON_MAP = {
    "RUBBISH": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
    "BATTERIES-SMALL ELECTRICALS-TEXTILES": "mdi:battery",
    "FOOD WASTE": "mdi:food",
}
REGEX = r"(\d+\/\d+\/\d+\/[\d\w]+)"


class Source:
    def __init__(self, house, postcode, street = ""):
        self._house = str(house.upper().strip())
        self._street = street.upper().replace(" ", "+").strip()
        self._postcode = postcode.upper().replace(" ", "+").strip()


    def fetch(self):
        s = requests.Session()

        # Load landing page and extract tracking ID needed for subsequent requests
        r0 = s.get(
            "https://asjwsw-wrpwokingmunicipal-live.whitespacews.com/#!",
            )
        trackingID = re.findall(REGEX,r0.text)[0]

        # Load search form
        r1 = s.get(
            f"https://asjwsw-wrpwokingmunicipal-live.whitespacews.com/?Track={trackingID}&serviceID=A&seq=1#!",
        )
        print(trackingID)
        # These headers seem to be required for subsequent queries
        headers= {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://asjwsw-wrpwokingmunicipal-live.whitespacews.com',
            'Pragma': 'no-cache',
            'Referer': 'https://asjwsw-wrpwokingmunicipal-live.whitespacews.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 OPR/98.0.0.0',
            'sec-ch-ua': '"Chromium";v="112", "Not_A Brand";v="24", "Opera GX";v="98"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        # Supply search parameters
        payload = {
            "address_name_number": self._house,
            "address_street": self._street,
            "street_town": "",
            "address_postcode": self._postcode
        }
        print(payload)
        # Post address search
        r2 = s.post(
            f"https://asjwsw-wrpwokingmunicipal-live.whitespacews.com/mop.php?serviceID=A&Track={trackingID}&seq=2",
            headers=headers,
            params=payload,
            )
        # Now retrieve schedule
        r3 = s.get(
            f"https://asjwsw-wrpwokingmunicipal-live.whitespacews.com/mop.php?Track={trackingID}&serviceID=A&seq=3&pIndex=1",
            headers=headers,
            )

        # Extract dates and waste types
        soup = BeautifulSoup(r3.text, "html.parser")
        schedule = soup.findAll("p", {"class": "colorblack fontfamilyTahoma fontsize12rem"})

        waste_types = schedule[1::2]
        waste_dates = schedule[::2]


        entries = []
        for  i in range(0, len(waste_dates)):
            entries.append(
                Collection(
                    date=datetime.strptime(waste_dates[i].text, "%d/%m/%Y").date(),
                    t=waste_types[i].text,
                    icon=ICON_MAP.get(waste_types[i].text.upper()),
                )
            )


        return entries
