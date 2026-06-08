import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
)

TITLE = "Castle Point Borough Council"
DESCRIPTION = "Source for Castle Point Borough Council waste collections."
URL = "https://www.castlepoint.gov.uk"
COUNTRY = "uk"

TEST_CASES = {
    "ABBOTSWOOD": {"roadID": "4448"},
    "Ash Road": {"street_name": "Ash Road"},
    "St Marys Road": {"street_name": "St Marys Road"},
}

API_URLS = {
    "fetch_schedule": "https://apps.castlepoint.gov.uk/cpapps/index.cfm?fa=myStreet.displayDetails&roadID=",
    "find_road": "https://apps.castlepoint.gov.uk/cpapps/index.cfm?fa=myStreet.search",
}

ICON_MAP = {
    "Organic and Residual (Food/Garden/non-recyclable (black sack))": Icons.GENERAL_WASTE,
    "Recycling (Food/Garden/Pink sack/Glass)": Icons.RECYCLING,
}

NAME_MAP = {
    "normal": "Organic and Residual (Food/Garden/non-recyclable (black sack))",
    "pink": "Recycling (Food/Garden/Pink sack/Glass)",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Go to https://apps.castlepoint.gov.uk/cpapps/index.cfm?fa=myStreet&f=homepage1 "
        "either enter your street name in the search box or select the first letter of your street. "
        "Click on the street name and look for the roadID in the URL."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "roadID": "Your roadID retrieved from the URL after selecting your street.",
        "street_name": "The name of your street (only needed if you don't provide roadID).",
    }
}

PARAM_TRANSLATIONS = {"en": {"roadID": "Road ID", "street_name": "Street Name"}}


class Source:
    def __init__(self, roadID=None, street_name=None):
        if roadID is None and street_name is None:
            errors = []
            if roadID is None:
                errors.append("roadID")
            if street_name is None:
                errors.append("street_name")
            raise SourceArgumentExceptionMultiple(
                errors,
                "Either roadID or street_name is required to fetch waste collection schedule.",
            )

        self._roadID = roadID if roadID is not None else self._get_road_id(street_name)
        self._street_name = street_name

    def _get_road_id(self, street_name):
        session = requests.Session()
        search_url = API_URLS["find_road"]

        payload = {"searchterm": street_name}

        response = session.post(search_url, data=payload, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "roadID=" in href:
                params = href.split("?")[-1].split("&")
                for p in params:
                    if p.startswith("roadID="):
                        road_id = p.split("=")[1]
                        return road_id

        raise SourceArgumentNotFound(
            "street_name",
            street_name,
            f"Could not find a matching roadID for street name '{street_name}'.\nPlease check that the street name is correct and try again. If the problem persists, the council may have changed their website structure which would require an update to this integration.",
        )

    def fetch(self):
        url = f"{API_URLS['fetch_schedule']}{self._roadID}"
        session = requests.Session()
        response = session.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        # Find all tables or calendar container blocks on the page
        calendar_tables = soup.find_all("table", class_="calendar")

        for table in calendar_tables:
            # 1. Look for the header block specifically within this table container
            header = table.find("th")
            if not header:
                continue

            header_text = header.text.strip().lower()

            # Extract the month name
            month_match = re.search(
                r"(january|february|march|april|may|june|july|august|september|october|november|december)",
                header_text,
            )
            if not month_match:
                continue  # Skip tables that aren't calendar months (e.g., layout tables)

            month_name = month_match.group(1)
            month = datetime.strptime(month_name.capitalize(), "%B").month

            # Extract the year, defaulting to current year if missing
            year_match = re.search(r"\b(\d{4})\b", header_text)
            year = int(year_match.group(1)) if year_match else datetime.now().year

            # 2. Now scope your search for days ONLY inside this specific month's table
            day_elements = table.select(".pink, .normal")

            for element in day_elements:
                try:
                    day_text = re.search(r"\b(\d{1,2})\b", element.text)
                    if not day_text:
                        continue
                    day = int(day_text.group(1))

                    bin_type = (
                        NAME_MAP.get("pink")
                        if "pink" in element.get("class", [])
                        else NAME_MAP.get("normal")
                    )
                    date_obj = date(year, month, day)

                    entries.append(
                        Collection(
                            date=date_obj, t=bin_type, icon=ICON_MAP.get(bin_type)
                        )
                    )
                except ValueError:
                    continue
        if not entries:
            raise ValueError(
                "Could not get collections for the specified road. The page structure may have changed."
            )

        return entries
