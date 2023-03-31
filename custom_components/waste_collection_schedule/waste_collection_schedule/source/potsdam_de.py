import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

from datetime import datetime, timedelta
from dateutil import rrule
import json

TITLE = "Potsdam"
DESCRIPTION = "Source for Potsdam."
URL = "https://www.potsdam.de"
TEST_CASES = {"Golm Akazienweg": {"ortsteil": "Golm", "strasse": "Akazienweg"}}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}

TYPE_MAP = {
    1: "Restabfall",
    2: "Bioabfall",
    3: "Leichtverpackungen",
    4: "Altpapier",
    5: "Biotonnenreinigung",
    6: "Weihnachtsbaumabholung",
}

RYTHM_MAP = {
    1: "2x pro Woche",
    2: "wöchentlich",
    3: "14-tägig",
    4: "4-wöchentlich",
}


API_URL = "https://www.geben-und-nehmen-markt.de/abfallkalender/potsdam/2023/page-data/index/page-data.json"


class Source:
    def __init__(self, ortsteil: str, strasse: str):
        self._ortsteil: str = ortsteil
        self._strasse: str = strasse

    def fetch(self):
        # get json file
        r = requests.get(API_URL)
        r.raise_for_status()

        data = r.json()["result"]["data"]["dbapi"]
        now = datetime.now()

        holidays = []

        for holiday in data["allFeiertage"]:
            h = datetime(holiday["jahr"], holiday["monat"],
                         holiday["tag"]).date()
            if h <= now.date():
                continue
            holidays.append(h)

        entries = []

        for ortsteil in data["allRegionen"][0]["regionen"][0]["ortsteile"]:
            if ortsteil["name"] != self._ortsteil:
                continue
            for strasse in ortsteil["strassen"]:
                if strasse["name"].lower().strip() != self._strasse.lower().strip():
                    continue

                for eintrag in strasse["eintraege"]:
                    exceptions = [datetime.strptime(e, "%d.%m.%Y").date(
                    ) for e in json.loads(eintrag["ausnahmen"])]

                    dates = []

                    start = datetime.fromisoformat(eintrag["termin1"].replace(
                        "Z", "+00:00")).date() + timedelta(weeks=eintrag["woche"])
                    dates.extend(list(rrule.rrule(interval=eintrag["rhythmus"], freq=rrule.WEEKLY, dtstart=start, until=datetime(
                        now.year+1, 1, 1).date(), byweekday=eintrag["tag1"]-1)))
                    print(dates)

                    if (eintrag["tag2"] != 0):
                        start = datetime.fromisoformat(eintrag["termin2"].replace(
                            "Z", "+00:00")).date() + timedelta(weeks=eintrag["woche2"])

                        dates.extend(list(rrule.rrule(interval=eintrag["rhythmus"], freq=rrule.WEEKLY, dtstart=start, until=datetime(
                            now.year+1, 1, 1).date(), byweekday=eintrag["tag2"]-1)))

                    for date in dates:
                        if date.date() in exceptions or date.date() < now.date():
                            continue
                        icon = ICON_MAP.get(eintrag["typ"])  # Collection icon
                        type = TYPE_MAP.get(eintrag["typ"])
                        if (eintrag["rhythmus"] in RYTHM_MAP):
                            type += " (" + RYTHM_MAP.get(
                                eintrag["rhythmus"]) + ")"
                        entries.append(Collection(
                            date=date.date(), t=type, icon=icon))

                break

        # entries = []
        
        entries.sort(key=lambda x: x.date)

        return entries
