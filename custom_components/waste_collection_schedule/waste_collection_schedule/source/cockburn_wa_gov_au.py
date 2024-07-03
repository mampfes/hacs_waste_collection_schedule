import re
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Cockburn"  # Title will show up in README.md and info.md
DESCRIPTION = "Source script for cockburn.wa.gov.au"  # Describe your source
# Insert url to service homepage. URL will show up in README.md and info.md
URL = "https://www.cockburn.wa.gov.au"

API_URL = "https://gis1.cockburn.wa.gov.au/webapiv2/PropertyInfoSearch/PropertyNo"

TEST_CASES = {
    "Thursday": {
        "address": "23 Snowden St, Hammond Park WA 6164",
    },
    "Friday": {
        "address": "1 Eucalyptus Dr Hammond Park"
    },
    "Tuesday": {
        "property_no": "6025742"
    }
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Junk Waste": "mdi:microwave",
    "Green Waste": "mdi:tree",
    "Green Bin": "mdi:leaf",
}

HEADERS = {
    "User-Agent": "Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    "Accept": "application/xhtml+xml,text/json,application/xml"
}


class Source:
    def __init__(self, address=None, property_no=None):

        self.address = address
        self.property_no = property_no
        self.search_method = None

        if self.address:
            address = address.strip()
            address = re.sub(" +", " ", address)
            address = re.sub(",", "", address)
            address = re.sub(" st ", " street ", address, flags=re.IGNORECASE)
            address = re.sub(" hwy ", " highway ",
                             address, flags=re.IGNORECASE)
            address = re.sub(" ave ", " avenue ", address, flags=re.IGNORECASE)
            address = re.sub(" rd ", " road ", address, flags=re.IGNORECASE)
            address = re.sub(" ch ", " chase ", address, flags=re.IGNORECASE)
            address = re.sub(" lp ", " loop ", address, flags=re.IGNORECASE)
            address = re.sub(" dr ", " drive ", address, flags=re.IGNORECASE)
            address = re.sub(
                r"western australia (\d{4})", "WA \\1", address, flags=re.IGNORECASE
            )
            address = re.sub(r" wa (\d{4})", "  WA  \\1",
                             address, flags=re.IGNORECASE)
            self.address = address
            self.search_method = "address"

        # property_no = self.property_no
        if self.property_no:
            self.property_no = property_no
            self.search_method = "property_no"

    def collect_dates(self, start_date, weeks):
        dates = []
        dates.append(start_date)
        for _ in range(1, 4 // weeks):
            start_date = start_date + timedelta(days=(weeks * 7))
            dates.append(start_date)
        return dates

    def extract_date(self, text):
        # Define the pattern for the date format DD-MMM-YYYY
        pattern = r"\d{1,2}-\w{3}-\d{4}"
        # Search for the pattern in the text
        match = re.search(pattern, text)

        # If a match is found, return the matched string (the date)
        if match:
            original_date = match.group()
            # Convert the matched string to a datetime object
            formatted_date = datetime.strptime(original_date, "%d-%b-%Y")
            return formatted_date

        else:
            return None

    def fetch(self):
        entries = []

        # Determine the search method and value based on what's available

        if self.search_method == "address":
            search_method = "address"
            search_value = re.sub(
                r"\s+", "+", self.address.strip())

            full_url = f"{API_URL}?q={search_value}&search_method={search_method}"
            # print(full_url)

        # Check if property_no is available
        if self.search_method == "property_no":
            search_method = "property_no"
            search_value = self.property_no.strip()
            full_url = f"{API_URL}?q={search_value}&search_method={search_method}"
            # print(full_url)

        # Build the full URL
        if full_url is not None:
            r = requests.get(full_url, headers=HEADERS)
            r.raise_for_status()  # Raise an exception if the status code is not 200 (OK)

            data = r.json()[0]

            if not data:
                raise Exception("address not found")

            # Convert the bin day to a date
            date_rubbish = datetime.today()
            while date_rubbish.strftime("%A") != data["BinDay"]:
                date_rubbish += timedelta(days=1)

            # Create bin collection date object
            bin_dates = [date_rubbish.date()]

            # Create green bin collection date object removing the unneeded text
            grn_bin_dates = [self.extract_date(data["GardenWaste"]).date()]

            # Format the Junk Waste collection dates
            jnk_dates = [
                datetime.strptime(
                    data["JunkWhite1"], "%d-%b-%Y").date(),
                datetime.strptime(
                    data["JunkWhite2"], "%d-%b-%Y").date(),
            ]

            # Format the Green Waste collection dates
            grn_waste_dates = [
                datetime.strptime(
                    data["GreenWaste1"], "%d-%b-%Y").date(),
                datetime.strptime(
                    data["GreenWaste2"], "%d-%b-%Y").date(),
            ]

            collections = []
            collections.append({"type": "Rubbish", "dates": bin_dates})
            collections.append({"type": "Recycling", "dates": bin_dates})
            collections.append({"type": "Junk Waste", "dates": jnk_dates})
            collections.append(
                {"type": "Green Waste", "dates": grn_waste_dates})
            collections.append(
                {"type": "Green Bin", "dates": grn_bin_dates})

            # print(collections)

            for collection in collections:
                for date in collection["dates"]:
                    entries.append(
                        Collection(
                            date=date,
                            t=collection["type"],
                            icon=ICON_MAP.get(
                                collection["type"], "mdi:delete")
                        )
                    )

        return entries
