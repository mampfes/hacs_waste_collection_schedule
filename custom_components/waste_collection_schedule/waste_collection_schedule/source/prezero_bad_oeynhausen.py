import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS
from bs4 import BeautifulSoup

TITLE = "Abfallkalender Stadt Bad Oeynhausen"
DESCRIPTION = "Waste collection schedule for Bad Oeynhausen."
URL = "https://abfallkalender.prezero.network/bad-oeynhausen"
TEST_CASES = {
    "street": "Eidingsen",
    "houseNo": "6"
}

class Source:
    def __init__(self, street, houseNo):
        self._street = street
        self._houseNo = houseNo
        self._ics = ICS()

    def fetch(self):
        args = {"street": self._street, "houseNo": self._houseNo}

        response = requests.post(URL, data=args, verify=False)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            ical_form = soup.find('form', {'action': True, 'class': 'ical'})
            if not ical_form:
                raise ValueError("iCal form not found on the page.")

            ical_url = "https://abfallkalender.prezero.network" + ical_form['action']

            ical_response = requests.post(ical_url, data=args, verify=False)
            if ical_response.status_code != 200:
                raise ValueError(f"Failed to download iCal. Status code: {ical_response.status_code}")

            ical_data = ical_response.content.decode('utf-8')

            dates = self._ics.convert(ical_data)
            entries = []
            for d in dates:
                entries.append(Collection(d[0], d[1]))

            return entries
        else:
            raise ValueError(f"Failed to fetch calendar page. Status code: {response.status_code}")
