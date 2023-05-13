import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

from datetime import datetime, timedelta
from dateutil import rrule
import json

TITLE = "Potsdam"
DESCRIPTION = "Source for Potsdam."
URL = "https://www.potsdam.de"
TEST_CASES = {
    "Golm Akazienweg mixed ": {
        "ortsteil": "Golm",
        "strasse": "Akazienweg",
        "rest_rhythm": 4,
        "papier_rhythm": 2,
        "bio_rhythm": 3,
    },
    "Teltower Vorstadt  Albert-Einstein-Str. 2": {
        "ortsteil": "Teltower Vorstadt",
        "strasse": "Albert-Einstein-Str.",
        "rest_rhythm": 1,
        "papier_rhythm": 3,
        "bio_rhythm": 5,
    },
    "Uetz  Kanalweg ": {
        "ortsteil": "Uetz",
        "strasse": "Kanalweg",
        "rest_rhythm": 4,
        "papier_rhythm": 4,
        "bio_rhythm": 2,
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

RHYTHM_MAP = {
    1: "2x pro Woche",
    2: "wöchentlich",
    3: "14-tägig",
    4: "4-wöchentlich",
    5: "Kombileerung",
}


API_URL = "https://www.geben-und-nehmen-markt.de/abfallkalender/potsdam/{year}/page-data/index/page-data.json"


class Source:
    def __init__(self, ortsteil: str, strasse: str, rest_rhythm: int = 0, papier_rhythm: int = 0, bio_rhythm: int = 0, gelb_rhythm: int = 3):
        self._ortsteil: str = ortsteil
        self._strasse: str = strasse
        self._rhythms = {
            1: int(rest_rhythm),
            2: int(bio_rhythm),
            3: int(gelb_rhythm),
            4: int(papier_rhythm),
        }

    def __get_entries_for_street(self, year: int, today: datetime) -> list[dict[str, str | int]] | None:
        try:
            # get json file
            r = requests.get(API_URL.format(year=year))
            r.raise_for_status()
        except:
            if year == today.year:
                raise Exception("culd not get data from url exit")
            return

        try:
            data = r.json()["result"]["data"]["dbapi"]
        except Exception as e:
            raise Exception("culd not decode server response") from e

        for ortsteil in data["allRegionen"][0]["regionen"][0]["ortsteile"]:
            if ortsteil["name"].lower().strip() != self._ortsteil.lower().strip():
                continue
            for strasse in ortsteil["strassen"]:
                if strasse["name"].lower().strip() != self._strasse.lower().strip():
                    continue
                return strasse["eintraege"]

    # generate dates, typematch and date_is_collection* are nearly 1:1 implementation of teir original crappy js code
    def __generate_dates(self, start, end):
        while start <= end:
            yield start
            start += timedelta(days=1)

    def __typematch(self, partm, partd, bin_type, turnus, schwarz, gruen, blau):
        startkombi = '0401'
        endekombi = '1031'

        return ((bin_type == 1) and (schwarz == turnus)) or \
            ((bin_type == 2) and ((gruen == turnus) or ((gruen == 5) and (((turnus == 2) and (partm + partd >= startkombi) and (partm + partd <= endekombi)) or ((turnus == 3) and ((partm + partd < startkombi) or (partm + partd > endekombi))))))) or \
            ((bin_type == 4) and (blau == turnus)) or \
            (bin_type == 3)

    def __date_is_collection(self, node, day: datetime, exceptions) -> bool:
        return self.__date_is_collection_1_to_4(node, day, exceptions) or self.__date_is_collection5_6(node, day)

    def __date_is_collection5_6(self, node, day: datetime) -> bool:
        if not node["typ"] in (5, 6):
            return False
        termin1 = datetime.fromisoformat(
            node["termin1"].replace("Z", "+00:00")).date()
        termin2 = datetime.fromisoformat(
            node["termin2"].replace("Z", "+00:00")).date()
        day = day.date()
        return (termin1 == day) or (termin2 == day)

    def __date_is_collection_1_to_4(self, node, day: datetime, exceptions, check_exception=True) -> bool:
        weekno = day.isocalendar()[1]
        weekeven = weekno % 2 == 0
        dow = day.weekday() + 1

        if check_exception:
            for e_from, e_to in exceptions.items():
                if day == e_from:
                    return False
                if day == e_to:
                    return self.__date_is_collection_1_to_4(node, e_from, exceptions, check_exception=False)

        return (((node["rhythmus"] == 1) and self.__typematch(day.strftime("%m"), day.strftime("%d"), node["typ"], 2, self._rhythms[1], self._rhythms[2], self._rhythms[4])) and (((node["tag1"] == dow) and (node["tag2"] == 0)) or (((node["tag1"] == dow) and not weekeven) or ((node["tag2"] == dow) and weekeven)))) or \
            (((node["rhythmus"] == 2) and self.__typematch(day.strftime("%m"), day.strftime("%d"), node["typ"], 3, self._rhythms[1], self._rhythms[2], self._rhythms[4])) and (((node["woche"] == 2) and not weekeven) or ((node["woche"] == 3) and weekeven)) and (node["tag1"] == dow)) or \
            (((node["rhythmus"] == 3) and self.__typematch(day.strftime("%m"), day.strftime("%d"), node["typ"], 4, self._rhythms[1], self._rhythms[2], self._rhythms[4])) and ((weekno - node["beginn"]) % 4 == 0) and (node["tag1"] == dow)) or \
            (((node["rhythmus"] == 4) and self.__typematch(day.strftime("%m"), day.strftime("%d"), node["typ"], 1, self._rhythms[1], self._rhythms[2], self._rhythms[4])) and ((node["tag1"] == dow) or ((node["tag2"] > 0) and (node["tag2"] == dow)))) and \
            (weekno >= node["beginn"])

    def fetch(self):
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        collections: list[Collection] = []

        years = [today.year]
        if today.month == 12:
            years.append(today.year + 1)

        for year in years:
            entries = self.__get_entries_for_street(year, today)
            if today.year != year:
                today = datetime(year, 1, 1)

            if entries is None:
                continue

            for entry in entries:
                exceptions = {datetime.strptime(d_from, "%d.%m.%Y"): datetime.strptime(d_to, "%d.%m.%Y") for d_from, d_to in json.loads(entry["ausnahmen"]).items()}
                icon = ICON_MAP.get(entry["typ"])
                type = TYPE_MAP.get(entry["typ"])
                rhythm_type = self._rhythms.get(entry["typ"])
                if (rhythm_type in RHYTHM_MAP):
                    type += " (" + RHYTHM_MAP.get(rhythm_type) + ")"

                for day in self.__generate_dates(today, datetime(year+1, 1, 1)):
                    if not self.__date_is_collection(entry, day, exceptions):
                        continue

                    collections.append(Collection(
                        date=day.date(), t=type, icon=icon))

        collections.sort(key=lambda x: x.date)
        return collections
