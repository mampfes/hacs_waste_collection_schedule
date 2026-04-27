import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Zweckverband Abfallwirtschaft Kreis Bergstraße"
TITLE_LANG = "de"
DESCRIPTION = "Source for Zweckverband Abfallwirtschaft Kreis Bergstraße."
URL = "https://www.zakb.de"
TEST_CASES = {
    "Abtsteinach, Am Hofböhl 1 ": {
        "city": "Abtsteinach",
        "street": "Am Hofböhl",
        "house_number": "1",
        "hnr_zusatz": "",
    },
    "Gorxheimertal, Am Herrschaftswald 10": {
        "city": "Gorxheimertal",
        "street": "Am Herrschaftswald",
        "house_number": "10",
    },
    "Rimbach, Ahornweg 1 B": {
        "city": "Rimbach",
        "street": "Ahornweg",
        "house_number": "1",
        "hnr_zusatz": "B",
    },
    "Zwingenberg, Diefenbachstraße 57": {
        "city": "Zwingenberg",
        "street": "Diefenbachstraße",
        "house_number": 57,
        "hnr_zusatz": "",
    },
    "Bensheim im Bangert 9 a": {
        "city": "Bensheim",
        "street": "Im Bangert",
        "house_number": 9,
        "hnr_zusatz": "A",
    },
}

ICON_MAP = {
    "Restabfallbehaelter": "mdi:trash-can",
    "Restabfallcontainer": "mdi:trash-can",
    "Bioabfallbehaelter": "mdi:leaf",
    "Papierbehaelter": "mdi:package-variant",
    "Papiercontainer": "mdi:package-variant",
    "Gelber Sack": "mdi:recycle",
    "Gruensperrmuell": "mdi:forest",
}

API_URL = "https://www.zakb.de/online-service/abfallkalender/"


class Source:
    def __init__(
        self, city: str, street: str, house_number: str | int, hnr_zusatz: str = ""
    ):
        self._ort: str = city
        self._strasse: str = street
        self._hnr: str = str(house_number)
        self._hnr_zusatz: str = hnr_zusatz
        self._ics = ICS()

    def fetch(self):
        # inizilize session
        session = requests.Session()

        # make request to get session cookie
        r = session.get(API_URL)
        r.raise_for_status()

        args = {
            "aos[Ort]": self._ort,
            "aos[Strasse]": self._strasse,
            "aos[Hausnummer]": self._hnr,
            "aos[Hausnummerzusatz]": self._hnr_zusatz,
            "aos[CheckBoxRestabfallbehaelter]": "on",
            "aos[CheckBoxRestabfallcontainer]": "on",
            "aos[CheckBoxBioabfallbehaelter]": "on",
            "aos[CheckBoxPapierbehaelter]": "on",
            "aos[CheckBoxPapiercontainer]": "on",
            "aos[CheckBoxGruensperrmuell]": "on",
            "aos[CheckBoxGelber+Sack]": "on",
            "aos[CheckBoxDSD-Container]": "on",
            "submitAction": "CITYCHANGED",
            "pageName": "Lageadresse",
        }

        # make request to call CITYCHANGED
        r = session.post(API_URL, data=args)
        r.raise_for_status()

        # make request to set data for session
        args["submitAction"] = "nextPage"
        r = session.post(API_URL, data=args)
        r.raise_for_status()

        # make request to get ical file
        r = session.post(
            API_URL,
            data={"submitAction": "filedownload_ICAL", "pageName": "Terminliste"},
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1].strip(), ICON_MAP.get(d[1].strip())))
        return entries
