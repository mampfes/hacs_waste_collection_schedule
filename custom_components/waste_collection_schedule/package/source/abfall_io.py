import csv
import datetime

import requests

from ..helpers import CollectionAppointment

DESCRIPTION = "Source for AbfallPlus.de based services. Service is hosted on abfall.io"
URL = "https://www.abfallplus.de"
TEST_CASES = {
    "Waldenbuch": {
        "key": "8215c62763967916979e0e8566b6172e",
        "f_id_kommune": 2999,
        "f_id_strasse": 1087,
        # "f_abfallarten": [50, 53, 31, 299, 328, 325]
    },
    "Landshut": {
        "key": "bd0c2d0177a0849a905cded5cb734a6f",
        "f_id_kommune": 2655,
        "f_id_bezirk": 2655,
        "f_id_strasse": 763,
        # "f_abfallarten": [31, 17, 19, 218]
    },
    "Schoenmackers": {
        "key": "e5543a3e190cb8d91c645660ad60965f",
        "f_id_kommune": 3682,
        "f_id_strasse": "3682adenauerplatz",
        "f_id_strasse_hnr": "20417",
        # "f_abfallarten": [691,692,696,695,694,701,700,693,703,704,697,699],
    },
}

MODUS_KEY = "d6c5855a62cf32a4dadbc2831f0f295f"
HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


class Source:
    def __init__(
        self,
        key,
        f_id_kommune,
        f_id_strasse,
        f_id_bezirk=None,
        f_id_strasse_hnr=None,
        f_abfallarten=[],
    ):
        self._key = key
        self._kommune = f_id_kommune
        self._bezirk = f_id_bezirk
        self._strasse = f_id_strasse
        self._strasse_hnr = f_id_strasse_hnr
        self._abfallarten = f_abfallarten  # list of integers

    def fetch(self):
        args = {"f_id_kommune": self._kommune, "f_id_strasse": self._strasse}

        if self._bezirk is not None:
            args["f_id_bezirk"] = self._bezirk

        if self._strasse_hnr is not None:
            args["f_id_strasse_hnr"] = self._strasse_hnr

        for i in range(len(self._abfallarten)):
            args[f"f_id_abfalltyp_{i}"] = self._abfallarten[i]

        args["f_abfallarten_index_max"] = len(self._abfallarten)
        args["f_abfallarten"] = ",".join(map(lambda x: str(x), self._abfallarten))

        now = datetime.datetime.now()
        date2 = now.replace(year=now.year + 1)
        args["f_zeitraum"] = f"{now.strftime('%Y%m%d')}-{date2.strftime('%Y%m%d')}"

        params = {"key": self._key, "modus": MODUS_KEY, "waction": "export_csv"}

        # get csv file
        r = requests.post(
            f"https://api.abfall.io", params=params, data=args, headers=HEADERS
        )

        # prepare csv reader
        reader = csv.reader(r.text.split("\n"), dialect="unix", delimiter=";")

        fieldnames = []  # contains type of waste, e.g. Restmuell, Biomuell, ...

        entries = []
        for line in reader:
            if reader.line_num == 1:
                # store file names from 1st row
                fieldnames = line
            else:
                # process all cells,
                for idx, cell in enumerate(line):
                    if cell != "":
                        # ignore empty cell
                        date = datetime.datetime.strptime(cell, "%d.%m.%Y").date()
                        entries.append(CollectionAppointment(date, fieldnames[idx]))

        return entries
