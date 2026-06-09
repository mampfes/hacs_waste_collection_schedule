from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Bedford Borough Council"
DESCRIPTION = "Source for bedford.gov.uk services for Bedford Borough Council, UK."
URL = "https://bedford.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100080009302"},
    "Test_002": {"uprn": "100081207036"},
    "Test_003": {"uprn": "100080018481"},
    "Test_004": {"uprn": "100080023672"},
}

# Extended headers to bypass upstream request blocking (e.g., WAF)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bedford.gov.uk/",
    "Origin": "https://www.bedford.gov.uk",
}

ICON_MAP = {
    "BLACK BIN": Icons.GENERAL_WASTE,
    "ORANGE BIN": Icons.RECYCLING,
    "GREEN BIN": Icons.ORGANIC,
    "CADDY BIN": Icons.BIO_KITCHEN,
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        s = requests.Session()
        r = s.get(
            f"https://bbaz-as-prod-bartecapi.azurewebsites.net/api/bincollections/residential/getbyuprn/{self._uprn}",
            headers=HEADERS,
        )
        
        # Raise an exception if the server returns an error (e.g. 403 Forbidden)
        r.raise_for_status()

        # Parse the JSON response
        json_data = r.json().get("BinCollections", [])

        entries = []

        for day in json_data:
            for bin_data in day:
                bin_type = bin_data.get("BinType", "")
                job_start = bin_data.get("JobScheduledStart")

                if not job_start or not bin_type:
                    continue

                entries.append(
                    Collection(
                        date=datetime.strptime(
                            job_start, "%Y-%m-%dT00:00:00"
                        ).date(),
                        t=bin_type,
                        icon=ICON_MAP.get(bin_type.upper()),
                    )
                )

        return entries
