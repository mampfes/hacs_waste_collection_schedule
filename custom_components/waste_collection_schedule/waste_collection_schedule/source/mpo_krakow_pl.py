import logging
import re
import requests
from datetime import datetime
from io import BytesIO
from PyPDF2 import PdfReader
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

_LOGGER = logging.getLogger(__name__)

# CONSTANTS
TITLE = "MPO Kraków"
DESCRIPTION = "Source script for MPO Kraków"
URL = "https://harmonogram.mpo.krakow.pl/"

TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
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
    """Fetch available streets as a dictionary."""
    logging.info("Fetching streets from the API.")
    response = requests.post(API_URL, data={"token": TOKEN})
    response.raise_for_status()
    data = response.json()
    if data != "error":
        return {item["name"]: item["id"] for item in data if item["id"] != "0" or item["name"] != "-Brak-"}
    raise SourceArgumentNotFound("Could not fetch streets.")

def fetch_numbers(street_id: str) -> dict[str, str]:
    """Fetch house numbers for a given street as a dictionary."""
    logging.info(f"Fetching house numbers for street ID: {street_id}")
    response = requests.post(API_URL, data={"ulica": street_id, "token": TOKEN})
    response.raise_for_status()
    data = response.json()
    if data != "error":
        return {item["name"]: item["id"] for item in data if item["id"] != "0" or item["name"] != "-Brak-"}
    raise SourceArgumentNotFound(f"Could not fetch house numbers for street ID {street_id}.")

def download_pdf_to_memory(number_id: str) -> BytesIO:
    """Download the schedule PDF for a specific house number."""
    logging.info(f"Downloading PDF for house number ID: {number_id}")
    pdf_url = f"{API_URL}pdf/"
    response = requests.get(pdf_url, params={"id_numeru": number_id, "token": TOKEN}, stream=True)
    response.raise_for_status()
    return BytesIO(response.content)

def extract_text_from_pdf(pdf_file: BytesIO) -> str:
    """Extract text from the downloaded PDF."""
    logging.info("Extracting text from the PDF.")
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text.strip()

def extract_year(text: str) -> int:
    """Extract year from datestamp text."""
    year_pattern = r'Data generowania:\s\d{4}-\d{2}-\d{2}'
    match = re.search(year_pattern, text)
    if match:
        return int(match.group(0).split()[2].split('-')[0])
    raise Exception("Year not found in the text.")

def extract_schedule(text: str) -> list[dict]:
    """Extract schedule from text."""
    logging.info("Extracting schedule from the text.")
    current_year = extract_year(text)
    schedule_pattern = r'(\w+\n\d+\s\w+)\n([\w\s]+?)(?=\n\w+\n\d+\s\w+|$)'
    matches = re.findall(schedule_pattern, text)

    schedule = []
    previous_month = None

    miesiace = {
        "stycznia": "January", "lutego": "February", "marca": "March",
        "kwietnia": "April", "maja": "May", "czerwca": "June",
        "lipca": "July", "sierpnia": "August", "września": "September",
        "października": "October", "listopada": "November", "grudnia": "December"
    }

    for date, waste_types in matches:
        date_cleaned = date.replace('\n', ' ').strip()
        waste_types_cleaned = waste_types.replace('\n', ', ').strip()

        for pl, en in miesiace.items():
            date_cleaned = date_cleaned.replace(pl, en)

        date_cleaned = " ".join(date_cleaned.split()[1:]).strip()
        date_obj = datetime.strptime(f"{date_cleaned} {current_year}", "%d %B %Y")
        current_month = date_obj.month

        if previous_month is not None and previous_month > current_month:
            current_year += 1
        previous_month = current_month

        date_with_year = f"{date_cleaned} {current_year}"
        waste_types = waste_types_cleaned.split(", ")
        for waste_type in waste_types:
            schedule.append({
                "Date": date_with_year,
                "Waste_type": waste_type.strip().capitalize(),
            })

    return schedule


class Source:
    def __init__(self, street_name: str, building_number: str):
        if not street_name:
            raise SourceArgumentRequired("street_name is required.")
        if not building_number:
            raise SourceArgumentRequired("building_number is required.")
        self.street_name = street_name
        self.building_number = building_number

    def fetch(self) -> list[Collection]:
        streets = fetch_streets()
        selected_street_id = streets.get(self.street_name)
        if not selected_street_id:
            raise SourceArgumentNotFoundWithSuggestions(
                f"Street '{self.street_name}' not found.",
                suggestions=list(streets.keys())
            )

        numbers = fetch_numbers(selected_street_id)
        selected_number_id = numbers.get(self.building_number)
        if not selected_number_id:
            raise SourceArgumentNotFoundWithSuggestions(
                f"Building number '{self.building_number}' not found for street '{self.street_name}'.",
                suggestions=list(numbers.keys())
            )

        pdf_file = download_pdf_to_memory(selected_number_id)
        pdf_text = extract_text_from_pdf(pdf_file)
        schedule = extract_schedule(pdf_text)

        if not schedule:
            raise SourceArgumentException(
                "Schedule data could not be extracted. The PDF might be empty or formatted incorrectly."
            )

        return [
            Collection(
                date=datetime.strptime(item['Date'], "%d %B %Y").date(),
                t=item['Waste_type'],
                icon=ICON_MAP.get(item['Waste_type']),
            )
            for item in schedule
        ]
