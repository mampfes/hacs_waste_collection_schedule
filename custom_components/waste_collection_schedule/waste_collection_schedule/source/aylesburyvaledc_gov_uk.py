from bs4 import BeautifulSoup
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Aylesbury Vale District Council"
DESCRIPTION = "Source for aylesburyvaledc.gov.uk services for Aylesbury Vale District Council, UK."
URL = "https://aylesburyvaledc.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100011821616"},
    "Test_002": {"uprn": "100011776859"},
    "Test_003": {"uprn": 100011749007},
}
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "GARDEN": "mdi:leaf",
    "RECYCLING": "mdi:recycle",
    "FOOD": "mdi:food",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        # Build SOAP1.2 request
        url = "http://avdcbins.web-labs.co.uk/RefuseApi.asmx"
        headers = {
            "Content-Type": "application/soap+xml; charset=utf-8"
        }
        body = f"""<?xml version="1.0" encoding="utf-8"?>
            <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                <soap12:Body>
                    <GetCollections xmlns="http://tempuri.org/">
                        <uprn>{uprn}</uprn>
                    </GetCollections>
                </soap12:Body>
            </soap12:Envelope>
        """
        response = requests.post(url,data=body,headers=headers)
        soup = BeautifulSoup(response.content, "xml")
        bins = soup.find_all("BinCollection")
        
        entries = []
        for item in bins:
            dt = item.find("Date")
            for waste in ICON_MAP:
                w = item.find(waste.capitalize())
                if w.text == "true":
                    entries.append(
                        Collection(
                            date=datetime.strptime(dt, "").date(),
                            t=waste,
                            icon=ICON_MAP.get(waste),
                        )
                    )
                    # print(dt.text, waste)   

        return entries
