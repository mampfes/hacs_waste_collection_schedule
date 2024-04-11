import base64
import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
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

        session = requests.Session()

        # Start a session
        r = session.get(API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        # Extract form submission url and form data
        form_url = soup.find(
            "form", attrs={"id": "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGION_FORM"}
        )["action"]
        pageSessionId = soup.find(
            "input",
            attrs={"name": "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGION_PAGESESSIONID"},
        )["value"]
        sessionId = soup.find(
            "input", attrs={"name": "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGION_SESSIONID"}
        )["value"]
        nonce = soup.find(
            "input", attrs={"name": "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGION_NONCE"}
        )["value"]

        form_data = {
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGION_PAGESESSIONID": pageSessionId,
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGION_SESSIONID": sessionId,
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGION_NONCE": nonce,
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGION_FORMACTION_NEXT": "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGION_FINDBUTTON",
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGION_UPRN": self._uprn,
            "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGION_CUSTODIAN": "738",
        }

        # Submit form
        r = session.post(form_url, data=form_data)
        r.raise_for_status()

        # Extract encoded response data
        soup = BeautifulSoup(r.text, features="html.parser")
        pattern = re.compile(
            r"var LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONFormData = \"(.*?)\";$",
            re.MULTILINE | re.DOTALL,
        )
        script = soup.find("script", text=pattern)

        response_data = pattern.search(script.text).group(1)

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
                    # If date is "Date not available" then skip (Winter period)
                    if date_node.text.strip() == "Date not available":
                        continue

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

        return entries
