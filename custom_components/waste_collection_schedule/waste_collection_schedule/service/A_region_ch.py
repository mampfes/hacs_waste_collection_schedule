from typing import Literal

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule.source.ics import Source as ICS

SERVICES = {
    "winterthur": "https://m.winterthur.ch",
    "a_region": "https://www.a-region.ch",
    "koeniz": "https://koeniz.citymobile.ch",
}
SERVICES_LITERALS = Literal["winterthur", "a_region", "koeniz"]


class A_region_ch:
    def __init__(
        self,
        service: SERVICES_LITERALS,
        region_url: str,
        district: str | None = None,
        regex: str | None = None,
    ):
        if service not in SERVICES:
            raise Exception(f"service '{service}' not found")
        self._base_url = SERVICES[service]

        self._regex = regex

        self._municipality_url = region_url
        self._district = district

    def fetch(self) -> list[ICS]:
        waste_types = self.get_waste_types(self._municipality_url)

        entries = []

        for tour, link in waste_types.items():
            entries += self.get_ICS_sources(link, tour)
        return entries

    def get_municipalities(self) -> dict[str, str]:
        municipalities: dict[str, str] = {}

        # get PHPSESSID
        session = requests.session()
        r = session.get(f"{self._base_url}")
        r.raise_for_status()

        # cookies = {'PHPSESSID': requests.utils.dict_from_cookiejar(r.cookies)['PHPSESSID']}

        params: dict[str, str | int] = {"apid": "13875680", "apparentid": "4618613"}
        r = session.get(f"{self._base_url}/index.php", params=params)
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
                f"{self._base_url}/appl/ajax/index.php", params=params, headers=headers
            )
            r.raise_for_status()
            if r.text == "":
                break
            self.extract_municipalities(r.text, municipalities)
            page = page + 1
        return municipalities

    def extract_municipalities(self, text: str, municipalities: dict[str, str]):
        soup = BeautifulSoup(text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        for download in downloads:
            # href ::= "/index.hp"
            href = download.get("href")
            if "ref=search" in href:
                for title in download.find_all("div", class_="title"):
                    # title ::= "Abfallkalender Andwil"
                    municipalities[title.string.removeprefix("Abfallkalender ")] = href

    def get_waste_types(self, link: str) -> dict[str, str]:
        if not link.startswith("http"):
            link = f"{self._base_url}{link}"
        r = requests.get(link)
        r.raise_for_status()

        waste_types = {}

        soup = BeautifulSoup(r.text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        for download in downloads:
            # href ::= "/index.php?apid=12731252&amp;apparentid=5011362"
            href = download.get("href")
            if download.find("div", class_="badgeIcon") or download.find(
                "img", class_="rowImg"
            ):
                titles = download.find_all("div", class_="title")
                if "PDF" in titles:
                    continue
                titles = [title.string for title in titles]
                if not titles:
                    titles = [download.get_text(strip=True)]
                for title in titles:
                    # title ::= "Altmetall"
                    waste_types[title] = href

        return waste_types

    def get_ICS_sources(self, link: str, tour: str) -> list[ICS]:
        if not link.startswith("http"):
            link = f"{self._base_url}{link}"
        r = requests.get(link)
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
                    district_name_split = title.string.split(": ")
                    districts[
                        district_name_split[1 if len(district_name_split) > 1 else 0]
                    ] = href
        if len(districts) > 0:
            if len(districts) == 1:
                # only one district found -> use it
                return self.get_ICS_sources(list(districts.values())[0], tour)
            if self._district is None:
                raise Exception("district is missing")
            if self._district not in districts:
                raise Exception(f"district '{self._district}' not found")
            return self.get_ICS_sources(districts[self._district], tour)

        dates = list()

        downloads = soup.find_all("a", href=True)
        for download in downloads:
            # href ::= "/appl/ics.php?apid=12731252&amp;from=2022-05-04%2013%3A00%3A00&amp;to=2022-05-04%2013%3A00%3A00"
            href = download.get("href")
            if href.startswith("webcal") and "ical.php" in href:
                dates.append(ICS(url=href, regex=self._regex))
                break

        return dates


def get_region_url_by_street(
    service: SERVICES_LITERALS,
    street: str,
    search_url: str,
    district: str | None = None,
    regex: str | None = None,
) -> A_region_ch:
    r = requests.get(search_url, params={"q": street})
    r.raise_for_status()

    soup = BeautifulSoup(r.text, features="html.parser")
    as_ = soup.select("a")
    if len(as_) == 0:
        raise Exception("No streets found")
    streets = []
    for a in as_:
        href = a.get("href")
        if not isinstance(href, str):
            continue
        streets.append(a.get_text(strip=True))

        if a.get_text(strip=True).lower().replace(" ", "") == street.lower().replace(
            " ", ""
        ):
            return A_region_ch(service, href, district, regex)

    raise Exception("Street not found, use one of")
