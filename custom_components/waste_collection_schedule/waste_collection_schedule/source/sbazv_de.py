import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Südbrandenburgischer Abfallzweckverband"
DESCRIPTION = "SBAZV Brandenburg, Deutschland"
URL = "https://www.sbazv.de"
TEST_CASES = {
    "Wildau": {"city": "wildau", "district": "Wildau", "street": "Miersdorfer Str."},
    "Schönefeld": {
        "city": "Schönefeld",
        "district": "Großziethen",
        "street": "kleistring",
    },
}

ICON_MAP = {
    "Restmülltonnen": "mdi:trash-can",
    "Laubsäcke": "mdi:leaf",
    "Gelbe Säcke": "mdi:sack",
    "Papiertonnen": "mdi:package-variant",
    "Weihnachtsbäume": "mdi:pine-tree",
}

# _LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, city, district, street=None):
        self._city = city
        self._district = district
        self._street = street
        self._ics = ICS()

    def fetch(self):
        args = {
            "city": self._city,
            "district": self._district,
            "street": self._street,
        }

        # get ics file
        # https://www.sbazv.de/entsorgungstermine/klein.ics?city=Wildau&district=Wildau&street=Miersdorfer+Str.
        r = requests.get(
            "https://www.sbazv.de/entsorgungstermine/klein.ics", params=args
        )

        # parse ics file
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            waste_type = d[1].strip()
            next_pickup_date = d[0]
            # remove duplicates
            if any(
                e.date == next_pickup_date and e.type == waste_type for e in entries
            ):
                continue
            entries.append(
                Collection(
                    date=next_pickup_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
