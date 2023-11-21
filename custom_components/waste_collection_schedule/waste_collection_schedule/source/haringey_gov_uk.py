from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Haringey Council"
DESCRIPTION = "Source for haringey.gov.uk services for Haringey Council, UK."
URL = "https://www.haringey.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": "100021209182"},
    "Test_002": {"uprn": "100021207181"},
    "Test_003": {"uprn": "100021202738"},
    "Test_004": {"uprn": 100021202131},
}
ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Collect Domestic Recycling": "mdi:recycle",
    "Food Waste": "mdi:food-apple",
    "Collect Paid Domestic Garden": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        api_url = f"https://wastecollections.haringey.gov.uk/property/{self._uprn}"
        response = requests.get(api_url)

        soup = BeautifulSoup(response.text, features="html.parser")
        soup.prettify()

        entries = []

        service_elements = soup.select(".service-wrapper")

        for service_element in service_elements:
            service_name = service_element.select(".service-name")[0].text.strip()
            next_service_date = service_element.select("td.next-service")[0]

            next_service_date.span.extract()

            entries.append(
                Collection(
                    date=datetime.strptime(
                        next_service_date.text.strip(), "%d/%m/%Y"
                    ).date(),
                    t=service_name,
                    icon=ICON_MAP.get(service_name),
                )
            )

        return entries
