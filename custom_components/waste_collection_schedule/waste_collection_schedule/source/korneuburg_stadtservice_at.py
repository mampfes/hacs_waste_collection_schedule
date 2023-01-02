import json
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS # type: ignore[attr-defined]

TITLE = "Stadtservice Korneuburg"
DESCRIPTION = "Source for Stadtservice Korneuburg"
URL = "https://www.korneuburg.gv.at"
TEST_CASES = {
    "Rathaus": {"street_name": "Hauptplatz", "street_number": 39},  # Teilgebiet 4
    "Rathaus using Teilgebiet": {
        "street_name": "SomeStreet",
        "street_number": "1A",
        "teilgebiet": "4",
    },  # Teilgebiet 4
    "Werft": {"street_name": "Am Hafen", "street_number": 6},  # Teilgebiet 2
}

# Mapping of teilgebiete to calendar urls
WASTE_TYPE_URLS = {
    "1": ("Biomuell_3", "Restmuell_3", "Papier_2", "Gelber_Sack_4"),
    "2": ("Biomuell_4", "Restmuell_2", "Papier_3", "Gelber_Sack_1"),
    "3": ("Biomuell_1", "Restmuell_1", "Papier_1", "Gelber_Sack_2"),
    "4": ("Biomuell_2", "Restmuell", "Papier", "Gelber_Sack_3"),
}


class Source:
    def __init__(self, street_name, street_number, teilgebiet=-1):
        self.street_name = street_name
        self.street_number = street_number
        self.teilgebiet = teilgebiet

        self._region = None
        self._street_name_id = -1
        self._street_number_id = -1
        self._headers = {"User-Agent": "Mozilla/5.0"}
        self._cookies = {"ris_cookie_setting": "g7750"}  # Accept Cookie Consent
        self._ics = ICS()

    @staticmethod
    def extract_street_numbers(soup):

        scripts = soup.findAll("script", {"type": "text/javascript"})

        street_number_idx = 0
        for s in scripts:
            if s.string and "var strassenArr" in s.string:
                break
            street_number_idx += 1

        possible_numbers = json.loads(
            scripts[street_number_idx]
            .string[19:]
            .replace("\r\n", "")
            .replace(", ]", "]")
            .replace("'", '"')
        )

        number_dict = dict()

        for idx, street_id in enumerate(possible_numbers):
            number_dict[street_id[0]] = {
                e[1]: (e[0], e[2]) for _idx, e in enumerate(possible_numbers[idx][1])
            }

        return number_dict

    @staticmethod
    def extract_street_names(soup):
        street_selector = soup.find(
            "select", {"id": "225991280_boxmuellkalenderstrassedd"}
        ).findAll("option")
        available_streets = {
            street.string: int(street["value"])
            for _idx, street in enumerate(street_selector)
        }

        return available_streets

    @staticmethod
    def extract_region(soup):
        region = -1

        for span in soup.findAll("span"):
            if span.parent.name == "td" and "teilgebiet" in span.string.lower():
                region = span.string.split(" ")[1]
                break

        return region

    def determine_region(self):
        """finds the target region for the street and street number"""

        if 0 < int(self.teilgebiet) <= 4:
            return str(self.teilgebiet)

        # request address selection form
        url = urljoin(URL, "Rathaus/Buergerservice/Muellabfuhr")
        page = requests.get(url=url, headers=self._headers, cookies=self._cookies)
        soup = BeautifulSoup(page.content, "html.parser")

        # extract possible street and number combinations from html source
        available_streets = self.extract_street_names(soup)
        number_dict = self.extract_street_numbers(soup)

        street_found = self.street_name in available_streets.keys()

        if not street_found:
            raise Exception(
                f"{self.street_name} not found. Please check back spelling with the official site: {url}"
            )

        self._street_name_id = available_streets.get(self.street_name)

        self._street_number_id, street_number_link = number_dict.get(
            available_streets.get(self.street_name)
        ).get(str(self.street_number), (-1, "not found"))

        if street_number_link == "not found":
            raise Exception(
                f"{self.street_number} not found. Available numbers for {self.street_name} are\
             {list(number_dict.get(available_streets['Am Hafen']).keys())}"
            )

        # add selection cookie
        self._cookies["riscms_muellkalender"] = str(
            f"{self._street_name_id}_{self._street_number_id}"
        )

        # request overview with address selection to get the region
        url = urljoin(URL, "system/web/kalender.aspx")
        page = requests.get(
            url=url,
            headers=self._headers,
            cookies=self._cookies,
            params={
                "sprache": "1",
                "menuonr": "225991280",
                "typids": street_number_link,
            },
        )
        soup = BeautifulSoup(page.content, "html.parser")

        region = self.extract_region(soup)

        if region == -1:
            raise Exception("Region could not be found")

        return str(region)

    def get_region_links(self):
        """traverses the pages for different waste types and collects download links for the iCals"""

        if self._region is None:
            self._region = self.determine_region()

        # create waste type urls
        ical_urls = []
        urls = [urljoin(URL, u) for u in WASTE_TYPE_URLS.get(self._region)]

        for u in urls:
            r = requests.get(url=u, headers=self._headers, cookies=self._cookies)
            soup = BeautifulSoup(r.content, "html.parser")
            download_link = soup.findAll(
                "a",
                {
                    "class": "piwik_download_tracker",
                    "data-trackingtyp": "iCal/Kalender",
                },
            )
            if len(download_link):
                ical_urls.append(urljoin(URL, download_link[0].get("href")))

        return ical_urls

    def process_waste_type(self, url):
        """downloads one calendar and returns list with entries"""

        r = requests.get(url=url, headers=self._headers, cookies=self._cookies)
        r.encoding = r.apparent_encoding

        dates = self._ics.convert(r.text)

        entries = [Collection(d[0], d[1]) for d in dates]

        return entries

    def fetch(self):

        ical_urls = self.get_region_links()
        all_entries = []

        for ical in ical_urls:
            entries = self.process_waste_type(url=ical)
            all_entries = all_entries + entries

        return all_entries
