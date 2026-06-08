import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons

TITLE = "Harlow Council"
DESCRIPTION = "Source for harlow.gov.uk, Harlow Council, UK"
URL = "https://www.harlow.gov.uk"
TEST_CASES = {
    "12 Kingfisher Gate, Old Harlow": {"uprn": 10033891501},
    "4 Ryecroft, Harlow": {"uprn": 100090544008},
    "2 The Crescent, Harlow": {"uprn": 100090546627},
    "1 Kerril Croft, Harlow": {"uprn": 10003708086},
}

API_URL = "https://selfserve.harlow.gov.uk/appshost/firmstep/self/apps/custompage/bincollectionsecho?uprn={uprn}"

ICON_MAP = {
    "Non-Recycling": Icons.GENERAL_WASTE,
    "Food Caddy": Icons.BIO_KITCHEN,
    "Recycling": Icons.RECYCLING,
    "Green Waste Subscription": Icons.GARDEN,
    "Communal Non-Recycling": Icons.GENERAL_WASTE,
    "Communal Recycling": Icons.RECYCLING,
}


class Source:
    def __init__(self, uprn=None):
        self._uprn = uprn

    def fetch(self):
        q = str(API_URL).format(uprn=self._uprn)

        r = requests.get(q)
        r.raise_for_status()

        responseContent = r.text

        entries = []

        soup = BeautifulSoup(responseContent, "html.parser")
        x = soup.findAll("div", {"class": "row collectionsrow"})
        for row in x:
            fields = row.findChildren()
            if (
                fields[0].text.strip()
                == "Please select an address to view the upcoming collections."
            ):
                continue

            entries.append(
                Collection(
                    date=datetime.datetime.strptime(
                        fields[3].text, "%a - %d %b %Y\n"
                    ).date(),
                    t=fields[2].text,
                    icon=ICON_MAP.get(fields[2].text),
                )
            )

        return entries
