"""Source for Předměřice nad Labem, Czech Republic."""

import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Předměřice nad Labem"
DESCRIPTION = "Source for Předměřice nad Labem, Czech Republic."
URL = "https://www.predmericenl.cz/odpady"
COUNTRY = "cz"

TEST_CASES = {
    "Předměřice nad Labem": {},
}

SOURCE_CODEOWNERS = ["@ArzykDev"]

ICON_MAP = {
    "Směsný komunální odpad": Icons.GENERAL_WASTE,
    "Plasty": Icons.PLASTIC_PACKAGING,
    "Papír a lepenky": Icons.PAPER,
}

# Header cell carries a 6-digit waste-catalogue code prefix, e.g.
# "200301 Směsný komunální odpad" — capture the name after the code.
WASTE_TYPE_RE = re.compile(r"^\d{6}\s+(.+)$")
DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")


class Source:
    def __init__(self):
        pass

    def fetch(self) -> list[Collection]:
        r = requests.get(URL, timeout=30)
        r.raise_for_status()
        r.encoding = "utf-8"

        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table", class_="svozovy_plan")
        if not tables:
            raise ValueError("No collection schedule tables found on the page.")

        entries: list[Collection] = []
        for table in tables:
            waste_type = None
            for td in table.find_all("td"):
                text = td.get_text(strip=True)
                match = WASTE_TYPE_RE.match(text)
                if match:
                    waste_type = match.group(1)
                    break
            if waste_type is None:
                continue

            icon = ICON_MAP.get(waste_type)
            for td in table.find_all("td"):
                text = td.get_text(strip=True)
                if DATE_RE.match(text):
                    date = datetime.strptime(text, "%d.%m.%Y").date()
                    entries.append(Collection(date=date, t=waste_type, icon=icon))

        if not entries:
            raise ValueError("No collection dates found on the page.")

        return entries
