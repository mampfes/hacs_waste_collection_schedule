import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Movar IKS"
DESCRIPTION = "Source script for movar.no"
URL = "https://movar.no"
TEST_CASES = {
    "Vålerveien 1148, Våler": {"address": "Vålerveien 1148, Våler"},
    "Skråtorpveien 20A, Råde": {"address": "Skråtorpveien 20A, Råde"},
    "Fjellveien 1, Moss": {"address": "Fjellveien 1, Moss"},
    "Rådhusgata 1, Vestby": {"address": "Rådhusgata 1, Vestby"},
}

API_URL = "https://movar.no/kalender.html"
ICON_MAP = {
    "Restavfall": "mdi:trash-can",  # residual waste
	"Papp og papir": "mdi:newspaper-variant-multiple",  # cardboard and paper
    "Våtorganisk": "mdi:leaf",  # wet organic
	"Glass og metallemballasje": "mdi:recycle",  # glass and metal packaging
	"Drikkekartonger": "mdi:recycle",  # drink cartons
	"Spesialavfall": "mdi:recycle",  # special waste
	"Plastemballasje": "mdi:recycle",  # plastic packaging
	"Hageavfall": "mdi:tree",  # yard waste
	"Metaller": "mdi:recycle",  # metals
	"Papp": "mdi:newspaper-variant-multiple",  # cardboard
}


class Source:
    def __init__(self, address):
        self._address = address

    def connect(self, url, headers, params):
        requests.options(url, headers=headers, params=params)
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        return r.json()

    def fetch(self):
        # search address
        url = "https://fritekstsok.api.norkart.no/search/kommunecustom"

        params ={
            "Targets": "gateadresse",
            "Query": self._address,
            "Size": "100",
        }

        headers = {
            "accept": "application/json",
            "access-control-request-headers": "x-waapi-token",
            "access-control-request-method": "GET",
            "origin": "https://movar.no",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "sec-gpc": "1",
            "x-waapi-token": "e6727744-e3f9-4162-a43f-3480fdb1861d",
        }
        
        data = self.connect(url, headers, params)

        results = data["SearchResults"][0]["Source"]
        
        # return waste types
        url = "https://mdt-proxy.movar.no/api/Fraksjoner"

        params = {
            "apitoken": "e6727744-e3f9-4162-a43f-3480fdb1861d",
        }

        headers = {
            "access-control-request-headers": "kommunenr",
            "access-control-request-method": "GET",
            "accept": "*/*",
            "origin": "https://movar.no",
            "sec-fetch-mode": "cors",
            "kommunenr": str(results["KommuneNummer"])
        }
        
        wastetypes = self.connect(url, headers, params)
        
        # get collection dates
        url = "https://mdt-proxy.movar.no/api/Tommekalender"
        
        next_year = str(int(datetime.now().strftime("%Y")) +1)

        params = {
            "dato": next_year + "-12-31T23:59:59+11:00",
            "gatenavn": results["GateNavn"],
            "husnr": str(results["AdresseHusNummer"]),
            "apitoken": "e6727744-e3f9-4162-a43f-3480fdb1861d",
        }

        headers = {
            "accept": "application/json",
            "kommunenr": str(results["KommuneNummer"]),
            "origin": "https://movar.no",
            "referer": "https://movar.no/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "sec-gpc": "1",
        }

        collections = self.connect(url, headers, params)
        entries = []

        for wastetype in wastetypes:
            for collection in collections:
                if collection["fraksjonId"] == wastetype["id"]:
                    for collect_date in collection["tommedatoer"]:
                        entries.append(
                            Collection(
                                date = datetime.strptime(collect_date[:10], "%Y-%m-%d").date(),  # Collection date
                                t = wastetype["navn"],  # Collection type
                                icon = ICON_MAP.get(wastetype["navn"]),  # Collection icon
                            )
                        )

        return entries