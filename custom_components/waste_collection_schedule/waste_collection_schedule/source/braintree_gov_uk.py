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
}

ICON_MAP = {
    "Grey Bin": "mdi:trash-can",
    "Clear Sack": "mdi:recycle",
    "Green Bin": "mdi:leaf",
    "Food Bin": "mdi:food-apple",
}


class Source:
    def __init__(self, post_code: str, house_number: str):
        self.post_code = post_code
        self.house_number = house_number
        self.url = f"{URL}/xfp/form/554"
        self.form_data = {
            "qe15dda0155d237d1ea161004d1839e3369ed4831_0_0": (None, post_code),
            "page": (None, 5730),
        }

    def fetch(self):
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
                collection_type, collection_date = results.text.strip().split("\n")
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
