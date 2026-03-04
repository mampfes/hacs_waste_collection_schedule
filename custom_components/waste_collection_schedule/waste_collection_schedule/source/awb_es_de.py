import ssl

import cloudscraper
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaftsbetrieb Esslingen"
DESCRIPTION = "Source for AWB Esslingen, Germany"
URL = "https://www.awb-es.de"

TEST_CASES = {
    "Aichwald": {"city": "Aichwald", "street": "Alte Dorfstraße Alle Hausnummern"},
    "Kohlberg": {"city": "Kohlberg", "street": "alle Straßen"},
}


class Source:
    def __init__(self, city: str, street: str | None = None):
        self._city = city
        self._street = street
        self._ics = ICS()

    def _validate_city(self) -> None:
        data = {
            "search": self._city,
            "parent": "",
            "kind": "removaldate.city",
        }
        r = self._session.post(
            "https://www.awb-es.de/statics/abfallplus/search.json.php",
            data=data,
        )
        r.raise_for_status()
        suggestsion = r.json()["suggestions"]
        for suggestion in suggestsion:
            if suggestion["value"].lower() == self._city.lower():
                return

        raise SourceArgumentNotFoundWithSuggestions(
            "city",
            self._city,
            suggestions=[suggestion["value"] for suggestion in suggestsion],
        )

    def _validate_street(self) -> None:
        data = {
            "search": self._street,
            "parent": self._city,
            "kind": "removaldate.street",
        }
        r = self._session.post(
            "https://www.awb-es.de/statics/abfallplus/search.json.php", data=data
        )
        r.raise_for_status()
        suggestsion = r.json()["suggestions"]
        for suggestion in suggestsion:
            assert self._street is not None
            if suggestion["value"].lower() == self._street.lower():
                return
        raise SourceArgumentNotFoundWithSuggestions(
            "street",
            self._street,
            suggestions=[suggestion["value"] for suggestion in suggestsion],
        )

    def fetch(self) -> list[Collection]:
        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("DEFAULT@SECLEVEL=1")
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        self._session = cloudscraper.create_scraper(ssl_context=ssl_context)

        params = {
            "city": self._city,
            "street": self._street,
            "direct": "true",
        }
        r = self._session.get(
            "https://www.awb-es.de/abfuhr/abfuhrtermine/__Abfuhrtermine.html",
            params=params,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        ics_urls = list()
        for download in downloads:
            href = download.get("href")
            if (
                "t=ics" in href and href not in ics_urls
            ):  # The website lists the same url multiple times, we only want it once
                ics_urls.append(href)

        if not ics_urls:
            self._validate_city()
            self._validate_street()
            raise Exception("ics url not found")

        entries = []
        for ics_url in ics_urls:
            # get ics file
            r = self._session.get(ics_url)
            r.raise_for_status()

            # parse ics file
            dates = self._ics.convert(r.text)

            for d in dates:
                entries.append(Collection(d[0], d[1]))

        return entries
