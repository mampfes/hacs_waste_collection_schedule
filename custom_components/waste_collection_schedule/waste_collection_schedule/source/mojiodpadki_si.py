import datetime
import logging
import requests

from bs4 import BeautifulSoup
from waste_collection_schedule import Collection


TITLE = "Moji odpadki, Ljubljana"
DESCRIPTION = "Source script for mojiodpadki.si"
URL = "https://www.mojiodpadki.si"
TEST_CASES = {
    "DrzavniZbor": {"uprn": "1049"},
}

API_URL = "https://www.mojiodpadki.si/urniki/urniki-odvoza-odpadkov"
ICON_MAP = {
    "MKO": "mdi:trash-can",  # unsorted waste
    "EMB": "mdi:recycle",  # packaging waste
    "BIO": "mdi:leaf",  # biodegradable waste
    "PAP": "mdi:newspaper",  # paper waste
}

# month names from mojiodpadki.si (sl_SI)
MONTHS = {
    "JANUAR": 1,
    "FEBRUAR": 2,
    "MAREC": 3,
    "APRIL": 4,
    "MAJ": 5,
    "JUNIJ": 6,
    "JULIJ": 7,
    "AVGUST": 8,
    "SEPTEMBER": 9,
    "OKTOBER": 10,
    "NOVEMBER": 11,
    "DECEMBER": 12,
}

_LOGGER = logging.getLogger(__name__)


class Source:


    def __init__(self, uprn):
        _LOGGER.info(f"Initializing mojiodpadki.si waste collection service for uprn={uprn}")
        self._uprn = uprn


    def fetch(self):
        # GET request returns schedule for matching uprn
        url = f"{API_URL}/s/{self._uprn}"
        _LOGGER.info(f"Getting mojiodpadki.si waste collection schedule for uprn={self._uprn}, url={url}")
        r = requests.Session().get(url)
        body = r.text
        _LOGGER.debug(f"mojiodpadki.si waste collection schedule for uprn={self._uprn}: {body}")

        # list that holds collection schedule
        entries = []

        # response is in HTML - parse it
        soup = BeautifulSoup(body, "html.parser")
        _LOGGER.debug(f"Parsed mojiodpadki.si response")

        # find years, months, dates and waste tags in all document tables
        year = datetime.date.today().year
        for table in soup.find_all("table"):
            # <table class="calendar table-responsive">
            # <thead>
            # <tr>
            # <td class="year fs-5 fw-bold" colspan="2">2023</td> <!-- year or &nbsp; -->
            # ...
            # <tr>
            # <td class="month fs-5 fw-bold bg-primary text-light text-center" colspan="3">FEBRUAR</td>
            hy = table.thead.find("td", class_="year").string
            if hy and hy.isnumeric():
                _LOGGER.debug(f"found year={year}")
                year = hy
            month = table.thead.find("td", class_="month").string
            _LOGGER.debug(f"found month={month}")

            # <table class="calendar table-responsive">
            # ...
            # <tbody>
            # <tr class="">
            # <td class="day-number text-center">1</td>
            # <td class="day-info text-end"><span class="small ms-1 badge tag pap" data-bs-toggle="tooltip" title="Papir in karton" tabindex="0">PAP</span>&nbsp;</td>
            # ...
            for tag in table.tbody.find_all("span", class_="tag"):
                _LOGGER.debug(f"found tag={tag.string}")
                day = tag.parent.parent.find("td", class_="day-number").string
                _LOGGER.debug(f"found day={day}, tag={tag.string}, title={tag['title']}")
                entries.append(
                    Collection(
                        date=datetime.date(int(year), MONTHS.get(month), int(day)),
                        t=tag["title"],
                        icon=ICON_MAP.get(tag.string)
                    )
                )

        return entries
