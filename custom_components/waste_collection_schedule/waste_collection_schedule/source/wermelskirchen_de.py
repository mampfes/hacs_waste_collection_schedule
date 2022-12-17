import requests
from datetime import datetime
import urllib.parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallkalender Wermelskirchen"
DESCRIPTION = "Source for Abfallabholung Wermelskirchen, Germany"
URL = "https://www.wermelskirchen.de/rathaus/buergerservice/formulare-a-z/abfallkalender-online/"

TEST_CASES = {
    "Rathaus": {"street": "Telegrafenstraße", "house_number": "29"},
    "Krankenhaus": {"street": "Königstraße", "house_number": "100"},
    "Mehrzweckhalle": {"street": "An der Mehrzweckhalle", "house_number": "1"},
}

INFOS = {
    "Restabfall 2-woechentlich": {
        "icon": "mdi:trash-can", 
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/1/b/csm_Restmuell_6b2b32c774.png" 
    },
    "Restabfall 4-woechentlich": {
        "icon": "mdi:trash-can",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/1/b/csm_Restmuell_6b2b32c774.png"
    },
    "Restabfall 6-woechentlich": {
        "icon": "mdi:trash-can",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/1/b/csm_Restmuell_6b2b32c774.png"
    },
    "Gelber Sack": {
        "icon": "mdi:recycle-variant", 
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/f/4/csm_GelbeTonne_24ffc276b2.png"
    },
    "Papier": {
        "icon": "mdi:package-variant",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/2/3/csm_Papiertonne_919ed3b5da.png"
    },
    "Biotonne": {
        "icon": "mdi:leaf",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/6/f/csm_Biotonne_wk_ae1b0e61aa.png"    
    },
    "Schadstoffsammlung": {
        "icon": "mdi:bottle-tonic-skull",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/4/2/csm_sondermuell_62f5701a7b.png"
    },
    "Weihnachtsbaum": {
        "icon": "mdi:pine-tree",
        "image": ""
    },
}

class Source:
    def __init__(self, street, house_number):
        self._street = street
        self._house_number = str(house_number)
        self._ics = ICS()

    def fetch(self):
        # the url contains the current year, but this doesn't really seems to matter at least for the ical, since the result is always the same
        # still replace it for compatibility sake
        now = datetime.now()
        url = (
            "https://abfallkalender.citkomm.de/wermelskirchen/abfallkalender-"+
            str(now.year)+
            "/ics/FrontendIcs.html?tx_citkoabfall_abfallkalender%5Bstrasse%5D="+
            urllib.parse.quote_plus(self._street)+
            "&tx_citkoabfall_abfallkalender%5Bhausnummer%5D="+
            urllib.parse.quote_plus(self._house_number)+
            "&tx_citkoabfall_abfallkalender%5Babfallarten%5D%5B0%5D=86&tx_citkoabfall_abfallkalender%5Babfallarten%5D%5B1%5D=85&tx_citkoabfall_abfallkalender%5Babfallarten%5D%5B2%5D=84&tx_citkoabfall_abfallkalender%5Babfallarten%5D%5B3%5D=82&tx_citkoabfall_abfallkalender%5Babfallarten%5D%5B4%5D=81&tx_citkoabfall_abfallkalender%5Babfallarten%5D%5B5%5D=80&tx_citkoabfall_abfallkalender%5Babfallarten%5D%5B6%5D=79&tx_citkoabfall_abfallkalender%5Babfallarten%5D%5B7%5D=76&tx_citkoabfall_abfallkalender%5Babfallarten%5D%5B8%5D=75&tx_citkoabfall_abfallkalender%5Babfallarten%5D%5B9%5D=74"
        )
        r = requests.get(url)
        r.raise_for_status()

        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            info = INFOS.get(d[1], {"icon": "mdi:trash-can", "image": ""})    
            entries.append(Collection(
                d[0], 
                d[1],
                picture = info['image'],
                icon = info['icon']
            ))
        return entries
