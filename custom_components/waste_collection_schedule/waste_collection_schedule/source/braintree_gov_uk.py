import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Braintree District Council"
DESCRIPTION = "Braintree District Council, UK - Waste Collection"
URL = "https://www.braintree.gov.uk"
TEST_CASES = {
    "30 Boars Tye Road": {"house_number": "30", "post_code": "CM8 3QE"},
    "64 Silver Street": {"house_number": "64", "post_code": "CM8 3QG"},
    "18 St Mary's Road": {"house_number": "1", "post_code": "CM8 3PE"},
    "20 Peel Crescent": {"house_number": "20", "post_code": "CM7 2RS"},
    "Causeway House": {"house_number": "Causeway House", "post_code": "CM7 9HB"},
}

ICON_MAP = {
    "Grey Bin": "mdi:trash-can",
    "Clear Sack": "mdi:recycle",
    "Garden Bin": "mdi:leaf",
    "Food Bin": "mdi:food-apple",
}


class Source:
    def __init__(self, post_code: str, house_number: str):
        self.post_code = post_code
        self.house_number = house_number
        self.url = f"{URL}/xfp/form/554"

    def initialize_form_data(self):
        self.form_data = {
            "qe15dda0155d237d1ea161004d1839e3369ed4831_0_0": (None, self.post_code),
            "page": (None, 5730),
        }

    def fetch(self):
        self.initialize_form_data()  # Re-initialize form data before each fetch otherwise subsequent fetchs fail
        address_lookup = requests.post(
            "https://www.braintree.gov.uk/xfp/form/554", files=self.form_data
        )
        address_lookup.raise_for_status()
        addresses = {}
        for address in BeautifulSoup(address_lookup.text, "html.parser").find_all(
            "option"
        ):
            if len(address["value"]) > 5:  # Skip the first option
                addresses[address["value"]] = address.text.strip()
        id = next(
            address
            for address in addresses
            if addresses[address].startswith(self.house_number)
        )
        self.form_data["qe15dda0155d237d1ea161004d1839e3369ed4831_1_0"] = (None, id)
        self.form_data["next"] = (None, "Next")
        collection_lookup = requests.post(
            "https://www.braintree.gov.uk/xfp/form/554", files=self.form_data
        )
        collection_lookup.raise_for_status()
        entries = []
        for results in BeautifulSoup(collection_lookup.text, "html.parser").find_all(
            "div", class_="date_display"
        ):
            try:
                collection_info = results.text.strip().split("\n")
                collection_type = collection_info[0].strip()

                # Skip if no collection date is found
                if len(collection_info) < 2:
                    continue

                collection_date = collection_info[1].strip()

                entries.append(
                    Collection(
                        date=parser.parse(collection_date, dayfirst=True).date(),
                        t=collection_type,
                        icon=ICON_MAP.get(collection_type),
                    )
                )
            except (StopIteration, TypeError):
                pass
        return entries
