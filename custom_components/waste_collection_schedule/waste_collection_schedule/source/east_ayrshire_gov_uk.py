import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

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
    "General waste bin": "mdi:trash-can",
    "Garden waste bin": "mdi:leaf",
    "Recycling trolley": "mdi:recycle",
}


class Source:
    def __init__(self, uprn):
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
