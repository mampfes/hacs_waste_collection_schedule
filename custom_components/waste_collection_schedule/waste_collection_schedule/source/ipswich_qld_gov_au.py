import datetime
import urllib
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection

TITLE = "Ipswich City Council"
DESCRIPTION = "Source for Ipswich City Council rubbish collection."
URL = "https://www.ipswich.qld.gov.au"
TEST_CASES = {
    "Camira State School": {"street": "184-202 Old Logan Rd", "suburb": "Camira"},
    "Random": {"street": "50 Brisbane Road", "suburb": "Redbank"},
}


ICON_MAP = {
    "Waste Bin": "mdi:trash-can",
    "Recycle Bin": "mdi:recycle",
    "FOGO Bin": "mdi:leaf",
}


def toDate(dateStr: str):
    items = dateStr.split("-")
    return datetime.date(int(items[1]), int(items[2]), int(items[3]))


class IpswichGovAuParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._entries = []
        self._state = None
        self._level = 0
        self._class = ""
        self._li_level = 0
        self._li_valid = False
        self._span_level = 0
        self._load_date = False
        self._load_bin = False
        self._loaded_date = None

    @property
    def entries(self):
        return self._entries

    def handle_endtag(self, tag):

        if tag == "li":
            self._li_level -= 1
            self._loaded_date = None

        if tag == "span":
            self._span_level -= 1

    def handle_starttag(self, tag, attrs):

        d = dict(attrs)
        cls = d.get("class", "")

        if tag == "li":
            self._li_level += 1
            if self._li_level == 1 and cls == "WBD-result-item":
                self._li_valid = True
            else:
                self._li_valid = False
                self._loaded_date = None

        if tag == "span":
            self._span_level += 1
            if self._li_valid and self._span_level == 1 and cls == "WBD-event-date":
                self._load_date = True

            if self._li_valid and self._span_level == 3 and cls == "WBD-bin-text":
                self._load_bin = True

    def handle_data(self, data):
        if not self._li_valid:
            return

        if self._load_date:
            self._load_date = False

            items = data.strip().split("-")
            self._loaded_date = datetime.date(
                int(items[0]), int(items[1]), int(items[2])
            )

        if self._load_bin:
            self._load_bin = False

            self._entries.append(
                Collection(
                    self._loaded_date, data, icon=ICON_MAP.get(data)
                )
            )


class Source:
    def __init__(self, street, suburb):
        self._street = street
        self._suburb = suburb

    def fetch(self):

        address = urllib.parse.quote_plus(f"{self._street}, {self._suburb}")
        params = {
            "apiKey": "b8dbca0c-ad9c-4f8a-8b9c-080fd435c5e7",
            "agendaResultLimit": "3",
            "dateFormat": "yyyy-MM-dd",
            "displayFormat": "agenda",
            "address": f"{address}+QLD%2C+Australia",
        }

        r = requests.get("https://console.whatbinday.com/api/search", params=params)
        p = IpswichGovAuParser()
        p.feed(r.text)
        return p.entries
