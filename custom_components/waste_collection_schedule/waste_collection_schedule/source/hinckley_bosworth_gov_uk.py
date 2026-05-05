import json
import re
from datetime import datetime, timedelta
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Hinckley & Bosworth Borough Council"
DESCRIPTION = "Source for Hinckley & Bosworth Borough Council."
URL = "https://www.hinckley-bosworth.gov.uk"

TEST_CASES = {
    "Test_House": {"uprn": "100030499851"},
}

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
    "Food": "mdi:food-apple",
}

PARAM_TRANSLATIONS = {
    "en": {"uprn": "Property UPRN (Unique Property Reference Number)"},
    "de": {"uprn": "UPRN der Immobilie"},
    "it": {"uprn": "UPRN della proprietà"},
    "fr": {"uprn": "UPRN du bien"},
}

PARAM_DESCRIPTIONS = {
    "en": {"uprn": "Find your UPRN at https://www.findmyaddress.co.uk/"},
    "de": {"uprn": "Finden Sie Ihre UPRN unter https://www.findmyaddress.co.uk/"},
    "it": {"uprn": "Trova il tuo UPRN su https://www.findmyaddress.co.uk/"},
    "fr": {"uprn": "Trovez votre UPRN sur https://www.findmyaddress.co.uk/"},
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        location_data = {
            "postcode": "",
            "myaddress": "",
            "uprn": self._uprn,
            "usrn": "",
            "ward": "",
            "parish": "",
            "lng": 0,
            "lat": 0,
        }
        cookie_value = quote(json.dumps(location_data, separators=(",", ":")))

        with requests.Session() as session:
            session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-GB,en;q=0.9",
                }
            )
            session.cookies.set(
                "mylocation", cookie_value, domain="www.hinckley-bosworth.gov.uk"
            )
            response = session.get(
                "https://www.hinckley-bosworth.gov.uk/collections",
                timeout=10,
            )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        date_containers = soup.find_all(
            "div", class_=re.compile(r"(first|last)_date_bins")
        )
        if not date_containers:
            raise ValueError(
                f"No collection containers found for UPRN {self._uprn} — page structure may have changed."
            )

        entries = []
        now = datetime.now()

        for container in date_containers:
            h3 = container.find("h3", class_="collectiondate")
            if not h3:
                continue

            raw_date = re.sub(r"[^a-zA-Z0-9 ]", "", h3.get_text(strip=True)).strip()
            try:
                date_obj = datetime.strptime(
                    f"{raw_date} {now.year}", "%A %d %B %Y"
                ).date()
                if date_obj < now.date() - timedelta(days=30):
                    date_obj = date_obj.replace(year=now.year + 1)
            except ValueError:
                continue

            for img in container.find_all("img"):
                title = (img.get("title") or img.get("alt") or "").lower()

                waste_type = None
                if "refuse" in title or "black" in title:
                    waste_type = "Refuse"
                elif "recycling" in title or "blue" in title or "lid" in title:
                    waste_type = "Recycling"
                elif "garden" in title or "brown" in title:
                    waste_type = "Garden"
                elif "food" in title or "caddy" in title:
                    waste_type = "Food"

                if waste_type:
                    entries.append(
                        Collection(
                            date=date_obj,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                        )
                    )

        return entries
