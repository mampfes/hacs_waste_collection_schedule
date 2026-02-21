from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Panda Waste"
DESCRIPTION = "Source for Panda Waste, Ireland."
URL = "https://www.panda.ie/"
TEST_CASES = {
    "!secret panda_account_number !secret panda_pin": {
        "account_number": "!secret panda_account_number",
        "pin": "!secret panda_pin",
    }
}


ICON_MAP = {
    "Waste": "mdi:trash-can",
    "Compost": "mdi:leaf",
    "Recycling": "mdi:recycle",
}


COLLECTION_URL = (
    "https://domesticmobileserviceapi.azurewebsites.net/api/Account/GetData"
)
LOGIN_URL = "https://domesticmobileserviceapi.azurewebsites.net/token"
COMPANY_KEY = "7ACA415F-E1DB-421B-90D7-6302D2B51FF7"

# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "You can use the account id and pin provided by the company, which are the same details to access their mobile apps.",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "account_number": "The account number",
        "pin": "The PIN",
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "account_number": "Account Number",
        "pin": "PIN",
    },
}

# ### End of arguments affecting the configuration GUI ####


class Source:
    def __init__(self, account_number: str, pin: str):
        self._account_number: str = account_number
        self._pin: str = pin

    def fetch(self) -> list[Collection]:
        now = datetime.now()
        r = requests.post(
            LOGIN_URL,
            data={
                "grant_type": "password",
                "username": f"{COMPANY_KEY}_{self._account_number}",
                "password": self._pin,
            },
        )
        r.raise_for_status()
        data = r.json()
        if "error" in data and data["error_description"] != "":
            raise Exception(data["error_description"])

        token = data["access_token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "updatetime": now.strftime("%d/%m/%Y %H:%M:%S"),
            "companykey": COMPANY_KEY,
        }
        r = requests.get(COLLECTION_URL, headers=headers)
        r.raise_for_status()

        data = r.json()

        entries = []

        for detail in data["nextCollectionDetails"]:
            date = datetime.strptime(
                detail["nextCollectionDate"], "%Y-%m-%dT%H:%M:%S"
            ).date()
            bin_type = detail["binType"]
            icon = ICON_MAP.get(bin_type)
            entries.append(Collection(date=date, t=bin_type, icon=icon))
        return entries
