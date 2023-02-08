import logging
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Abfallwirtschaft Stadt Schweinfurt"
DESCRIPTION = "Source for Schweinfurt, Germany"
URL = "https://www.schweinfurt.de"
TEST_CASES = {
    "TestcaseI": {"address": "Ahornstrasse"},
    "TestcaseII": {"address": "Ahornstrasse", "showmobile": "True"},
}

_LOGGER = logging.getLogger(__name__)

API_URL = "https://www.schweinfurt.de/leben-freizeit/umwelt/abfallwirtschaft/4427.Aktuelle-Abfuhrtermine-und-Muellkalender.html"


class Source:
    def __init__(self, address, showmobile=False):
        self._address = address
        self._showmobile = showmobile

    def fetch(self):
        headers = {"referer": API_URL}

        s = requests.session()
        r = s.get(API_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        params = None
        for tag in soup.find_all("option"):
            if self._address in tag.text:
                now = datetime.now()
                nex = now + timedelta(days=365)
                params = {
                    "_func": "evList",
                    "_mod": "events",
                    "ev[start]": now.strftime("%Y-%m-%d"),
                    "ev[end]": nex.strftime("%Y-%m-%d"),
                    "ev[addr]": tag.get("value"),
                }

        if params is None:
            raise Exception("Address not found")

        r = s.get(API_URL, params=params, headers=headers)
        r.raise_for_status()

        data = r.json()

        s.close()

        entries = []
        for entry in data["contents"]:
            if (
                "Wertstoffhof" not in data["contents"][entry]["title"]
                or self._showmobile
            ):
                entries.append(
                    Collection(
                        datetime.strptime(
                            data["contents"][entry]["start"], "%Y-%m-%d %H:%M:%S"
                        ).date(),
                        data["contents"][entry]["title"],
                    )
                )
        return entries
