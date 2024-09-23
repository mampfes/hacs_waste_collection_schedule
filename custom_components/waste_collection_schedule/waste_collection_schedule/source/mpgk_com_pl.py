import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "MPGK Katowice"
DESCRIPTION = "Source for MPGK Katowice."
URL = "https://www.mpgk.com.pl/"
TEST_CASES = {
    "Warszawska 17": {"street": "Warszawska", "number": 17},
    "3 Maja 38": {"street": "3 Maja", "number": "38"},
}


ICON_MAP = {
    "tworzyw": "mdi:recycle",
    "papier": "mdi:newspaper",
    "szklane": "mdi:glass-wine",
    "komunalne": "mdi:trash-can",
    "wielkogabarytowe": "mdi:truck",
}


API_URL = "https://www.mpgk.com.pl/mod/harmonogram/ics"


class Source:
    def __init__(self, street: str, number: str | int):
        self._street: str = street
        self._number: str | int = number
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        args = {"street": self._street, "number": self._number}

        # get json file
        r = requests.post(API_URL, data=args)
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            icon_get_string = (
                d[1]
                .removeprefix("Odpady ")
                .removeprefix("z ")
                .replace(",", "")
                .split()[0]
            )
            entries.append(Collection(d[0], d[1], ICON_MAP.get(icon_get_string)))

        return entries
