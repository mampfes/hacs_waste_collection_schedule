import datetime
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wastenet"
DESCRIPTION = "Source for Wastenet.org.nz."
URL = "https://www.wastenet.org.nz"
TEST_CASES = {
    "Chesney Street": {"address": "67 Chesney Street"},
    "Tweed Street": {"address": "157 Tweed Street"},
    "Foyle Street": {"address": "198 Foyle Street"},
}


# Parser for <div> element with class wasteSearchResults
class WasteSearchResultsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._entries = []
        self._wasteType = None
        self._withinCollectionDay = False

    @property
    def entries(self):
        return self._entries

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            d = dict(attrs)
            if d.get("class", "").startswith("wasteSearchResults "):
                self._wasteType = d["class"][19:]  # remove "wasteSearchResults "

    def handle_data(self, data):
        if data == "Next Collection Day":
            self._withinCollectionDay = True
        elif self._withinCollectionDay:
            date = None
            if data.lower() == "today":
                date = datetime.date.today()
            elif data.lower() == "tomorrow":
                date = datetime.date.today() + datetime.timedelta(days=1)
            else:
                date = datetime.datetime.strptime(
                    data.partition(",")[2].strip(), "%d %B %Y"
                ).date()

            if self._wasteType is not None:
                self._entries.append(Collection(date, self._wasteType))

            self._withinCollectionDay = False


class Source:
    def __init__(
        self, address,
    ):
        self._address = address

    def fetch(self):
        # get token
        params = {"view": 1, "address": self._address}

        r = requests.get(
            "http://www.wastenet.org.nz/RecycleRubbish/WasteCollectionSearch.aspx",
            params=params,
        )

        p = WasteSearchResultsParser()
        p.feed(r.text)
        return p.entries
