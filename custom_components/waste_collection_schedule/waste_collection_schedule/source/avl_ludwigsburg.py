import requests
import json
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS
from bs4 import BeautifulSoup

TITLE = "avl-ludwigsburg.de"
DESCRIPTION = "Abfallverwertungsgesellschaft des Landkreises Ludwigsburg mbH"
URL = "https://www.avl-ludwigsburg.de/privatkunden/termine/abfallkalender/suche/"

TEST_CASES = {
    "CityWithoutStreet": {
        "city": "Möglingen",
    },
    "CityWithStreet": {
        "city": "Ludwigsburg",
        "street": "Bahnhofstraße",
    },
}

class Source:
    def __init__(self, city, street=None):
        self._city = city
        self._street = street
        self._ics = ICS()

    def fetch(self):
        # Get the hidden parameters by loading the page
        s = requests.Session()
        response = s.get(URL)
        soup = BeautifulSoup(response.text, features="html.parser")
        hidden_tags = soup.find_all("input", type="hidden")
        
        # Prepare data for the real web request
        data = {}
        for tag in hidden_tags:
            data[tag.get("name")] = tag.get("value")
        
        # Find the cities which do need a street name
        data_cities_with_streets = soup.find_all("input", type="text", placeholder="Ort eingeben")
        cities_with_streets = ""
        for tag in data_cities_with_streets:
            cities_with_streets += tag.get("data-cities-with-streets")
        cities_with_streets = cities_with_streets.split(",")
        
        data['tx_avlcollections_pi5[wasteCalendarLocationItem]']= self._city
        data['tx_avlcollections_pi5[wasteCalendarStreetItem]']= self._street
        
        # Remove some data which the webserver doesn't like
        data.pop('id', None)
        data.pop('tx_kesearch_pi1[page]', None)
        data.pop('tx_kesearch_pi1[resetFilters]', None)
        data.pop('tx_kesearch_pi1[sortByField]', None)
        data.pop('tx_kesearch_pi1[sortByDir]', None)

        # Depending on the city remove the street from the data set
        if self._city.lower() not in cities_with_streets:
            data.pop('tx_avlcollections_pi5[wasteCalendarStreetItem]', None)

        # Creat the headers and cookies
        headers = {}

        cookies = {
            'agree': 'false',
            'track_ga': 'false',
        #    '_ga': 'GA1.2.783849652.1646596236',
        #    '_gid': 'GA1.2.801427368.1646596236',
        }

        # Get the final data
        response = s.post(URL, data=data, headers=headers, cookies=cookies)

        # Stop if something else as status code 200 is returned
        if response.status_code != 200:
            raise Exception(
                "Error: failed to fetch url: {}".format(
                    URL
                )
            )

        if response.text.find("Ort konnte nicht gefunden werden.") != -1:
            raise Exception(
                "Error: Ort konnte nicht gefunden werden."
            )

        if response.text.find("Straße konnte nicht gefunden werden.") != -1:
            raise Exception(
                "Error: Ort konnte nicht gefunden werden."
            )

        if response.text.find(".ics") == -1:
            raise Exception(
                "Error: No ics link found."
            )

        soup = BeautifulSoup(response.text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        ics_link = ""
        for download in downloads:
            link = download.get("href")
            if ".ics" in link:
                ics_link = link
        full_url = ("https://www.avl-ludwigsburg.de" + ics_link)
        return self.fetch_ics(full_url)

    def fetch_ics(self, url):
        r = requests.get(url, headers={
            "Referer": URL
        })

        if not r.ok:
            raise Exception(
                "Error: failed to fetch url: {}".format(
                    url
                )
            )
        
        # Parse ics file, fix broken encoding dynamically - if necessary
        if r.encoding!="uf-8":
            dates = self._ics.convert(r.text.encode(r.encoding).decode("utf-8"))
        else:
            dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
