#!/usr/bin/env python3

import datetime
import json

import requests

SERVICE_DOMAINS = [
    {
        "title": "Stadt Aachen",
        "url": "https://www.aachen.de",
        "service_id": "aachen",
    },
    {
        "title": "AWA Entsorgungs GmbH",
        "url": "https://www.awa-gmbh.de/",
        "service_id": "zew2",
    },
    {
        "title": "Abfallwirtschaftsbetrieb Bergisch Gladbach",
        "url": "https://www.bergischgladbach.de/",
        "service_id": "aw-bgl2",
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
        "title": "Gütersloh",
        "url": "https://www.guetersloh.de/",
        "service_id": "gt2",
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
        "title": "AWG Kreis Warendorf",
        "url": "https://www.awg-waf.de/",
        "service_id": "krwaf",
    },
    {
        "title": "Gemeinde Lindlar",
        "url": "https://www.lindlar.de/",
        "service_id": "lindlar",
    },
    {
        "title": "Stadt Norderstedt",
        "url": "https://www.betriebsamt-norderstedt.de/",
        "service_id": "nds",
    },
    {
        "title": "Abfallwirtschaft Stadt Nürnberg",
        "url": "https://www.nuernberg.de/",
        "service_id": "nuernberg",
    },
    {
        "title": "WBO Wirtschaftsbetriebe Oberhausen",
        "url": "https://www.wbo-online.de/",
        "service_id": "oberhausen",
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
    #    {
    #        "title": "'Stadt Straelen",
    #        "url": "https://www.straelen.de/",
    #        "service_id": "straelen",
    #    },
    #    {
    #        "title": "Kreis Viersen",
    #        "url": "https://www.kreis-viersen.de/",
    #        "service_id": "viersen",
    #    },
    {
        "title": "EGW Westmünsterland",
        "url": "https://www.egw.de/",
        "service_id": "wml2",
    },
]


class AbfallnaviDe:
    def __init__(self, service_domain):
        self._service_domain = service_domain
        self._service_url = f"https://{service_domain}-abfallapp.regioit.de/abfall-app-{service_domain}/rest"

    def _fetch(self, path, params=None):
        r = requests.get(f"{self._service_url}/{path}", params=params)
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
        return r.text

    def _fetch_json(self, path, params=None):
        return json.loads(self._fetch(path, params=params))

    def get_cities(self):
        """Return all cities of service domain."""
        cities = self._fetch_json("orte")
        result = {}
        for city in cities:
            result[city["id"]] = city["name"]
        return result

    def get_city_id(self, city):
        """Return id for given city string."""
        cities = self.get_cities()
        return self._find_in_inverted_dict(cities, city)

    def get_streets(self, city_id):
        """Return all streets of a city."""
        streets = self._fetch_json(f"orte/{city_id}/strassen")
        result = {}
        for street in streets:
            result[street["id"]] = street["name"]
        return result

    def get_street_id(self, city_id, street):
        """Return id for given street string."""
        streets = self.get_streets(city_id)
        return self._find_in_inverted_dict(streets, street)

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
        return self._find_in_inverted_dict(house_numbers, house_number)

    def get_waste_types(self):
        waste_types = self._fetch_json("fraktionen")
        result = {}
        for waste_type in waste_types:
            result[waste_type["id"]] = waste_type["name"]
        return result

    def _get_dates(self, target, id, waste_types=None):
        # retrieve collections
        args = []

        if waste_types is None:
            waste_types = self.get_waste_types()

        for f in waste_types.keys():
            args.append(("fraktion", f))

        results = self._fetch_json(f"{target}/{id}/termine", params=args)

        entries = []
        for r in results:
            date = datetime.datetime.strptime(r["datum"], "%Y-%m-%d").date()
            fraktion = waste_types[r["bezirk"]["fraktionId"]]
            entries.append([date, fraktion])
        return entries

    def get_dates_by_street_id(self, street_id):
        return self._get_dates("strassen", street_id, waste_types=None)

    def get_dates_by_house_number_id(self, house_number_id):
        return self._get_dates("hausnummern", house_number_id, waste_types=None)

    def get_dates(self, city, street, house_number=None):
        """Get dates by strings only for convenience."""
        # find city_id
        city_id = self.get_city_id(city)
        if city_id is None:
            raise Exception(f"No id found for city: {city}")

        # find street_id
        street_id = self.get_street_id(city_id, street)
        if street_id is None:
            raise Exception(f"No id found for street: {street}")

        # find house_number_id (which is optional: not all house number do have an id)
        house_number_id = self.get_house_number_id(street_id, house_number)

        # return dates for specific house number of street if house number
        # doesn't have an own id
        if house_number_id is not None:
            return self.get_dates_by_house_number_id(house_number_id)
        else:
            return self.get_dates_by_street_id(street_id)

    def _find_in_inverted_dict(self, mydict, value):
        inverted_dict = dict(map(reversed, mydict.items()))
        return inverted_dict.get(value)


def main():
    aachen = AbfallnaviDe("aachen")
    print(aachen.get_dates("Aachen", "Abteiplatz", "7"))

    lindlar = AbfallnaviDe("lindlar")
    print(lindlar.get_dates("Lindlar", "Aggerweg"))

    roe = AbfallnaviDe("roe")
    print(roe.get_dates("Roetgen", "Am Sportplatz", "2"))


if __name__ == "__main__":
    main()
