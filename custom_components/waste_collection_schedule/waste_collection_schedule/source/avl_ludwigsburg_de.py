import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "avl-ludwigsburg.de"
DESCRIPTION = "Abfallverwertungsgesellschaft des Landkreises Ludwigsburg mbH"
URL = "https://www.avl-ludwigsburg.de/privatkunden/termine/abfallkalender/suche/"

TEST_CASES = {
    "CityWithoutStreet": {"city": "Möglingen"},
    "CityWithStreet": {"city": "Ludwigsburg", "street": "Bahnhofstraße"},
}


class Source:
    def __init__(self, city, street=None):
        self._city = city
        self._street = street
        self._ics = ICS()

    def fetch(self):
        # Get the hidden parameters by loading the page
        session = requests.Session()
        r = session.get(URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        hidden_tags = soup.find_all("input", type="hidden")

        # Prepare data for the real web request
        data = {}
        for tag in hidden_tags:
            data[tag.get("name")] = tag.get("value")

        # Find the cities which do need a street name
        data_cities_with_streets = soup.find_all(
            "input", type="text", placeholder="Ort eingeben"
        )
        cities_with_streets = ""
        for tag in data_cities_with_streets:
            cities_with_streets += tag.get("data-cities-with-streets")
        cities_with_streets = cities_with_streets.split(",")

        data["tx_avlcollections_pi5[wasteCalendarLocationItem]"] = self._city
        data["tx_avlcollections_pi5[wasteCalendarStreetItem]"] = self._street

        # Remove some data which the webserver doesn't like
        data.pop("id", None)
        data.pop("tx_kesearch_pi1[page]", None)
        data.pop("tx_kesearch_pi1[resetFilters]", None)
        data.pop("tx_kesearch_pi1[sortByField]", None)
        data.pop("tx_kesearch_pi1[sortByDir]", None)

        # Depending on the city remove the street from the data set
        if self._city.lower() not in cities_with_streets:
            data.pop("tx_avlcollections_pi5[wasteCalendarStreetItem]", None)

        # Get the final data
        r = session.post(URL, data=data)
        r.raise_for_status()

        if r.text.find("Ort konnte nicht gefunden werden.") != -1:
            raise Exception("Error: Ort konnte nicht gefunden werden.")

        if r.text.find("Straße konnte nicht gefunden werden.") != -1:
            raise Exception("Error: Ort konnte nicht gefunden werden.")

        if r.text.find(".ics") == -1:
            raise Exception("Error: No ics link found.")

        soup = BeautifulSoup(r.text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        ics_link = ""
        for download in downloads:
            link = download.get("href")
            if ".ics" in link:
                ics_link = link
        full_url = "https://www.avl-ludwigsburg.de" + ics_link
        return self.fetch_ics(full_url)

    def fetch_ics(self, url):
        r = requests.get(url)
        r.raise_for_status()

        # Parse ics file
        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
