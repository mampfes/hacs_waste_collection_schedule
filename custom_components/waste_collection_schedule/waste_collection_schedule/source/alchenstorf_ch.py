import json
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Alchenstorf"
DESCRIPTION = " Source for 'Alchenstorf, CH'"
URL = "https://www.alchenstorf.ch"
TEST_CASES: dict[str, dict] = {"TEST": {}}

ICON_MAP = {
    "Grünabfuhr Alchenstorf": "mdi:leaf",
    "Kehrichtabfuhr Alchenstorf": "mdi:trash-can-outline",
    "Kartonsammlung Alchenstorf": "mdi:recycle",
    "Papiersammlung Alchenstorf": "mdi:newspaper-variant-multiple-outline",
    "Alteisenabfuhr Alchenstorf": "mdi:desktop-classic",
}


class Source:
    def __init__(self):
        pass

    def fetch(self):
        response = requests.get("https://www.alchenstorf.ch/abfalldaten")
        response.raise_for_status()

        html = BeautifulSoup(response.text, "html.parser")

        table = html.find("table", attrs={"id": "icmsTable-abfallsammlung"})
        if not table:
            raise ValueError("Could not find the waste collection table on the page")

        try:
            data = json.loads(table.attrs["data-entities"])
        except (json.JSONDecodeError, KeyError):
            raise ValueError("Could not parse the waste collection data from the page")

        entries = []
        for item in data.get("data", []):
            try:
                waste_type = BeautifulSoup(item["name"], "html.parser").text.strip()
                icon = ICON_MAP.get(waste_type, "mdi:trash-can")

                date_html = item["_anlassDate"]
                date_soup = BeautifulSoup(date_html, "html.parser")

                date_span = date_soup.find("span", class_="text-nowrap")
                date_text = date_span.get_text().strip()

                clean_date_part = date_text.split(",")[0].strip()

                dates_to_add = []

                if " - " in clean_date_part:
                    parts = clean_date_part.split(" - ")
                    start_str = parts[0].strip()
                    end_str = parts[1].strip()

                    start_date = datetime.strptime(start_str, "%d.%m.%Y").date()
                    end_date = datetime.strptime(end_str, "%d.%m.%Y").date()

                    current_date = start_date
                    while current_date <= end_date:
                        dates_to_add.append(current_date)
                        current_date += timedelta(days=1)
                else:
                    single_date = datetime.strptime(clean_date_part, "%d.%m.%Y").date()
                    dates_to_add.append(single_date)

                for pickup_date in dates_to_add:
                    entries.append(
                        Collection(
                            date=pickup_date,
                            t=waste_type,
                            icon=icon,
                        )
                    )

            except Exception:
                raise ValueError("Could not parse the waste collection entry")

        return entries
