import requests
import datetime
import icalendar
import json
from collections import OrderedDict

from ..helpers import CollectionAppointment


DESCRIPTION = "Source for AbfallNavi (= regioit.de) based services"
URL = "https://www.regioit.de"
TEST_CASES = OrderedDict(
    [
        (
            "Aachen, Abteiplatz 7",
            {"service": "aachen", "strasse": 6654812, "hausnummer": 6654817},
        ),
        ("Lindlar, Aggerweg", {"service": "lindlar", "strasse": 63202}),
        ("Roetgen, Am Sportplatz 2", {"service": "roe", "strasse": 52073}),
    ]
)


class Source:
    def __init__(self, service, strasse, hausnummer=None):
        self._url = f"https://{service}-abfallapp.regioit.de/abfall-app-{service}/rest"
        if hausnummer is not None:
            self._url += f"/hausnummern/{hausnummer}"
        else:
            self._url += f"/strassen/{strasse}"

    def fetch(self):
        # get fraktionen
        r = requests.get(f"{self._url}/fraktionen")
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
        fraktionen_list = json.loads(r.text)
        fraktionen = {}
        for fraktion in fraktionen_list:
            fraktionen[fraktion["id"]] = fraktion["name"]

        # retrieve appointments
        args = []
        for f in fraktionen.keys():
            args.append(("fraktion", f))

        r = requests.get(f"{self._url}/termine", params=args)
        results = json.loads(r.text)

        entries = []
        for r in results:
            date = datetime.datetime.strptime(r["datum"], "%Y-%m-%d").date()
            fraktion = fraktionen[r["bezirk"]["fraktionId"]]
            entries.append(CollectionAppointment(date, fraktion))

        return entries
