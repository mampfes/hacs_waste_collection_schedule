import logging
import requests
import time

from datetime import datetime
from waste_collection_schedule import Collection

TITLE = 'Middlesbrough Council'
DESCRIPTION = 'Source for waste collection services for Middlesbrough Council'
URL = 'https://www.middlesbrough.gov.uk'
TEST_CASES = {
    "Tollesby Road - number" : {"uprn": 100110140843},
    "Tollesby Road - string" : {"uprn": "100110140843"},
    "Victoria Road - number" : {"uprn": 100110774949},
    "Victoria Road - string" : {"uprn": "100110774949"},
}

API_URLS = {
    'session': 'https://my.middlesbrough.gov.uk/en/AchieveForms/?mode=fill&consentMessage=yes&form_uri=sandbox-publish://AF-Process-37a44b6e-cbef-499a-9fb9-d8d507613c95/AF-Stage-bfbb065e-0dda-4ae6-933d-9e6b91cc56ce/definition.json&process=1&process_uri=sandbox-processes://AF-Process-37a44b6e-cbef-499a-9fb9-d8d507613c95&process_id=AF-Process-37a44b6e-cbef-499a-9fb9-d8d507613c95&noLoginPrompt=1',
    'auth': 'https://my.middlesbrough.gov.uk/authapi/isauthenticated?uri=https%253A%252F%252Fmy.middlesbrough.gov.uk%252Fen%252FAchieveForms%252F%253Fmode%253Dfill%2526consentMessage%253Dyes%2526form_uri%253Dsandbox-publish%253A%252F%252FAF-Process-37a44b6e-cbef-499a-9fb9-d8d507613c95%252FAF-Stage-bfbb065e-0dda-4ae6-933d-9e6b91cc56ce%252Fdefinition.json%2526process%253D1%2526process_uri%253Dsandbox-processes%253A%252F%252FAF-Process-37a44b6e-cbef-499a-9fb9-d8d507613c95%2526process_id%253DAF-Process-37a44b6e-cbef-499a-9fb9-d8d507613c95%2526noLoginPrompt%253D1&hostname=my.middlesbrough.gov.uk&withCredentials=true',
    'schedule': 'https://my.middlesbrough.gov.uk/apibroker/runLookup?id=5d78f40439054&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&'
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
}

COOKIES = {
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)
    def fetch(self):
        s = requests.Session()

        #This request sets up the cookies
        r0 = s.get(API_URLS['session'], headers=HEADERS)
        r0.raise_for_status()

        #This request gets the session key from the PHPSESSID (in the cookies)
        authRequest = s.get(API_URLS['auth'], headers=HEADERS)
        authData = authRequest.json()
        sessionKey = authData['auth-session']
        now = time.time_ns() // 1_000_000

        #now query using the uprn
        payload = {
            "formValues": { "Find My Collection Dates": { "uprn_search": { "value": self._uprn } } }
        }
        scheduleRequest = s.post(API_URLS['schedule'] + '&_' + str(now) + '&sid=' + sessionKey , headers=HEADERS, json=payload)
        data = scheduleRequest.json()['integration']['transformed']['rows_data']['0']

        refuseDates = data['Refuse'].split('<br />')
        recyclingDates = data['Recycling'].split('<br />')
        greenDates = data['Green'].split('<br />')

        entries = []

        for date in refuseDates:
            if len(date) > 0:
                entries.append(Collection(
                    date = datetime.strptime(date, '%d/%m/%Y').date(),
                    t = 'refuse bin',
                    icon = 'mdi:trash-can'
                ))

        for date in recyclingDates:
            if len(date) > 0:
                entries.append(Collection(
                    date = datetime.strptime(date, '%d/%m/%Y').date(),
                    t = 'recycling bin',
                    icon = 'mdi:recycle'
                ))

        for date in greenDates:
            if len(date) > 0:
                entries.append(Collection(
                    date = datetime.strptime(date, '%d/%m/%Y').date(),
                    t = 'green bin',
                    icon = 'mdi:leaf'
                ))

        return entries
