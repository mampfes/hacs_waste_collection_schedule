import datetime
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "A-Region"
DESCRIPTION = "Source for A-Region, Switzerland waste collection."
URL = "https://www.a-region.ch"


def EXTRA_INFO():
    return [{"title": m} for m in MUNICIPALITIES]


TEST_CASES = {
    "Andwil": {"municipality": "Andwil"},
    "Rorschach": {"municipality": "Rorschach", "district": "Unteres Stadtgebiet"},
    "Wolfhalden": {"municipality": "Wolfhalden"},
}

BASE_URL = "https://www.a-region.ch"

MUNICIPALITIES = {
    "Andwil": "/index.php?ref=search&refid=13875680&apid=5011362",
    "Appenzell": "/index.php?ref=search&refid=13875680&apid=7502696",
    "Berg": "/index.php?ref=search&refid=13875680&apid=3106981",
    "Bühler": "/index.php?ref=search&refid=13875680&apid=4946039",
    "Eggersriet": "/index.php?ref=search&refid=13875680&apid=7419807",
    "Gais": "/index.php?ref=search&refid=13875680&apid=7001813",
    "Gaiserwald": "/index.php?ref=search&refid=13875680&apid=9663627",
    "Goldach": "/index.php?ref=search&refid=13875680&apid=1577133",
    "Grub": "/index.php?ref=search&refid=13875680&apid=10619556",
    "Heiden": "/index.php?ref=search&refid=13875680&apid=13056683",
    "Herisau": "/index.php?ref=search&refid=13875680&apid=10697513",
    "Horn": "/index.php?ref=search&refid=13875680&apid=7102181",
    "Hundwil": "/index.php?ref=search&refid=13875680&apid=7705668",
    "Häggenschwil": "/index.php?ref=search&refid=13875680&apid=1590277",
    "Lutzenberg": "/index.php?ref=search&refid=13875680&apid=301262",
    "Muolen": "/index.php?ref=search&refid=13875680&apid=9000564",
    "Mörschwil": "/index.php?ref=search&refid=13875680&apid=12765590",
    "Rehetobel": "/index.php?ref=search&refid=13875680&apid=15824437",
    "Rorschach": "/index.php?ref=search&refid=13875680&apid=7773833",
    "Rorschacherberg": "/index.php?ref=search&refid=13875680&apid=13565317",
    "Schwellbrunn": "/index.php?ref=search&refid=13875680&apid=10718116",
    "Schönengrund": "/index.php?ref=search&refid=13875680&apid=8373248",
    "Speicher": "/index.php?ref=search&refid=13875680&apid=11899879",
    "Stein": "/index.php?ref=search&refid=13875680&apid=9964399",
    "Steinach": "/index.php?ref=search&refid=13875680&apid=16358152",
    "Teufen": "/index.php?ref=search&refid=13875680&apid=662596",
    "Thal": "/index.php?ref=search&refid=13875680&apid=5087375",
    "Trogen": "/index.php?ref=search&refid=13875680&apid=14835149",
    "Tübach": "/index.php?ref=search&refid=13875680&apid=6762782",
    "Untereggen": "/index.php?ref=search&refid=13875680&apid=5661056",
    "Urnäsch": "/index.php?ref=search&refid=13875680&apid=1891722",
    "Wald": "/index.php?ref=search&refid=13875680&apid=4214292",
    "Waldkirch": "/index.php?ref=search&refid=13875680&apid=15180335",
    "Waldstatt": "/index.php?ref=search&refid=13875680&apid=15561367",
    "Wittenbach": "/index.php?ref=search&refid=13875680&apid=13277954",
    "Wolfhalden": "/index.php?ref=search&refid=13875680&apid=5642491",
}


class Source:
    def __init__(self, municipality, district=None):
        self._municipality = municipality
        self._district = district

    def fetch(self):
        # municipalities = self.get_municipalities()
        municipalities = MUNICIPALITIES
        if self._municipality not in municipalities:
            raise Exception(f"municipality '{self._municipality}' not found")

        waste_types = self.get_waste_types(municipalities[self._municipality])

        entries = []

        for (waste_type, link) in waste_types.items():
            dates = self.get_dates(link)

            for d in dates:
                entries.append(Collection(d, waste_type))

        return entries

    def get_municipalities(self):
        municipalities = {}

        # get PHPSESSID
        session = requests.session()
        r = session.get(f"{BASE_URL}")
        r.raise_for_status()

        # cookies = {'PHPSESSID': requests.utils.dict_from_cookiejar(r.cookies)['PHPSESSID']}

        params = {"apid": "13875680", "apparentid": "4618613"}
        r = session.get(f"{BASE_URL}/index.php", params=params)
        r.raise_for_status()
        self.extract_municipalities(r.text, municipalities)

        page = 1
        while True:
            params = {
                "do": "searchFetchMore",
                "hash": "606ee79ca61fc6eef434ab4fca0d5956",
                "p": page,
            }
            headers = {
                "cookie": "PHPSESSID=71v67j0et4ih04qa142d402ebm;"
            }  # TODO: get cookie from first request
            r = session.get(
                f"{BASE_URL}/appl/ajax/index.php", params=params, headers=headers
            )
            r.raise_for_status()
            if r.text == "":
                break
            self.extract_municipalities(r.text, municipalities)
            page = page + 1
        return municipalities

    def extract_municipalities(self, text, municipalities):
        soup = BeautifulSoup(text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        for download in downloads:
            # href ::= "/index.hp"
            href = download.get("href")
            if "ref=search" in href:
                for title in download.find_all("div", class_="title"):
                    # title ::= "Abfallkalender Andwil"
                    municipalities[title.string.removeprefix("Abfallkalender ")] = href

    def get_waste_types(self, link):
        r = requests.get(f"{BASE_URL}{link}")
        r.raise_for_status()

        waste_types = {}

        soup = BeautifulSoup(r.text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        for download in downloads:
            # href ::= "/index.php?apid=12731252&amp;apparentid=5011362"
            href = download.get("href")
            if "apparentid" in href:
                for title in download.find_all("div", class_="title"):
                    # title ::= "Altmetall"
                    waste_types[title.string] = href

        return waste_types

    def get_dates(self, link):
        r = requests.get(f"{BASE_URL}{link}")
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")

        # check for additional districts
        districts = {}
        downloads = soup.find_all("a", href=True)
        for download in downloads:
            href = download.get("href")
            if "apparentid" in href:
                title = download.find("div", class_="title")
                if title is not None:
                    # additional district found ->
                    districts[title.string.split(": ")[1]] = href
        if len(districts) > 0:
            if self._district is None:
                raise Exception("district is missing")
            if self._district not in districts:
                raise Exception(f"district '{self._district}' not found")
            return self.get_dates(districts[self._district])

        dates = set()

        downloads = soup.find_all("a", href=True)
        for download in downloads:
            # href ::= "/appl/ics.php?apid=12731252&amp;from=2022-05-04%2013%3A00%3A00&amp;to=2022-05-04%2013%3A00%3A00"
            href = download.get("href")
            if "ics.php" in href:
                parsed = urlparse(href)
                query = parse_qs(parsed.query)
                date = datetime.datetime.strptime(query["from"][0], "%Y-%m-%d %H:%M:%S")
                dates.add(date.date())

        return dates
