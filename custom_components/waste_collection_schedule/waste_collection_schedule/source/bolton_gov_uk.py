import datetime
import re
import ssl
from bs4 import BeautifulSoup
import requests
import urllib3
from urllib3.util.ssl_ import create_urllib3_context
from waste_collection_schedule import Collection

TITLE = "Bolton Council"
DESCRIPTION = "Source for Bolton Council, UK."
URL = "https://bolton.gov.uk"

API_URLS = {
    "collection": "https://carehomes.bolton.gov.uk/bins.aspx",
}

TEST_CASES = {
    "Test_Postcode_Without_Space": {
        "postcode": "BL52AX",
        "house_number": "3",
    },
    "Test_Postcode_With_Space": {
        "postcode": "BL1 5BQ",
        "house_number": "14",
    },
    "Test_Single_Digit_House": {
        "postcode": "BL1 5XR",
        "house_number": "2",
    },
}

ICON_MAP = {
    "Grey Bin": "mdi:trash-can",
    "Beige Bin": "mdi:newspaper-variant",
    "Burgundy Bin": "mdi:bottle-soda",
    "Green Bin": "mdi:leaf",
    "Food container": "mdi:food",
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
}


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(
            cert_reqs=ssl.CERT_NONE, ciphers="DEFAULT:@SECLEVEL=1"
        )
        context.options |= 0x4
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
        kwargs["ssl_context"] = context
        return super().init_poolmanager(*args, **kwargs)


class Source:
    def __init__(self, postcode: str, house_number: str):
        self._postcode = postcode
        self._house_number = str(house_number)

    def fetch(self):
        # Disable only the InsecureRequestWarning
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        entries = []
        session = requests.Session()
        session.headers.update(HEADERS)
        session.verify = False

        adapter = CustomHttpAdapter()
        session.mount("https://", adapter)

        try:
            # Get initial form tokens
            r = session.get(API_URLS["collection"], timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # Submit postcode
            viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
            viewstategenerator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})[
                "value"
            ]
            eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]

            r = session.post(
                API_URLS["collection"],
                data={
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstategenerator,
                    "__EVENTVALIDATION": eventvalidation,
                    "txtPostcode": self._postcode,
                    "btnSubmit": "Submit",
                },
                timeout=30,
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # Find the correct address and get its UPRN
            address_select = soup.find("select", {"name": "ddlAddresses"})
            if not address_select:
                raise ValueError(f"No addresses found for postcode {self._postcode}")

            uprn = None
            for option in address_select.find_all("option"):
                if option.text.strip().lower().startswith(self._house_number.lower()):
                    uprn = option["value"]
                    break

            if not uprn:
                raise ValueError(
                    f"Could not find house number {self._house_number} in postcode {self._postcode}"
                )

            # Select address
            viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
            viewstategenerator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})[
                "value"
            ]
            eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]

            r = session.post(
                API_URLS["collection"],
                data={
                    "__EVENTTARGET": "ddlAddresses",
                    "__EVENTARGUMENT": "",
                    "__LASTFOCUS": "",
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstategenerator,
                    "__EVENTVALIDATION": eventvalidation,
                    "txtPostcode": self._postcode,
                    "ddlAddresses": uprn,
                },
                timeout=30,
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # Parse collection dates
            for bin_info in soup.find_all("div", class_="bin-info"):
                strong_tag = bin_info.find("strong")
                if strong_tag:
                    text = strong_tag.text.strip()
                    match = re.match(
                        r"Your next (.*?) collection\(s\) will be on", text
                    )
                    if match:
                        # Get the bin type and capitalise color and 'bin'
                        bin_type = match.group(1)
                        if "bin" in bin_type.lower():
                            # Split into words and capitalise each part
                            parts = bin_type.lower().split()
                            bin_type = f"{parts[0].capitalize()} Bin"

                        for date_p in bin_info.find_all("p", class_="date"):
                            date_text = date_p.find("span").text.strip()
                            try:
                                collection_date = datetime.datetime.strptime(
                                    date_text, "%A %d %B %Y"
                                ).date()
                                entries.append(
                                    Collection(
                                        date=collection_date,
                                        t=bin_type,
                                        icon=ICON_MAP.get(bin_type),
                                    )
                                )
                            except ValueError:
                                continue

        except requests.RequestException as e:
            raise Exception(f"Error fetching data: {e}")

        return entries
