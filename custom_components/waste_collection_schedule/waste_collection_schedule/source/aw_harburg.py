import requests
import json
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS
from bs4 import BeautifulSoup

TITLE = "AW Harburg"
DESCRIPTION = "Abfallwirtschaft Landkreis Harburg"
URL = "https://www.landkreis-harburg.de/bauen-umwelt/abfallwirtschaft/abfallkalender/"

TEST_CASES = {
    "CityWithTwoLevels": {
        "district_level_1": "Hanstedt",
        "district_level_2": "Evendorf",
    },
    "CityWithThreeLevels": {
        "district_level_1": "Buchholz",
        "district_level_2": "Buchholz mit Steinbeck (ohne Reindorf)",
        "district_level_3": "Seppenser Mühlenweg Haus-Nr. 1 / 2",
    },
}

class Source:
    def __init__(self, district_level_1, district_level_2, district_level_3=None):
        self._district_level_1 = district_level_1
        self._district_level_2 = district_level_2
        self._district_level_3 = district_level_3
        self._ics = ICS()

    def fetch(self):
        # Use a session to keep cookies and stuff
        s = requests.Session()
        
        # Creat some fake header because for some reason people seem to believe it is bad
        # to read public garbage collection data via a script
        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Opera";v="84"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 OPR/84.0.4316.21',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Accept-Language': 'de-DE,de;q=0.9',
        }

        # Get the IDs of the districts on the first level
        # Double loading is on purpose because sometimes the webpage has an overlay
        # which is gone on the second try in a session
        response = s.get(URL, headers=headers)
        if "Zur aufgerufenen Seite" in response.text:
            response = s.get(URL, headers=headers)
        if response.status_code != 200:
            raise Exception(
                "Error: failed to fetch first url: {}".format(
                    URL
                )
            )
        soup = BeautifulSoup(response.text, features="html.parser")
        select_content = soup.find_all("select", id="strukturEbene1")
        soup = BeautifulSoup(str(select_content), features="html.parser")
        options_content = soup.find_all("option")
        level_1_ids = {}
        for option in options_content:
            # Ignore the "Bitte wählen..."
            if option.get("value")!="0":
                level_1_ids[option.text] = option.get("value")
        if level_1_ids == {}:
            raise Exception(
                "Error: Level 1 Dictionary empty"
                )
        if self._district_level_1 not in level_1_ids:
            raise Exception(
                "Error: District 1 is not in the dictionary: {}".format(
                    (self._district_level_1, level_1_ids)
                )
            )

        # Get the IDs of the districts on the second level
        url = 'https://www.landkreis-harburg.de/ajax/abfall_gebiete_struktur_select.html?parent=' + level_1_ids[self._district_level_1] + '&ebene=1&portal=1&selected_ebene=0'
        
        response = s.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(
                "Error: failed to fetch second url: {}".format(
                    url
                )
            )
        soup = BeautifulSoup(response.text, features="html.parser")
        select_content = soup.find_all("select", id="strukturEbene2")
        soup = BeautifulSoup(str(select_content), features="html.parser")
        options_content = soup.find_all("option")
        level_2_ids = {}
        for option in options_content:
            # Ignore the "Bitte wählen..."
            if option.get("value")!="0":
                level_2_ids[option.text] = option.get("value")
        if level_2_ids == {}:
            raise Exception(
                "Error: Level 2 Dictionary empty"
                )
        if self._district_level_2 not in level_2_ids:
            raise Exception(
                "Error: District 2 is not in the dictionary: {}".format(
                    (self._district_level_2, level_2_ids)
                )
            )

        # Get the IDs of the third level - if applicable
        if self._district_level_3 != None:
            # Get the IDs of the districts on the third level
            url = 'https://www.landkreis-harburg.de/ajax/abfall_gebiete_struktur_select.html?parent=' + level_2_ids[self._district_level_2] + '&ebene=2&portal=1&selected_ebene=0'
            
            response = s.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(
                    "Error: failed to fetch third url: {}".format(
                        url
                    )
                )
            soup = BeautifulSoup(response.text, features="html.parser")
            select_content = soup.find_all("select", id="strukturEbene3")
            soup = BeautifulSoup(str(select_content), features="html.parser")
            options_content = soup.find_all("option")
            level_3_ids = {}
            for option in options_content:
                # Ignore the "Bitte wählen..."
                if option.get("value")!="0":
                    level_3_ids[option.text] = option.get("value")
            if level_3_ids == {}:
                raise Exception(
                    "Error: Level 3 Dictionary empty"
                    )
            if self._district_level_3 not in level_3_ids:
                raise Exception(
                    "Error: District 3 is not in the dictionary: {}".format(
                        (self._district_level_3, level_3_ids)
                    )
                )

        # Prepare data for the real web request
        if self._district_level_3 != None:
            url = 'https://www.landkreis-harburg.de/abfallkalender/abfallkalender_struktur_daten_suche.html?selected_ebene=' + level_3_ids[self._district_level_3] + '&owner=20100'
        else:
            url = 'https://www.landkreis-harburg.de/abfallkalender/abfallkalender_struktur_daten_suche.html?selected_ebene=' + level_2_ids[self._district_level_2] + '&owner=20100'

        response = s.get(url, headers=headers)
        # Sometimes there is no garbage calendar available
        if "Es sind keine Abfuhrbezirke hinterlegt." in response.text:
            raise Exception(
                "Error: \"Es sind keine Abfuhrbezirke hinterlegt.\" for \"" + self._district_level_3 + "\" please use different input data."
            )
        soup = BeautifulSoup(response.text, features="html.parser")
        links = soup.find_all("a")
        ical_url = ""
        for any_link in links:
            if " als iCal" in any_link.text:
                ical_url = any_link.get("href")

        if "ical.html" not in ical_url:
            raise Exception(
                "No ical Link in the result: " + str(links)
            )

        # Get the final data
        response = s.post(ical_url, headers=headers)

        # Stop if something else as status code 200 is returned
        if response.status_code != 200:
            raise Exception(
                "Error: failed to fetch ical_url: {}".format(
                    ical_url
                )
            )

        return self.fetch_ics(ical_url, headers=headers)

    def fetch_ics(self, url, headers={}):
        r = requests.get(url, headers=headers)

        if not r.ok:
            raise Exception(
                "Error: failed to fetch url: {}".format(
                    url
                )
            )
        
        # Parse ics file, fix broken encoding
        if r.encoding=="ISO-8859-1":
            dates = self._ics.convert(r.text.encode("latin_1").decode("utf-8"))
        else:
            dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
