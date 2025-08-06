from datetime import datetime

import html
import json
import re
import requests

from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from bs4 import BeautifulSoup

TITLE = "Greyhound Recycling"
DESCRIPTION = "Source for Greyhound Recycling, Ireland."
URL = "https://greyhound.ie/"
TEST_CASES = {
    "Greyhound (secrets.yaml)": {
        "account_number": "!secret greyhound_account_number",
        "pin": "!secret greyhound_pin",
    }
}

ICON_MAP = {
    "BLACK": "mdi:trash-can",
    "BROWN": "mdi:leaf",
    "GREEN": "mdi:recycle",
}


COLLECTION_URL = (
    "https://app.greyhound.ie/collection/collection_calendar"
)
LOGIN_URL = "https://app.greyhound.ie/"


# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "You can use the account number and pin provided by the company, which are the same details to access their mobile app.",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "account_number": "Account Number",
        "pin": "PIN",
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "account_number": "Account Number",
        "pin": "PIN Number",
    },
}

# ### End of arguments affecting the configuration GUI ####

class GreyhoundAPIError(Exception):
    """Exception raised for errors in the Greyhound API."""


class GreyhoundAPICommunicationError(GreyhoundAPIError):
    """Communication error with the API."""



class Source:
    def __init__(self, account_number: str, pin: str):
        if not account_number:
            raise SourceArgumentRequired(
                argument="account_number",
                reason="Account number is required to authenticate with Greyhound API."
            )
        if not pin:
            raise SourceArgumentRequired(
                argument="pin",
                reason="PIN is required to authenticate with Greyhound API."
            )             
        self._account_number: str = account_number
        self._pin: str = pin

    def fetch(self) -> list[Collection]:
        now = datetime.now()
        # Start a session to persist cookies
        session = requests.Session()
        
        try:
            response = session.get(LOGIN_URL)
            response.raise_for_status()
        except requests.RequestException as err:
            raise GreyhoundAPICommunicationError("Failed to load login page") from err
        
        soup = BeautifulSoup(response.text, 'html.parser')

        token_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        if token_input:
            csrf_token = token_input['value']  # type: ignore
        else:
            raise Exception("CSRF token not found. The page layout may have changed.")
        
        login_data = {
            'csrfmiddlewaretoken': csrf_token,
            'customerNo':  self._account_number,
            'pinCode': self._pin
        }        
        headers = {
            "Referer": LOGIN_URL,
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
        }    
   
        post = session.post(LOGIN_URL, data=login_data, headers=headers)        
        post.raise_for_status()     
               
        calendar_page = session.get(COLLECTION_URL)
        calendar_page.raise_for_status()  
            
        # 1. Extract the content of the `var data = "..."` string
        match = re.search(r'var data = "(.*?)getJSONData', calendar_page.text, re.DOTALL)
        if not match:
            raise GreyhoundAPIError("Could not find embedded calendar data.")
        
        raw_data_str = match.group(1)
        unescaped = html.unescape(raw_data_str)
        json_match = re.search(r'({.*?})"', unescaped, re.DOTALL)        
        if not json_match:
            raise GreyhoundAPIError("Failed to extract JSON payload.")

        try:
            raw_json = json.loads(json_match.group(1))
            collection_days = raw_json["data"]["collection_days"]
        except (json.JSONDecodeError, KeyError) as err:        
            raise GreyhoundAPIError("Invalid calendar data format.") from err
        
        entries = []
        
        for date_str, bin_entries in collection_days.items():
            try:
                event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue            
        
            for bin_entry in bin_entries:
                for bin_type in bin_entry.get("waste_types", []):
                    bin_type_normalized = bin_type.strip().upper()
                    icon = ICON_MAP.get(bin_type_normalized)
                    entries.append(Collection(date=event_date, t=bin_type_normalized, icon=icon))   
                    
        return entries
