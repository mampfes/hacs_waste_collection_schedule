import logging

import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "East Ayrshire Council"
DESCRIPTION = "Source for east-ayrshire.gov.uk services for East Ayrshire"
URL = "https://www.east-ayrshire.gov.uk/"
API_URL = "https://www.east-ayrshire.gov.uk/Housing/RubbishAndRecycling/Collection-days/ViewYourRecyclingCalendar.aspx?r="

TEST_CASES = {
    "Test_001": {"uprn": "127071649"},
    "Test_002": {"uprn": 127072649},
    "Test_003": {"uprn": 127072016},
}

ICON_MAP = {
    "General waste bin": Icons.GENERAL_WASTE,
    "Garden waste bin": Icons.GARDEN,
    "Recycling trolley": Icons.RECYCLING,
}


class Source:
    def __init__(self, uprn):
        _LOGGER.warning(
            "The east_ayrshire_gov_uk source is deprecated and will be removed in "
            "the next major release. East Ayrshire Council has retired the "
            "UPRN-based recycling calendar this source reads (it now redirects to "
            "a page without collection dates) and publishes bin days via ReCollect "
            "(area 'EastAyrshireUK'). Use source 'recollect_net' with the place_id "
            "of your address, service_id='waste' and locale='en-GB'. See "
            "https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/east_ayrshire_gov_uk.md"
        )
        self._uprn = str(uprn)

    def fetch(self):
        session = requests.Session()
        return self.__get_bin_collection_info_page(session, self._uprn)

    def __get_bin_collection_info_page(self, session, uprn):
        r = session.get(API_URL + uprn)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        bin_list = soup.find_all("time")
        entries = []
        for bins in bin_list:
            entries.append(
                Collection(
                    date=parser.parse(bins["datetime"]).date(),
                    t=bins.select_one("span.ScheduleItem").get_text().strip(),
                    icon=ICON_MAP.get(
                        bins.select_one("span.ScheduleItem").get_text().strip()
                    ),
                )
            )
        return entries
