from bs4 import BeautifulSoup
from curl_cffi import requests
from dateutil.parser import parse
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Islington Council"
DESCRIPTION = "Source for Islington Council, UK."
URL = "https://www.islington.gov.uk"
TEST_CASES = {
    "Test_001": {"postcode": "n1 1xr", "uprn": "5300094897"},
    "Test_002": {"postcode": "N1 0DD", "uprn": 10001295652},
    "Test_003": {"postcode": "N19 4TA", "uprn": "5300078702"},
}
ICON_MAP = {
    "Green recycling box": Icons.RECYCLING,
    "Dry recycling bin": Icons.RECYCLING,
    "Communal dry recycling bin": Icons.RECYCLING,
    "Small kitchen waste box": Icons.BIO_KITCHEN,
    "Large brown kitchen waste box": Icons.BIO_KITCHEN,
    "Reuseable garden waste sack": Icons.GARDEN,
    "Household refuse sack": Icons.GENERAL_WASTE,
    "Refuse skip": Icons.COMMERCIAL,
    "Food waste recycling": Icons.BIO_KITCHEN,
    "Mixed dry recycling": Icons.RECYCLING,
    "Non-recyclable rubbish": Icons.GENERAL_WASTE,
}


class Source:
    def __init__(self, postcode, uprn):
        self._uprn = str(uprn)
        self._postcode = str(postcode)
        self._session = requests.Session(impersonate="chrome124")

    def fetch(self):
        url = f"https://www.islington.gov.uk/your-area?Postcode={self._postcode}&Uprn={self._uprn}"

        response = self._session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        waste_table = (
            soup.find(string="Waste and recycling collections")
            .find_next("div", class_="m-toggle-content")
            .find("table")
        )

        if waste_table:
            rows = waste_table.find_all("tr")
            for row in rows:
                waste_type = row.find("td").text.strip().split(",")[0].split(" - ")[0]
                collection_day = (
                    row.find("td").text.strip().split(",")[1].split(" on ")[1]
                )

                entries.append(
                    Collection(
                        date=parse(collection_day).date(),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
