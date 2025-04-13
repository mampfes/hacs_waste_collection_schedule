import requests
import json

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS  # ICS parser from the codebase


### TODO Update Documentation
TITLE = "AWISTA Düsseldorf DE"
DESCRIPTION = "Source for AWISTA Düsseldorf waste collection."
URL = "https://www.awista-kommunal.de"
TEST_CASES = {
    "Zeppenheimer Straße 141": {"street": '["Zeppenheimer Straße 141"]'.encode("utf8")},
    "Erkrather Straße 316": {"street": '["Erkrather Straße 316"]'.encode("utf8")},
    "Prinz-Georg-Straße 40": {"street": '["Prinz-Georg-Straße 40"]'.encode("utf8")},
}

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "Papier": "mdi:recycle",
    "Gelber Sack": "mdi:recycle",
}

class Source:
    def __init__(self, street: str):
        self._street = street
        self._url = "https://awista-kommunal.de/abfallkalender"
        ### Headers might change
        ### TODO check headers 
        self._headers = {
            "Host": "www.awista-kommunal.de",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
            "Accept": "text/x-component",
            "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://www.awista-kommunal.de/abfallkalender",
            "Next-Action": "40728fab1a26a5c561f7ec9c0869e118f9d5e7fa77",
            "Next-Router-State-Tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22abfallkalender%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2C%22%2Fabfallkalender%22%2C%22refresh%22%5D%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
            "x-deployment-id": "dpl_5M3qWDfcnfRjxoSczpeYSQkbLW1Y",
            "Content-Type": "text/plain;charset=UTF-8",
            "Origin": "https://www.awista-kommunal.de",
            "Connection": "keep-alive",
        }

    def fetch(self):
        # Find URL for ICS by Street + House Number
        response = requests.post(
            url=self._url, headers=self._headers, data=self._street, allow_redirects=True
        )
        response.encoding = response.apparent_encoding

        try:
            # Parse the response to extract the ICS URL
            ics_data = json.loads(
                response.text[response.text.rfind("\n1:") + 3:]
            )
            ics_url = f"https://awista-kommunal.de/abfallkalender/{ics_data['items'][0]['id']}/calendar.ics"

            # Fetch and parse the ICS file
            ics_response = requests.get(ics_url)
            ics_response.raise_for_status()
            calendar = ICS()  # Initialize the ICS parser
            events = calendar.convert(ics_response.text)

            # Extract collection dates and types
            entries = []
            for collection_date, waste_type in events:
                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                    )
                )

            return entries
        ### TODO implement exception handling from documentation
        # generic exception
        except (KeyError, IndexError, json.JSONDecodeError, requests.RequestException) as e:
            raise ValueError(f"Failed to fetch or parse data: {e}")