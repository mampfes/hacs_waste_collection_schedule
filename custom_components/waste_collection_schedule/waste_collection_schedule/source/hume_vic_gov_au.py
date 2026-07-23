import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Hume City Council"
DESCRIPTION = "Source for hume.vic.gov.au Waste Collection Services"
URL = "https://hume.vic.gov.au"
TEST_CASES = {
    "19 Potter": {
        "address": "19 Potter Street Craigieburn 3064",
        "predict": True,
    },
    "1/90 Vineyard": {"address": "1/90 Vineyard Road Sunbury, VIC 3429"},  # Wednesday
    "9-19 McEwen": {"address": "9-19 MCEWEN DRIVE SUNBURY VICTORIA 3429"},  # Wednesday
    "33 Toyon": {"address": "33 TOYON ROAD KALKALLO  3064"},  # Friday
}

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.hume.vic.gov.au/Residents/Waste/Know-my-bin-day",
    "Sec-Fetch-Site": "same-origin",
    "X-Requested-With": "XMLHttpRequest",
}

ICON_MAP = {
    "Garbage": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Food and garden": Icons.BIO_KITCHEN,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.hume.vic.gov.au",
    argument_name="address",
    headers=HEADERS,
    use_curl_cffi=True,
    impersonate="chrome124",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, address="", predict=False):
        address = address.strip()
        address = re.sub(" +", " ", address)
        address = re.sub(",", "", address)
        address = re.sub(r"victoria (\d{4})", " \\1", address, flags=re.IGNORECASE)
        address = re.sub(r" vic (\d{4})", " \\1", address, flags=re.IGNORECASE)
        self.address = address

        if not isinstance(predict, bool):
            raise Exception("'predict' must be a boolean value")
        self.predict = predict
        self._client = OpenCitiesClient(_CONFIG)

    def collect_dates(self, start_date, weeks):
        dates = []
        dates.append(start_date)
        for _i in range(1, int(4 / weeks)):
            start_date = start_date + timedelta(days=(weeks * 7))
            dates.append(start_date)
        return dates

    def fetch(self) -> list[Collection]:
        if not self.predict:
            return self._client.fetch(address=self.address)

        # `predict` needs each block's "note" text (a fortnightly/weekly
        # hint) that the shared client's parser doesn't return, so fetch
        # and parse the raw HTML locally for this path.
        geolocation_id = self._client.resolve_geolocation_id(self.address)
        html = self._client.get_waste_services_html(geolocation_id)
        soup = BeautifulSoup(html, "html.parser")
        services = soup.find_all("div", attrs={"class": "waste-services-result"})

        entries = []
        for item in services:
            date_text = item.find("div", attrs={"class": "next-service"})
            title = item.find("h3")
            if date_text is None or title is None:
                continue
            date_format = "%a %d/%m/%Y"
            try:
                cleaned_date_text = (
                    date_text.text.replace("\r", "").replace("\n", "").strip()
                )
                date = datetime.strptime(cleaned_date_text, date_format).date()
            except ValueError:
                continue

            waste_type = title.text.strip()

            dates = [date]
            interval_text = item.find("div", attrs={"class": "note"})
            if interval_text is not None:
                if "fortnight" in interval_text.get_text():
                    weeks = 2
                elif "same day each week" in interval_text.get_text():
                    weeks = 1
                else:
                    weeks = None
                if weeks is not None:
                    dates = self.collect_dates(date, weeks)

            for d in dates:
                entries.append(
                    Collection(
                        date=d,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type, Icons.GENERAL_WASTE),
                    )
                )

        return entries
