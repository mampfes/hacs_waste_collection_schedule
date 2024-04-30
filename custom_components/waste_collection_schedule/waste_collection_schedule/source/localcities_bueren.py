import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from waste_collection_schedule import Collection

TITLE = "Büren an der Aare"
DESCRIPTION = "Waste collection schedule extraction for Büren an der Aare from Localcities.ch"
URL = "https://www.localcities.ch/de/entsorgung/bueren-an-der-aare/849"
COUNTRY = "ch"

TEST_CASES = {
    "Grünabfälle": {"waste_type": "Grünabfälle"},
    "Altpapier": {"waste_type": "Altpapier"},
    "Karton": {"waste_type": "Karton"}
}

ICON_MAP = {
    "Grünabfälle": "mdi:leaf",
    "Altpapier": "mdi:recycle",
    "Karton": "mdi:archive"
}


class Source:
    def __init__(self, waste_type):
        self.waste_type = waste_type

    def fetch(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the year from the webpage
        year_tag = soup.find("h1", text=lambda text: text and '2024' in text)
        year = year_tag.text.strip()[-4:] if year_tag else "2024"  # default to the current year if not found

        entries = []
        waste_class_mapping = {
            "Grünabfälle": "list-calendar-item--waste-green-waste",
            "Altpapier": "list-calendar-item--waste-paper",
            "Karton": "list-calendar-item--waste-cardboard"
        }

        waste_items = soup.find_all("div", {"class": waste_class_mapping.get(self.waste_type, "")})
        for item in waste_items:
            date_tag = item.find_previous("div", {"class": "col-4 col-md-2 text-md-right waste-calender-list__date"})
            if date_tag:
                date_text = date_tag.find("h2", {"class": "h3"}).text.strip()
                if date_text.lower() == "heute":
                    date = datetime.now().date()
                elif date_text.lower() == "morgen":
                    date = (datetime.now() + timedelta(days=1)).date()
                else:
                    date_str = date_text + "." + year
                    date = datetime.strptime(date_str, "%d.%m.%Y").date()

                entries.append(
                    Collection(
                        date=date,
                        t=self.waste_type,
                        icon=ICON_MAP.get(self.waste_type)
                    )
                )
        return entries


# Example usage
#source = Source("Grünabfälle")
#collections = source.fetch()
#for collection in collections:
#   print(f"Collection on: {collection.date}, Type: {collection.type}, Icon: {collection.icon}")
