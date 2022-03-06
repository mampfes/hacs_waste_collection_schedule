import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "AWB Bad Kreuznach"
DESCRIPTION = "Source for AWB Bad Kreuznach."
URL = "https://app.awb-bad-kreuznach.de/"
TEST_CASES = {
    "Hargesheim": {"ort": "Hargesheim", "strasse": "Winzenheimer Straße", "nummer": 16}
}

TYPES = ("restmuell", "bio", "wert", "papier")


class Source:
    def __init__(self, ort, strasse, nummer):
        self._ort = ort
        self._strasse = strasse
        self._nummer = nummer

    def fetch(self):
        pass
        args = {
            "ort": self._ort,
            "strasse": self._strasse,
            "nummer": self._nummer,
        }

        # get latitude/longitude file
        r = requests.post(
            "https://app.awb-bad-kreuznach.de/api/checkAddress.php", data=args
        )
        data = json.loads(r.text)

        # get dates
        del args["nummer"]
        args["mode"] = "web"
        args["lat"] = data["lat"]
        args["lon"] = data["lon"]
        print(args)
        r = requests.post(
            "https://app.awb-bad-kreuznach.de/api/loadDates.php", data=args
        )
        data = json.loads(r.text)

        entries = []

        for d in data["termine"]:
            date = datetime.date.fromisoformat(d["termin"])
            for type in TYPES:
                if d[type] != "0":
                    entries.append(Collection(date, type, date))

        return entries
