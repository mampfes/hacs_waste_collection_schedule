from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import integer
from waste_collection_schedule.parsers import ArgumentGuard, JsonParser
from waste_collection_schedule.preprocessors import Compose, ExplodeList
from waste_collection_schedule.retrievers import Request, Suggestions
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://api.skycms.com.pl/api/v1/rest"

# Public API key of the "Gmina Trzebnica" SkyCMS app. It identifies the
# municipality (tenant), not a user, and is shipped with the public app.
# Other SkyCMS municipalities use their own key and their own region IDs,
# so this source is scoped to Gmina Trzebnica.
_HEADERS = {
    "x-skycms-key": "a90a376c6b19307acf1334b1a3937235",
    "x-skycms-device": "waste-collection-schedule",
    "x-skycms-type": "web",
    "x-skycms-model": "waste-collection-schedule",
    "x-skycms-version": "1.0.0",
    "x-skycms-app-version": "1.0.0",
    "x-skycms-language": "pl",
}


def _region_ids(response, **_) -> list[str]:
    """All region IDs known to the app, offered as suggestions."""
    regions = (response.json().get("data") or {}).get("regions") or []
    return [f"{r['id']} ({r.get('name', '')})" for r in regions if "id" in r]


@final
class Source(BaseSource):
    TITLE = "Gmina Trzebnica"
    DESCRIPTION = "Source for Gmina Trzebnica, Poland (SkyCMS municipal app API)"
    URL = "https://trzebnica.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@Tymon3310"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Trzebnica - Brzyków (Sołectwa 8)": {"region_id": 88},
        "Trzebnica 2": {"region_id": 8},
    }

    PARAMS = (integer("region_id", label="Region ID", optional=False),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Install the 'Gmina Trzebnica' app and look up your waste collection "
            "region. The region ID can be found in the app's waste calendar "
            "section, or in the region list linked from the documentation of "
            "this source."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
    ]

    retrieve = Request(
        lambda region_id, **_: f"{_API}/garbage/disposals/{region_id}",
        headers=_HEADERS,
    )
    # An unknown region still answers HTTP 200 with success=true, but the data
    # only holds a message instead of the schedule.
    parse = ArgumentGuard(
        JsonParser("data"),
        argument="region_id",
        contains="garbage_kinds",
        suggestions=Suggestions(
            f"{_API}/garbage/regions", headers=_HEADERS, pick=_region_ids
        ),
        hint="it must be a valid region ID of the Gmina Trzebnica app.",
    )
    preprocess = Compose(
        ExplodeList("garbage_kinds"),
        ExplodeList("disposals", into="disposal"),
    )
    transform = JsonTransformer(
        date_key=lambda record: record["disposal"]["id"],
        type_key="name",
        type_value_map={
            "Odpady Zielone / Kuchenne (Sołectwa)": wt.ORGANIC,
            "Odpady Zielone / Kuchenne (Trzebnica)": wt.ORGANIC,
            "Odpady Zielone": wt.GARDEN_WASTE,
            "Wielkogabarytowe": wt.BULKY_WASTE,
            "Tworzywa sztuczne": wt.RECYCLABLES,
            "Zmieszane": wt.GENERAL_WASTE,
            "Papier": wt.PAPER,
            "Szkło": wt.GLASS,
            "Bio": wt.ORGANIC,
        },
        skip_unparseable_dates=True,
    )
