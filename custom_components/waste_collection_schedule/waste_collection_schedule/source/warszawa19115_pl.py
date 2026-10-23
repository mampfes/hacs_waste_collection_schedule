from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    location_id,
    street_address,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import JsonTransformer

_SCHEDULE_URL = "https://warszawa19115.pl/harmonogramy-wywozu-odpadow"
_PORTLET = (
    "portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ"
)

# The portal answers "no next date" with this placeholder instead of omitting
# the entry.
_NO_DATE = "1900-01-01"


def _address_point_id(response, *keys, street_address=None, **_) -> str:
    """The address search answers ``[{"fullName": ..., "addressPointId": ...}]``."""
    matches = response.json()
    if not matches or "addressPointId" not in matches[0]:
        raise SourceArgumentNotFound("street_address", street_address)
    return str(matches[0]["addressPointId"])


@final
class Source(BaseSource):
    TITLE = "Warsaw"
    DESCRIPTION = "Source for Warsaw city garbage collection"
    URL = "https://warszawa19115.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Street Name": {"street_address": "MARSZAŁKOWSKA 84/92, 00-514 Śródmieście"},
        "Geolocation ID": {"geolocation_id": "27044650"},
    }

    PARAMS = (
        alternatives(
            [street_address("street_address")], [location_id("geolocation_id")]
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address as `street_address`, in the form the "
            "[Warsaw 19115 portal](https://warszawa19115.pl/harmonogramy-wywozu-odpadow) "
            "suggests it (for example `MARSZAŁKOWSKA 84/92, 00-514 Śródmieście`), "
            "or the portal's numeric address point id as `geolocation_id`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _SCHEDULE_URL,
                params=lambda street_address=None, **_: {
                    "p_p_id": _PORTLET,
                    "p_p_lifecycle": "2",
                    "p_p_resource_id": "autocompleteResource",
                    f"_{_PORTLET}_name": street_address,
                },
                given=lambda geolocation_id=None, **_: geolocation_id,
                pick=_address_point_id,
            ),
        ),
        url=_SCHEDULE_URL,
        params=lambda address_point_id, **_: {
            "p_p_id": _PORTLET,
            "p_p_lifecycle": "2",
            "p_p_resource_id": "ajaxResource",
            f"_{_PORTLET}_addressPointId": address_point_id,
        },
    )

    parse = parsers.JsonParser()

    preprocess = preprocessors.Compose(
        preprocessors.ExplodeList("harmonogramyZ"),
        preprocessors.RowFilter(
            lambda record, _: record.get("data") not in (None, "", _NO_DATE)
        ),
    )

    transform = JsonTransformer(
        date_key="data",
        type_key=lambda record: record["frakcja"]["id_frakcja"],
        type_value_map={
            "BG": wt.FOOD_WASTE,
            "BK": wt.FOOD_WASTE,
            "MT": wt.RECYCLABLES,
            "OP": wt.PAPER,
            "OS": wt.GLASS,
            "OZ": wt.GARDEN_WASTE,
            "WG": wt.BULKY_WASTE,
            "ZM": wt.GENERAL_WASTE,
        },
    )
