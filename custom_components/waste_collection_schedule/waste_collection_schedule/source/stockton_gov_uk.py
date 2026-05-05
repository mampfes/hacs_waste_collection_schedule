import base64
import json
import re
from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection

# Source code based on gateshead_gov_uk

TITLE = "Stockton-on-Tees Borough Council"
DESCRIPTION = "Source for Stockton-on-Tees Borough Council."
URL = "https://www.stockton.gov.uk/"
TEST_CASES = {
    "100110203615": {"uprn": "100110203615"},
    "100110160417": {"uprn": "100110160417"},
    "20002027430": {"uprn": 20002027430},
    "100110206644": {"uprn": 100110206644},
}


ICON_MAP = {
    "Waste": "mdi:trash-can",
    "Garden Waste": "mdi:leaf",
    "Recycling": "mdi:recycle",
}


API_URL = "https://www.stockton.gov.uk/bin-collection-days"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        """Fetch using curl_cffi to bypass Cloudflare anti-bot protection."""
        scraper = requests.Session(impersonate="chrome124")

        # Start a session with the target URL
        r = scraper.get(API_URL, timeout=30)
        r.raise_for_status()

        # Process the response and extract collection data
        soup = BeautifulSoup(r.text, features="html.parser")

        # Stockton migrated this form to a V2 name (and action URL includes pageSessionId)
        form = soup.find(
            "form",
            attrs={"id": "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_FORM"},
        )
        if not form or not form.get("action"):
            raise ValueError(
                "Could not find LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_FORM or action"
            )
        form_url = form["action"]

        pageSessionId_input = soup.find(
            "input",
            attrs={"name": "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_PAGESESSIONID"},
        )
        sessionId_input = soup.find(
            "input",
            attrs={"name": "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_SESSIONID"},
        )
        nonce_input = soup.find(
            "input",
            attrs={"name": "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_NONCE"},
        )
        if not pageSessionId_input or not pageSessionId_input.get("value"):
            raise ValueError(
                "Could not find LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_PAGESESSIONID"
            )
        if not sessionId_input or not sessionId_input.get("value"):
            raise ValueError(
                "Could not find LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_SESSIONID"
            )
        if not nonce_input or not nonce_input.get("value"):
            raise ValueError(
                "Could not find LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_NONCE"
            )

        pageSessionId = pageSessionId_input["value"]
        sessionId = sessionId_input["value"]
        nonce = nonce_input["value"]

        form_data = {
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_PAGESESSIONID": pageSessionId,
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_SESSIONID": sessionId,
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_NONCE": nonce,
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_FORMACTION_NEXT": "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_FINDBUTTON",
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_UPRN": self._uprn,
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2_CUSTODIAN": "738",
        }

        # Submit form
        r = scraper.post(form_url, data=form_data, timeout=30)
        r.raise_for_status()

        # Extract encoded response data
        soup = BeautifulSoup(r.text, features="html.parser")
        pattern = re.compile(
            r"var LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2FormData = \"(.*?)\";$",
            re.MULTILINE | re.DOTALL,
        )
        script = soup.find("script", string=pattern)
        if not script:
            raise ValueError(
                "Could not find LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2FormData in response"
            )
        match = pattern.search(script.get_text())
        if not match:
            raise ValueError(
                "Could not extract LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2FormData value"
            )
        response_data = match.group(1)

        # Decode base64 encoded response data and convert to JSON
        decoded_data = base64.b64decode(response_data)
        data = json.loads(decoded_data)

        entries = []
        for key in data["_PAGEORDER_"]:
            soup = BeautifulSoup(
                data[key]["COLLECTIONDETAILS2"], features="html.parser"
            )
            for waste_type_div in soup.find_all("div", attrs={"class": "grid__cell"}):
                waste_type = waste_type_div.find(
                    "p", attrs={"class": "myaccount-block__title--bin"}
                ).text.strip()

                # Get date nodes from not garden waste
                date_nodes = waste_type_div.find_all(
                    "p", attrs={"class": "myaccount-block__date--bin"}
                )

                # Get Both dates from Garden Waste
                if date_nodes is None or len(date_nodes) == 0:
                    date_nodes = [
                        waste_type_div.find_all("p")[1].find_all("strong")[i]
                        for i in range(2)
                    ]

                for date_node in date_nodes:
                    try:
                        # Remove ordinal suffixes from date string
                        date_string = re.sub(
                            r"(?<=[0-9])(?:st|nd|rd|th)", "", date_node.text.strip()
                        )
                        date = datetime.strptime(date_string, "%a %d %B %Y").date()
                        entries.append(
                            Collection(
                                date=date,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )
                    except (ValueError, AttributeError):
                        # Skip any invalid date strings (e.g., "Date not available", empty strings, etc.)
                        # Stockton.GOV.UK tend to show "Date not available" during winter months for garden waste
                        continue

        return entries
