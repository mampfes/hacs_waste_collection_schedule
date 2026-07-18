from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    epoch_ms_to_date,
    feature_query,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GENERAL_WASTE,
    HAZARDOUS,
    RECYCLABLES,
)

# Fredrikstad kommune's MinRenovasjon MapServer splits the flow across two
# unrelated layers: layer 0 resolves a street address to an "AvtLnr" (renovation
# agreement number) via an attribute query; layer 1 holds the actual dated pickup
# events, queried by that AvtLnr. That is two different feature_url values, so
# the shared ArcGisTwoStepFeatureRetriever (one feature_url for both steps) does
# not fit; retrieve() queries each layer directly via feature_query and adds a
# third request for layer 1's field metadata, whose AvfallId coded-value domain
# supplies the Norwegian waste-type names. parse() decodes that domain and pairs
# it with the schedule features; a plain ICSTransformer types the (date, label)
# rows it yields.

BASE_URL = "https://arcgis.fredrikstad.kommune.no/server/rest/services/Renovasjon/MinRenovasjon/MapServer"
SCHEDULE_DAYS = 365

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
    "Restavfall": GENERAL_WASTE,
    "Papir og plast": RECYCLABLES,
    "Glass og metall": RECYCLABLES,
    "Farlig avfall": HAZARDOUS,
    "Matavfall": FOOD_WASTE,
}


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

    PARAMS = (text_field("address", "Street Address"),)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())

    def retrieve(self, source: "Source"):
        address = self.params["address"]
        lookup = feature_query(
            f"{BASE_URL}/0",
            where=f"UPPER(Adresse) = '{address.upper()}' AND AvtStatus = 0",
            out_fields="AvtLnr",
            timeout=self.TIMEOUT,
        )
        matches = ArcGisFeatureParser()(lookup, source)
        if not matches:
            raise SourceArgumentNotFound("address", address)
        avt_lnr = matches[0]["AvtLnr"]

        today = date.today()
        end_date = today + timedelta(days=SCHEDULE_DAYS)
        schedule = feature_query(
            f"{BASE_URL}/1",
            where=(
                f"AvtLnr = {avt_lnr} "
                f"AND Dato >= date '{today.isoformat()}' "
                f"AND Dato <= date '{end_date.isoformat()}'"
            ),
            out_fields="Dato,AvfallId",
            timeout=self.TIMEOUT,
        )
        # The coded-value domain for AvfallId, fetched from the layer's field
        # metadata rather than /query, so it must go through source.session
        # directly (feature_query always targets /query).
        domain = source.session.get(
            f"{BASE_URL}/1", params={"f": "json"}, timeout=self.TIMEOUT
        )
        return schedule, domain

    def parse(self, raw, source: "Source | None" = None) -> list[tuple[date, str]]:
        schedule_response, domain_response = raw
        features = ArcGisFeatureParser()(schedule_response, source)

        domain_response.raise_for_status()
        waste_types: dict[int, str] = {}
        for field in domain_response.json().get("fields", []):
            if field["name"] == "AvfallId":
                domain = field.get("domain") or {}
                if domain.get("type") == "codedValue":
                    waste_types = {
                        cv["code"]: cv["name"] for cv in domain["codedValues"]
                    }
                break

        records: list[tuple[date, str]] = []
        for attrs in features:
            avfall_id = attrs["AvfallId"]
            waste_name = waste_types.get(avfall_id) or WASTE_TYPE_FALLBACK.get(
                avfall_id, f"Avfall {avfall_id}"
            )
            records.append((epoch_ms_to_date(attrs["Dato"]), waste_name))
        return records
