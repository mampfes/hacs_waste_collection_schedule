import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

#https://muellkalender.sector27.de/web/fetchPickups?callback=callbackFunc&licenseKey=DTTLN20137REKE382EHSE&cityId=9&streetId=2343&viewdate=1627812000&viewrange=yearRange&_=1629554459739
TITLE = "Sector 27"
DESCRIPTION = "Source for Muellkalender in Kreis RE."
URL = "https://muellkalender.sector27.de/web/fetchPickups"
TEST_CASES = {"Datteln": {"licenseKey":"DTTLN20137REKE382EHSE","cityId":"9","streetId":"2143"},
                "Marl": { "licenseKey":"MRL3102HBBUHENWIP","cityId":"3","streetId":"1055"}
            }

class Source:
    def __init__(self, licenseKey, cityId, streetId):
        self._licenseKey = licenseKey
        self._cityId = cityId
        self._streetId = streetId

    def getviewRange(self):
        now = datetime.datetime.now()
        mRange = []
        m = now.month
        
        y = now.year
        
        # fetch 3 Month

        for x in range(m,m+3):
            if x < 13:
                d = datetime.datetime(y,x,1,hour=12)
            else:
                d = datetime.datetime(y,x,1,hour=12)

            mRange.append(int(datetime.datetime.timestamp(d)))

        return mRange

    def fetch(self):
        args = {
            "licenseKey" : self._licenseKey,
            "cityId" :  self._cityId,
            "streetId" : self._streetId
        }    
        
        args["viewrange"] = "monthRange"
        entries = []

        for m in self.getviewRange():
            args["viewdate"] = m
            # get json file
            r = requests.get(URL, params=args)
            
            data = json.loads(r.text.replace("callbackFunc(","").replace(");",""))
            
            for d in data["pickups"]:

                type = data["pickups"][d][0]["label"]

                pickupdate = datetime.date.fromtimestamp(int(d))
                
                entries.append(Collection(pickupdate, type))

        return entries