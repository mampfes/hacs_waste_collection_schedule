import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Stadt Willich"
DESCRIPTION = "Source for Stadt Willich waste collection."
URL = "https://www.stadt-willich.de"
ICONS = {
    "Graue Tonne": "mdi:trash-can",
    "Blaue Tonne": "mdi:newspaper-variant-multiple",
    "Gelbe Tonne": "mdi:recycle",
    "Bio Tonne": "mdi:bio",
    "Grünbündel": "mdi:tree",
}
TEST_CASES = {
    "Altufer": {"street": "Altufer"},
    "Zum Schickerhof": {"street": "Zum Schickerhof"},
}


class Source:
    def __init__(self, street):
        self._street = street
        self._ics = ICS()

    def fetch(self):
        # get Bezirk/area ID
        r = requests.get(
            'https://www.stadt-willich.de/de/dienstleistungen/abfallkalender-als-ical-datei/',
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        select = soup.find_all(['option', 'value'])
        area = [i for i in select if self._street in i]
        if len(area) == 0:
            raise Exception("Street not found")
        area_id = area[0].get('value')
        if " " in area_id:
            area_id = "+".join(area_id.split())

        # Encode params with area_id from above, without encoding the '+'
        params = {
            "rule": "neu",
            "path": "/sys/dienstleistungslayout-abfallservice-ausgabe-2/",
            "Bezirk": area_id,
        }
        params_enc = urlencode(params, safe='+')
        # Get ICS file
        r = requests.get(
            f"https://www.stadt-willich.de/www/web_io.nsf/index.xsp",
            params=params_enc,
        )
        r.raise_for_status()

        # Fix issue with a mix of Windows/Mac line breaks
        ics_data = r.text.replace("\r", "\n")
        ics_data = ics_data.replace("\n\n", "\n")

        # Convert ICS String to events
        dates = self._ics.convert(ics_data)

        entries = []
        for d in dates:
            icon = ICONS.get(d[1], "mdi:trash-can")
            entries.append(Collection(
                date=d[0],
                t=d[1],
                icon=icon
            )
            )
        return entries
