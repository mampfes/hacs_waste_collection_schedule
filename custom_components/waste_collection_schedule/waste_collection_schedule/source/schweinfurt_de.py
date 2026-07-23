import logging
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Abfallwirtschaft Stadt Schweinfurt"
DESCRIPTION = "Source for Schweinfurt, Germany"
URL = "https://www.schweinfurt.de"
TEST_CASES = {
    "TestcaseI": {"address": "Ahornstrasse"},
    "TestcaseII": {"address": "Ahornstrasse", "showmobile": "True"},
    "TestcaseIII": {"address": "Ahornstrasse", "showmobile": "False"},
    "TestcaseIV": {"address": "Ahornstrasse", "showmobile": False},
}

_LOGGER = logging.getLogger(__name__)

API_URL = "https://www.schweinfurt.de/leben-freizeit/umwelt/abfallwirtschaft/4427.Aktuelle-Abfuhrtermine-und-Muellkalender.html"

# Titles (or title fragments) that are announcements rather than an actual
# collection/drop-off event, e.g. "Wertstoffhof geschlossen" (recycling
# center closed) or "Aktion Kompostverkauf" (compost sale campaign). These
# are never useful as a "collection" entry, so they are always filtered
# out, regardless of the `showmobile` setting.
NON_COLLECTION_KEYWORDS = ["geschlossen", "Aktion Kompostverkauf"]


def _to_bool(value) -> bool:
    """Coerce a bool or a (possibly quoted YAML) string into a bool.

    YAML configs sometimes pass booleans as quoted strings (e.g.
    `showmobile: "False"`). A naive `bool("False")` evaluates to `True`
    since any non-empty string is truthy, so this helper normalizes both
    real booleans and their string representations.
    """
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


class Source:
    def __init__(self, address, showmobile=False):
        self._address = address
        self._showmobile = _to_bool(showmobile)

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
            raise SourceArgumentNotFound("address", self._address)

        r = s.get(API_URL, params=params, headers=headers)
        r.raise_for_status()

        data = r.json()

        s.close()

        entries = []
        for entry in data["contents"]:
            title = data["contents"][entry]["title"]

            if any(
                keyword.lower() in title.lower() for keyword in NON_COLLECTION_KEYWORDS
            ):
                continue

            if "Wertstoffhof" in title and not self._showmobile:
                continue

            entries.append(
                Collection(
                    datetime.strptime(
                        data["contents"][entry]["start"], "%Y-%m-%d %H:%M:%S"
                    ).date(),
                    title,
                )
            )
        return entries
