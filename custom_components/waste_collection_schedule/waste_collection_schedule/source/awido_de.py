import datetime
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "AWIDO Online"
DESCRIPTION = "Source for AWIDO waste collection."
URL = "https://www.awido-online.de/"
EXTRA_INFO = [
    {
        "title": "Abfallwirtschaft Rems-Murr",
        "url": "https://www.abfallwirtschaft-rems-murr.de/",
    },
    {
        "title": "Landkreis Schweinfurt",
        "url": "https://www.landkreis-schweinfurt.de",
    },
    {
        "title": "Landkreis Gotha",
        "url": "https://www.landkreis-gotha.de/",
    },
    {
        "title": "Zweckverband Abfallwirtschaft Saale-Orla",
        "url": "https://www.zaso-online.de/",
    },
    {
        "title": "Gemeinde Unterhaching",
        "url": "https://www.unterhaching.de/",
    },
    {
        "title": "Stadt Kaufbeuren",
        "url": "https://www.kaufbeuren.de/",
    },
    {
        "title": "Landkreis Berchtesgadener Land",
        "url": "https://www.lra-bgl.de/",
    },
    {
        "title": "Pullach im Isartal",
        "url": "https://www.pullach.de/",
    },
    {
        "title": "AWB Landkreis Fürstenfeldbruck",
        "url": "https://www.awb-ffb.de/",
    },
    {
        "title": "Stadt Unterschleißheim",
        "url": "https://www.unterschleissheim.de/",
    },
    {
        "title": "Landkreis Tirschenreuth",
        "url": "https://www.kreis-tir.de/",
    },
    {
        "title": "Landkreis Rosenheim",
        "url": "https://www.abfall.landkreis-rosenheim.de/",
    },
    {
        "title": "Landkreis Tübingen",
        "url": "https://www.abfall-kreis-tuebingen.de/",
    },
    {
        "title": "Landkreis Kronach",
        "url": "https://www.landkreis-kronach.de/",
    },
    {
        "title": "Landkreis Erding",
        "url": "https://www.landkreis-erding.de/",
    },
    {
        "title": "Zweckverband München-Südost",
        "url": "https://www.zvmso.de/",
    },
    {
        "title": "Landkreis Coburg",
        "url": "https://www.landkreis-coburg.de/",
    },
    {
        "title": "Landkreis Ansbach",
        "url": "https://www.landkreis-ansbach.de/",
    },
    {
        "title": "AWB Landkreis Bad Dürkheim",
        "url": "http://awb.kreis-bad-duerkheim.de/",
    },
    {
        "title": "Landratsamt Aichach-Friedberg",
        "url": "https://lra-aic-fdb.de/",
    },
    {
        "title": "WGV Recycling GmbH",
        "url": "https://wgv-quarzbichl.de/",
    },
    {
        "title": "Neustadt a.d. Waldnaab",
        "url": "https://www.neustadt.de/",
    },
    {
        "title": "Landkreis Kelheim",
        "url": "https://www.landkreis-kelheim.de/",
    },
    {
        "title": "Landkreis Günzburg",
        "url": "https://kaw.landkreis-guenzburg.de/",
    },
    {
        "title": "Stadt Memmingen",
        "url": "https://umwelt.memmingen.de/",
    },
    {
        "title": "Landkreis Südliche Weinstraße",
        "url": "https://www.suedliche-weinstrasse.de/",
    },
    {
        "title": "Landratsamt Dachau",
        "url": "https://www.landratsamt-dachau.de/",
    },
    {
        "title": "Landkreisbetriebe Neuburg-Schrobenhausen",
        "url": "https://www.landkreisbetriebe.de/",
    },
    {
        "title": "Abfallwirtschaftsbetrieb Landkreis Altenkirchen",
        "url": "https://www.awb-ak.de/",
    },
    {
        "title": "Abfallwirtschaft Lahn-Dill-Kreises",
        "url": "https://www.awld.de/",
    },
    {
        "title": "Abfallwirtschafts-Zweckverband des Landkreises Hersfeld-Rotenburg",
        "url": "https://www.azv-hef-rof.de/",
    },
    {
        "title": "Abfall-Wirtschafts-Verband Nordschwaben",
        "url": "https://www.awv-nordschwaben.de/",
    },
]
TEST_CASES = {
    "Schorndorf, Miedelsbacher Straße 30 /1": {
        "customer": "rmk",
        "city": "Schorndorf",
        "street": "Miedelsbacher Straße",
        "housenumber": "30 /1",
    },
    "Altomünster, Maisbrunn": {
        "customer": "lra-dah",
        "city": "Altomünster",
        "street": "Maisbrunn",
    },
    "SOK-Alsmannsdorf": {"customer": "zaso", "city": "SOK-Alsmannsdorf"},
    "Kaufbeuren, Rehgrund": {
        "customer": "kaufbeuren",
        "city": "Kaufbeuren",
        "street": "Rehgrund",
    },
    "Tübingen, Dettenhausen": {"customer": "tuebingen", "city": "Dettenhausen"},
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, customer, city, street=None, housenumber=None):
        self._customer = customer
        self._city = city
        self._street = street
        self._housenumber = housenumber

    def fetch(self):
        # Retrieve list of places
        r = requests.get(
            f"https://awido.cubefour.de/WebServices/Awido.Service.svc/secure/getPlaces/client={self._customer}"
        )
        r.raise_for_status()
        places = r.json()

        # create city to key map from retrieved places
        city_to_oid = {place["value"].strip(): place["key"] for (place) in places}

        if self._city not in city_to_oid:
            raise Exception(f"city not found: {self._city}")

        oid = city_to_oid[self._city]

        if self._street is None:
            # test if we have to use city also as street name
            self._street = self._city
            r = requests.get(
                f"https://awido.cubefour.de/WebServices/Awido.Service.svc/secure/getGroupedStreets/{oid}",
                params={"client": self._customer},
            )
            r.raise_for_status()
            streets = r.json()

            # create street to key map from retrieved places
            street_to_oid = {
                street["value"].strip(): street["key"] for (street) in streets
            }

            if self._street in street_to_oid:
                oid = street_to_oid[self._street]

        else:
            # street specified
            r = requests.get(
                f"https://awido.cubefour.de/WebServices/Awido.Service.svc/secure/getGroupedStreets/{oid}",
                params={"client": self._customer},
            )
            r.raise_for_status()
            streets = r.json()

            # create street to key map from retrieved places
            street_to_oid = {
                street["value"].strip(): street["key"] for (street) in streets
            }

            if self._street not in street_to_oid:
                raise Exception(f"street not found: {self._street}")

            oid = street_to_oid[self._street]

            if self._housenumber is not None:
                r = requests.get(
                    f"https://awido.cubefour.de/WebServices/Awido.Service.svc/secure/getStreetAddons/{oid}",
                    params={"client": self._customer},
                )
                r.raise_for_status()
                hsnbrs = r.json()

                # create housenumber to key map from retrieved places
                hsnbr_to_oid = {
                    hsnbr["value"].strip(): hsnbr["key"] for (hsnbr) in hsnbrs
                }

                if self._housenumber not in hsnbr_to_oid:
                    raise Exception(f"housenumber not found: {self._housenumber}")

                oid = hsnbr_to_oid[self._housenumber]

        # get calendar data
        r = requests.get(
            f"https://awido.cubefour.de/WebServices/Awido.Service.svc/secure/getData/{oid}",
            params={"fractions": "", "client": self._customer},
        )
        r.raise_for_status()
        cal_json = r.json()

        # map fraction code to fraction name
        fractions = {fract["snm"]: fract["nm"] for (fract) in cal_json["fracts"]}

        # calendar also contains public holidays. In this case, 'ad' is None
        calendar = [item for item in cal_json["calendar"] if item["ad"] is not None]

        entries = []
        for calitem in calendar:
            date = datetime.datetime.strptime(calitem["dt"], "%Y%m%d").date()

            # add all fractions for this date
            for fracitem in calitem["fr"]:
                waste_type = fractions[fracitem]
                entries.append(Collection(date, waste_type))

        return entries
