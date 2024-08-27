from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Dover District Council"
DESCRIPTION = "Source for Dover District Council."
URL = "https://www.dover.gov.uk"
TEST_CASES = {
    "200002423404": {"uprn": 200002423404},
    "100060905828": {"uprn": "100060905828"},
}


ICON_MAP = {
    "Garden Waste Collection": "mdi:leaf",
    "Food Collection": "mdi:food-apple",
    "Refuse Collection": "mdi:trash-can",
    "Paper/Card Collection": "mdi:package-variant",
    "Recycling Collection": "mdi:recycle",
}


API_URL = "https://collections.dover.gov.uk/"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self) -> list[Collection]:
        # copy of haringey_gov_uk.py just some minor changes
        api_url = f"https://collections.dover.gov.uk/property/{self._uprn}"
        response = requests.get(api_url)

        soup = BeautifulSoup(response.text, features="html.parser")
        soup.prettify()

        entries = []

        service_elements = soup.select(".service-wrapper")

        for service_element in service_elements:
            service_name = service_element.select(".service-name")[0].text.strip()

            next_service_dates = service_element.select(
                "td.next-service"
            ) + service_element.select("td.last-service")
            if len(next_service_dates) == 0:
                continue
            for next_service_date in next_service_dates:
                next_service_date.span.extract()

                if next_service_date.text.strip().strip("-") == "":
                    continue

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
