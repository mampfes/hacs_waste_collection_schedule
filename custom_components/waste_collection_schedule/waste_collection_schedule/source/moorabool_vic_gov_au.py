# Highly inspired by the Blacktown source

import datetime
import json
from typing import TypedDict

import requests
from bs4 import BeautifulSoup
from requests.utils import requote_uri
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Moorabool Shire Council"
DESCRIPTION = "Source for Moorabool Shire Council rubbish collection."
URL = "https://www.moorabool.vic.gov.au"


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to <https://www.moorabool.vic.gov.au/Waste-and-environment/Household-bins/Find-your-bin-collection-day> and make sure your address matches the auto-complete suggestions."
}

TEST_CASES = {
    "Workers Blacktown": {
        "address": "18 Campbell Street, Blacktown, NSW 2148",
    },
}

API_URLS = {
    "address_search": "https://www.moorabool.vic.gov.au/api/v1/myarea/search?keywords={}",
    "collection": "https://www.moorabool.vic.gov.au/ocapi/Public/myarea/wasteservices?geolocationid={}&ocsvclang=en-AU",
}

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.moorabool.vic.gov.au/Waste-and-environment/Household-bins/Find-your-bin-collection-day",
}


ICON_MAP = {
    "Garbage": "trash-can",
    "Recycling": "mdi:recycle",
}


class ApiItem(TypedDict):
    Id: str
    AddressSingleLine: str
    MunicipalSubdivision: str
    Distance: int
    Score: float
    LatLon: tuple[int, int]


class ApiResult(TypedDict):
    Items: list[ApiItem]
    Offset: int
    Limit: int
    Total: int


class Source:
    def __init__(self, address: str):
        self.address = address

    @staticmethod
    def search_address(address: str, session: requests.Session) -> ApiResult:
        q = requote_uri(str(API_URLS["address_search"]).format(address))

        # Retrieve suburbs
        r = session.get(q)

        return json.loads(r.text)

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(HEADERS)
        locationId = ""

        data = self.search_address(self.address, session)

        if len(data["Items"]) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address",
                self.address,
                [item["AddressSingleLine"] for item in data["Items"]],
            )
        if len(data["Items"]) == 0:
            splitted_address = self.address.split()
            data = self.search_address(
                (
                    (splitted_address[0] + splitted_address[1][:4])
                    if len(splitted_address) > 1
                    else splitted_address[0]
                ),
                session,
            )
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self.address,
                [item["AddressSingleLine"] for item in data["Items"]],
            )

        # Find the ID for our suburb
        locationId = data["Items"][0]["Id"]

        if locationId == 0:
            raise ValueError(
                f"Unable to find location ID for {self.address}, maybe you misspelled your address?"
            )

        # Retrieve the upcoming collections for our property
        q = requote_uri(str(API_URLS["collection"]).format(locationId))

        r = session.get(q)

        col_data = json.loads(r.text)

        responseContent = col_data["responseContent"]

        soup = BeautifulSoup(responseContent, "html.parser")
        services = soup.select("div.waste-services-result")

        entries = []

        for item in services:
            # test if <div> contains a valid date. If not, is is not a collection item.
            date_text = item.select_one("div.next-service")
            if not date_text:
                continue

            date_format = "%a %d/%m/%Y"

            try:
                # Strip carriage returns and newlines out of the HTML content
                cleaned_date_text = (
                    date_text.text.replace("\r", "").replace("\n", "").strip()
                )

                # Parse the date
                date = datetime.datetime.strptime(cleaned_date_text, date_format).date()

            except ValueError:
                continue

            waste_type_h3 = item.select_one("h3")

            if not waste_type_h3:
                continue
            waste_type = waste_type_h3.text.strip().removesuffix("collection").strip()

            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                )
            )

        return entries
