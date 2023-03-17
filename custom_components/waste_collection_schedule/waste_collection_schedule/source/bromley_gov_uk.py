import re
import requests
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "London Borough of Bromley."
DESCRIPTION = "Source for bromley.gov.uk services for London Borough of Bromley, UK."
URL = "https://bromely.gov.uk"
TEST_CASES = {
    "Test_001": {"PropertyID": "6328436"},
    "Test_002": {"PropertyID": "6146611"},
    "Test_003": {"PropertyID": 6328436}
}

ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GREEN": "mdi:leaf",
    "COMMUNAL REFUSE": "mdi:trash-can",
    "COMMUNAL RECYCLING": "mdi:recycle",
}

REGEX_TITLES = r"<h3.*>([A-za-z;&\-\(\), ]*)[<\/h3]"
REGEX_NEXT = r"([a-zA-Z]*, [0-9]{1,2}[a-z]{2} [A-Za-z]*)[\n]"
REGEX_LAST = r"([a-zA-Z]*, [0-9]{1,2}[a-z]{2} [A-Za-z]*),\sat\s*[0-9]{1,2}:[0-9]{2}"
REGEX_ORDINALS = r"(st|nd|rd|th) "

class Source:
    def __init__(self, property):
        self._property = str(property)

    def fetch(self):

        today = datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        yr = int(today.year)

        s = requests.Session()
        r = s.get(f"https://recyclingservices.bromley.gov.uk/waste/{self._property}")

        waste_col = re.findall(REGEX_TITLES, r.text)
        next_col = re.findall(REGEX_NEXT, r.text)
        last_col = re.findall(REGEX_LAST, r.text)

        # website doesn't include the year, so lets add them
        # and try and deal with year-end transitions
        date_collection = []
        for (t, n, l) in zip(waste_col, next_col, last_col):
            x = t.replace("&amp;", "&")
            d = re.compile(REGEX_ORDINALS).sub("", n.split(", ")[1])
            if "December" in l and "January" in n:
                d = d + str(yr+1)
            else:
                d = d + str(yr)
            d = datetime.strptime(d,"%d%B%Y").date()
            date_collection.append([x, d])

        entries = []
        for item in date_collection:
            entries.append(
                Collection(
                    date=item[1],
                    t=item[0],
                    icon=ICON_MAP.get(t),
                )
            )
        
        return entries
