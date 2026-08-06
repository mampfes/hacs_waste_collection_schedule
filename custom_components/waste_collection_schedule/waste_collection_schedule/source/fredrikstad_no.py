from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.ArcGis import (
    ArcGisCodedValueParser,
    ArcGisTwoStepFeatureRetriever,
    epoch_ms_to_date,
)
from waste_collection_schedule.transformers import JsonTransformer

# Fredrikstad kommune's MinRenovasjon MapServer splits the flow across two
# unrelated layers: layer 0 resolves a street address to an "AvtLnr" (renovation
# agreement number) via an attribute query; layer 1 holds the actual dated pickup
# events, queried by that AvtLnr. That is the shared two-step retriever with its
# lookup pointed at a second layer (lookup_url). Layer 1 stores the waste type as
# an integer whose Norwegian names come from the layer's own AvfallId coded-value
# domain, which ArcGisCodedValueParser decodes onto each feature.

BASE_URL = "https://arcgis.fredrikstad.kommune.no/server/rest/services/Renovasjon/MinRenovasjon/MapServer"
SCHEDULE_DAYS = 365
_TIMEOUT = 30

# Static fallback mapping for when the ArcGIS coded value domain does not
# return proper Norwegian waste type names. Values confirmed by a Fredrikstad
# resident (GitHub issue #2525).
WASTE_TYPE_FALLBACK: dict[int, str] = {
    1: "Restavfall",
    2: "Papir og plast",
    4: "Glass og metall",
    6: "Farlig avfall",
    16: "Matavfall",
}

# Known Norwegian labels mapped to a canonical type. Norwegian isn't one of the
# shared vocabulary's supported languages, so without this an unrecognised label
# is preserved verbatim (still correct, just without a canonical icon/colour).
_TYPE_MAP = {
    "Restavfall": wt.GENERAL_WASTE,
    "Papir og plast": wt.RECYCLABLES,
    "Glass og metall": wt.RECYCLABLES,
    "Farlig avfall": wt.HAZARDOUS,
    "Matavfall": wt.FOOD_WASTE,
}


def _lookup_where(**params) -> str:
    address = params["address"]
    return f"UPPER(Adresse) = '{address.upper()}' AND AvtStatus = 0"


def _schedule_where(avt_lnr, **params) -> str:
    today = date.today()
    end_date = today + timedelta(days=SCHEDULE_DAYS)
    return (
        f"AvtLnr = {avt_lnr} "
        f"AND Dato >= date '{today.isoformat()}' "
        f"AND Dato <= date '{end_date.isoformat()}'"
    )


@final
class Source(BaseSource):
    TITLE = "Fredrikstad kommune"
    DESCRIPTION = "Source for Fredrikstad kommune waste collection."
    URL = "https://www.fredrikstad.kommune.no"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Kanelveien 4": {"address": "Kanelveien 4"},
    }

    PARAMS = (street_address(),)

    retrieve = ArcGisTwoStepFeatureRetriever(
        f"{BASE_URL}/1",
        lookup_url=f"{BASE_URL}/0",
        lookup_where=_lookup_where,
        schedule_where=_schedule_where,
        argument="address",
        id_field="AvtLnr",
        lookup_fields="AvtLnr",
        out_fields="Dato,AvfallId",
        timeout=_TIMEOUT,
    )
    parse = ArcGisCodedValueParser(
        f"{BASE_URL}/1",
        "AvfallId",
        into="AvfallNavn",
        fallback=WASTE_TYPE_FALLBACK,
        unknown="Avfall {code}",
        timeout=_TIMEOUT,
    )
    transform = JsonTransformer(
        date_key=lambda attrs: epoch_ms_to_date(attrs["Dato"]),
        type_key="AvfallNavn",
        type_value_map=_TYPE_MAP,
    )
