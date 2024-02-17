import re
from datetime import datetime
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Gore, Invercargill & Southland"
DESCRIPTION = "Source for Wastenet.org.nz."
URL = "http://www.wastenet.org.nz"
TEST_CASES = {
    "166 Lewis Street": {"address": "166 Lewis Street"},
    "Old Format: 199 Crawford Street": {"address": "199 Crawford Street INVERCARGILL"},
    "Old Format: 156 Tay Street": {"address": "156 Tay Street INVERCARGILL"},
    "entry_id glass only": {"entry_id": "23571"},
    # "31 Conyers Street": {"address": "31 Conyers Street INVERCARGILL"},  # Thursday
    # "67 Chesney Street": {"address": "67 Chesney Street INVERCARGILL"},  # Friday
}

ICON_MAP = {
    "Glass": "mdi:glass-mug-variant",
    "Rubbish": "mdi:delete-empty",
    "Recycle": "mdi:recycle",
}


class WasteSearchResultsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._entries = []
        self._wasteType = None
        self._withinCollectionDay = False
        self._withinType = False

    @property
    def entries(self):
        return self._entries

    def handle_starttag(self, tag, attrs):
        if tag == "span":
            d = dict(attrs)
            if d.get("class", "").startswith("badge"):
                self._withinType = True

    def handle_data(self, data):
        if self._withinType:
            self._withinType = False
            self._wasteType = data
        elif data.startswith("Next Service Date:"):
            self._withinCollectionDay = True
        elif self._withinCollectionDay:
            date = datetime.strptime(data, "%y/%m/%d").date()
            if self._wasteType is not None:
                self._entries.append(Collection(date, self._wasteType))
            self._withinCollectionDay = False


HEADER = {"User-Agent": "Mozilla/5.0"}

SITE_URL = "https://www.wastenet.org.nz/bin-day/"
ADDRESS_URL = "https://www.wastenet.org.nz/wp-admin/admin-ajax.php"


class Source:
    def __init__(self, address: str | None = None, entry_id=None):
        if not address and not entry_id:
            raise ValueError("Address or entry_id must be provided")

        self._address = address.replace(" INVERCARGILL", "") if address else None
        self._entry_id = entry_id

    def get_entry_id(self, s):
        r = s.get(SITE_URL)
        r.raise_for_status()
        # regex find security: 'KEY'
        match = re.search(r"security: '(\w+)'", r.text)
        if not match:
            raise ValueError("Security key not found")
        security_key = match.group(1)

        # get token
        params = {
            "action": "we_data_autocomplete",
            "term": self._address,
            "security": security_key,
        }

        r = s.get(
            ADDRESS_URL,
            params=params,
        )
        r.raise_for_status()

        return r.json()["data"][0]["url"].split("=")[1]

    def fetch(self):
        s = requests.Session()
        s.headers.update(HEADER)

        if self._entry_id is None:
            self._entry_id = self.get_entry_id(s)

        r = s.get(SITE_URL, params={"entry_id": self._entry_id})
        r.raise_for_status()
        p = WasteSearchResultsParser()
        p.feed(r.text)
        return p.entries
