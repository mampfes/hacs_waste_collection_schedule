import datetime
import json
import time
from urllib.parse import quote

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Seattle Public Utilities"
DESCRIPTION = "Source for Seattle Public Utilities waste collection."
URL = "https://myutilities.seattle.gov/eportal/#/accountlookup/calendar"    
TEST_CASES = {
    "City Hall": {"street_address": "600 4th Ave"},
    "Honey Hole": {"street_address": "703 E Pike St"},
    "Carmona Court": {"street_address": "1127 17th Ave E"},
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):

        # Mimicking the same API calls the calendar lookup page uses:
        # 1. find account code
        # 2. find account ID for a given address
        # 3. get token (uses basic auth and the customerID = guest
        # 4. get account summary
        # 5. get calendar

        #step 1
        find_address_payload = {
            "address": {
                "addressLine1": "1127 17th Ave E",
                "city": "",
                "zip": ""
            }
        }

        r = requests.post(
            f"https://myutilities.seattle.gov/rest/serviceorder/findaddress",
            json=find_address_payload)

        address_info = json.loads(r.text)
        prem_code = address_info["address"][0]["premCode"]
        
        #step 2 
        find_account_payload = {
            "address": {
                "premCode": prem_code
            }
        }

        r = requests.post(
            f"https://myutilities.seattle.gov/rest/serviceorder/findAccount",
            json=find_account_payload)


        account_info = json.loads(r.text)
        account_number = account_info["account"]["accountNumber"]



        #step 3
        token_payload = {"grant_type": "password", "username":"guest","password":"guest"}

        r = requests.post(
            f"https://myutilities.seattle.gov/rest/auth/token",
            data=token_payload)
       
        token_info = json.loads(r.text)
        token = token_info["access_token"]

        headers = {
            "Authorization": "Bearer {0}".format(token)
        }

        #step 4
        swsummary_payload = {
            "customerId": "guest",
            "accountContext": {
                "accountNumber": account_number,
                "personId": None,
                "companyCd": None,
                "serviceAddress": None
            }
        }

        r = requests.post(
            f"https://myutilities.seattle.gov/rest/account/swsummary",
            json=swsummary_payload,
            headers=headers)


    
        summary_info = json.loads(r.text)
        # the description property in each service in swServices it's either 'Garbage', 'Recycle', or 'Food/Yard Waste'
        swServices = summary_info["accountSummaryType"]["swServices"][0]["services"]
        personId = summary_info["accountContext"]["personId"]
        companyCd = summary_info["accountContext"]["companyCd"]


        #step 5
        waste_calendar_payload = {
            "customerId": "guest",
            "accountContext": {
                "accountNumber": account_number,
                "personId": personId,
                "companyCd": companyCd
            },
            "servicePoints": []
        }

        #fill out payload
        for service in swServices:
            waste_calendar_payload["servicePoints"].append(service["servicePointId"])


        r = requests.post(
            f"https://myutilities.seattle.gov/rest/solidwastecalendar",
            json=waste_calendar_payload,
            headers=headers)


        calendar_info = {}
        entries = []


        calendar_info = json.loads(r.text)

        for service in swServices:
            name = service["description"]
            servicePointId = service["servicePointId"]
            next_date = datetime.datetime.strptime(calendar_info["calendar"][servicePointId+"_NP"][0], "%m/%d/%Y").date()
            
            if name == "Garbage":
                entries.append(
                    Collection(date=next_date, t="Garbage", icon="mdi:trash-can")
                )

            elif name == "Recycle":
                entries.append(
                    Collection(date=next_date, t="Recycling", icon="mdi:recycle")
                )

            elif name == "Food/Yard Waste":
                entries.append(
                    Collection(date=next_date, t="Recycling", icon="mdi:leaf")
                )

        return entries
