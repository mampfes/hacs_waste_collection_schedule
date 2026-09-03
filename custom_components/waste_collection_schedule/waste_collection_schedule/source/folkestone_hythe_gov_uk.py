import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Folkestone and Hythe District Councol"
DESCRIPTION = "Source for Folkestone and Hythe District Council, United Kingdom."
URL = "https://www.folkestone-hythe.gov.uk/"
TEST_CASES = {
    "Folkestone_Test": {"uprn": 50032102},
    "Hythe_Test": {"uprn": "50019287"},
}
ICON_MAP = {
    "Non-Recyclables (Green Lid) and Food Waste": Icons.BIO_KITCHEN,
    "Recycling (Purple Lid / Black Box and Food Waste)": Icons.BIO_KITCHEN,
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
        bin_tab = soup.find("div", {"id": "bincollections"})
        if bin_tab is None:
            # The page answers 200 with no collections panel at all for a UPRN
            # the council does not hold. Subscripting the empty result set
            # raised "list index out of range", which tells the visitor
            # nothing about what to correct.
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "Folkestone and Hythe returned no bin collections for this "
                "UPRN. Check it against the council's own address search.",
            )
        waste_types = bin_tab.findAll("span", {"class": "bold"})
        schedules = bin_tab.findAll("ul")

        entries = []

        for idx, item in enumerate(waste_types):
            if idx >= len(schedules):
                # A waste type listed with no dates beneath it.
                continue
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
