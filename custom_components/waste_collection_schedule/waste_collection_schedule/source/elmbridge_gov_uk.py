from calendar import month
import logging
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from time import sleep
from waste_collection_schedule import Collection

TITLE = 'elmbridge.gov.uk'
DESCRIPTION = (
    'Source for waste collection services for Elmbridge Borough Council'
)
URL = 'https://www.elmbridge.gov.uk/waste-and-recycling/'


HEADERS = {
    "user-agent": "Mozilla/5.0",
}

TEST_CASES = {
    "Test_001" : {"uprn": 10013119164},
    "Test_002": {"uprn": "100061309206"},   # need to change this one
    "Test_003": {"uprn": 100031205198},
    "Test_004": {"uprn": "100061343923"}
}

API_URLS = {
    'session': 'https://emaps.elmbridge.gov.uk/myElmbridge.aspx',
    'search': 'https://emaps.elmbridge.gov.uk/myElmbridge.aspx?action=SetAddress&UniqueId={}',
    'schedule': 'https://emaps.elmbridge.gov.uk/myElmbridge.aspx?tab=0#Refuse_&_Recycling',
}

ICONS = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "FOOD": "mdi:food",
    "GARDEN": "mdi:leaf",
}


_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, uprn: str = None):
        self._uprn = str(uprn)

    def fetch(self):
        # Collection dates returned do not contain a year, so assume they are for the current year.
        # This'll cause problems in December as upcoming January collections will have been assigned dates in the past.
        # Some clunky logic can deal with this:
        #   If a date in less than 1 month in the past, it doesn't matter as the collection will have recently occured.
        #   If a date is more than 1 month in the past, assume it's an incorrectly assigned date and increment the year by 1.
        # Better ideas welcome!

        today = datetime.now()
        today = today.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        year = today.year

        s = requests.Session()

        r0 = s.get(API_URLS['session'], headers=HEADERS)
        r0.raise_for_status()
        sleep(5)
        print(API_URLS['search'].format(self._uprn))
        r1 = s.get(API_URLS['search'].format(self._uprn), headers=HEADERS)
        r1.raise_for_status()
        sleep(5)
        r2 = s.get(API_URLS['schedule'], headers=HEADERS)
        r2.raise_for_status()
        
        responseContent = r2.content
        # print(responseContent)

        soup = BeautifulSoup(responseContent, 'html.parser')

        entries = []

        frame = soup.find('div', {'class': 'atPanelContent atAlt1 atLast'})
        table = frame.find('table')

        rows = table.find_all('tr')
        # print(rows)
        # tds = table.find_all('td')
        # print(tds)


        for tr in table.find_all('tr'):
            row = []
            for td in tr.find_all('td'):
                row.append(td.text.strip())
            row.pop(1)  # removed superflous element
            dt = row[0] + ' ' + str(year)
            dt = datetime.strptime(dt, '%d %b %Y')
            print(dt)
            if (dt - today) < timedelta(-365/12):
                dt = dt.replace(year = dt.year + 1)
            row[0] = dt

            wastetypes = row[1].split(' + ')
            for waste in wastetypes:
                entries.append(
                    Collection(
                        date = row[0],
                        t = waste + ' bin',
                        icon = ICONS.get(waste.upper())
                    )
                )
        print(entries)
        return entries
