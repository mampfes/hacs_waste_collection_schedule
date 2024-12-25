from datetime import datetime
import logging
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.SSLError import get_legacy_session
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentRequired,
)

PARAM_TRANSLATIONS = {
    "en": {
        "apn": "APN"
    }
}

TITLE = "Minneapolis MN USA" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for apps_ci_minneapolis_mn_us"  # Describe your source
URL = "https://www.minneapolismn.gov"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script

    "TestName1": {"apn": 2602924220080}, # GOvernment Center
    "TestName2": {"apn": 2302924330044}, # City Hall
    "TestName3": {"apn": 2402924310071} # Library

}


#1402824330026

# https://apps.ci.minneapolis.mn.us/RecyclingFinderApp/RecyclingRpt.aspx?AppID=RecycleFinderApp&apn=0902824440154
API_URL = "https://apps.ci.minneapolis.mn.us/RecyclingFinderApp/RecyclingRpt.aspx"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "DOMESTIC": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "ORGANIC": "mdi:leaf"
}


#### End of arguments affecting the configuration GUI ####

class Source:
    def __init__(self,apn):
        """Initialize the Minneapolis City waste collection source.

        Args:
            apn: Area Parcel Number in Minneapolis

        Raises:
            SourceArgumentRequired: If apn is not provided
        """
        if not apn:
            raise SourceArgumentRequired(
                "street_address",
                "A Area Parcel Number in Minneapolis is required to look up collection schedule",
            )
        self._area_number = apn

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


        # Updated request using SSL code snippet
    def fetch(self):

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": "https://www.minneapolismn.gov/solid-waste/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "sec-ch-ua-platform": "macOS",        
            }

        

        response = get_legacy_session().get(
            f"https://apps.ci.minneapolis.mn.us/RecyclingFinderApp/RecyclingRpt.aspx?AppID=RecycleFinderApp&apn={self._area_number}",
            headers=headers
        )
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        # 1. Find the next garbage collection date
        garbage_collection_text = soup.find('strong', text='Next Garbage Collection:').find_next('a').text.strip()
        logging.info("garbage_collection_text: %s", garbage_collection_text)
        garbage_collection_date_str = ' '.join(garbage_collection_text.split()[1:])  # Remove first word (day of the week)
        logging.info("garbage_collection_date_str: %s", garbage_collection_date_str)
        garbage_collection_date = datetime.strptime(garbage_collection_date_str, '%b. %d, %Y')
        logging.info("garbage_collection_date: %s", garbage_collection_date)

        

        # 2. Find the next recycling collection date
        recycling_collection_text = soup.find('strong', text='Next Recycling Collection:').find_next('a').text.strip()
        logging.info("recycling_collection_text: %s", recycling_collection_text)
        grecycling_collection_date_str = ' '.join(recycling_collection_text.split()[1:])  # Remove first word (day of the week)
        logging.info("recycling_collection_date_str: %s", grecycling_collection_date_str)
        recycling_collection_date = datetime.strptime(grecycling_collection_date_str, '%b. %d, %Y')
        logging.info("recycling_collection_date: %s", recycling_collection_date)



        # if ERROR_CONDITION:
        #     raise Exception("YOUR ERROR MESSAGE HERE") # DO NOT JUST return []

        entries = []  # List that holds collection schedule

        entries.append(
            Collection(
                date = garbage_collection_date.date(),
                t = "Garbage",  # Collection type
                icon = "mdi:trash-can"  # Collection icon
            )
        )

        entries.append(
            Collection(
                date = recycling_collection_date.date(),
                t = "Recycling",  # Collection type
                icon = "mdi:leaf"  # Collection icon
            )
        )


        return entries