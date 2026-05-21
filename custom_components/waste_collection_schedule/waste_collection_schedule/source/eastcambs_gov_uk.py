import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons

TITLE = "East Cambridgeshire District Council"
DESCRIPTION = "Source for eastcambs.gov.uk, East Cambridgeshire District Council, UK"
URL = "https://www.eastcambs.gov.uk"
TEST_CASES = {
    "East Cambridgeshire District Council, CB7 4EE": {"uprn": 10002597178},
}

API_URL = "https://eastcambs-self.achieveservice.com/appshost/firmstep/self/apps/custompage/bincollections?uprn={uprn}"

ICON_MAP = {
    "Black Bag": Icons.GENERAL_WASTE,
    "Blue Bin": Icons.RECYCLING,
    "Green or Brown Bin": Icons.BIO_KITCHEN,
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
                        fields[3].text, "%a - %d %b %Y"
                    ).date(),
                    t=fields[2].text,
                    icon=ICON_MAP.get(fields[2].text),
                )
            )

        return entries
