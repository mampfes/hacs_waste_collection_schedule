import datetime
from waste_collection_schedule import Collection
import datetime
import requests
import re
from bs4 import BeautifulSoup



TITLE = "ZAW Darmstadt-Dieburg" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for waste collection in Darmstadt-Dieburg zaw-online.de"  # Describe your source
URL = "https://zaw-online.de/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "AlsbachAkatienweg": {"city": "MQ", "street": "Nzc0MQ"},
    "GriesheimDonaustr": {"city": "OA", "street": "MzUyMQ"},
    "MesselMeisenweg": {"city": "MTI", "street": "ODM5Ng"},
    "SeeheimAmselweg": {"city": "MjM", "street": "NzI0NA"}
}

API_URL = "https://zipo.zaw-online.de/api/calendar.php"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "Restmüll": "mdi:trash-can",
    "Schadstoffmobil": "mdi:truck-alert-outline",
    "Gelber Sack": "mdi:sack",
    "Biomüll": "mdi:leaf",
    "Papier": "mdi:package-variant",
}


class Source:
    def __init__(self, street, city): 
        self.street = street
        self.city = city

    def fetch(self):
        ticket_search = re.search("https://zipo\.zaw-online\.de/api/calendar\.php\?ticket=[A-Za-z0-9]*",
            requests.post(API_URL).text)
        
        if ticket_search is None:
            print("No ticket found")
            return []
        ticket = ticket_search.group(0).split("=")[1]
        #  replace this comment with
        #  api calls or web scraping required
        #  to capture waste collection schedules
        #  and extract date and waste type details
        params = {'ticket': ticket}
        data = {
            "filterFormData": f"wastelOrt={self.city}&wastelStreet={self.street}&artid[]=Mw&artid[]=NA&artid[]=Mg&artid[]=MQ&artid[]=NQ&excludeweekly=1"
        }
        entries = []  # List that holds collection schedule

        r = requests.post(
            API_URL, params=params, data=data
        )
        soup = BeautifulSoup(r.text, features="html.parser")
        table = soup.find("table", {"id": "termineTable"})
        if table is None:
            return []
        
        rows = table.find("tbody").find_all("tr")
        
        for row in rows:
            cells = row.find_all("td")
            if len(cells) != 4:
                continue
            date = datetime.datetime.strptime(cells[1].text, "%d.%m.%Y").date()
            waste_type = cells[2].text
            entries.append(
                Collection(
                    date=  date,  # Collection date
                    t= waste_type,  # Collection type
                    icon = ICON_MAP.get(waste_type),  # Collection icon
                )
            )
        return entries