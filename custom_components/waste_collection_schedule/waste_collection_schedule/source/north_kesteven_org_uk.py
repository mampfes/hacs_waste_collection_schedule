import requests

from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
import re

TITLE = "North Kesteven District Council"
DESCRIPTION = "Source for n-kesteven.org.uk services for North Kesteven District Council, UK."
URL = "https://n-kesteven.org.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100030866950"},
    "Test_002": {"uprn": "10006514327"},
    "Test_003": {"uprn": "100030857039"},
    "Test_004": {"uprn": 100030864449},
}
ICON_MAP = {
    "BLACK (DOMESTIC)": "mdi:trash-can",
    "GREEN (RECYCLING)": "mdi:recycle",
    "PURPLE (PAPER/CARD)": "mdi:newspaper",
    "BROWN (GARDEN WASTE)": "mdi:leaf"
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        r = s.get(f"https://www.n-kesteven.org.uk/bins/display?uprn={self._uprn}")
        soup = BeautifulSoup(r.text, "html.parser")
        bins = soup.findAll("div", {"class":"bins-next"})
        
        entries = []
        for bin in bins:
            if not bin.has_attr("class"):
                continue
            bin_name = bin.find("h3").text
            icon = ICON_MAP.get(bin_name.upper())
            
            date_div_id = ""
            for c in bin["class"]:
                if re.match(r"bin-\w+-next", c):
                    date_div_id = c.replace("bin-", "").replace("-next", "") + "-view"
                    break
                
            if not date_div_id:
                continue
            
            dates_div = soup.find("div", {"id": date_div_id})
            if not dates_div:
                continue
            
            for date_li in dates_div.find_all("li"):
                date = date_li.text
                try:
                    date = datetime.strptime(date.split(",")[1].strip(), "%d %B %Y").date()
                except:
                    print("No date")
                    continue
            
                entries.append(
                            Collection(
                                date=date,
                                t=bin_name,
                                icon=icon,
                            )
                        )
        
        return entries
    