from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, street_address
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.transformers import JsonTransformer

URL = "https://calendrier.rmrlac.qc.ca"
_COMPONENT = "wasteCollectionComposanteSearch0"
_CALENDAR = f"{_COMPONENT}::calendar"

_TYPE_MAP = {
    "trash": wt.GENERAL_WASTE,
    "recycling": wt.RECYCLABLES,
    "compost": wt.ORGANIC,
}


def _rows(calendar, source) -> list[dict]:
    """One row per date of each ``data-dates-<type>="2026-09-07,2026-09-21,..."`` attribute."""
    rows = []
    for key in _TYPE_MAP:
        raw = str(calendar.get(f"data-dates-{key}") or "")
        rows.extend(
            {"type": key, "date": date.strip()}
            for date in raw.split(",")
            if date.strip()
        )
    return rows


@final
class Source(BaseSource):
    TITLE = "RMR Lac-Saint-Jean (QC)"
    DESCRIPTION = "Source script for RMR Lac-Saint-Jean waste collection"
    URL = URL
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Métabetchouan-Lac-à-la-Croix": {
            "street_number_and_name": "1201 16e Chemin",
            "locality": "Métabetchouan-Lac-à-la-Croix",
        },
    }

    PARAMS = (
        street_address("street_number_and_name"),
        municipality("locality"),
    )

    HOWTO: ClassVar[dict] = {
        "en": "Enter your street number and name along with your municipality, e.g. '1201 16e Chemin' in 'Métabetchouan-Lac-à-la-Croix'.",
        "fr": "Entrez votre numéro et nom de rue ainsi que votre municipalité, p. ex. '1201 16e Chemin' à 'Métabetchouan-Lac-à-la-Croix'.",
    }

    retrieve = retrievers.HttpPostRetriever(
        f"{URL}/calendrier-de-collectes",
        params={"url": "/calendrier-de-collectes", "component": _COMPONENT},
        data=lambda street_number_and_name, locality, **_: {
            "address": f"{street_number_and_name}, {locality}",
            "localisation_lat": "",
            "localisation_lng": "",
        },
        headers={
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "X-October-Request-Flash": "1",
            "X-October-Request-Handler": f"{_COMPONENT}::onSubmitAddress",
            "X-October-Request-Partials": f"{_COMPONENT}::not-found&{_CALENDAR}",
        },
    )

    parse = parsers.HtmlParser("div.collection-calendar", from_json_key=_CALENDAR)

    preprocess = ExplodeList(_rows)

    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )
