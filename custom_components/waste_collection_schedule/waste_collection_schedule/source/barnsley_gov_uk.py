# Credit where it's due:
# This is predominantly a refactoring of the Bristol City Council script from the UKBinCollectionData repo
# https://github.com/robbrad/UKBinCollectionData


from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Barnsley Metropolitan Borough Council"
DESCRIPTION = "Source for Barnsley Metropolitan Borough Council."
URL = "https://barnsley.gov.uk"
TEST_CASES = {
    "S71 1EE 100050671689": {"postcode": "S71 1EE", "uprn": 100050671689},
    "S75 1QF 10032783992": {"postcode": "S75 1QF", "uprn": "10032783992"},
}


ICON_MAP = {
    "grey": "mdi:trash-can",
    "green": "mdi:leaf",
    "blue": "mdi:package-variant",
    "brown": "mdi:recycle",
}


API_URL = "https://waste.barnsley.gov.uk/ViewCollection/SelectAddress"


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode: str = postcode
        self._uprn: str | int = uprn

    def fetch(self):
        entries = []

        # Pass in form data and make the POST request
        headers = {
            "authority": "waste.barnsley.gov.uk",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-GB,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://waste.barnsley.gov.uk",
            "pragma": "no-cache",
            "referer": "https://waste.barnsley.gov.uk/ViewCollection/SelectAddress",
            "sec-ch-ua": '"Chromium";v="118", "Opera GX";v="104", "Not=A?Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.118 Safari/537.36",
        }
        form_data = {
            "personInfo.person1.HouseNumberOrName": "",
            "personInfo.person1.Postcode": f"{self._postcode}",
            "personInfo.person1.UPRN": f"{self._uprn}",
            "person1_SelectAddress": "Select address",
        }
        response = requests.post(
            "https://waste.barnsley.gov.uk/ViewCollection/SelectAddress",
            headers=headers,
            data=form_data,
        )
        soup = BeautifulSoup(response.text, features="html.parser")
        soup.prettify()

        if response.status_code != 200:
            raise ConnectionRefusedError(
                "Error getting results from website! Please open an issue on GitHub!"
            )

        # Parse the response, getting the top box first and then tabled collections after
        results = soup.find("div", {"class": "panel"}).find_all("fieldset")[0:2]
        heading = results[0].find_all("p")[1:3]
        bin_text = heading[1].text.strip() + " bin"
        bin_date = datetime.strptime(heading[0].text, "%A, %B %d, %Y").date()
        entries.append(
            Collection(
                t=bin_text,
                date=bin_date,
                icon=ICON_MAP.get(bin_text.split(" ")[0].lower()),
            )
        )

        results_table = [row for row in results[1].find_all("tbody")[0] if row != "\n"]
        for row in results_table:
            text_list = [item.text.strip() for item in row.contents if item != "\n"]
            bin_text = text_list[1] + " bin"
            bin_date = datetime.strptime(text_list[0], "%A, %B %d, %Y").date()
            entries.append(
                Collection(
                    t=bin_text,
                    date=bin_date,
                    icon=ICON_MAP.get(bin_text.split(" ")[0].lower()),
                )
            )

        return entries
