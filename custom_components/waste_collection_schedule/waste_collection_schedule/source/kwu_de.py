import requests
from bs4 import BeautifulSoup
from datetime import date
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "KWU Entsorgung Landkreis Oder-Spree"
DESCRIPTION = "Source for KWU Entsorgung, Germany"
URL = "https://www.kwu-entsorgung.de/"
TEST_CASES = {
    "Erkner": {"city": "Erkner", "street": "Heinrich-Heine-Straße", "number": "11"},
    "Bad Saarow": {"city": "Bad Saarow", "street": "Ahornallee", "number": "1"}
}

HEADERS = {"user-agent": "Mozilla/5.0 (xxxx Windows NT 10.0; Win64; x64)"}
ICON_MAP  = {
    "Restabfall": "mdi:trash-can-outline",
    "Gelber Sack" : "mdi:recycle",
    "Papiertonne" : "mdi:package-variant",
    "Biotonne": "mdi:food-apple-outline",
} 


class Source:
    def __init__(self, city, street, number):
        self._city = city
        self._street = street
        self._number = number
        self._ics = ICS()

    def fetch(self):
        session = requests.Session()

        params = {
            "city": self._city,
            "street": self._street,
            "number": self._number,
            "direct": "true",
        }

        r = requests.get("https://www.kwu-entsorgung.de/inc/wordpress/kal_objauswahl.php", headers=HEADERS)
        parsed_html = BeautifulSoup(r.text, "html.parser")
        Orte = parsed_html.find_all('option')

        for Ort in Orte:
            if self._city in Ort.text:
                OrtValue = Ort['value']
                break

        r = requests.get("https://www.kwu-entsorgung.de/inc/wordpress/kal_str2ort.php", params={"ort": OrtValue}, headers=HEADERS)
        parsed_html = BeautifulSoup(r.text, "html.parser")
        Strassen = parsed_html.find_all('option')

        for Strasse in Strassen:
            if self._street in Strasse.text:
                StrasseValue = Strasse['value']
                break

        r = requests.get("https://www.kwu-entsorgung.de/inc/wordpress/kal_str2ort.php", params={"ort": OrtValue, "strasse": StrasseValue}, headers=HEADERS)
        parsed_html = BeautifulSoup(r.text, "html.parser")
        Objekte = parsed_html.find_all('option')

        for Objekt in Objekte:
            if self._number in Objekt.text:
                ObjektValue = Objekt['value']
                break

        r = requests.post("https://www.kwu-entsorgung.de/inc/wordpress/kal_uebersicht-2020.php", data={"ort": OrtValue, "strasse": StrasseValue, "objekt": ObjektValue, "jahr": date.today().year}, headers=HEADERS)

        parsed_html = BeautifulSoup(r.text, "html.parser")
        Links = parsed_html.find_all('a')

        for Link in Links:
           if 'ICal herunterladen' in Link.text:
               ics_url = Link['href']

        if ics_url is None:
            raise Exception(f"ics url not found")

        # get ics file
        r = session.get(ics_url, headers=HEADERS)
        r.raise_for_status()

        # parse ics file
        dates = self._ics.convert(r.text)

        entries = []
        #for d in dates:
        #    entries.append(Collection(d[0], d[1]))
        #return entries
        for d in dates:
#            _LOGGER.error(d)
            waste_type = d[1].strip()
            next_pickup_date = d[0]
            
            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=ICON_MAP.get(waste_type,"mdi:trash-can")))

        return entries

