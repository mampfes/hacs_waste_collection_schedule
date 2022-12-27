from datetime import datetime
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Südbrandenburgischer Abfallzweckverband"
DESCRIPTION = "SBAZV Brandenburg, Deutschland"
URL = "https://www.sbazv.de"
TEST_CASES = {
    "Wildau": {
        "city": "wildau",
        "district": "Wildau",
        "street": "Miersdorfer Str."
    }
}

ICON_MAP = {
    "Restmülltonnen": "mdi:trash-can",
    "Laubsäcke" : "mdi:leaf",
    "Gelbe Säcke" : "mdi:sack",
    "Papiertonnen" : "mdi:package-variant",
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
        now = datetime.now()
        entries = self.fetch_year(now.year, self._city, self._district, self._street)
        if now.month == 12:
            # also get data for next year if we are already in december
            try:
                entries.extend(
                    self.fetch_year(
                        (now.year + 1), self._city, self._district, self._street
                    )
                )
            except Exception:
                # ignore if fetch for next year fails
                pass
        return entries

    def fetch_year(self, year, city, district, street):
        args = {
            "city": city,
            "district": district,
            "street": street,
        }

        # get ics file
        # https://www.sbazv.de/entsorgungstermine/klein.ics?city=Wildau&district=Wildau&street=Miersdorfer+Str.
        r = requests.get("https://www.sbazv.de/entsorgungstermine/klein.ics", params=args)

        # parse ics file
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
#            _LOGGER.error(d)
            waste_type = d[1].strip()
            next_pickup_date = d[0]
            
            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=ICON_MAP.get(waste_type,"mdi:trash-can")))

        return entries
