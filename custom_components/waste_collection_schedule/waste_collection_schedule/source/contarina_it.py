from datetime import datetime
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Contarina"
DESCRIPTION = (
    "Waste collection provider in Treviso, Italy"
)
URL = "https://contarina.it/"

TEST_CASES = {
    "Trevignano": {"district": "Trevignano"},
    "Montebelluna": {"district": "Montebelluna"},
}

API_URL = f"{URL}cittadino/raccolta-differenziata/eco-calendario"

ICON_MAP = {
    "secco": "mdi:trash-can",
    "vpl": "mdi:recycle",
    "carta": "mdi:package-variant",
    "umido": "mdi:leaf",
    "vegetale": "mdi:leaf",
}

class Source:
    def __init__(self, district : str):
        self._disctrict = district.lower()
    
    def _find_district_table(self, soup: BeautifulSoup) -> BeautifulSoup:
        tables = soup.find_all("table", {"class": ["table", "comune"]})
        for table in tables:
            row = table.find_all("tr")[0]
            cells = row.find_all("td")
            print(f"cells: {cells}")
            if len(cells) > 0 and cells[0].text.strip().lower() == self._disctrict:
                return table
        return None

    def fetch(self) -> list[Collection]:
        print(f"Fetching {API_URL}...")
        # Fetch the page
        r = requests.get(API_URL)

        # Parse the page
        soup = BeautifulSoup(r.content, "html.parser")

        # Find the table that contains the given district
        # in the first column of the first row
        table = self._find_district_table(soup)

        if table is None:
            raise Exception(f"Could not find district {self._disctrict}")
        
        # The first cell of the second rows contains another table
        # with header "Date" and "Waste type"
        second_row = table.find_all("tr")[1]
        waste_table = second_row.find_all("table")[0]
        waste_rows = waste_table.find_all("tr")

        # Skip first row and parse the rest as collections
        # NOTE: there may be more than one collection per day
        collections = []
        for row in waste_rows[1:]:
            cells = row.find_all("td")
            date = datetime.strptime(cells[0].text.strip(), "%d-%m-%Y")
            paragraphs = cells[1].find_all("p")
            for paragraph in paragraphs:
                waste_text = paragraph.text.strip()
                icon = ICON_MAP[waste_text.lower()]
                collections.append(Collection(date, waste_text, icon))
        
        return collections
