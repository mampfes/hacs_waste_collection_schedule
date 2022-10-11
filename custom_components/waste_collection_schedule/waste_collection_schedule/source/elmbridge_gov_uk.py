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
    "Test_001" : {"uprn": 10013119164}, #F
    "Test_002": {"uprn": "100061309206"}, #F
    "Test_003": {"uprn": 100062119825}, #Tu
    "Test_004": {"uprn": "100061343923"}, #M
    "Test_005": {"uprn": 100062372553}, #W & Tu
}

API_URLS = {
    'session': 'https://emaps.elmbridge.gov.uk/myElmbridge.aspx',
    'search': 'https://emaps.elmbridge.gov.uk/myElmbridge.aspx?action=SetAddress&UniqueId={}',
    'schedule': 'https://emaps.elmbridge.gov.uk/myElmbridge.aspx?tab=0#Refuse_&_Recycling',
}

OFFSETS = {
    'Monday': 0,
    'Tuesday': 1,
    'Wednesday': 2,
    'Thursday': 3,
    'Friday': 4,
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
        # API's do not return the year, nor the date of the collection.
        # They return a list of dates for the beginning of a week, and the day of the week the collection is on.
        # This script assumes the week-commencing dates are for the current year, but...
        # This'll cause problems in December as upcoming January collections will have been assigned dates in the past.
        # Some clunky logic can deal with this:
        #   If a date in less than 1 month in the past, it doesn't matter as the collection will have recently occured.
        #   If a date is more than 1 month in the past, assume it's an incorrectly assigned date and increment the year by 1.
        # One that's been done, offset the week-commencing dates given to match day of the week each waste collection type is scheduled. 
        # If you have a better way of doing this, feel free to update via a Pull Request!

        # Get current date and year in format consistent with API result
        today = datetime.now()
        today = today.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        year = today.year

        s = requests.Session()

        r0 = s.get(API_URLS['session'], headers=HEADERS)
        r0.raise_for_status()
        sleep(5)
        # print(API_URLS['search'].format(self._uprn))
        r1 = s.get(API_URLS['search'].format(self._uprn), headers=HEADERS)
        r1.raise_for_status()
        sleep(5)
        r2 = s.get(API_URLS['schedule'], headers=HEADERS)
        r2.raise_for_status()
        
        responseContent = r2.content
        soup = BeautifulSoup(responseContent, 'html.parser')

        entries = []

        notice = soup.find('div', {'class': 'atPanelContent atFirst atAlt0'})
        notices = notice.text.replace('\nRefuse and recycling collection days\n', '').split('.')
        # temp2 = temp.replace('\nRefuse and recycling collection days\n', '')
        # notices = temp2.split('.')
        notices.pop(-1) # Remove superflous element
        # print(notices)
        frame = soup.find('div', {'class': 'atPanelContent atAlt1 atLast'})
        table = frame.find('table')

        for tr in table.find_all('tr'):
            row = []
            for td in tr.find_all('td'):
                row.append(td.text.strip())
            row.pop(1)  # removes superflous element
            dt = row[0] + ' ' + str(year)
            dt = datetime.strptime(dt, '%d %b %Y')

            # Amend year, if necessary
            if (dt - today) < timedelta(days = -31):
                dt += timedelta(year = 1)
            row[0] = dt

            # Separate out same-day waste collections
            wastetypes = row[1].split(' + ')

            # Now sort out date offsets for each collection type
            for waste in wastetypes:
                for day, offset in OFFSETS.items():
                    for sentance in notices:
                        if (waste in sentance) and (day in sentance):
                            # print(waste, day, row[0], offset)
                            new_date = row[0] + timedelta(days = offset)
                            entries.append(
                                Collection(
                                    date = new_date.date(),
                                    t = waste + ' bin',
                                    icon = ICONS.get(waste.upper()),
                                )
                            )

        return entries
