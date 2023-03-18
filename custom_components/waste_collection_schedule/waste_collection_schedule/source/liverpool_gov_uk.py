from datetime import datetime

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from waste_collection_schedule import Collection

TITLE = "Liverpool City Council"
DESCRIPTION = "Source for liverpool.gov.uk services for Liverpool City"
URL = "https://www.liverpool.gov.uk"

TEST_CASES = {
    "52 Swallowhurst Crescent Liverpool L11 2UZ": {"uprn": "38148233"},
    "1 Aston Street Liverpool L19 8LR": {"uprn": "38010019"},
}

API_URL = "https://liverpool.gov.uk/Bins/BinDatesTable?UPRN={uprn}&HideGreenBin=False&ShowTable=True"

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green": "mdi:leaf",
}


class Source:
    def __init__(self, uprn=None, postcode=None, name_number=None):
        self._uprn = uprn

    def fetch(self):
        today = datetime.today().date()
        entries = []

        def trimsuffix(s):                                             
            return re.sub(r'(\d)(st|nd|rd|th)', r'\1', s)
        
        q = str(API_URL).format(uprn=self._uprn)
        
        r = requests.get(q)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.findAll('table')

        rows = table[0].findAll(lambda tag: tag.name=='tr')

        for row in rows[1:]:
            type=' '.join(row.find('th').text.split())
            fields = row.find_all('td')
            for field in fields:
                collectiondate = trimsuffix(' '.join(field.text.split()) + " " + datetime.today().strftime("%Y"))
                if re.match('Today',collectiondate):
                    date = today
                elif re.match('Tomorrow',collectiondate):
                    date = today + timedelta(days=1)
                else:
                    date = datetime.strptime(collectiondate, '%A, %d %B %Y').date()
        
                # As no year is specified we might need to add one year if it crosses Dec 31st
                if date < today:
                        date.replace(year = today.year + 1)
        
                entries.append(
                    Collection(
                        date=date,
                        t=type,
                        icon=ICON_MAP.get(type),
                    )
                )
        
        return entries
