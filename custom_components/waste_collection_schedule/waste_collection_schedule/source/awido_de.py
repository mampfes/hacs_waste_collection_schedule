import datetime
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "AWIDO Online"
DESCRIPTION = "Source for AWIDO waste collection."
URL = "https://www.awido-online.de/"


def EXTRA_INFO():
    return [
        {
            "title": s["title"],
            "url": s["url"],
            "default_params": {
                "customer": s["service_id"],
                **s.get("default_params", {}),
            },
        }
        for s in SERVICE_MAP
    ]


SERVICE_MAP = [
    {
        "title": "Abfallwirtschaft Rems-Murr (AWRM) - AWIDO Version",
        "url": "https://www.abfallwirtschaft-rems-murr.de/",
        "service_id": "rmk",
    },
    {
        "title": "Landkreis Schweinfurt",
        "url": "https://www.landkreis-schweinfurt.de",
        "service_id": "lra-schweinfurt",
    },
    {
        "title": "Landkreis Gotha",
        "url": "https://www.landkreis-gotha.de/",
        "service_id": "gotha",
    },
    {
        "title": "Zweckverband Abfallwirtschaft Saale-Orla",
        "url": "https://www.zaso-online.de/",
        "service_id": "zaso",
    },
    {
        "title": "Gemeinde Unterhaching",
        "url": "https://www.unterhaching.de/",
        "service_id": "unterhaching",
    },
    {
        "title": "Stadt Kaufbeuren",
        "url": "https://www.kaufbeuren.de/",
        "service_id": "kaufbeuren",
    },
    {
        "title": "Landkreis Berchtesgadener Land",
        "url": "https://www.lra-bgl.de/",
        "service_id": "bgl",
    },
    {
        "title": "Pullach im Isartal",
        "url": "https://www.pullach.de/",
        "service_id": "pullach",
    },
    {
        "title": "AWB Landkreis Fürstenfeldbruck",
        "url": "https://www.awb-ffb.de/",
        "service_id": "ffb",
    },
    {
        "title": "Stadt Unterschleißheim",
        "url": "https://www.unterschleissheim.de/",
        "service_id": "unterschleissheim",
    },
    {
        "title": "Landkreis Tirschenreuth",
        "url": "https://www.kreis-tir.de/",
        "service_id": "kreis-tir",
    },
    {
        "title": "Landkreis Rosenheim",
        "url": "https://www.abfall.landkreis-rosenheim.de/",
        "service_id": "rosenheim",
    },
    {
        "title": "Landkreis Tübingen",
        "url": "https://www.abfall-kreis-tuebingen.de/",
        "service_id": "tuebingen",
    },
    {
        "title": "Landkreis Kronach",
        "url": "https://www.landkreis-kronach.de/",
        "service_id": "kronach",
    },
    {
        "title": "Landkreis Kulmbach",
        "url": "https://www.landkreis-kulmbach.de/",
        "service_id": "kulmbach",
    },
    {
        "title": "Landkreis Erding",
        "url": "https://www.landkreis-erding.de/",
        "service_id": "erding",
    },
    {
        "title": "Zweckverband München-Südost",
        "url": "https://www.zvmso.de/",
        "service_id": "zv-muc-so",
    },
    {
        "title": "Landkreis Coburg",
        "url": "https://www.landkreis-coburg.de/",
        "service_id": "coburg",
    },
    {
        "title": "Landkreis Ansbach",
        "url": "https://www.landkreis-ansbach.de/",
        "service_id": "ansbach",
    },
    {
        "title": "AWB Landkreis Bad Dürkheim",
        "url": "http://awb.kreis-bad-duerkheim.de/",
        "service_id": "awb-duerkheim",
    },
    {
        "title": "Landratsamt Aichach-Friedberg",
        "url": "https://lra-aic-fdb.de/",
        "service_id": "aic-fdb",
    },
    {
        "title": "WGV Recycling GmbH",
        "url": "https://wgv-quarzbichl.de/",
        "service_id": "wgv",
    },
    {
        "title": "Neustadt a.d. Waldnaab",
        "url": "https://www.neustadt.de/",
        "service_id": "neustadt",
    },
    {
        "title": "Landkreis Kelheim",
        "url": "https://www.landkreis-kelheim.de/",
        "service_id": "kelheim",
    },
    {
        "title": "Landkreis Günzburg",
        "url": "https://kaw.landkreis-guenzburg.de/",
        "service_id": "kaw-guenzburg",
    },
    {
        "title": "Stadt Memmingen",
        "url": "https://umwelt.memmingen.de/",
        "service_id": "memmingen",
    },
    {
        "title": "Landkreis Südliche Weinstraße",
        "url": "https://www.suedliche-weinstrasse.de/",
        "service_id": "eww-suew",
    },
    {
        "title": "Landratsamt Dachau",
        "url": "https://www.landratsamt-dachau.de/",
        "service_id": "lra-dah",
    },
    {
        "title": "Landkreisbetriebe Neuburg-Schrobenhausen",
        "url": "https://www.landkreisbetriebe.de/",
        "service_id": "landkreisbetriebe",
    },
    {
        "title": "Abfallwirtschaftsbetrieb Landkreis Altenkirchen",
        "url": "https://www.awb-ak.de/",
        "service_id": "awb-ak",
    },
    {
        "title": "Abfallwirtschaft Lahn-Dill-Kreises",
        "url": "https://www.awld.de/",
        "service_id": "awld",
    },
    {
        "title": "Abfallwirtschafts-Zweckverband des Landkreises Hersfeld-Rotenburg",
        "url": "https://www.azv-hef-rof.de/",
        "service_id": "azv-hef-rof",
    },
    {
        "title": "Abfall-Wirtschafts-Verband Nordschwaben",
        "url": "https://www.awv-nordschwaben.de/",
        "service_id": "awv-nordschwaben",
    },
    {
        "title": "Stadt Regensburg",
        "url": "https://www.regensburg.de/",
        "service_id": "regensburg",
    },
    {
        "title": "Abfallwirtschaft Isar-Inn",
        "url": "https://www.awv-isar-inn.de/",
        "service_id": "awv-isar-inn",
    },
    {
        "title": "Landkreis Fulda",
        "url": "https://www.landkreis-fulda.de/",
        "service_id": "fulda",
    },
    {
        "title": "Stadt Fulda",
        "url": "https://www.fulda.de/",
        "service_id": "fulda-stadt",
    },
    {
        "title": "Landkreis Aschaffenburg",
        "url": "https://www.landkreis-aschaffenburg.de/",
        "service_id": "lra-ab",
    },
    {
        "title": "Landkreis Mühldorf a. Inn",
        "url": "https://www.lra-mue.de/",
        "service_id": "lra-mue",
    },
    {
        "title": "Landkreis Roth",
        "url": "https://www.landratsamt-roth.de/",
        "service_id": "roth",
    },
    {
        "title": "Landratsamt Regensburg",
        "url": "https://www.landkreis-regensburg.de/",
        "service_id": "lra-regensburg",
    },
    {
        "title": "Landkreis Gießen",
        "url": "https://www.lkgi.de/",
        "service_id": "lkgi",
    },
    {
        "title": "Landkreis Gifhorn",
        "url": "https://www.gifhorn.de/",
        "service_id": "gifhorn",
    },
    {
        "title": "Stadt Königstein im Taunus",
        "url": "https://www.koenigstein.de/",
        "service_id": "koenigstein",
    },
    {
        "title": "Anzing",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Anzing"},
    },
    {
        "title": "Aßling",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Aßling"},
    },
    {
        "title": "Baiern",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Baiern"},
    },
    {
        "title": "Bruck",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Bruck"},
    },
    {
        "title": "Ebersberg",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Ebersberg"},
    },
    {
        "title": "Egmating",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Egmating"},
    },
    {
        "title": "Emmering",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Emmering"},
    },
    {
        "title": "Forstinning",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Forstinning"},
    },
    {
        "title": "Frauenneuharting",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Frauenneuharting"},
    },
    {
        "title": "Glonn",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Glonn"},
    },
    {
        "title": "Grafing",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Grafing"},
    },
    {
        "title": "Hohenlinden",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Hohenlinden"},
    },
    {
        "title": "Kirchseeon",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Kirchseeon"},
    },
    {
        "title": "Moosach",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Moosach"},
    },
    {
        "title": "Oberpframmern",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Oberpframmern"},
    },
    {
        "title": "Pliening",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Pliening"},
    },
    {
        "title": "Poing",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Poing"},
    },
    {
        "title": "Steinhöring",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Steinhöring"},
    },
    {
        "title": "Vaterstetten",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Vaterstetten"},
    },
    {
        "title": "Zorneding",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Zorneding"},
    },
    {
        "title": "Ingelsberg (Zorneding)",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Zorneding"},
    },
    {
        "title": "Markt Schwaben",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Markt Schwaben"},
    },
    {
        "title": "Pöring (Zorneding)",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Zorneding"},
    },
    {
        "title": "Wolfesing (Zorneding)",
        "url": "https://www.lra-ebe.de/",
        "service_id": "ebe",
        "default_params": {"city": "Zorneding"},
    },

]

TEST_CASES = {
    "Giffhorn, Hankensbüttel, Allersehl": {
        "customer": "gifhorn",
        "city": "Hankensbüttel",
        "street": "Allersehl",
    },
    "coburg rödental krötenleite 4": {
        "customer": "coburg",
        "city": "rödental",
        "street": "krötenleite",
        "housenumber": 4,
    },
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
    "Berchtesgadener Land": {
        "customer": "bgl",
        "city": "Laufen",
        "street": "Ahornweg",
        "housenumber": 1,
    },
    "Daaden-Herdorf": {
        "customer": "awb-ak",
        "city": "VG Daaden-Herdorf - Kernstadt Herdorf",
    },
    "Mühldorf": {
        "customer": "lra-mue",
        "city": "Ampfing",
        "street": "Marktplatz",
    },
    "Roth": {
        "customer": "roth",
        "city": "Spalt",
        "street": "Pflugsmühler Weg",
    },
    "Kissing Karwendelweg": {
        "customer": "aic-fdb",
        "city": "Kissing",
        "street": "Karwendelweg",
    },
    "Gießen": {"customer": "lkgi", "city": "Langgöns", "street": "Hauptstraße"},
}

_LOGGER = logging.getLogger(__name__)


class JSONNotSupported(Exception):
    pass


PARAM_TRANSLATIONS = {
    "de": {
        "customer": "Kunde",
        "city": "Ort",
        "street": "Straße",
        "housenumber": "Hausnummer",
    }
}


class Source:
    def __init__(
        self,
        customer: str,
        city: str,
        street: str | None = None,
        housenumber: str | int | None = None,
    ):
        self._customer = customer.lower()
        self._city = city.lower()
        self._street = street.lower() if street else None
        self._housenumber = None if housenumber is None else str(housenumber).lower()
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        # Retrieve list of places
        r = requests.get(
            f"https://awido.cubefour.de/WebServices/Awido.Service.svc/secure/getPlaces/client={self._customer}"
        )
        r.raise_for_status()
        places = r.json()

        # create city to key map from retrieved places
        city_to_oid = {
            place["value"].strip().lower(): place["key"] for (place) in places
        }

        if self._city not in city_to_oid:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, suggestions=list(city_to_oid.keys())
            )

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
            oid = streets[0]["key"]

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
                street["value"].strip().lower(): street["key"] for (street) in streets
            }

            if self._street not in street_to_oid:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street", self._street, suggestions=list(street_to_oid.keys())
                )

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
                    hsnbr["value"].strip().lower(): hsnbr["key"] for (hsnbr) in hsnbrs
                }
                if (
                    len(hsnbr_to_oid) == 0
                    or len(hsnbr_to_oid) == 1
                    and "" in hsnbr_to_oid
                ):
                    _LOGGER.warning(
                        "No housenumbers found for street, using street only"
                    )
                else:
                    if self._housenumber not in hsnbr_to_oid:
                        raise SourceArgumentNotFoundWithSuggestions(
                            "housenumber",
                            self._housenumber,
                            suggestions=list(hsnbr_to_oid.keys()),
                        )
                    oid = hsnbr_to_oid[self._housenumber]

        try:
            return self.get_json_data(oid)
        except JSONNotSupported:
            return self.get_ics_data(oid)

    def get_ics_data(self, oid) -> list[Collection]:
        now = datetime.datetime.now()

        entries: list[Collection] = []

        for year in [now.year, now.year + 1] if now.month == 12 else [now.year]:
            r = requests.get(
                f"https://awido.cubefour.de/Customer/{self._customer}/KalenderICS.aspx",
                params={
                    "oid": oid,
                    "jahr": year,
                    "fraktionen": "",
                    "reminder": "-1.17:00",
                },
            )
            r.raise_for_status()
            ics_file = r.text

            dates = self._ics.convert(ics_file)

            entries = []
            for d in dates:
                # prevents duplicates
                if any(e.date == d[0] and e.type == d[1] for e in entries):
                    continue
                entries.append(Collection(d[0], d[1]))

        return entries

    def get_json_data(self, oid) -> list[Collection]:
        # get calendar data
        r = requests.get(
            f"https://awido.cubefour.de/WebServices/Awido.Service.svc/secure/getData/{oid}",
            params={"fractions": "", "client": self._customer},
        )
        if r.status_code != 200 or r.text.strip() == "":
            raise JSONNotSupported()
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
