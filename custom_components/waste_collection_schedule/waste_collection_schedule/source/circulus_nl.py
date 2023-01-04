import requests
from datetime import date, timedelta, datetime
from waste_collection_schedule import Collection

TITLE = "Circulus"
DESCRIPTION = "Source for circulus.nl waste collection."
URL = "https://mijn.circulus.nl"

TEST_CASES = {
    "Test1": {"postal_code": "7206AC", "house_number": "1"},
}

ICON_MAP = {
    "REST": "mdi:trash-can",
    "ZWAKRA": "mdi:recycle",
    "GFT": "mdi:leaf",
    "PAP": "mdi:newspaper-variant-multiple"
}

WASTE_MAP = {
    "REST": "Zwarte Kliko",
    "ZWAKRA": "Glas & Blik",
    "GFT": "Groene Kliko",
    "PAP": "Papier"
}


class Source:
    def __init__(self, postal_code, house_number):
        self._postal_code = postal_code
        self._house_number = house_number

    def fetch(self):
        location_data = {
            'zipCode': self._postal_code,
            'number': self._house_number
        }
        cookie_url = 'https://mijn.circulus.nl/register/zipcode.json'
        json_url = 'https://mijn.circulus.nl/afvalkalender.json'
        entries = []

        # Make a post request and store the cookies
        fetchcookie = requests.post(cookie_url, data=location_data).cookies

        # Check if the CB_SESSION cookie exists
        if 'CB_SESSION' in fetchcookie:
            # Make a GET request and store the JSON data
            req_params = {
                'from': date.today().strftime('%Y-%m-%d'),
                'till': (date.today()+timedelta(days=365)).strftime('%Y-%m-%d')
            }

            garbagedata = requests.get(json_url, params=req_params, cookies=fetchcookie).json()['customData']['response']['garbage']

            for item in garbagedata:
                for newdate in item['dates']:
                    entries.append(
                        Collection(
                            date=datetime.strptime(newdate, '%Y-%m-%d').date(),
                            t=WASTE_MAP[item['code']],
                            icon=ICON_MAP[item['code']]
                        )
                    )
            return entries
        else:
            return entries
