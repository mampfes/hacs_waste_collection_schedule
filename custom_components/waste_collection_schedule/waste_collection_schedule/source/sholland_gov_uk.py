import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from bs4 import BeautifulSoup, Tag
import datetime
import re

TITLE = "South Holland District Council"
DESCRIPTION = "Source for South Holland District Council."
URL = "https://www.sholland.gov.uk/"
TEST_CASES = {
    "10002546801": {
        "uprn": 10002546801,
        "postcode": "PE11 2FR",
    },
    "PE12 7AR": {
        "uprn": "100030897036",
        "postcode": "PE12 7AR",
    }
}

ICON_MAP = {
    "refuse": "mdi:trash-can",
    "garden": "mdi:leaf",
    "recycling": "mdi:recycle",
}


API_URL = "https://www.sholland.gov.uk/article/7156/Check-your-collection-days"

class Source:
    def __init__(self, uprn: str | int, postcode: str):
        self._uprn: str | int = str(uprn)
        self._postcode: str = postcode
         

    def fetch(self):
        args: dict[str, str|list] = {
            "SHDCWASTECOLLECTIONS_FORMACTION_NEXT": "SHDCWASTECOLLECTIONS_PAGE1_CONTINUEBUTTON",
            "SHDCWASTECOLLECTIONS_PAGE1_POSTCODENEW": self._postcode,
            "SHDCWASTECOLLECTIONS_PAGE1_BUILDING": "",
            "SHDCWASTECOLLECTIONS_PAGE1_ADDRESSLIST": ["", self._uprn]
        }
        s = requests.Session()
        
        r = s.get(API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        
        form = soup.find("form", {"id": "SHDCWASTECOLLECTIONS_FORM"})
        if not form or not isinstance(form, Tag):
            raise Exception("Unable to find form")
        
        request_url = form.attrs.get("action")
        hidden_values = form.find_all("input", {"type": "hidden"})
        
        if not hidden_values:
            raise Exception("Unable to find hidden values")
        
        for val in hidden_values:
            if not isinstance(val, Tag) or "SHDCWASTECOLLECTIONS_PAGE1_ADDRESSLIST" == str(val.attrs.get("name")):
                continue           
            args[str(val.attrs.get("name"))] = str(val.attrs.get("value"))         
        
        

        
        # get collection page
        r = requests.post(str(request_url), data=args)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
            
        entries = []
        for d in soup.find_all("div", {"class": "nextcoll"}):
            if not isinstance(d, Tag):
                continue
                
            collection_text = d.text.strip()

            bin_type = collection_text.split(" ")[1]
            icon=ICON_MAP.get(bin_type.lower())  # Collection icon

            splittet_text = collection_text.split(":")
            
            dates_str = [splittet_text[1].split("(")[0]]
            if len(splittet_text) > 2:
                dates_str.append(splittet_text[2].split("(")[0])
                
            for date_str in dates_str:
                date_str = date_str.replace("*", "").strip()
                date = datetime.datetime.strptime(re.sub(r'(\d)(st|nd|rd|th)', r'\1', date_str), "%A %d %B %Y").date()
                entries.append(Collection(date=date, t=bin_type,icon=icon))

        return entries
