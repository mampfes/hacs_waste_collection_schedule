#!/usr/bin/env python3

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

import requests

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

SERVICE_DOMAINS = [
    {
        "title": "Stadt Aachen",
        "url": "https://www.aachen.de",
        "service_id": "aachen",
    },
    {
        "title": "Abfallwirtschaft Stadt Nürnberg",
        "url": "https://www.nuernberg.de/",
        "service_id": "nuernberg",
    },
    {
        "title": "Abfallwirtschaftsbetrieb Bergisch Gladbach",
        "url": "https://www.bergischgladbach.de/",
        "service_id": "aw-bgl2",
    },
    {
        "title": "AWA Entsorgungs GmbH",
        "url": "https://www.awa-gmbh.de/",
        "service_id": "zew2",
    },
    {
        "title": "AWG Kreis Warendorf",
        "url": "https://www.awg-waf.de/",
        "service_id": "krwaf",
    },
    {
        "title": "Bergischer Abfallwirtschaftverbund",
        "url": "https://www.bavweb.de/",
        "service_id": "bav",
    },
    {
        "title": "Kreis Coesfeld",
        "url": "https://wbc-coesfeld.de/",
        "service_id": "coe",
    },
    {
        "title": "Stadt Cottbus",
        "url": "https://www.cottbus.de/",
        "service_id": "cottbus",
    },
    {
        "title": "Dinslaken",
        "url": "https://www.dinslaken.de/",
        "service_id": "din",
    },
    {
        "title": "Stadt Dorsten",
        "url": "https://www.ebd-dorsten.de/",
        "service_id": "dorsten",
    },
    {
        "title": "EGW Westmünsterland",
        "url": "https://www.egw.de/",
        "service_id": "wml2",
    },
    {
        "title": "Kreis Gütersloh GEG",
        "url": "https://www.geg-gt.de/",
        "service_id": "krwaf",
    },
    {
        "title": "Halver",
        "url": "https://www.halver.de/",
        "service_id": "hlv",
    },
    {
        "title": "Kreis Heinsberg",
        "url": "https://www.kreis-heinsberg.de/",
        "service_id": "krhs",
    },
    {
        "title": "Kronberg im Taunus",
        "url": "https://www.kronberg.de/",
        "service_id": "kronberg",
    },
    {
        "title": "MHEG Mülheim an der Ruhr",
        "url": "https://www.mheg.de/",
        "service_id": "muelheim",
    },
    {
        "title": "Stadt Norderstedt",
        "url": "https://www.betriebsamt-norderstedt.de/",
        "service_id": "nds",
    },
    {
        "title": "Kreis Pinneberg",
        "url": "https://www.kreis-pinneberg.de/",
        "service_id": "pi",
    },
    {
        "title": "Gemeinde Roetgen",
        "url": "https://www.roetgen.de/",
        "service_id": "roe",
    },
    {
        "title": "Stadt Solingen",
        "url": "https://www.solingen.de/",
        "service_id": "solingen",
    },
    {
        "title": "STL Lüdenscheid",
        "url": "https://www.stl-luedenscheid.de/",
        "service_id": "stl",
    },
    {
        "title": "GWA - Kreis Unna mbH",
        "url": "https://www.gwa-online.de/",
        "service_id": "unna",
    },
    {
        "title": "Kreis Viersen",
        "url": "https://www.kreis-viersen.de/",
        "service_id": "viersen",
    },
    {
        "title": "WBO Wirtschaftsbetriebe Oberhausen",
        "url": "https://www.wbo-online.de/",
        "service_id": "oberhausen",
    },
    {
        "title": "ZEW Zweckverband Entsorgungsregion West",
        "url": "https://zew-entsorgung.de/",
        "service_id": "zew2",
    },
    #    {
    #        "title": "'Stadt Straelen",
    #        "url": "https://www.straelen.de/",
    #        "service_id": "straelen",
    #    },
    {
        "title": "Stadt Cuxhaven",
        "url": "https://www.cuxhaven.de/",
        "service_id": "cux",
    },
    {
        "title": "Stadt Frankenthal",
        "url": "https://www.frankenthal.de/",
        "service_id": "frankenthal",
    },
    {
        "title": "Abfallwirtschaftsverband Lippe",
        "url": "https://www.abfall-lippe.de/",
        "service_id": "awvlippe",
    },
    {
        "title": "Gemeinde Kranenburg",
        "url": "https://www.kranenburg.de/",
        "service_id": "kranenburg",
    },
    {
        "title": "Stadt Porta Westfalica",
        "url": "https://www.portawestfalica.de/",
        "service_id": "portawestfalica",
    },
]

DEFAULT_TIMEOUT = 20


class AbfallnaviDe:
    # Services where the per-service subdomain DNS is dead;
    # use the shared domain directly to avoid DNS timeout.
    SHARED_DOMAIN_SERVICES = {
        "unna",
        "frankenthal",
        "awvlippe",
        "kranenburg",
    }

    def __init__(self, service_domain):
        self._service_domain = service_domain
        if service_domain in self.SHARED_DOMAIN_SERVICES:
            self._service_url = (
                f"https://abfallapp.regioit.de/abfall-app-{service_domain}/rest"
            )
            self._service_url_fallback = (
                f"https://{service_domain}"
                f"-abfallapp.regioit.de/"
                f"abfall-app-{service_domain}/rest"
            )
        else:
            self._service_url = (
                f"https://{service_domain}"
                f"-abfallapp.regioit.de/"
                f"abfall-app-{service_domain}/rest"
            )
            self._service_url_fallback = (
                f"https://abfallapp.regioit.de/abfall-app-{service_domain}/rest"
            )
        self._session = requests.Session()

    def _fetch(self, path, params=None):
        try:
            r = self._session.get(
                f"{self._service_url}/{path}", params=params, timeout=DEFAULT_TIMEOUT
            )
        except requests.exceptions.ConnectionError:
            self._service_url = self._service_url_fallback
            r = self._session.get(
                f"{self._service_url}/{path}", params=params, timeout=DEFAULT_TIMEOUT
            )
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
        if r.status_code == 404:
            raise SourceArgumentNotFoundWithSuggestions(
                "service",
                self._service_domain,
                [s["service_id"] for s in SERVICE_DOMAINS],
            )
        r.raise_for_status()
        return r

    def _fetch_json(self, path, params=None):
        return self._fetch(path, params=params).json()

    def get_cities(self):
        """Return all cities of service domain."""
        cities = self._fetch_json("orte")
        return {city["id"]: city["name"] for city in cities}

    def get_city_id(self, city):
        """Return id for given city string."""
        cities = self.get_cities()
        city_id = self._find_in_inverted_dict(cities, city)
        if not city_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", city, list(cities.values())
            )
        return city_id

    def get_streets(self, city_id):
        """Return all streets of a city."""
        streets = self._fetch_json(f"orte/{city_id}/strassen")
        return {street["id"]: street["name"] for street in streets}

    def get_street_ids(self, city_id, street):
        """Return ids for given street string.

        may return multiple on change of id (may occur on year change)
        """
        streets = self.get_streets(city_id)
        if len(streets) == 1:
            return list(streets.keys())
        if street is None:
            raise SourceArgumentRequiredWithSuggestions(
                "street", "street is required of this city", list(streets.values())
            )
        matches = [id for id, name in streets.items() if name == street]
        if len(matches) == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", street, list(streets.values())
            )
        return matches

    def get_house_numbers(self, street_id):
        """Return all house numbers of a street."""
        house_numbers = self._fetch_json(f"strassen/{street_id}")
        result = {}
        for hausNr in house_numbers.get("hausNrList", {}):
            # {"id":5985445,"name":"Adalbert-Stifter-Straße","hausNrList":[{"id":5985446,"nr":"1"},
            result[hausNr["id"]] = hausNr["nr"]
        return result

    def get_house_number_id(self, street_id, house_number):
        """Return id for given house number string."""
        house_numbers = self.get_house_numbers(street_id)
        if len(house_numbers) == 0:
            return None
        if len(house_numbers) == 1:
            return list(house_numbers.keys())[0]
        if house_number is None:
            raise SourceArgumentRequiredWithSuggestions(
                "house_number",
                "house number is required for this street",
                list(house_numbers.values()),
            )
        house_number_id = self._find_in_inverted_dict(house_numbers, house_number)
        if house_number_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", house_number, list(house_numbers.values())
            )

        return house_number_id

    def get_waste_types(self):
        waste_types = self._fetch_json("fraktionen")
        return {waste_type["id"]: waste_type["name"] for waste_type in waste_types}

    def _find_in_inverted_dict(self, mydict, value):
        inverted_dict = {v: k for k, v in mydict.items()}
        return inverted_dict.get(value)


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# regio iT / Abfallnavi resolves a place across several requests (city -> id,
# street -> id, house -> id) before fetching the date feed, and the date feed
# only carries a ``fraktionId`` that has to be decoded against a separate
# ``fraktionen`` reference list. The split:
#
#     retrieve = AbfallnaviRetriever(service="service", city="city", ...)
#     parse    = AbfallnaviParser()
#
# AbfallnaviRetriever performs the multi-request acquisition and returns the two
# *raw* payloads it gathered, bundled: the ``termine`` feed and the ``fraktionen``
# reference map. AbfallnaviParser does no I/O — it cross-references the two into
# ``(date, label)`` rows. Acquisition (many requests) and interpretation stay
# separate; a plain ICSTransformer then maps each label onto a canonical type.
# --------------------------------------------------------------------------- #


class AbfallnaviRetriever(RetrieverFunc):
    """Resolve the place and return the raw ``termine`` feed + ``fraktionen`` map.

    Args are the ``source.params`` field names holding the regio iT service id,
    the city, the street and (optionally) the house number.
    """

    def __init__(
        self,
        service: str = "service",
        city: str = "city",
        street: str = "street",
        house_number: str = "house_number",
    ):
        self.service = service
        self.city = city
        self.street = street
        self.house_number = house_number

    def __call__(self, source: "BaseSource") -> dict[str, Any]:
        params = source.params
        client = AbfallnaviDe(params[self.service])

        city_id = client.get_city_id(params.get(self.city))
        street_ids = client.get_street_ids(city_id, params.get(self.street))
        fraktionen = client.get_waste_types()

        termine: list[dict] = []
        for street_id in street_ids:
            house_number_id = client.get_house_number_id(
                street_id, params.get(self.house_number)
            )
            if house_number_id is not None:
                target, object_id = "hausnummern", house_number_id
            else:
                target, object_id = "strassen", street_id
            args = [("fraktion", fraktion_id) for fraktion_id in fraktionen]
            termine += client._fetch_json(f"{target}/{object_id}/termine", params=args)

        return {"termine": termine, "fraktionen": fraktionen}


class AbfallnaviParser(Parser["list[tuple[date, str]]"]):
    """Decode the raw ``termine`` feed into ``(date, label)`` rows.

    Cross-references each entry's ``fraktionId`` against the ``fraktionen``
    reference map gathered by the retriever. Does no I/O, so it runs standalone
    against a cached ``{"termine": ..., "fraktionen": ...}`` fixture.
    """

    def __call__(
        self, raw: dict[str, Any], source: "BaseSource | None" = None
    ) -> list[tuple[date, str]]:
        from waste_collection_schedule import response_shape

        response_shape.expect(
            isinstance(raw, dict) and "termine" in raw and "fraktionen" in raw,
            source_name=response_shape.source_name(source),
            detail="Abfallnavi response missing 'termine'/'fraktionen'",
            raw=raw,
        )
        fraktionen = raw["fraktionen"]
        rows: list[tuple[date, str]] = []
        for entry in raw["termine"]:
            collection_date = datetime.strptime(entry["datum"], "%Y-%m-%d").date()
            label = fraktionen.get(entry["bezirk"]["fraktionId"], "")
            rows.append((collection_date, label))
        return rows
