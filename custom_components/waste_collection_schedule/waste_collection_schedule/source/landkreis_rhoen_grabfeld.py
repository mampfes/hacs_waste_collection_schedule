import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Landkreis Rhön Grabfeld"
DESCRIPTION = "Source for Landkreis Rhön Grabfeld in Germany. Uses service by offizium."
URL = "https://www.abfallinfo-rhoen-grabfeld.de/"
COUNTRY = "de"
TEST_CASES = {
    "City only": {"city": "Ostheim"},
    "City + District": {"city": "Ostheim", "district": "Oberwaldbehrungen"},
    "District only": {"district": "Oberwaldbehrungen"},
    "empty": {},
}

API_URL = "https://aht1gh-api.sqronline.de/api/modules/abfall/webshow"

EVENT_BLACKLIST = [
    "Wertstoffhof Mellrichstadt",
    "Wertstoffhof Bad Königshofen",
    "Wertstoffzentrum Bad Neustadt",
    "Wertstoffsammelstelle Ostheim",
    "Wertstoffsammelstelle Bischofsheim",
]

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Bio": "mdi:leaf",
    "Gelbe Tonne": "mdi:recycle-variant",
    "Papier": "mdi:package-variant",
    "Problemmüll": "mdi:biohazard",
}


PARAM_TRANSLATIONS = {
    "de": {
        "city": "Stadt, Markt, Gemeinde",
        "district": "Ort, Ortsteil",
    }
}

class Source:
    def __init__(self, city: str | None = None, district: str | None = None):
        self._city = city
        self._district = district

    def fetch(self):
        r = requests.get(
            API_URL, params={"module_division_uuid": "fde08d95-111b-11ef-bbd4-b2fd53c2005a"}
        )

        r.raise_for_status()

        city_id = None
        area_id = None

        json = r.json()
        config = json["mdiv"]["config"]

        if self._city is not None:
            # determine city id
            for city in config["cities"]:
                if city["name"] == self._city:
                    city_id = int(city["id"])
                    break
            if city_id is None:
                raise Exception(f"'{self._city}' is not a valid city")

        if self._district is not None:
            # determine district id
            for area in config["areas"]:
                if area["name"] == self._district and int(area["city_id"]) == city_id:
                    area_id = int(area["id"])
            if area_id is None:
                raise Exception(f"'{self._area}' is not a valid district")

        # determine trash types
        trash_types_map_id_to_name = {}
        for t in config["abfall_types"]["normal"]:
            trash_types_map_id_to_name[int(t["id"])] = t["name"]
        for t in config["abfall_types"]["special"]:
            trash_types_map_id_to_name[int(t["id"])] = t["name"]

        entries = []
        for event in json["abfall_dates"]:
            trash_type = trash_types_map_id_to_name.get(event["abfall_type_id"], None)
            # filter out Sammelstellen, Wertstoffhof and Wertstoffzentrum
            if trash_type is not None and trash_type not in EVENT_BLACKLIST:
                # filter by city and district if provided
                if (city_id is None or city_id == event["abfall_city_id"]) and (area_id is None or area_id == event["abfall_area_id"]):
                    entries.append(
                        Collection(
                            date=datetime.datetime.fromisoformat(event["date"]).date(),
                            t=trash_type,
                            icon=ICON_MAP.get(trash_type, "mdi:trash-can"),
                        )
                    )

        return entries
