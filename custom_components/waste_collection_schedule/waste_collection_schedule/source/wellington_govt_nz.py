import datetime
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wellington City Council"
DESCRIPTION = "Source for Wellington City Council."
URL = "https://wellington.govt.nz"
TEST_CASES = {
    "Chelsea St": {"streetName": "chelsea street"},  # Friday
    "Campbell St (ID Only)": {"streetId": "6515"},  # Wednesday
}
#Image Links: 
#https://wellington.govt.nz/assets/images/rubbish-recycling/rubbish-bag.png
#https://wellington.govt.nz/assets/images/rubbish-recycling/wheelie-bin.png
#https://wellington.govt.nz/assets/images/rubbish-recycling/glass-crate.png
MONTH = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def toDate(formattedDate):
    items = formattedDate.split()
    return datetime.date(int(items[2]), MONTH[items[1]], int(items[0]))


# Parser for <div> element with class wasteSearchResults
class WasteSearchResultsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._entries = []
        self._wasteType = None
        self._withinRecyclingClass = False
        self._withinCollectionDateClass = False
        self._withinCollectionItemsClass = False
        self._todaysDate = None
        self._workingWasteDate = None

    @property
    def entries(self):
        return self._entries

    def handle_endtag(self, tag):
        if tag == "div" and self._withinRecyclingClass:
            self._withinRecyclingClass = False        
        if tag == "br" and self._withinCollectionDateClass:
            self._withinCollectionDateClass = False
        if tag == "li" and self._withinCollectionItemsClass:
            self._withinCollectionItemsClass = False


    def handle_starttag(self, tag, attrs):
        if tag == "div":
            o = dict(attrs)
            if o.get("class", "") == "recycling-search-padder-content":
                self._withinRecyclingClass = True

        if tag == "p" and self._withinRecyclingClass:
            d = dict(attrs)
            className = d.get("class", "")
            if className.startswith("collection-date"):
                self._withinCollectionDateClass = True

        if tag == "li" and self._withinRecyclingClass:
            r = dict(attrs)
            className = r.get("class", "")
            if "h4 mt-0" in className:
                self._withinCollectionItemsClass = True
                

    def handle_data(self, data):

        # date span comes first, doesn't have a year
        if self._withinRecyclingClass:
            if self._withinCollectionDateClass:
                #TODO this needs a lot of clean up, I feel like its not optimised
                todays_date = datetime.date.today()
                # use current year, unless Jan is in data, and we are still in Dec
                year = todays_date.year
                if "January" in data and todays_date.month == 12:
                    # then add 1
                    year = year + 1
                fullDate = data.split(",")[-1].lstrip() + " " + f"{year}"
                self._workingWasteDate = toDate(fullDate)
        
            if self._withinCollectionItemsClass:
                wasteType = data
                self._entries.append(Collection(
                    self._workingWasteDate, 
                    wasteType,
                    picture=self.get_image(wasteType)
                    ))

    def get_image(self, wasteType):
        if wasteType == "Rubbish":
            return "https://wellington.govt.nz/assets/images/rubbish-recycling/rubbish-bag.png"
        if wasteType == "Glass crate":
            return "https://wellington.govt.nz/assets/images/rubbish-recycling/glass-crate.png"
        if wasteType == "Wheelie bin or recycling bags":
            return "https://wellington.govt.nz/assets/images/rubbish-recycling/wheelie-bin.png"
        


class Source:
    def __init__(
        self, streetId= None, streetName= None
    ):
        self._streetId = streetId
        self._streetName = streetName


    def fetch(self):
        # get token
        if self._streetName:  
            import json
            url = "https://wellington.govt.nz/layouts/wcc/GeneralLayout.aspx/GetRubbishCollectionStreets"
            headers = requests.structures.CaseInsensitiveDict()
            headers["Origin"] = "https://wellington.govt.nz/rubbish-recycling-and-waste/when-to-put-out-your-rubbish-and-recycling"
            headers["Access-Control-Request-Method"] = "POST"
            headers["Content-Type"] = "application/json"
            data = {"partialStreetName":self._streetName}
            json_string = json.dumps(data)
            r = requests.post(url, headers=headers, data=json_string)
            data = json.loads(r.text)
            if len(data["d"]) == 0:
                raise Exception(f"No result found for {self._streetName}") 
            if len(data["d"]) > 1: 
                raise Exception(f"More then one result returned for {self._streetName}, be more specific or use StreetId instead")
            self._streetId = data["d"][0].get('Key')
        if self._streetId:
            params = {"streetid": self._streetId}
            url = "https://wellington.govt.nz/rubbish-recycling-and-waste/when-to-put-out-your-rubbish-and-recycling/components/collection-search-results"
            r = requests.get(url, params=params)
            p = WasteSearchResultsParser()
            p.feed(r.text)
            return p.entries
