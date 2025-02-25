import datetime
import json
import re

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Telford and Wrekin Council"
DESCRIPTION = "Source for telford.gov.uk, Telford and Wrekin Council, UK"
URL = "https://www.telford.gov.uk"

TEST_CASES = {
    "10 Long Row Drive, Lawley": {"uprn": "000452097493"},
    "126 Dunsheath, Telford": {"post_code": "TF3 2DA", "name_number": "126"},
    "11 Pinewoods, Telford": {"post_code": "TF10 9LN", "name_number": "11"},
}

API_URLS = {
    "address_search": "https://dac.telford.gov.uk/BinDayFinder/Find/PostcodeSearch",
    "collection": "https://dac.telford.gov.uk/BinDayFinder/Find/PropertySearch",
}

# Map the names to icons
ICON_MAP = {
    "Red Top Container": "mdi:trash-can",
    "Purple / Blue Containers": "mdi:recycle",
    "Green Container": "mdi:leaf",
    "Silver Containers": "mdi:food",
}

# Path to the images provided by the council for the containers
IMAGEPATH = "https://dac.telford.gov.uk/BinDayFinder/Content/BinIcons/"


class Source:
    def __init__(self, post_code=None, name_number=None, uprn=None):
        self._post_code = post_code
        self._name_number = name_number
        self._uprn = uprn

    def fetch(self):
        if not self._uprn:
            # look up the UPRN for the address

            params = {"postcode": self._post_code}
            r = requests.get(API_URLS["address_search"], params=params)
            if r.status_code == 500:
                raise SourceArgumentException(
                    "post_code",
                    "Postcode is not in the correct format or service is unavailable",
                )

            r.raise_for_status()

            # Required to parse the returned JSON
            addresses = json.loads(r.json())
            if len(addresses["properties"]) == 0:
                raise SourceArgumentNotFound("post_code", self._post_code)

            for property in addresses["properties"]:
                if property["PrimaryName"].lower() == self._name_number.lower():
                    self._uprn = property["UPRN"]

            if not self._uprn:
                raise SourceArgumentNotFoundWithSuggestions(
                    "name_number",
                    self._name_number,
                    [property["PrimaryName"] for property in addresses["properties"]],
                )

        # Get the collection information

        params = {"uprn": self._uprn}

        r = requests.get(API_URLS["collection"], params=params)

        r.raise_for_status()

        x = json.loads(r.json())
        collections = x["bincollections"]

        entries = []

        if collections:
            for collection in collections:
                # Parse the data as the council JSON API returns no year for the collections
                # and so it needs to be calculated to format the date correctly

                today = datetime.date.today()
                year = today.year

                # Remove nd,rd,th,st from the date so it can be parsed

                datestring = (
                    re.sub(r"(\d)(st|nd|rd|th)", r"\1", collection["nextDate"])
                    + " "
                    + str(year)
                )

                date = datetime.datetime.strptime(datestring, "%A %d %B %Y").date()

                # Calculate the year. As we only get collections 2 weeks in advance we can assume the current
                # year unless the month is January in December where it will be next year

                if (date.month == 1) and (today.month == 12):
                    date = date.replace(year=year + 1)

                entries.append(
                    Collection(
                        date=date,
                        t=collection["name"],
                        icon=ICON_MAP.get(collection["name"]),
                        picture=IMAGEPATH + collection["imageURL"],
                    )
                )

        return entries
