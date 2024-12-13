import logging
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Südbrandenburgischer Abfallzweckverband"
DESCRIPTION = "SBAZV Brandenburg, Deutschland"
URL = "https://www.sbazv.de"
TEST_CASES = {
    "Schönefeld": {"url": "https://fahrzeuge.sbazv.de/WasteManagementSuedbrandenburg/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=1385852001&AboID=23187&Fra=P;R;WB;L;GS"},
}

ICON_MAP = {
    "Restmülltonnen": "mdi:trash-can",
    "Laubsäcke": "mdi:leaf",
    "Gelbe Säcke": "mdi:sack",
    "Papiertonnen": "mdi:package-variant",
    "Weihnachtsbäume": "mdi:pine-tree",
}

_LOGGER = logging.getLogger(__name__)

PARAM_TRANSLATIONS = {}
#    "de": {
#        "city": "Ort",
#        "district": "Ortsteil",
#        "street": "Straße",
#    },
#}


class Source:
    def __init__(self, url):
        self._url = url
        self._ics = ICS()

    def fetch(self):

        # get ics file
        # https://fahrzeuge.sbazv.de/WasteManagementSuedbrandenburg/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=1448170001&AboID=12386&Fra=P;R;WB;L;GS
        # https://www.sbazv.de/entsorgungstermine/klein.ics?city=Wildau&district=Wildau&street=Miersdorfer+Str.
        r = requests.get(self._url)

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
