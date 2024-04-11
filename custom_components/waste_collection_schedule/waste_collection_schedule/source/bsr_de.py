import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Berliner Stadtreinigungsbetriebe"
DESCRIPTION = "Source for Berliner Stadtreinigungsbetriebe waste collection."
URL = "https://bsr.de"
TEST_CASES = {
    "Bahnhofstr., 12159 Berlin (Tempelhof-Schöneberg)": {
        "abf_strasse": "Bahnhofstr., 12159 Berlin (Tempelhof-Schöneberg)",
        "abf_hausnr": 1,
    },
    "Am Ried, 13467 Berlin (Reinickendorf)": {
        "abf_strasse": "Am Ried, 13467 Berlin (Reinickendorf)",
        "abf_hausnr": "11G",
    },
}


def initializeSession(abf_strasse, abf_hausnr):
    s = requests.Session()

    s.get("https://www.bsr.de/abfuhrkalender-20520.php")

    # # start search using street name (without PLZ)
    args = {"script": "dynamic_search", "step": 1, "q": abf_strasse.split(",")[0]}
    s.get("https://www.bsr.de/abfuhrkalender_ajax.php", params=args)

    # retrieve house number list
    args = {"script": "dynamic_search", "step": 2, "q": abf_strasse}
    s.get("https://www.bsr.de/abfuhrkalender_ajax.php", params=args)

    return s


def downloadMonthlyICS(s, abf_strasse, abf_hausnr, month, year):
    args = {
        "abf_strasse": abf_strasse.split(",")[0],
        "abf_hausnr": abf_hausnr,
        "tab_control": "Monat",
        "abf_config_weihnachtsbaeume": "",
        "abf_config_restmuell": "on",
        "abf_config_biogut": "on",
        "abf_config_wertstoffe": "on",
        "abf_config_laubtonne": "on",
        "abf_selectmonth": f"{month} {year}",
    }
    s.post(
        "https://www.bsr.de/abfuhrkalender_ajax.php?script=dynamic_kalender_ajax",
        data=args,
    )

    args["script"] = "dynamic_iCal_ajax"
    args["abf_strasse"] = abf_strasse
    r = s.get("https://www.bsr.de/abfuhrkalender_ajax.php", params=args)
    return r.text


def downloadChristmastreeICS(s, abf_strasse, abf_hausnr):
    args = {
        "abf_strasse": abf_strasse.split(",")[0],
        "abf_hausnr": abf_hausnr,
        "tab_control": "Liste",
        "abf_config_weihnachtsbaeume": "on",
        "abf_config_restmuell": "",
        "abf_config_biogut": "",
        "abf_config_wertstoffe": "",
        "abf_config_laubtonne": "",
    }

    s.post(
        "https://www.bsr.de/abfuhrkalender_ajax.php?script=dynamic_kalender_ajax",
        data=args,
    )

    args["script"] = "dynamic_iCal_ajax"
    args["abf_strasse"] = abf_strasse
    r = s.get("https://www.bsr.de/abfuhrkalender_ajax.php", params=args)
    return r.text


class Source:
    def __init__(self, abf_strasse, abf_hausnr):
        self._abf_strasse = abf_strasse
        self._abf_hausnr = abf_hausnr
        self._ics = ICS(offset=1)

    def fetch(self):
        dates = []

        session = initializeSession(self._abf_strasse, self._abf_hausnr)

        now = datetime.datetime.now()

        # fetch monthly ics files for the next 12 months
        for i in range(12):
            month, year = now.month + i, now.year
            if month > 12:
                month = month % 12
                year = year + 1

            ics = downloadMonthlyICS(
                session, self._abf_strasse, self._abf_hausnr, month, year
            )
            dates.extend(self._ics.convert(ics))

        if now.month in [12, 1]:
            # have to reinitialize session and address search for fetching christmas tree collection schedules, otherwise it doesn't work
            sessionChristmastrees = initializeSession(
                self._abf_strasse, self._abf_hausnr
            )
            ics = downloadChristmastreeICS(
                sessionChristmastrees, self._abf_strasse, self._abf_hausnr
            )
            dates.extend(self._ics.convert(ics))

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
