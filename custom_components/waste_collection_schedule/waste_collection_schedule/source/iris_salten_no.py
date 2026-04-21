import datetime
import urllib.parse

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Iris Salten"
DESCRIPTION = "Fetches waste collection schedule from Iris Salten (based on address)."
URL = "https://www.iris-salten.no"

# Tests to verify that the module works in Waste Collection Schedule
TEST_CASES = {"My address": {"address": "Alsosgården 11", "kommune": "Bodø kommune"}}

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:food-apple",
    "Papir": "mdi:package-variant",
    "Plast": "mdi:recycle",
    "Glass": "mdi:bottle-soda",
}

MONTH_MAP = {
    "januar": 1,
    "februar": 2,
    "mars": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}


class Source:
    def __init__(self, address: str, kommune: str = ""):
        self._address = address
        self._kommune = kommune

    def fetch(self):
        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
            }
        )

        # =========================================================
        # STEP 1: Find UUID for the address via JSON API
        # =========================================================
        safe_adresse = urllib.parse.quote(self._address)
        search_url = f"https://iris-salten.no/wp-content/themes/iris/data/location-search.php?query={safe_adresse}"

        r_search = s.get(search_url, timeout=30)
        r_search.raise_for_status()

        try:
            results = r_search.json()
        except ValueError as exc:
            raise ValueError(
                "Failed to read JSON data from Iris Salten address search."
            ) from exc

        uuid = None

        # Iterate through results and find an exact match for the address
        for result in results:
            if result.get("adresse", "").lower() == self._address.lower():
                # If municipality is provided in config, check it as well
                if self._kommune:
                    if self._kommune.lower() in result.get("kommune", "").lower():
                        uuid = result.get("id")
                        break
                else:
                    # If no municipality is provided, pick the first matching address
                    uuid = result.get("id")
                    break

        if not uuid:
            raise Exception(
                f"Found no valid ID for the address: {self._address}. Check your spelling."
            )

        # =========================================================
        # STEP 2: Fetch the actual calendar using the found UUID
        # =========================================================
        safe_address_param = urllib.parse.quote_plus(self._address)
        safe_kommune_param = urllib.parse.quote_plus(self._kommune)

        schedule_url = f"https://iris-salten.no/privat/tommeplan/?lookup={uuid}&address={safe_address_param}&municipality={safe_kommune_param}"

        r_schedule = s.get(schedule_url, timeout=30)
        r_schedule.raise_for_status()

        soup = BeautifulSoup(r_schedule.text, "html.parser")
        calendar_list = soup.select("ul.calendar__list li")

        entries = []

        for item in calendar_list:
            text = item.get_text(" ", strip=True)
            parts = text.split()

            if len(parts) < 4:
                continue

            try:
                day_str = parts[1].replace(".", "")
                month_str = parts[2].lower()

                # Keep the original casing for fallback, but use lower for searching
                waste_original = " ".join(parts[3:])
                waste_lower = waste_original.lower()

                day = int(day_str)
                month = MONTH_MAP.get(month_str)

                if not month:
                    continue

                now = datetime.date.today()
                year = now.year

                # Year rollover logic
                if month < now.month and (now.month - month) > 6:
                    year += 1
                elif month > now.month and (month - now.month) > 6:
                    year -= 1

                date_obj = datetime.date(year, month, day)

                # Check for multiple waste types on the same day independently,
                # and map them back to the exact descriptive names used by Iris Salten.
                found_any = False

                if "restavfall" in waste_lower:
                    entries.append(
                        Collection(
                            date=date_obj, t="Restavfall", icon=ICON_MAP["Restavfall"]
                        )
                    )
                    found_any = True

                if "matavfall" in waste_lower:
                    name = (
                        "Matavfall uten hageavfall"
                        if "uten hageavfall" in waste_lower
                        else "Matavfall"
                    )
                    entries.append(
                        Collection(date=date_obj, t=name, icon=ICON_MAP["Matavfall"])
                    )
                    found_any = True

                if "papir" in waste_lower:
                    name = "Papir og papp" if "og papp" in waste_lower else "Papir"
                    entries.append(
                        Collection(date=date_obj, t=name, icon=ICON_MAP["Papir"])
                    )
                    found_any = True

                if "plast" in waste_lower:
                    name = "Plastemballasje" if "emballasje" in waste_lower else "Plast"
                    entries.append(
                        Collection(date=date_obj, t=name, icon=ICON_MAP["Plast"])
                    )
                    found_any = True

                if "glass" in waste_lower or "metall" in waste_lower:
                    name = (
                        "Glass- og metallemballasje"
                        if "metallemballasje" in waste_lower
                        else "Glass og metall"
                    )
                    entries.append(
                        Collection(date=date_obj, t=name, icon=ICON_MAP["Glass"])
                    )
                    found_any = True

                # Fallback in case they add a new type of waste we haven't mapped yet
                if not found_any:
                    entries.append(
                        Collection(
                            date=date_obj, t=waste_original, icon=ICON_MAP["Restavfall"]
                        )
                    )

            except (ValueError, IndexError):
                # Ignore lines that fail during parsing
                continue

        return entries
