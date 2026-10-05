from datetime import date, datetime
from typing import ClassVar, final

from waste_collection_schedule import field_terms, regions, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import RowTransformer

API_URL = "https://www.zvo.com/api/wastecollection"


def _city_id(response, *, city, **_):
    cities = response.json()
    for item in cities:
        if item["name"].casefold() == city.casefold():
            return item["id"]
    suggestions = [
        item["name"] for item in cities if city.casefold() in item["name"].casefold()
    ]
    if suggestions:
        raise SourceArgumentNotFoundWithSuggestions("city", city, suggestions)
    raise SourceArgumentNotFound("city", city)


def _street_id(response, *_, street, **kwargs):
    streets = response.json()
    for item in streets:
        if item["name"].casefold() == street.casefold():
            return item["id"]
    if streets:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", street, [item["name"] for item in streets]
        )
    raise SourceArgumentNotFound("street", street)


def _latest(response, *_, city, **kwargs):
    collections = response.json()
    if not collections:
        raise SourceArgumentNotFound("city", city)
    return max(collections, key=lambda item: item["tstamp"])


def _events(response, city_id, street_id, collection, **_):
    cutoff = date.today().replace(month=1, day=1)
    rows = []
    for item in response.json():
        collection_date = datetime.strptime(
            item["collect_date"]["date"], "%Y-%m-%d %H:%M:%S.%f"
        ).date()
        if collection_date < cutoff:
            continue
        labels = ["Gelbe Tonne", "Biotonne", "Restmülltonne"]
        if item["color"] == collection["color"]:
            labels.append("Papiertonne")
        rows.extend((collection_date, label) for label in labels)
    return rows


@final
class Source(BaseSource):
    TITLE = "ZVO Entsorgung - Zweckverband Ostholstein"
    DESCRIPTION = "Source for ZVO waste collection schedule in Ostholstein, Germany."
    URL = "https://www.zvo.com"
    COUNTRY = "de"
    TEST_CASES: ClassVar[dict] = {
        "Bad Schwartau, Lindenstraße": {
            "city": "Bad Schwartau",
            "street": "Lindenstraße",
        },
        "Curau (no street)": {"city": "Curau"},
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Find your city and street at https://www.zvo.com/abfuhrkalender2026. Some "
        "smaller towns do not require a street.",
        "de": "Finden Sie Ihren Ort und Ihre Straße unter "
        "https://www.zvo.com/abfuhrkalender2026. Einige kleinere Orte benötigen keine "
        "Straße.",
    }
    RAISE_ON_EMPTY = True

    PARAMS = (
        text_field("city", term=field_terms.MUNICIPALITY),
        text_field("street", term=field_terms.STREET, optional=True),
    )
    REGIONS = regions.from_yaml("zvo_com", country="country")
    ERROR_TEST_CASES: ClassVar[dict] = {"Unknown city": {"city": "__unknown_city__"}}
    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GENERAL_WASTE,
        wt.PAPER,
    ]
    retrieve = retrievers.Chain(
        retrievers.Lookup(f"{API_URL}/cities", pick=_city_id),
        retrievers.Lookup(
            f"{API_URL}/streets",
            method="POST",
            json=lambda city_id, **_: {"city": city_id},
            pick=_street_id,
            given=lambda *_, street=None, **kwargs: 0 if not street else None,
        ),
        retrievers.Lookup(
            f"{API_URL}/wastecollection",
            method="POST",
            json=lambda city_id, street_id, **_: {"city": city_id, "street": street_id},
            pick=_latest,
        ),
        retrievers.Lookup(
            f"{API_URL}/wastecollectiondates",
            method="POST",
            json=lambda city_id, street_id, collection, **_: {
                "collection": collection["id"]
            },
            pick=_events,
        ),
    )
    parse = staticmethod(lambda keys, source: keys[-1])
    transform = RowTransformer(
        type_value_map={
            "Gelbe Tonne": wt.RECYCLABLES,
            "Biotonne": wt.ORGANIC,
            "Restmülltonne": wt.GENERAL_WASTE,
            "Papiertonne": wt.PAPER,
        },
        carry_raw_label=True,
    )
