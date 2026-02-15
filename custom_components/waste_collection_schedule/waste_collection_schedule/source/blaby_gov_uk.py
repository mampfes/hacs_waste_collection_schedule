TITLE = "Blaby District Council"
DESCRIPTION = "Recycling and refuse collection dates for Blaby District Council, UK."
URL = "https://my.blaby.gov.uk/collections"

import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

REGEX = r"\d{2}/\d{2}/\d{4}"

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
}

class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        r = session.get(
            "https://my.blaby.gov.uk/set-location.php",
            params={"ref": self._uprn, "redirect": "collections"},
            verify=False,
            timeout=30,
        )
        r.raise_for_status()

        r = session.get(
            "https://my.blaby.gov.uk/collections",
            verify=False,
            timeout=30,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        entries = []

        for h2 in soup.find_all("h2"):
            bin_type = h2.get_text(strip=True)
            if bin_type not in ICON_MAP:
                continue

            content = []
            for sib in h2.next_siblings:
                if getattr(sib, "name", None) == "h2":
                    break
                if hasattr(sib, "get_text"):
                    content.append(sib.get_text(" ", strip=True))

            text = " ".join(content)
            for d in re.findall(REGEX, text):
                entries.append(
                    Collection(
                        t=bin_type,
                        date=datetime.strptime(d, "%d/%m/%Y").date(),
                        icon=ICON_MAP[bin_type],
                    )
                )

        return entries