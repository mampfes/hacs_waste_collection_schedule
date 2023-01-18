from dateutil import parser
import re

from xml.dom.minidom import parseString
import requests
from waste_collection_schedule import Collection

TITLE = "Newport City Council"
DESCRIPTION = "Source for newport.gov.uk, Newport City Council, UK"
URL = "https://www.newport.gov.uk"
TEST_CASES = {
    "The Coach House, Newport": {"uprn": 100100688837},
}

API_URL = "https://api.newport.gov.uk/PropertyData/bincollection/properties/{uprn}/Waste Collection"

ICON_MAP = {
    "rubbish bin": "mdi:trash-can",
    "kerbside recycling": "mdi:recycle",
    "garden waste": "mdi:leaf",
}

def getText(element):
    s = ""
    for e in element.childNodes:
        if e.nodeType == e.TEXT_NODE:
            s += e.nodeValue
    return s

class Source:
    def __init__(self, uprn=None):
        self._uprn = uprn

    def fetch(self):
        q = str(API_URL).format(uprn=self._uprn)

        r = requests.get(q)
        r.raise_for_status()

        responseContent = r.text

        entries = []

        doc = parseString(responseContent)
        collections = doc.getElementsByTagName("channel")
        
        for collection in collections:
            nameFull = getText(collection.getElementsByTagName("title")[0])
            when = getText(collection.getElementsByTagName("title")[1])
            if "Info:" in when:
                continue
            if "will resume" in when:
                continue

            name = re.search('next (.+?) collection', nameFull).group(1)
            entries.append(
                Collection(
                    date=parser.parse(when).date(),
                    t=name,
                    icon=ICON_MAP.get(name),
                )
            )

        return entries
