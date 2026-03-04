import datetime
import json
import logging
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Gmina Zgierz"
DESCRIPTION = "Source for Gmina Zgierz garbage collection"
URL = "https://gminazgierz.pl"
TEST_CASES = {
    "Grotniki": {"location_name": "Grotniki"},
    "Biała": {"location_name": "Biała"},
    "Kębliny": {"location_name": "Kębliny"},
    "Rosanów": {"location_name": "Rosanów"},
}

_LOGGER = logging.getLogger(__name__)

API_URL = "https://bip.gminazgierz.pl/api/articles/59717"

ICON_MAP = {
    "Segregowane i zmieszane": "mdi:trash-can",
    "BIO": "mdi:recycle",
    "Gabaryty": "mdi:cupboard",
}

MONTH_MAP = {
    "styczeń": 1,
    "stycznia": 1,
    "luty": 2,
    "lutego": 2,
    "marzec": 3,
    "marca": 3,
    "kwiecień": 4,
    "kwietnia": 4,
    "maj": 5,
    "maja": 5,
    "czerwiec": 6,
    "czerwca": 6,
    "lipiec": 7,
    "lipca": 7,
    "sierpień": 8,
    "sierpnia": 8,
    "wrzesień": 9,
    "września": 9,
    "październik": 10,
    "października": 10,
    "listopad": 11,
    "listopada": 11,
    "grudzień": 12,
    "grudnia": 12,
}


class Source:
    def __init__(self, location_name: str):
        self.location_name = location_name.strip().title()

    def fetch(self) -> list[Collection]:
        try:
            r = requests.get(API_URL)
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            raise Exception("Error fetching or parsing data") from e

        html_content = data.get("content")
        if not html_content:
            raise Exception("HTML content not found in JSON response")

        soup = BeautifulSoup(html_content, "html.parser")

        # --- Step 1: Find the region for the given location ---
        found_region_name = None
        search_location_lower = self.location_name.lower()
        for p_tag in soup.find_all("p"):
            if search_location_lower in p_tag.get_text().lower():
                strong_tag = p_tag.find("strong")
                if strong_tag:
                    region_text = strong_tag.get_text(strip=True)
                    if region_text.lower().startswith("rejon"):
                        found_region_name = region_text.replace(":", "")
                        break

        if not found_region_name:
            # offer regions we discovered in the page
            available_regions = sorted({"Rejon I", "Rejon II", "Rejon III", "Rejon IV"})
            raise SourceArgumentNotFoundWithSuggestions(
                "location_name",
                self.location_name,
                suggestions=available_regions,
            )

        # --- Step 2: Find the correct table ---
        target_table = None
        all_tables = soup.find_all("table")
        for table in all_tables:
            header_row = table.find("tr")
            if not header_row:
                continue

            header_text = header_row.get_text(separator=" ")

            if re.search(r"\b" + re.escape(found_region_name) + r"\b", header_text):
                target_table = table
                break

        if not target_table:
            raise Exception(
                f"Could not find schedule table for region: {found_region_name}"
            )

        # --- Step 2a: Extract the year from the title ---
        year = None
        title_text = data.get("title", "")
        if title_text:
            match = re.search(r"\b(20\d{2})\b", title_text)
            if match:
                year = int(match.group(1))

        if not year:
            _LOGGER.warning(
                "Could not find year in title, falling back to current year."
            )
            year = datetime.date.today().year

        # --- Step 3: Process the table and create Collection objects ---
        entries = []

        header_cells = target_table.find("tr").find_all("td")
        headers = [h.get_text(" ", strip=True) for h in header_cells]

        headers = [h.replace("Rejon I I", "Rejon II") for h in headers]

        schedule_columns = {}
        for i, header in enumerate(headers):
            if re.match(r"\b" + re.escape(found_region_name) + r"\b", header):
                waste_type = "BIO" if "BIO" in header else "Segregowane i zmieszane"
                schedule_columns[i] = waste_type

        for row in target_table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if not cells or len(cells) < 2:
                continue

            month_str_raw = cells[0].get_text(strip=True).lower()

            month_num = MONTH_MAP.get(month_str_raw)
            if month_num:
                for col_index, waste_type in schedule_columns.items():
                    if col_index < len(cells):
                        days_text = cells[col_index].get_text(strip=True)
                        days_text_cleaned = re.sub(r"\(.*\)", "", days_text)
                        days = re.findall(r"\d+", days_text_cleaned)
                        for day in days:
                            try:
                                date = datetime.date(year, month_num, int(day))
                                entries.append(
                                    Collection(
                                        date=date,
                                        t=waste_type,
                                        icon=ICON_MAP.get(waste_type),
                                    )
                                )
                            except ValueError:
                                _LOGGER.warning(
                                    f"Invalid date created for {day}/{month_num}/{year}"
                                )

            elif "gabaryty" in month_str_raw:
                dates_text = None
                if found_region_name in ["Rejon I", "Rejon III"]:
                    if len(cells) > 1:
                        dates_text = cells[1].get_text(strip=True)
                elif found_region_name in ["Rejon II", "Rejon IV"]:
                    if len(cells) > 2:
                        dates_text = cells[2].get_text(strip=True)

                if dates_text:
                    matches = re.findall(r"(\d+)\s+([a-zA-Zśńćźżęółą]+)", dates_text)
                    for day, month_name in matches:
                        month_num_gabaryty = MONTH_MAP.get(month_name.lower())
                        if month_num_gabaryty:
                            try:
                                date = datetime.date(year, month_num_gabaryty, int(day))
                                entries.append(
                                    Collection(
                                        date=date,
                                        t="Gabaryty",
                                        icon=ICON_MAP.get("Gabaryty"),
                                    )
                                )
                            except ValueError:
                                _LOGGER.warning(
                                    f"Invalid gabaryty date for {day}/{month_name}"
                                )

        return entries
