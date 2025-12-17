import requests
import urllib3
from bs4 import BeautifulSoup
from dateutil.parser import parse
from waste_collection_schedule import Collection

# This line suppresses the InsecureRequestWarning when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TITLE = "GardenBags NZ"
DESCRIPTION = "Source for GatdenBags NZ."
URL = "https://gardenbags.co.nz"
TEST_CASES = {
    "Test 1": {
        "account_number": "!secret gardenbags_co_nz_account_number",
        "account_pin": "!secret gardenbags_co_nz_account_pin",
        "franchise": "!secret gardenbags_co_nz_franchise",
    },
}

COUNTRY = "nz"


class Source:
    def __init__(
        self, account_number: str, account_pin: str, franchise: str | None = None
    ):
        self._account_number: str = account_number
        self._account_pin: str = account_pin
        self._franchise: str | None = franchise

    def fetch(self):
        url = f"{URL}/4DACTION/Web_GF_Login"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "web_Username": self._account_number,
            "web_Password": self._account_pin,
            "web_Franchise": self._franchise,
            "web_Javascript": "false",
            "Submit": "Login",
        }

        response = requests.post(url, headers=headers, data=data, verify=False)

        soup = BeautifulSoup(response.content, "html.parser")
        upcoming_collection = soup.find(
            "div", class_="upcoming-collection next-collection"
        )

        entries = []

        if upcoming_collection:
            collection_date_str = upcoming_collection.find(
                "span", class_="not-v-cust"
            ).text.strip()
            collection_date = parse(collection_date_str, fuzzy=True)
            if collection_date:
                date = collection_date.date()
                entries.append(
                    Collection(date=date, t="Organic waste", icon="mdi:leaf")
                )

        return entries
