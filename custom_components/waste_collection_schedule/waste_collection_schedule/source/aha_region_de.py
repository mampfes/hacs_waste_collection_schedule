import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
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
}

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bioabfall": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Leichtverpackungen": "mdi:recycle",
}

API_URL = "https://www.aha-region.de/abholtermine/abfuhrkalender"


class Source:
    def __init__(
        self, gemeinde: str, strasse: str, hnr: str | int, zusatz: str | int = ""
    ):
        self._gemeinde: str = gemeinde
        self._strasse: str = strasse
        self._hnr: str = str(hnr)
        self._zusatz: str = str(zusatz)
        self._ics = ICS()

    def fetch(self):
        # find strassen_id
        r = requests.get(
            API_URL, params={"gemeinde": self._gemeinde, "von": "A", "bis": "["}
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
            raise Exception(
                "Street not found for gemeinde: "
                + self._gemeinde
                + " and strasse: "
                + self._strasse
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
        # find all ICAL download buttons
        download_buttons = soup.find_all("button", {"name": "ical_apple"})

        if not download_buttons:
            raise Exception(
                "Invalid response from server, check you configuration if it is correct."
            )

        entries = []

        for button in download_buttons:
            # get form data and request ICAL file for every waste type
            args = {}
            args["ical_apple"] = button["value"]
            form = button.parent
            for input in form.find_all("input"):
                args[input["name"]] = input["value"]

            r = requests.post(API_URL, data=args)
            r.encoding = "utf-8"

            dates = self._ics.convert(r.text)

            for d in dates:
                bin_type = d[1].replace("Abfuhr", "").strip()
                entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))

        return entries
