import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaft Landkreis Harburg"
DESCRIPTION = "Abfallwirtschaft Landkreis Harburg"
URL = "https://www.landkreis-harburg.de"

TEST_CASES = {
    "CityWithTwoLevels": {"level_1": "Hanstedt", "level_2": "Evendorf"},
    "CityWithThreeLevels": {
        "level_1": "Buchholz",
        "level_2": "Buchholz mit Steinbeck (ohne Reindorf)",
        "level_3": "Seppenser Mühlenweg Haus-Nr. 1 / 2",
    },
}

API_URL = (
    "https://www.landkreis-harburg.de/bauen-umwelt/abfallwirtschaft/abfallkalender/"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)",
}


class Source:
    def __init__(self, level_1, level_2, level_3=None):
        self._districts = [level_1, level_2, level_3]
        self._ics = ICS()

    def fetch(self):
        # Use a session to keep cookies and stuff
        session = requests.Session()

        # Get the IDs of the districts on the first level
        # Double loading is on purpose because sometimes the webpage has an overlay
        # which is gone on the second try in a session
        r = session.get(API_URL, headers=HEADERS)
        r.raise_for_status()
        if "Zur aufgerufenen Seite" in r.text:
            r = session.get(API_URL, headers=HEADERS)
            r.raise_for_status()

        # Get the IDs of the districts on the first level
        id = self.parse_level(r.text, 1)

        # Get the IDs of the districts on the second level
        url = (
            "https://www.landkreis-harburg.de/ajax/abfall_gebiete_struktur_select.html"
        )
        params = {
            "parent": id,
            "ebene": 1,
            "portal": 1,
            "selected_ebene": 0,
        }
        r = session.get(url, params=params, headers=HEADERS)
        r.raise_for_status()

        # Get the IDs of the districts on the second level
        id = self.parse_level(r.text, 2)

        # Get the IDs of the third level - if applicable
        if self._districts[3 - 1] is not None:
            # Get the IDs of the districts on the third level
            params = {
                "parent": id,
                "ebene": 2,
                "portal": 1,
                "selected_ebene": 0,
            }
            r = session.get(url, params=params, headers=HEADERS)
            r.raise_for_status()

            # Get the IDs of the districts on the third level
            id = self.parse_level(r.text, 3)

        # Prepare data for the real web request
        url = "https://www.landkreis-harburg.de/abfallkalender/abfallkalender_struktur_daten_suche.html"
        params = {
            "selected_ebene": id,
            "owner": 20100,
        }
        r = session.get(url, params=params, headers=HEADERS)
        r.raise_for_status()

        # Sometimes there is no garbage calendar available
        if "Es sind keine Abfuhrbezirke hinterlegt." in r.text:
            raise Exception(
                f'Error: "Es sind keine Abfuhrbezirke hinterlegt." for "{self._districts[3-1]}". Please use different input data.'
            )

        soup = BeautifulSoup(r.text, features="html.parser")
        links = soup.find_all("a")
        ical_urls = []
        for any_link in links:
            if " als iCal" in any_link.text:
                # multiple links occur during year transition
                ical_urls.append(any_link.get("href"))

        # Get the final data for all links
        entries = []
        for ical_url in ical_urls:
            r = requests.get(ical_url, headers=HEADERS)
            r.raise_for_status()

            # Parse ics file
            try:
                dates = self._ics.convert(r.text)

                for d in dates:
                    entries.append(Collection(d[0], d[1]))
            except ValueError:
                pass  # during year transition the ical for the next year may be empty
        return entries

    def parse_level(self, response, level):
        soup = BeautifulSoup(response, features="html.parser")
        select_content = soup.find_all("select", id=f"strukturEbene{level}")
        soup = BeautifulSoup(str(select_content), features="html.parser")
        options_content = soup.find_all("option")
        level_ids = {}
        for option in options_content:
            # Ignore the "Bitte wählen..."
            if option.get("value") != "0":
                level_ids[option.text] = option.get("value")

        if level_ids == {}:
            raise Exception(f"Error: Level {level} Dictionary empty")

        if self._districts[level - 1] not in level_ids:
            raise Exception(
                f"Error: District {self._districts[level]} is not in the dictionary: {level_ids}"
            )

        return level_ids[self._districts[level - 1]]
