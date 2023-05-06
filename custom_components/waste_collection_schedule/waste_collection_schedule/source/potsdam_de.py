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
    #"Golm Akazienweg mixed ": {
    #"ortsteil": "Golm",
    #"strasse": "Akazienweg",
    #"rest_rythm": 4,
    #"papier_rythm": 4,
    #"bio_rythm": 3,
    #},
    # "Teltower Vorstadt  Albert-Einstein-Str. 2 weekly ": {
    #    "ortsteil": "Teltower Vorstadt",
    #    "strasse": "Albert-Einstein-Str.",
    #    "rest_rythm": 3,
    #    "papier_rythm": 3,
    #    "bio_rythm": 3,
    # }
    #"Teltower Vorstadt  Albert-Einstein-Str. 2 weekly ": {
    #    "ortsteil": "Teltower Vorstadt",
    #    "strasse": "Albert-Einstein-Str.",
    #    "rest_rythm": 4,
    #    "papier_rythm": 3,
    #    "bio_rythm": 3,
    #}
    "Uetz  Kanalweg ": {
        "ortsteil": "Uetz",
        "strasse": "Kanalweg",
        "rest_rythm": 4,
        "papier_rythm": 4,
        "bio_rythm": 3,
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


# tag[2] correct for rythm 4 for trash type 1

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

    def __get_dates(self, entry, year, rythm_interval, now, days:dict[str,int] ) -> list[datetime]:
        # Need to capture older dates if I want to get their replacement dates if they are in the future
        date_start_calc = now - timedelta(weeks=4)
        dates: list[datetime] = []
        termin1 = datetime.fromisoformat(
            entry["termin1"].replace("Z", "+00:00"))
        termin2 = datetime.fromisoformat(
            entry["termin2"].replace("Z", "+00:00"))
        if days["tag1"] == 0:
            if termin1.date() > now.date():
                dates.append(termin1)
            if termin1 != termin2 and termin2.date() > now.date():
                dates.append(termin2)

        else:
            print("typ", entry["typ"], "rythm", entry["rhythmus"],  "woche", entry["woche"],"woche2", entry["woche2"], "tag1", days["tag1"], "termin1", entry["termin1"], "tag2", days["tag2"], "termin2", entry["termin2"])
            if entry["typ"] in self._rythms and self._rythms[entry["typ"]] == 1: #twice a week
                start1 = (termin1 + timedelta(weeks=(entry["rhythmus"])%4+1+entry["woche"])).date()
            else:
                start1 = (termin1 + timedelta(weeks=entry["woche"])).date()
                

            dates.extend(list(rrule.rrule(interval=rythm_interval, freq=rrule.WEEKLY, dtstart=start1, byweekday=entry["tag1"]-1).between(date_start_calc, datetime(
                year+1, 2, 1), inc=True)))

            # bio Kombileerung (* 1.4. bis 31.10. = weekly 1.11. bis 31.3. = every 14 days)
            if entry["typ"] == 2 and self._rythms[2] == 5:
                # remove dates that are not in the weekly scedule
                dates = list(filter(lambda x: 4 <= x.month <= 10, dates))

                winter_dates = list(rrule.rrule(interval=2, freq=rrule.WEEKLY, dtstart=start1, byweekday=entry["tag1"]-1).between(date_start_calc, datetime(
                    year+1, 2, 1), inc=True))

                winter_dates = list(
                    filter(lambda x: not (4 <= x.month <= 10), winter_dates))
                dates.extend(winter_dates)

            if (entry["typ"] in self._rythms and self._rythms[entry["typ"]] == 1 and days["tag2"] != 0 and days["tag2"] != days["tag1"]):
                print("TAHG2")
                start2 = (termin2 + timedelta(weeks=entry["woche2"]-2)).date()
                dates.extend(list(rrule.rrule(interval=rythm_interval, freq=rrule.WEEKLY, dtstart=start2, byweekday=days["tag2"]-1).between(date_start_calc, datetime(
                    year+1, 2, 1), inc=True)))

        return dates

    def fetch(self):
        today = datetime.now()
        years = [today.year]
        if today.month == 12:
            years.append(today.year + 1)

        collection_entries = []

        for year in years:
            try:
                # get json file
                r = requests.get(API_URL.format(year=year))
                r.raise_for_status()
            except:
                if year == today.year:
                    raise Exception("culd not get data from url exit")
                continue

            data = r.json()["result"]["data"]["dbapi"]
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            street_entries = self.__get_entries_for_street(data)


            entries_categoriezed: dict[int, list[dict[str, str | int]]] = {}
            entries_to_use: list[dict[str, str | int]] = []
            for entry in street_entries:

                if entry["typ"] in entries_categoriezed:
                    entries_categoriezed[entry["typ"]].append(entry)
                else:
                    entries_categoriezed[entry["typ"]] = [entry]
            
            days_by_type:dict[int,dict[str,int]] = {}
            
            for type, type_entries in entries_categoriezed.items():
                days_by_type[type] = {"tag1": 0, "tag2": 0}
                for entry in type_entries:
                    if entry["tag1"] != 0:
                        days_by_type[type]["tag1"] = entry["tag1"]
                    if entry["tag2"] != 0:
                        days_by_type[type]["tag2"] = entry["tag2"]
                        
                type_entries = filter(lambda x: (x["rhythmus"] <=2 or x["rhythmus"] <= self._rythms[x["typ"]]) and x["rhythmus"] <4, type_entries)
                
                if type == 2 and self._rythms[2] == 5:  # bio Kombileerung
                    entries_to_use.extend(
                        filter(lambda x: x["rhythmus"] == 2, type_entries))    
                else:
                    # add best fitting entry
                    sorted_type_entries = sorted(
                        type_entries, key=lambda x: x["rhythmus"], reverse=True)
                    entries_to_use.append(sorted_type_entries[0])

            
            collection_entries = []

            for entry in entries_to_use:

                exception_map = {datetime.strptime(key, "%d.%m.%Y"): datetime.strptime(
                    value, "%d.%m.%Y") for key, value in json.loads(entry["ausnahmen"]).items()}

                rythm_type = self._rythms[entry["typ"]
                                          ] if entry["typ"] in self._rythms else entry["rhythmus"]
                rythm = RYTHM_MAP[rythm_type]["rule"]

                dates: list[datetime] = self.__get_dates(
                    entry, year, rythm, today, days_by_type[entry["typ"]])

                for date in dates:
                    if date in exception_map:
                        date = exception_map[date]
                    if date.date() < today.date():
                        continue
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
