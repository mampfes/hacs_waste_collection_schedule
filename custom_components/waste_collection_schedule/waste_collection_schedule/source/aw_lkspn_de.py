import datetime
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

# URL, DESCRIPTION  and TITLE of the website
TITLE = "Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße"
DESCRIPTION = "Source for Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße."
URL = "https://www.eigenbetrieb-abfallwirtschaft.de"
COUNTRY = "de"
TEST_CASES = {
    "Forst (Lausitz), Rosenweg": {"city": "4", "street": "344"},
    "Peitz, Am See": {"city": "8", "street": "1077"},
    "Guben, Altsprucke": {"city": "5", "street": "410"},
}

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biotonne": "mdi:leaf",
    "Papiercontainer": "mdi:package-variant",
    "Gelbe(r) Sack/Tonne": "mdi:recycle",
}

class Source:
    def __init__(self, city: str, street: str):
        self._city: str = city
        self._street: str = street
        self._ics = ICS()

    def fetch(self):
        # get the current year
        now = datetime.datetime.now()
        year = now.year
        # build the urls and fetch the data ...
        # for this year ...
        url_this_year = f"{URL}/termine/abfuhrtermine/{year}/{self._city}/{self._street}.html"
        entries = self.get_data(url_this_year)
        # and in december for the next year
        if now.month == 12:
            try:
                url_next_year = f"{URL}/termine/abfuhrtermine/{year +1 }/{self._city}/{self._street}.html"
                entries += self.get_data(url_next_year)
            except Exception:
                pass
        return entries

    def get_data(self, url):
        # download the site
        response = requests.get(url)

        # check if the request was successful
        if response.status_code == 200:
            # parse the response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # check for an input element named 'ics'
            input_element = soup.find('input', {'name': 'ics'})
            
            # check if the input element was found
            if input_element:
                # try to find the parent form
                form = input_element.find_parent('form')
                
                # check if the parent form was found
                if form:
                    # extract the formular inputs
                    form_data = {}
                    for input_tag in form.find_all('input'):
                        name = input_tag.get('name')
                        value = input_tag.get('value', '')
                        form_data[name] = value
                    
                    # Die URL für die Formularübermittlung extrahieren (relative URL zu vollständiger URL konvertieren)
                    action_url = URL + form.get('action')

                    # send the formular to fetch the ics file
                    response = requests.post(action_url, data=form_data)
                    response.raise_for_status()
                    response.encoding = "utf-8"
                    # process the response
                    dates = self._ics.convert(response.text)
                    entries = []
                    for d in dates:
                        icon = ICON_MAP.get(d[1].split(" ")[0])
                        if icon is None:
                            icon = ICON_MAP.get(d[1])
                        entries.append(Collection(d[0], d[1], icon=icon))

                    return entries
                else:
                    raise Exception("Didn't find the ics request formular.")
            else:
                raise Exception("Didn't find the input named ics.")
        else:
            raise Exception(f"Error loading page {URL}, status code {response.status_code}.")
