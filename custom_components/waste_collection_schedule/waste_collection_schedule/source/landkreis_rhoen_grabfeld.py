from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, district
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

# Recycling centres and collection points are listed beside the bins in the
# provider's "special" types; they are opening days, not collections.
_NOT_COLLECTIONS = frozenset(
    {
        "Wertstoffhof Mellrichstadt",
        "Wertstoffhof Bad Königshofen",
        "Wertstoffzentrum Bad Neustadt",
        "Wertstoffsammelstelle Ostheim",
        "Wertstoffsammelstelle Bischofsheim",
    }
)


def _events(data, source):
    """The feed's events narrowed to the configured city and district.

    One response carries the whole district's lookup tables (``mdiv.config``)
    and every event; the city and district names are resolved to ids here and
    each event's type id is replaced by its name.
    """
    config = data["mdiv"]["config"]
    city_name = source.params.get("city")
    district_name = source.params.get("district")

    city_id = None
    area_id = None

    if city_name is not None:
        for entry in config["cities"]:
            if entry["name"] == city_name:
                city_id = int(entry["id"])
                break
        if city_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", city_name, [c["name"] for c in config["cities"]]
            )

    if district_name is not None:
        for area in config["areas"]:
            if area["name"] == district_name and (
                city_id is None or int(area["city_id"]) == city_id
            ):
                area_id = int(area["id"])
                break
        if area_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "district", district_name, [a["name"] for a in config["areas"]]
            )

    names = {
        int(t["id"]): t["name"]
        for group in ("normal", "special")
        for t in config["abfall_types"][group]
    }

    for event in data["abfall_dates"]:
        name = names.get(event["abfall_type_id"])
        if name is None or name in _NOT_COLLECTIONS:
            continue
        if city_id is not None and city_id != event["abfall_city_id"]:
            continue
        if area_id is not None and area_id != event["abfall_area_id"]:
            continue
        yield {"date": event["date"], "type": name}


@final
class Source(BaseSource):
    TITLE = "Landkreis Rhön Grabfeld"
    DESCRIPTION = (
        "Source for Landkreis Rhön Grabfeld in Germany. Uses service by offizium."
    )
    URL = "https://www.abfallinfo-rhoen-grabfeld.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "City only": {"city": "Ostheim"},
        "City + District": {"city": "Ostheim", "district": "Oberwaldbehrungen"},
        "District only": {"district": "Oberwaldbehrungen"},
    }

    PARAMS = (
        city("city", optional=True),
        district("district", optional=True),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.HAZARDOUS,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the municipality (`city`) and/or the village (`district`) "
            "exactly as listed on https://www.abfallinfo-rhoen-grabfeld.de/. "
            "Leave both empty to get the collections of the whole district."
        ),
        "de": (
            "Gib die Stadt, den Markt oder die Gemeinde (`city`) und/oder den "
            "Ortsteil (`district`) so an, wie sie auf "
            "https://www.abfallinfo-rhoen-grabfeld.de/ aufgeführt sind. Ohne "
            "Angabe werden die Termine des gesamten Landkreises geliefert."
        ),
    }

    retrieve = HttpGetRetriever(
        url="https://aht1gh-api.sqronline.de/api/modules/abfall/webshow",
        params=lambda **_: {
            "module_division_uuid": "fde08d95-111b-11ef-bbd4-b2fd53c2005a"
        },
    )
    parse = parsers.JsonParser()
    preprocess = staticmethod(_events)
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Bio": wt.ORGANIC,
            "Gelbe Tonne": wt.RECYCLABLES,
            "Papier": wt.PAPER,
            "Problemmüll": wt.HAZARDOUS,
        },
    )
