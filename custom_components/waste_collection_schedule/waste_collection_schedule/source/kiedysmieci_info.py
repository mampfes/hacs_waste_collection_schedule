import datetime
import json
import ssl
import urllib

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Kiedy śmieci"
DESCRIPTION = "Source script for Kiedy śmieci, Poland"
URL = "https://kiedysmieci.info"
COUNTRY = "pl"
TEST_CASES = {
    "Nadolany, podkarpackie, sanocki, Bukowsko": {
        "voivodeship": "podkarpackie",
        "district": "sanocki",
        "municipality": "Bukowsko",
        "street": "Nadolany",
    },
    "Kędzierz, podkarpackie, dębicki, Dębica": {
        "voivodeship": "podkarpackie",
        "district": "dębicki",
        "municipality": "Dębica",
        "street": "Kędzierz",
    },
}

API_URL = "https://cloud.fxsystems.com.pl:8078/odbiory_smieci/%s"

ICON_MAP = {
    "zmieszane": "mdi:trash-can",
    "metale i tworzywa sztuczne": "mdi:recycle",
    "papier i tektura": "mdi:file-outline",
    "szkło": "mdi:glass-fragile",
    "biodegradowalne": "mdi:leaf",
}


def get_json(url):
    # workaround to establish ssl connection to this host
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.set_ciphers("DEFAULT")

    response = urllib.request.urlopen(API_URL % url, context=ssl_ctx)
    return json.loads(response.read().decode("utf-8"))


class Source:
    def __init__(self, voivodeship: str, district: str, municipality: str, street: str):
        self.voivodeship = voivodeship
        self.district = district
        self.municipality = municipality
        self.street = street
        self.municipalities = self.get_municipalities()

        voivodeships_list = self.get_voivodeships_list()

        if voivodeship.lower() not in [v.lower() for v in voivodeships_list]:
            raise SourceArgumentNotFoundWithSuggestions(
                "voivodeship",
                voivodeship,
                suggestions=voivodeships_list,
            )

        districts_list = self.get_districts_list()

        if district.lower() not in [c.lower() for c in districts_list]:
            raise SourceArgumentNotFoundWithSuggestions(
                "district",
                district,
                suggestions=districts_list,
            )

        municipalities_list = self.get_municipalities_list()

        if municipality.lower() not in [m.lower() for m in municipalities_list]:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality",
                municipality,
                suggestions=municipalities_list,
            )

        streets_list = self.get_streets_list()

        if street.lower() not in [s.lower() for s in streets_list]:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                street,
                suggestions=streets_list,
            )

        self.schedule = self.get_schedule()

    def get_voivodeships_list(self):
        return list({m["wojewodztwo"] for m in self.municipalities})

    def get_districts_list(self):
        return list(
            {
                m["powiat"]
                for m in self.municipalities
                if m["wojewodztwo"].lower() == self.voivodeship.lower()
            }
        )

    def get_municipalities_list(self):
        return [
            m["gmina"]
            for m in self.municipalities
            if m["wojewodztwo"].lower() == self.voivodeship.lower()
            and m["powiat"].lower() == self.district.lower()
        ]

    def get_streets_list(self):
        try:
            streets = get_json(
                "dostepne_gminy?wojewodztwo={}&powiat={}&gmina={}".format(
                    urllib.parse.quote(self.voivodeship),
                    urllib.parse.quote(self.district),
                    urllib.parse.quote(self.municipality),
                )
            )["listaUlic"]
            streets = [s["ulica"] for s in streets]
        except Exception:
            streets = None

        return streets

    def get_municipalities(self):
        try:
            municipalities = get_json("dostepne_gminy/v5")["gminy"]
        except Exception:
            municipalities = None

        return municipalities

    def get_schedule(self):
        try:
            schedule = get_json(
                "lista_terminow/v6?wojewodztwo={}&powiat={}&gmina={}&ulica={}".format(
                    urllib.parse.quote(self.voivodeship),
                    urllib.parse.quote(self.district),
                    urllib.parse.quote(self.municipality),
                    urllib.parse.quote(self.street),
                )
            )["listaTerminow"]

        except Exception:
            schedule = None

        return schedule

    def fetch(self) -> list[Collection]:
        entries = []

        for entry in self.schedule:
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(
                        entry["dataOdbioru"], "%Y-%m-%d"
                    ).date(),
                    t=entry["nazwaTypuSmieci"],
                    icon=ICON_MAP.get(entry["nazwaTypuSmieci"], "mdi:trash-can"),
                )
            )

        return entries
