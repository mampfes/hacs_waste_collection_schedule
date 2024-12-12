from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Wakefield Council"
DESCRIPTION = "Source for Wakefield.gov.uk services for Wakefield Council"
URL = "https://wakefield.gov.uk"

TEST_CASES = {
    "uprn1": {"uprn": "63024087"},
    "uprn2": {"uprn": 63105305},
    "uprn3": {"uprn": "63012193"},
}

TYPES = {
    "Household": {"icon": "mdi:trash-can", "alias": "Household"},
    "Mixed": {"icon": "mdi:recycle", "alias": "Mixed Recycling"},
    "Garden": {"icon": "mdi:leaf", "alias": "Garden"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Enter your UPRN (available from [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/))."
    "Alternatively: you can also see it in the URL/location bar of your browser when you search the Wakefield site manually, look for 'uprn=' in the url and take the numbers immediately after. "
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self) -> List[Collection]:
        entries = []
        with requests.Session() as sess:
            url = "https://www.wakefield.gov.uk/where-i-live/"  # the a parameter is needed for page to load but contents doesn't matter
            request = sess.get(url, params={"uprn": {self._uprn}, "a": "Your Address"})
            soup = BeautifulSoup(request.content, "html.parser")
            collection_sections = soup.select(".tablet\\:l-col-fb-4.u-mt-10")
            for section in collection_sections:
                collection_dates = set()
                bin_type = section.find("strong").text.split(" ")[0]
                prev_and_next_collection = section.select(".u-mb-2")
                for collection in prev_and_next_collection:
                    if ", " not in collection.text:
                        continue
                    try:
                        collection_dates.add(
                            datetime.strptime(
                                collection.text.split(", ")[1].strip(), "%d %B %Y"
                            ).date()
                        )
                    except ValueError:
                        pass
                for collection_date in collection_dates:
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=TYPES[bin_type]["alias"],
                            icon=TYPES[bin_type]["icon"],
                        )
                    )
                list_elements = section.find_all("li")
                for element in list_elements:
                    entries.append(
                        Collection(
                            date=datetime.strptime(
                                element.text.split(", ")[1].strip(), "%d %B %Y"
                            ).date(),
                            t=TYPES[bin_type]["alias"],
                            icon=TYPES[bin_type]["icon"],
                        )
                    )
        return entries
