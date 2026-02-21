import logging
import re
from datetime import datetime
from io import BytesIO

import requests
from pypdf import PdfReader
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

_LOGGER = logging.getLogger(__name__)

# CONSTANTS
TITLE = "MPO Kraków"
DESCRIPTION = "Source script for MPO Kraków"
URL = "https://harmonogram.mpo.krakow.pl/"

TEST_CASES = {
    "Romanowicza 1 DM": {"street_name": "Romanowicza", "building_number": "1 DM"},
    "Na Wrzosach 43 DJ": {"street_name": "Na Wrzosach", "building_number": "43 DJ"},
    "Świtezianki 7 DB": {"street_name": "Świtezianki", "building_number": "7 DB"},
    "Przewóz 40d DW": {"street_name": "Przewóz", "building_number": "40d DW"},
}

API_URL = "https://kiedywywoz.pl/API/harmo_img/"
TOKEN = "OkkxhC6b9etJBAq7WTHJ0LhIglO18sip"

ICON_MAP = {
    "Zmieszane": "mdi:trash-can",
    "Szkło": "mdi:bottle-wine",
    "Papier": "mdi:package-variant",
    "Tworzywa sztuczne": "mdi:recycle",
    "Bio": "mdi:bio",
    "Zielone": "mdi:leaf",
    "Choinki": "mdi:pine-tree",
}


def fetch_streets() -> dict[str, str]:
    """Fetch available streets as a dictionary, selecting the smallest ID for duplicate names."""
    _LOGGER.debug("Fetching the full list of available streets from the API.")
    response = requests.post(API_URL, data={"token": TOKEN})
    response.raise_for_status()
    data = response.json()
    if data != "error":
        # Build a dictionary {StreetName: StreetID} excluding bad entries
        if isinstance(data, list):  # Ensure data is a list
            streets: dict[str, str] = {}
            for item in data:
                name = item["name"].strip().title()
                street_id = item["id"]
                if street_id != 0 and name != "-Brak-":
                    # If the name is already in the dictionary, keep the smallest ID
                    if name not in streets or street_id < streets[name]:
                        streets[name] = street_id
            return streets
    _LOGGER.error(
        "API returned 'error' while fetching the street list. Possibly invalid token or server issue."
    )
    raise Exception("Could not fetch streets from the API.")


def fetch_numbers(street_name: str) -> dict[str, str]:
    """Fetch building numbers for a given street as a dictionary."""
    if not street_name:
        _LOGGER.error("Street name is required but not provided.")
        raise SourceArgumentRequired(
            "street_name", "Street name is required to fetch building numbers."
        )

    streets = fetch_streets()
    street_id = streets.get(street_name)
    if not street_id:
        _LOGGER.error("Street ID not found for name '%s'.", street_name)
        raise SourceArgumentNotFound("street_name", street_name)

    _LOGGER.debug(
        f"Fetching building numbers for street '{street_name}' (ID: {street_id})."
    )
    response = requests.post(API_URL, data={"ulica": street_id, "token": TOKEN})
    response.raise_for_status()
    data = response.json()

    if data != "error":
        return {
            item["name"].strip().upper(): item["id"]
            for item in data
            if item["id"] != "0" and item["name"].strip() != "-Brak-"
        }

    _LOGGER.error(
        "API returned 'error' while fetching building numbers for street '%s'.",
        street_name,
    )
    raise Exception(
        f"Could not fetch building numbers for street '{street_name}' from the API."
    )


def fetch_pdf(street_name: str, building_number: str) -> BytesIO:
    """Download the schedule PDF for a specific building number."""
    if not street_name:
        _LOGGER.error("Street name is required but not provided.")
        raise SourceArgumentRequired(
            "street_name", "Street name is required to fetch the schedule PDF."
        )
    if not building_number:
        _LOGGER.error("Building number is required but not provided.")
        raise SourceArgumentRequired(
            "building_number", "Building number is required to fetch the schedule PDF."
        )

    numbers = fetch_numbers(street_name)
    number_id = numbers.get(building_number)
    if not number_id:
        _LOGGER.error(
            "Building number '%s' not found in the API data for street '%s'.",
            building_number,
            street_name,
        )
        raise SourceArgumentNotFound("building_number", building_number)

    _LOGGER.debug(
        f"Downloading schedule PDF for building number '{building_number}' (ID: {number_id})."
    )
    pdf_url = f"{API_URL}pdf/"
    response = requests.get(
        pdf_url, params={"id_numeru": number_id, "token": TOKEN}, stream=True
    )
    response.raise_for_status()
    return BytesIO(response.content)


def extract_text_from_pdf(pdf_file: BytesIO) -> str:
    """Extract text from the downloaded PDF."""
    _LOGGER.debug("Extracting text from the PDF.")
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()


def extract_year(text: str) -> int:
    """Extract year from the PDF's datestamp."""
    year_pattern = r"Data generowania:\s\d{4}-\d{2}-\d{2}"
    match = re.search(year_pattern, text)
    if match:
        return int(match.group(0).split()[2].split("-")[0])
    _LOGGER.error("Could not extract datestamp (year) from the PDF text.")
    raise Exception("Could not extract datestamp from the PDF")


def extract_schedule(text: str) -> list[dict]:
    """Extract schedule from the PDF text."""
    _LOGGER.debug("Extracting waste collection schedule from the text.")
    current_year = extract_year(text)

    # Pattern to capture a date line + types of waste until the next date line
    schedule_pattern = r"(\w+\n\d+\s\w+)\n([\w\s]+?)(?=\n\w+\n\d+\s\w+|$)"
    matches = re.findall(schedule_pattern, text)
    if not matches:
        _LOGGER.error(
            "Schedule data could not be extracted. The PDF might be empty or formatted incorrectly."
        )
        raise Exception(
            "Schedule data could not be extracted. The PDF might be empty or formatted incorrectly."
        )

    schedule = []
    previous_month = None

    miesiace = {
        "stycznia": "January",
        "lutego": "February",
        "marca": "March",
        "kwietnia": "April",
        "maja": "May",
        "czerwca": "June",
        "lipca": "July",
        "sierpnia": "August",
        "września": "September",
        "października": "October",
        "listopada": "November",
        "grudnia": "December",
    }

    for date, waste_types_raw in matches:
        date_cleaned = date.replace("\n", " ").strip()
        for pl, en in miesiace.items():
            date_cleaned = date_cleaned.replace(pl, en)

        # Example: date_cleaned might become "24 January"
        date_cleaned = " ".join(date_cleaned.split()[1:]).strip()

        # Convert to datetime
        date_obj = datetime.strptime(f"{date_cleaned} {current_year}", "%d %B %Y")
        current_month = date_obj.month

        # If new month is less than old month, year changed
        if previous_month is not None and previous_month > current_month:
            current_year += 1
            date_obj = datetime.strptime(f"{date_cleaned} {current_year}", "%d %B %Y")
        previous_month = current_month

        # Prepare final date string
        date_with_year = date_obj.strftime("%d %B %Y")

        # Parse types of waste
        waste_types_cleaned = waste_types_raw.replace("\n", ", ").strip()
        waste_types_list = [
            w.strip().capitalize() for w in waste_types_cleaned.split(",") if w.strip()
        ]

        for waste_type in waste_types_list:
            schedule.append(
                {
                    "Date": date_with_year,
                    "Waste_type": waste_type,
                }
            )
    return schedule


class Source:
    def __init__(self, street_name: str, building_number: str):
        # Validate input
        if not street_name:
            _LOGGER.error("Street name not provided to Source constructor.")
            raise SourceArgumentRequired(
                argument="street_name",
                reason="Street name is required to load the schedule.",
            )
        if not building_number:
            _LOGGER.error("Building number not provided to Source constructor.")
            raise SourceArgumentRequired(
                argument="building_number",
                reason="Building number is required to load the schedule.",
            )
        self.street_name = street_name.strip().title()
        self.building_number = building_number.strip().upper()

    def fetch(self) -> list[Collection]:
        _LOGGER.debug(
            "Fetching data for street '%s' and building number '%s'.",
            self.street_name,
            self.building_number,
        )

        streets = fetch_streets()
        if not streets.get(self.street_name):
            _LOGGER.error(
                "Street '%s' was not found in the fetched street list.",
                self.street_name,
            )
            raise SourceArgumentNotFound("street_name", self.street_name)

        numbers = fetch_numbers(self.street_name)
        if not numbers.get(self.building_number):
            _LOGGER.error(
                "Building number '%s' was not found in the fetched numbers list for street '%s'.",
                self.building_number,
                self.street_name,
            )
            raise SourceArgumentNotFound("building_number", self.building_number)

        pdf_file = fetch_pdf(self.street_name, self.building_number)
        pdf_text = extract_text_from_pdf(pdf_file)
        schedule = extract_schedule(pdf_text)

        if not schedule:
            _LOGGER.error("No schedule data found after extracting from the PDF.")
            raise Exception(
                "Schedule data could not be extracted. The PDF might be empty or formatted incorrectly."
            )

        # Build the final schedule list
        return [
            Collection(
                date=datetime.strptime(item["Date"], "%d %B %Y").date(),
                t=item["Waste_type"],
                icon=ICON_MAP.get(item["Waste_type"]),
            )
            for item in schedule
        ]
