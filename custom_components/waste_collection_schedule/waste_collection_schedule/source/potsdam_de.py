import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

from datetime import datetime, timedelta
from dateutil import rrule
import json

TITLE = "Potsdam"
DESCRIPTION = "Source for Potsdam."
URL = "https://www.potsdam.de"
TEST_CASES = {
    # "Golm Akazienweg All weekly": {
    #    "ortsteil": "Golm",
    #    "strasse": "Akazienweg",
    #    "rest_rythm": 2,
    #    "papier_rythm": 2,
    #    "bio_rythm": 2,
    # },
    # "Golm Akazienweg All 2 weekly": {
    #    "ortsteil": "Golm",
    #    "strasse": "Akazienweg",
    #    "rest_rythm": 3,
    #    "papier_rythm": 3,
    #    "bio_rythm": 3,
    # }
    # "Golm Akazienweg mixed ": {
    # "ortsteil": "Golm",
    # "strasse": "Akazienweg",
    # "rest_rythm": 4,
    # "papier_rythm": 4,
    # "bio_rythm": 5,
    # }
    #"Teltower Vorstadt  Albert-Einstein-Str. 2 weekly ": {
    #    "ortsteil": "Teltower Vorstadt",
    #    "strasse": "Albert-Einstein-Str.",
    #    "rest_rythm": 3,
    #    "papier_rythm": 3,
    #    "bio_rythm": 3,
    #}
    "Teltower Vorstadt  Albert-Einstein-Str. 2 weekly ": {
        "ortsteil": "Teltower Vorstadt",
        "strasse": "Albert-Einstein-Str.",
        "rest_rythm": 1,
        "papier_rythm": 2,
        "bio_rythm": 5,
    }
}


ICON_MAP = {
    1: "mdi:trash-can",
    2: "mdi:leaf",
    3: "mdi:recycle",
    4: "mdi:package-variant",
    5: "mdi:shower-head",
    6: "mdi:pine-tree",
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
    1: {"name": "2x pro Woche", "rule": 1},
    2: {"name": "wöchentlich", "rule": 1},
    3: {"name": "14-tägig", "rule": 2},
    4: {"name": "4-wöchentlich", "rule": 4},
    5: {"name": "Kombileerung", "rule": 1},
}


API_URL = "https://www.geben-und-nehmen-markt.de/abfallkalender/potsdam/{year}/page-data/index/page-data.json"


class Source:
    def __init__(self, ortsteil: str, strasse: str, rest_rythm: int, papier_rythm: int, bio_rythm: int, gelb_rythm: int = 3):
        self._ortsteil: str = ortsteil
        self._strasse: str = strasse
        self._rythms = {
            1: rest_rythm,
            2: bio_rythm,
            3: gelb_rythm,
            4: papier_rythm,
        }

        # self._rest_rythm: int = rest_rythm
        # self._papier_rythm: int= papier_rythm
        # self._bio_rythm:int=bio_rythm
        # self._gelb_rythm:int = gelb_rythm

    def __get_entries_for_street(self, data) -> list[dict[str, str | int]]:
        for ortsteil in data["allRegionen"][0]["regionen"][0]["ortsteile"]:
            if ortsteil["name"].lower().strip() != self._ortsteil.lower().strip():
                continue
            for strasse in ortsteil["strassen"]:
                if strasse["name"].lower().strip() != self._strasse.lower().strip():
                    continue
                return strasse["eintraege"]

    def __get_dates(self, entry, year, rythm) -> list[datetime]:
        dates: list[datetime] = []
        termin1 = datetime.fromisoformat(
            entry["termin1"].replace("Z", "+00:00"))
        termin2 = datetime.fromisoformat(
            entry["termin2"].replace("Z", "+00:00"))
        if entry["tag1"] == 0:
            dates.extend([termin1, termin2])
            

        else:
            start1 = (termin1 + timedelta(weeks=entry["woche"])).date()

            dates.extend(list(rrule.rrule(interval=rythm, freq=rrule.WEEKLY, dtstart=start1, byweekday=entry["tag1"]-1).between(datetime.now(), datetime(
                year+1, 2, 1), inc=True)))

            # bio Kombileerung (* 1.4. bis 31.10. = weekly 1.11. bis 31.3. = every 14 days)
            if entry["typ"] == 2 and self._rythms[2] == 5:
                # remove dates that are not in the weekly scedule
                dates = list(filter(lambda x: 4 <= x.month <= 10, dates))

                winter_dates = list(rrule.rrule(interval=2, freq=rrule.WEEKLY, dtstart=start1, byweekday=entry["tag1"]-1).between(datetime.now(), datetime(
                    year+1, 2, 1), inc=True))

                # print(list(winter_dates))
                winter_dates = list(
                    filter(lambda x: not (4 <= x.month <= 10), winter_dates))
                dates.extend(winter_dates)

            # print(dates)

            if (entry["tag2"] != 0 and entry["tag2"] != entry["tag1"]):
                start2 = (termin2 + timedelta(weeks=entry["woche2"])).date()
                dates.extend(list(rrule.rrule(interval=rythm, freq=rrule.WEEKLY, dtstart=start2, byweekday=entry["tag2"]-1).between(datetime.now(), datetime(
                    year+1, 2, 1), inc=True)))

        return dates

    def fetch(self):
        now = datetime.now()
        years = [now.year]
        if now.month == 12:
            years.append(now.year + 1)

        collection_entries = []

        for year in years:
            try:
                # get json file
                r = requests.get(API_URL.format(year=year))
                r.raise_for_status()
            except:
                if year == now.year:
                    raise Exception("culd not get data from url exit")
                continue

            data = r.json()["result"]["data"]["dbapi"]
            now = datetime.now()

            # TODO: REMOVE
            # holidays = []
            # for holiday in data["allFeiertage"]:
            #    h = datetime(holiday["jahr"], holiday["monat"],
            #                holiday["tag"]).date()
            #    if h <= now.date():
            #        continue
            #    holidays.append(h)

            street_entries = self.__get_entries_for_street(data)


            entries_categoriezed: dict[int, list[dict[str, str | int]]] = {}
            entries_to_use: list[dict[str, str | int]] = []
            for entry in street_entries:

                if entry["typ"] in self._rythms and entry["rhythmus"] > self._rythms[entry["typ"]]:
                    continue

                if entry["typ"] in entries_categoriezed:
                    entries_categoriezed[entry["typ"]].append(entry)
                else:
                    entries_categoriezed[entry["typ"]] = [entry]

            print(json.dumps(entries_categoriezed))
            for type, type_entries in entries_categoriezed.items():
                if type == 2 and self._rythms[2] == 5:  # bio Kombileerung
                    entries_to_use.extend(
                        filter(lambda x: x["rhythmus"] == 2, type_entries))
                else:
                    if type == 1:
                        print("type_entries", type_entries)
                    sorted_type_entries = sorted(type_entries, key=lambda x: x["rhythmus"], reverse=True)
                    entries_to_use.append(sorted_type_entries[0])
                    if len(sorted_type_entries) > 1 and sorted_type_entries[0]["rhythmus"] == sorted_type_entries[1]["rhythmus"]:
                        print("added:", sorted_type_entries[0])
                        print("additonal adding:", sorted_type_entries[1])
                        entries_to_use.append(sorted_type_entries[1])
                        
                        

            collection_entries = []

            for entry in entries_to_use:

                exception_map = {datetime.strptime(key, "%d.%m.%Y"): datetime.strptime(
                    value, "%d.%m.%Y") for key, value in json.loads(entry["ausnahmen"]).items()}

                rythm_type = self._rythms[entry["typ"]
                                          ] if entry["typ"] in self._rythms else entry["rhythmus"]
                rythm = RYTHM_MAP[rythm_type]["rule"]

                dates: list[datetime] = self.__get_dates(entry, year, rythm)

                for date in dates:
                    if date in exception_map:
                        date = exception_map[date]
                    # Collection icon
                    icon = ICON_MAP.get(entry["typ"])
                    type = TYPE_MAP.get(entry["typ"])
                    if (rythm_type in RYTHM_MAP and entry["tag1"] != 0):
                        type += " (" + RYTHM_MAP.get(
                            rythm_type)["name"] + ")"
                    collection_entries.append(Collection(
                        date=date.date(), t=type, icon=icon))

            # entries = []

            collection_entries.sort(key=lambda x: x.date)

        return collection_entries
