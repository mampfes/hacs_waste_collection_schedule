import datetime
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Jumomind"
DESCRIPTION = "Source for Jumomind.de waste collection."
URL = "https://www.jumomind.de"
TEST_CASES = {
    # DEPRECATED
    "ZAW": {"service_id": "zaw", "city_id": 106, "area_id": 94},
    "Bad Homburg, Bahnhofstrasse": {"service_id": "hom", "city_id": 1, "area_id": 411},
    "Bad Buchau via MyMuell": {
        "service_id": "mymuell",
        "city_id": 3031,
        "area_id": 3031,
    },
    # END DEPRECATED
    "sbm Minden Meißener Str. 6a": {
        "service_id": "sbm",
        "city": "Minden",
        "street": "Meißener Str.",
        "house_number": "6A",
    },
    "Darmstaadt ": {"service_id": "mymuell", "city": "Darmstadt", "street": "Achatweg"},
    "zaw Alsbach-Hähnlein Hähnleiner Str.": {
        "service_id": "zaw",
        "city": "Alsbach-Hähnlein",
        "street": "Hähnleiner Str.",
    },
    "ingolstadt": {
        "service_id": "ingol",
        "city": "Ingolstadt",
        "street": "Hauffstr.",
        "house_number": "9 1/2",
    },
    "mymuell only city": {
        "service_id": "mymuell",
        "city": "Bad Wünnenberg-Bleiwäsche",
    },
    "neustadt": {
        "service_id": "esn",
        "city": "Neustadt",
        "street": "Hauberallee (Kernstadt)",
    },
    "Goldberg": {
        "service_id": "zvo",
        "city": "Goldberg",
    },
    "Main-Kinzig-Kreis": {
        "service_id": "mkk",
        "city": "Freigericht",
        "street": "Hauptstraße (Altenmittlau)",
    },
    "ALW Wolfenbüttel": {
        "service_id": "wol",
        "city": "Linden",
        "street": "Am Buschkopf",
    },
}


ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Biomüll": "mdi:leaf",
    "Biotonne": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Papiertonne": "mdi:package-variant",
    "Gelber": "mdi:recycle",
    "Gelbe": "mdi:recycle",
    "Schadstoffmobil": "mdi:truck-alert",
}

SERVICE_MAP = {
    "zaw": {
        "url": "https://www.zaw-online.de",
        "list": ["Darmstadt-Dieburg (ZAW)"],
    },
    "aoe": {
        "url": "https://www.lra-aoe.de",
        "list": ["Altötting (LK)"],
    },
    "lka": {
        "url": "https://mkw-grossefehn.de",
        "list": ["Aurich (MKW)"],
    },
    "hom": {
        "url": "https://www.bad-homburg.de",
        "list": ["Bad Homburg vdH"],
    },
    "bdg": {
        "url": "https://www.kreiswerke-barnim.de/",
        "list": ["Barnim"],
    },
    "hat": {
        "url": "https://www.hattersheim.de",
        "list": ["Hattersheim am Main"],
    },
    "ingol": {
        "url": "https://www.in-kb.de",
        "list": ["Ingolstadt"],
    },
    "lue": {
        "comment": "Jumomind",  # has its own service
        "url": "https://www.luebbecke.de",
        "list": ["Lübbecke"],
    },
    "sbm": {
        "url": "https://www.minden.de/",
        "list": ["Minden"],
    },
    "ksr": {
        "url": "https://www.zbh-ksr.de",
        "list": ["Recklinghausen"],
    },
    "rhe": {
        "comment": "Jumomind",  # has its own service
        "url": "https://www.rh-entsorgung.de/",
        "list": ["Rhein-Hunsrück"],
    },
    "udg": {
        "url": "https://www.udg-uckermark.de/",
        "list": ["Uckermark"],
    },
    "mymuell": {
        "comment": "MyMuell App",
        "url": "https://www.mymuell.de/",
        "list": [
            "Aschaffenburg",
            "Bad Arolsen",
            "Beverungen",
            "Darmstadt",
            "Esens",
            "Flensburg",
            "Grävenwiesbach",
            "Großkrotzenburg",
            "Hainburg",
            "Holtgast",
            "Kamp-Lintfort",
            "Kirchdorf",
            "Landkreis Aschaffenburg",
            "Landkreis Biberach",
            "Landkreis Eichstätt",
            "Landkreis Friesland",
            "Landkreis Leer",
            "Landkreis Mettmann",
            "Landkreis Paderborn",
            "Landkreis Wittmund",
            "Landkreis Wittmund",
            "Main-Kinzig-Kreis",
            "Mühlheim am Main",
            "Nenndorf",
            "Neumünster",
            "Salzgitter",
            "Schmitten im Taunus",
            "Schöneck",
            "Seligenstadt",
            "Ulm",
            "Usingen",
            "Volkmarsen",
            "Vöhringen",
            "Wegberg",
            "Westerholt",
            "Wilhelmshaven",
        ],
    },
    "esn": {"list": ["Neustadt an der Weinstraße"], "url": "https://www.neustadt.eu/"},
    "zvo": {"list": ["Ostholstein"], "url": "https://www.zvo.com/"},
    "zac": {"list": ["Celle"], "url": "https://www.zacelle.de/"},
    "ben": {
        "list": ["Landkreis Grafschaft"],
        "url": "https://awb.grafschaft-bentheim.de/",
    },
    "enwi": {"list": ["Landkreis Harz"], "url": "https://www.enwi-hz.de/"},
    "hox": {"list": ["Höxter"], "url": "https://abfallservice.kreis-hoexter.de/"},
    "kbl": {"list": ["Langen"], "url": "https://www.kbl-langen.de/"},
    "ros": {"list": ["Rosbach Vor Der Höhe"], "url": "https://www.rosbach-hessen.de/"},
    "mkk": {"list": ["Main-Kinzig-Kreis"], "url": "https://abfall-mkk.de/"},
    "wol": {"list": ["ALW Wolfenbüttel"], "url": "https://www.alw-wf.de"},
}


def EXTRA_INFO():
    extra_info = []
    for provider, entries in SERVICE_MAP.items():
        url = entries["url"]
        comment = ""
        if "comment" in entries:
            comment = f" ({entries['comment']})"

        for area in entries["list"]:
            title = area + comment

            extra_info.append(
                {"title": title, "url": url, "default_params": {"service_id": provider}}
            )
    return extra_info


API_URL = "https://{provider}.jumomind.com/mmapp/api.php"


PARAM_TRANSLATIONS = {
    "de": {
        "service_id": "Service ID",
        "city": "Ort",
        "street": "Straße",
        "city_id": "Ort ID",
        "area_id": "Bereich ID",
        "house_number": "Hausnummer",
    }
}

LOGGER = logging.getLogger(__name__)


def validate_params(value):
    errors = {}
    service_id = value.get("service_id")
    city = value.get("city")
    street = value.get("street")
    city_id = value.get("city_id")
    area_id = value.get("area_id")
    house_number = value.get("house_number")
    if service_id is None:
        errors["service_id"] = "service_id is required"
    if city is None and city_id is None:
        errors["city"] = "city or city_id is required"
        errors["city_id"] = "city or city_id is required"
    if city is not None and city_id is not None:
        errors["city"] = "city or city_id is required. Do not use both"
        errors["city_id"] = "city or city_id is required. Do not use both"
    if city is None and street is not None:
        errors["street"] = "street is not needed without city"
    if city is None and house_number is not None:
        errors["house_number"] = "house_number is not needed without city"
    if city_id is not None and area_id is None:
        errors["area_id"] = "area_id is required when using city_id"
    if area_id is not None and city_id is None:
        errors["city_id"] = "city_id is required when using area_id"
    return errors


def normalize_street(value: str | None) -> str | None:
    return value and (
        value.lower()
        .strip()
        .casefold()
        .replace("straße", "strasse")
        .replace("str.", "strasse")
    )


class Source:
    def __init__(
        self,
        service_id: str,
        city: str | None = None,
        street: str | None = None,
        city_id=None,
        area_id=None,
        house_number=None,
    ):
        self._api_url: str = API_URL.format(provider=service_id)
        self._city: str | None = city.lower().strip() if city else None
        self._street: str | None = street.lower().strip() if street else None
        self._house_number: str | None = (
            str(house_number).lower().strip().lstrip("0") if house_number else None
        )

        self._service_id = service_id
        self._city_id = city_id if city_id else None
        self._area_id = area_id if area_id else None

    def fetch(self):
        session = requests.Session()
        session.headers.update({"Accept-Encoding": "identity"})

        city_id = self._city_id
        area_id = self._area_id

        if city_id is None and self._city is None:
            raise SourceArgumentExceptionMultiple(
                ["city", "city_id"], "City or city id is required"
            )
        if city_id is not None and self._city is not None:
            raise SourceArgumentExceptionMultiple(
                ["city", "city_id"], "City OR city id is required. Do not use both"
            )

        r = session.get(self._api_url, params={"r": "cities_web"})
        r.raise_for_status()

        cities = r.json()

        if city_id is not None:
            if area_id is None:
                raise SourceArgumentException(
                    "area_id",
                    "Area id is required when using city_id. Remove city id when using city (and street) name",
                )
        else:
            has_streets = True
            for city in cities:
                if (
                    city["name"].lower().strip() == self._city
                    or city["_name"].lower().strip() == self._city
                ):
                    city_id = city["id"]
                    area_id = city["area_id"]
                    has_streets = city["has_streets"]
                    break

            if city_id is None:
                raise SourceArgumentNotFoundWithSuggestions(
                    "city", self._city, [c["name"] for c in cities]
                )

            if has_streets:
                r = session.get(
                    self._api_url, params={"r": "streets", "city_id": city_id}
                )
                r.raise_for_status()
                streets = r.json()

                street_found = False
                for street in streets:
                    if normalize_street(street["name"]) == normalize_street(
                        self._street
                    ) or normalize_street(street["_name"]) == normalize_street(
                        self._street
                    ):
                        street_found = True
                        area_id = street["area_id"]
                        if "houseNumbers" in street:
                            for house_number in street["houseNumbers"]:
                                if (
                                    house_number[0].lower().strip().lstrip("0")
                                    == self._house_number
                                ):
                                    area_id = house_number[1]
                                    break
                        break
                if not street_found:
                    streets_suggestions = {s.get("name") for s in streets}
                    streets_suggestions.update({s.get("_name") for s in streets})
                    streets_suggestions -= {None}
                    raise SourceArgumentNotFoundWithSuggestions(
                        "street", self._street, streets_suggestions
                    )
            else:
                if self._street is not None:
                    LOGGER.warning(
                        "City does not need street name please remove it, continuing anyway"
                    )

        # get names for bins

        bin_name_map = {}
        r = session.get(
            self._api_url,
            params={"r": "trash", "city_id": city_id, "area_id": area_id},
        )
        r.raise_for_status()

        for bin_type in r.json():
            bin_name_map[bin_type["name"]] = bin_type["title"]
            if not bin_type["_name"] in bin_name_map:
                bin_name_map[bin_type["_name"]] = bin_type["title"]

        r = session.get(
            self._api_url,
            params={"r": "dates/0", "city_id": city_id, "area_id": area_id, "ws": 3},
        )
        r.raise_for_status()

        entries = []
        for event in r.json():
            bin_type = bin_name_map[event["trash_name"]]
            date = datetime.datetime.strptime(event["day"], "%Y-%m-%d").date()
            icon = ICON_MAP.get(bin_type.split(" ")[0])  # Collection icon
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries


def print_md_table():
    table = "|service_id|cities|\n|---|---|\n"

    for service, data in sorted(SERVICE_MAP.items()):
        print(f"service: {service}")
        args = {"r": "cities"}
        r = requests.get(f"https://{service}.jumomind.com/mmapp/api.php", params=args)
        r.raise_for_status()
        table += f"|{service}|"

        table += "`" + "`, `".join([c["name"] for c in r.json()]) + "`"
        table += "|\n"
    print(table)


if __name__ == "__main__":
    print_md_table()
