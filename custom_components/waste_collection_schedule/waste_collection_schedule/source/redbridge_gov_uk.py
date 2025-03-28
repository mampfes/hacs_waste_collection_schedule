from datetime import datetime
import requests
import pdfplumber
from io import BytesIO
import logging
import re
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Redbridge Council"
DESCRIPTION = "Source for redbridge.gov.uk services for Redbridge Council, UK."
URL = "https://redbridge.gov.uk"
TEST_CASES = {
    "council office recycling only": {"uprn": 10034922090},
    "refuse and recycling only": {"uprn": 10013585215},
    "garden, recycling, refuse": {"uprn": 100022196568}
}
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}

# Suppress unwanted warnings messages from pdfplumber about PDF document structure (e.g.: CropBox missing from /Page, defaulting to MediaBox)
logging.getLogger("pdfminer").setLevel(logging.ERROR)

class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        r = requests.get(
            "https://my.redbridge.gov.uk/RecycleRefuse/GetFile",
            params = {"uprn" : self._uprn}
        )
        r.raise_for_status()

        # Extract all tables from PDF
        tables = []
        with pdfplumber.open(BytesIO(r.content)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                tables.append(table)

        collections = []
        
        # Month and year regex pattern
        month_year_pattern = r"\b([A-Za-z]+) \d{4}\b"
        for table in tables:
            # Flatten each table
            flattened = [item for t in table for item in t]
            # Filter out all non-string values
            filtered = [item for item in flattened if isinstance(item, str)]
            month_year = ""
            date_waste_type = ""

            # Iterate through the list and extract only valuable elements (month, year, collection day and waste collection type)
            for e in filtered:
                m_y_match = re.match(month_year_pattern, e)
                isCollection = any(map(lambda word: word in e, ["Refuse", "Recycling", "Garden"]))
                if m_y_match:
                    month_year = m_y_match.group(0).strip()
                elif isCollection:
                    date_waste_type = e
                    try:
                        collections.append(
                            Collection(
                                date=datetime.strptime(f"{date_waste_type.split("\n")[0]} {month_year}", "%d %B %Y"),
                                t=f"{date_waste_type.split("\n")[1]}",
                                icon=ICON_MAP.get(date_waste_type.split("\n")[1].upper()),
                            )
                        )
                        # Added in case we have
                        if date_waste_type.split("\n")[1] != date_waste_type.split("\n")[-1]:
                            collections.append(
                                Collection(
                                    date=datetime.strptime(f"{date_waste_type.split("\n")[0]} {month_year}", "%d %B %Y"),
                                    t=f"{date_waste_type.split("\n")[-1]}",
                                    icon=ICON_MAP.get(date_waste_type.split("\n")[-1].upper()),
                                )
                            )
                    except:
                        pass

        return collections
