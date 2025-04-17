import logging

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Zweckverband Abfallwirtschaft Region Hannover"
DESCRIPTION = "Source for Zweckverband Abfallwirtschaft Region Hannover."
URL = "https://www.aha-region.de/"
TEST_CASES = {
    "Neustadt a. Rbge., Am Rotdorn / Nöpke, 1 ": {
        "gemeinde": "Neustadt a. Rbge.",
        "strasse": "Am Rotdorn / Nöpke",
        "hnr": 1,
    },
    "Isernhagen, Am Lohner Hof / Isernhagen Fb, 10": {
        "gemeinde": "Isernhagen",
        "strasse": "Am Lohner Hof / Isernhagen Fb",
        "hnr": "10",
    },
    "Hannover, Voltastr. / Vahrenwald, 25": {
        "gemeinde": "Hannover",
        "strasse": "Voltastr. / Vahrenwald",
        "hnr": "25",
    },
    "Hannover, Melanchthonstr., 10A": {
        "gemeinde": "Hannover",
        "strasse": "Melanchthonstr.",
        "hnr": "10",
        "zusatz": "A",
    },
    "Mit Ladeort": {
        "gemeinde": "Gehrden",
        "strasse": "Kirchstr. / Gehrden",
        "hnr": "1",
        "ladeort": "Kirchstr. 6, Gehrden / Gehrden",
    },
}

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bioabfall": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Leichtverpackungen": "mdi:recycle",
}

API_URL = "https://www.aha-region.de/abholtermine/abfuhrkalender"
LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self,
        gemeinde: str,
        strasse: str,
        hnr: str | int,
        zusatz: str | int = "",
        ladeort=None,
    ):
        self._gemeinde: str = gemeinde
        self._strasse: str = strasse
        self._hnr: str = str(hnr)
        self._zusatz: str = str(zusatz)
        self._ladeort: str | None = ladeort
        self._ics = ICS()

    def fetch(self):
        # find strassen_id
        r = requests.get(
            API_URL, params={"gemeinde": self._gemeinde, "von": self._strasse[0]}
        )
        r.raise_for_status()

        strassen_id = None
        selects = (
            BeautifulSoup(r.text, "html.parser")
            .find("select", {"id": "strasse"})
            .find_all("option")
        )
        for select in selects:
            if select.text.lower().replace(" ", "") == self._strasse.lower().replace(
                " ", ""
            ):
                strassen_id = select["value"]
                break

        if not strassen_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "strasse", self._strasse, [select.text for select in selects]
            )

        # request overview page
        args = {
            "gemeinde": self._gemeinde,
            "jsaus": "",
            "strasse": strassen_id,
            "hausnr": self._hnr,
            "hausnraddon": self._zusatz,
            "anzeigen": "Suchen",
        }

        r = requests.post(API_URL, data=args)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        ladeort_single = soup.find("input", {"name": "ladeort"})

        if not ladeort_single:
            ladeort_select = soup.find("select", {"name": "ladeort"})
            if not ladeort_select:
                raise Exception("No ladeort found")
            ladeort_options = ladeort_select.find_all("option")
            if not self._ladeort:
                raise SourceArgumentRequiredWithSuggestions(
                    "ladeort",
                    "Ladeort required for this address",
                    [ladeort_option.text for ladeort_option in ladeort_options],
                )
            for ladeort_option in ladeort_options:
                if ladeort_option.text.lower().replace(
                    " ", ""
                ) == self._ladeort.lower().replace(" ", ""):
                    ladeort_single = ladeort_option
                    break
            if not ladeort_single:
                raise SourceArgumentNotFoundWithSuggestions(
                    "ladeort",
                    self._ladeort,
                    [ladeort_option.text for ladeort_option in ladeort_options],
                )

        del args["anzeigen"]
        args["ladeort"] = ladeort_single["value"]
        args["ical"] = "ICAL Jahresübersicht"

        r = requests.post(API_URL, data=args)
        r.raise_for_status()
        r.encoding = "utf-8"
        try:
            dates = self._ics.convert(r.text)
        except ValueError as e:
            raise Exception("got invalid ics file") from e
        entries = []
        for d in dates:
            bin_type = d[1].replace("Abfuhr", "").strip()
            entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))

        return entries
