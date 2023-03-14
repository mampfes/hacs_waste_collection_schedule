
import datetime
import logging
import re
from bs4 import BeautifulSoup

import requests

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.AbfallIO import SERVICE_MAP
from waste_collection_schedule.service.ICS import ICS


URL = "https://www.mein-abfallkalender.de"
COUNTRY = "de"
DESCRIPTION = "Source for mein-abfallkalender.de waste collection."
TITLE = "main-abfallkalender.de"

TEST_CASES = { 
    "bad-vilbel": {
        "city": "bad-vilbel",
        "street_id": 1268,
        "waste_types": [ 
            21, 
            22, 
            24, 
            23, 
            25, 
            126, 
            26
        ],
        "user_email": "test2@test.com"
    },
    "bad-vilbel_upwd": {
        "city": "bad-vilbel",
        "street_id": 1268,
        "cid": 4,
        "waste_types": [ 
            21, 
            22, 
            24, 
            23, 
            25, 
            126, 
            26
        ],
        "user_id": 265216,
        "user_pwd": "7156df05d0"
    }
}



class Source:
    def __init__ (self, city, street_id, waste_types, user_id=None, user_pwd=None, user_email=None, cid=None):
        self._city = city
        self._street_id = street_id
        self._waste_types = waste_types
        self._cid = cid
        self._ics = ICS()
        self._session = requests.Session()

        if not user_id and not user_pwd:
            if not user_email:
                print(f"Either user_id / user_pwd or user_email is required")
            else:
                self._auth = "email"
                self._user_email = user_email
        else:
            self._auth = "user_pwd"
            self._user_id = user_id
            self._user_pwd = user_pwd

    def get_download_link (self, city, street_id, waste_types, user_email):
        waste_type_str = "&".join([ f"filter_waste={s}" for s in waste_types ])
        url = "https://{city}.mein-abfallkalender.de/app/webcal.html?street_id={street_id}&filter_period=next_1000&filter_time_delta=noalarm&filter_usage=ical_download&{waste_type_str}&user_email={user_email}&user_email_confirm={user_email}&user_dsgvo=1".format(city=city, street_id=street_id, waste_type_str=waste_type_str, user_email=user_email)
        
        r = self._session.get(url)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        for a in soup.find_all("a"):
            if "ical.ics" in a['href']:
                return a['href']
        return None

    def fetch(self):
        waste_type_ids = ",".join([str(i) for i in self._waste_types])

        if self._auth == "email":
            dwl = self.get_download_link(city=self._city, waste_types=self._waste_types, street_id=self._street_id, user_email=self._user_email)
        else:
            dwl = "http://{city}.mein-abfallkalender.de/ical.ics?sid={street_id}&cd=inline&ft=noalarm&fu=ical_download&fp=next_1000&wids={waste_type_ids}&uid={user_id}&pwid={user_pwd}&cid={cid}&fn=Mein-Abfallkalender_Stadt_Bad_Vilbel_Zukünftige_Termine.ics".format(
                city=self._city, street_id=self._street_id, waste_type_ids=waste_type_ids, user_id=self._user_id, user_pwd=self._user_pwd, cid=self._cid
            )
        if not dwl:
            print(f"Error getting the ICS calendar")
            return
        dwl = dwl.replace("cd=attachment", "cd=inline")

        r = self._session.get(dwl)
        r.raise_for_status()
        
        entries = []
        dates = self._ics.convert(r.text)
        for d in dates:
            entries.append(Collection(d[0], d[1]))

        return entries
        

