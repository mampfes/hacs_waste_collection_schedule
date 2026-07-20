import datetime
import re
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Lichfield District Council"
DESCRIPTION = "Source for Lichfield District Council, UK."
URL = "https://lichfielddc.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100031695248"},
    "Test_002": {"uprn": "100031704571"},
    "Test_003": {"uprn": "10002768095"},
    "Test_004": {"uprn": "100031699855"},
}
ICON_MAP = {
    "Black Bin": Icons.GENERAL_WASTE,
    "Blue Bin": Icons.RECYCLING,
    "Blue Sack": Icons.RECYCLING,
    "Purple Bin": Icons.RECYCLING,
    "Garden Bin": Icons.GARDEN,
    "Brown Bin": Icons.GARDEN,
    "Food Waste Caddy": Icons.BIO_KITCHEN,
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        response = requests.get(
            "https://www.lichfielddc.gov.uk/bincalendar",
            params={"uprn": self._uprn},
            headers={"User-Agent": "Mozilla"},
        )
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        boxes = soup.find_all("div",class_="boxed")

        for box in boxes:
            bdate_els = box.find_all("p",class_=re.compile("bin-collection-tasks__(date|frequency)"))
            if bdate_els:
                bdate_str = bdate_els[0].contents[-1].string
                bdate = parser.parse(bdate_str).date()
                bname_els = box.find_all("h3", class_="bin-collection-tasks__heading")
                bname = bname_els[0].contents[1]

                if (
                    bdate.month == 1
                    and datetime.date.today().month == 12
                    and bdate.year == datetime.date.today().year
                ):
                    bdate = bdate.replace(year=bdate.year + 1)

                entries.append(
                    Collection(
                        date=bdate,
                        t=bname,
                        icon=ICON_MAP.get(bname),
                    )
                )

        return entries
