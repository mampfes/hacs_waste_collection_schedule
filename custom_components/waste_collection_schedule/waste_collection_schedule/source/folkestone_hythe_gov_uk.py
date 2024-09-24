from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Folkestone and Hythe District Councol"
DESCRIPTION = "Source for Folkestone and Hythe District Council, United Kingdom."
URL = "https://www.folkestone-hythe.gov.uk/"
TEST_CASES = {
    "Folkestone_Test": {"uprn": 50032102},
    "Hythe_Test": {"uprn": "50019287"},
}
ICON_MAP = {
    "Non-Recyclables (Green Lid) and Food Waste": "mdi:trash-can",
    "Recycling (Purple Lid / Black Box and Food Waste)": "mdi:recycle",
}
REGEX_ORDINALS = r"(?<=\d)(st|nd|rd|th)"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self):

        s = requests.Session()
        r = s.get(
            f"https://service.folkestone-hythe.gov.uk/webapp/myarea/index.php?uprn={self._uprn}"
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        bin_tab = soup.findAll("div", {"id": "bincollections"})
        waste_types = bin_tab[0].findAll("span", {"class": "bold"})
        schedules = bin_tab[0].findAll("ul")

        entries = []

        for idx, item in enumerate(waste_types):
            for li in schedules[idx].findAll("li"):
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            re.compile(REGEX_ORDINALS).sub(" ", li.text), "%A %d %B %Y"
                        ).date(),
                        t=item.text,
                        icon=ICON_MAP.get(item.text),
                    )
                )

        return entries
