import datetime
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS


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

class Source:
    def __init__(self, streetId= None, streetName= None):
        self._streetId = streetId
        self._streetName = streetName
        self._ics = ICS()

    def get_icon(self, wasteType):
        if wasteType == "Rubbish Collection":
            return "mdi:trash-can"
        if wasteType == "Glass crate":
            return "mdi:glass-fragile"
        if wasteType == "Wheelie bin or recycling bags":
            return "mdi:recycle"
        return None

    def get_image(self, wasteType):
        if wasteType == "Rubbish Collection":
            return "https://wellington.govt.nz/assets/images/rubbish-recycling/rubbish-bag.png"
        if wasteType == "Glass crate":
            return "https://wellington.govt.nz/assets/images/rubbish-recycling/glass-crate.png"
        if wasteType == "Wheelie bin or recycling bags":
            return "https://wellington.govt.nz/assets/images/rubbish-recycling/wheelie-bin.png"
        return None
        

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
            url = "https://wellington.govt.nz/~/ical/"
            params = {"type":"recycling","streetId":self._streetId,"forDate": datetime.date.today()}
            r = requests.get(url, params=params)
            dates = self._ics.convert(r.text)
            entries = []
            for d in dates:
                for wasteType in d[1].split("&"):
                    wasteType = wasteType.strip()
                    entries.append(Collection(d[0], wasteType, picture=self.get_image(wasteType), icon=self.get_icon(wasteType)))
            return entries
