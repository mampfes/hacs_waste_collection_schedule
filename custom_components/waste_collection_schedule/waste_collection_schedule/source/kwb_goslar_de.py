import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.ICS import ICS

TITLE = "Kreiswirtschaftsbetriebe Goslar"
DESCRIPTION = "Source for kwb-goslar.de waste collection."
URL = "https://www.kwb-goslar.de"
TEST_CASES = {
    "Berliner Straße (Clausthal-Zellerfeld)": {"pois": "2523.602"},
    "Braunschweiger Straße (Seesen)": {"pois": "2523.409"},
}

ICON_MAP = {
    "Baum- und Strauchschnitt": Icons.ORGANIC,
    "Biotonne": Icons.BIO_KITCHEN,
    "Blaue Tonne": Icons.NEWSPAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Restmülltonne": Icons.GENERAL_WASTE,
    "Weihnachtsbäume": Icons.CHRISTMAS_TREE,
}


PARAM_TRANSLATIONS = {
    "de": {
        "pois": "POIS",
    },
    "en": {
        "pois": "POIS",
    },
}


class Source:
    def __init__(self, pois):
        self.ics = ICS()
        self.pois = pois

    def fetch(self):
        r = requests.get(
            url="https://www.kwb-goslar.de/output/options.php",
            params={
                "ModID": "48",
                "call": "ical",
                "pois": self.pois,
            },
            headers={
                "Referer": "https://www.kwb-goslar.de",
            },
        )

        if not r.ok:
            raise Exception(f"Error: failed to fetch url: {r.request.url}")

        dates = self.ics.convert(r.text)

        entries = []
        for d in dates:
            date, waste_type = d
            icon = ICON_MAP.get(waste_type)
            entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
