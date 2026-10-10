import re
from typing import ClassVar, final
from urllib.parse import quote

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

# Telge's schedule endpoint takes the exact (upper-case) address string of its
# autocomplete and answers with one record per emptying:
# {"date": "2026-09-15T00:00:00", "typeOfWaste": "HEMSORT",
#  "typeOfWasteDescription": "Hemsortering", "containerType": "K240L1", ...}.
# A property with two bins of one service (the four-compartment
# "Hemsortering" bins, K240L1 / K240L2) is told apart by the container's
# trailing number, as "Hemsortering (kärl 1)". An unknown address answers
# with an empty list; the autocomplete for its street then provides the
# suggestions.

API_URL = "https://www.telge.se/api/thorweb/garbagecollection"

_BIN_NUMBER = re.compile(r"L(\d+)$")


def _address(address: str) -> str:
    return quote(address.strip().upper(), safe=",")


def _label(record) -> str:
    waste_type = (record.get("typeOfWaste") or "").strip()
    label = (record.get("typeOfWasteDescription") or waste_type).strip()
    match = _BIN_NUMBER.search((record.get("containerType") or "").strip())
    if match:
        label += f" (kärl {match.group(1)})"
    return label


def _suggestions(response, **_) -> list[str]:
    suggestions = response.json()
    if not suggestions:
        raise ValueError("no suggestions")
    return suggestions


@final
class Source(BaseSource):
    TITLE = "Telge Återvinning"
    DESCRIPTION = "Source for Telge Återvinning, household waste collection in Södertälje municipality"
    URL = "https://www.telge.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.PLASTIC,
        wt.GLASS,
        wt.METAL,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Residential Södertälje": {"address": "BERGSGATAN 22, SÖDERTÄLJE"},
        "Rural with latrine": {"address": "BERGA 1, JÄRNA"},
        "Garden waste": {"address": "PALLSTIGEN 1, HÖLÖ"},
        "Commercial sorting": {"address": "STORGATAN 13 VÅRDCENTRAL JÄRNA, JÄRNA"},
        "Septic tank": {"address": "BACKA 3 MARIELUND, JÄRNA"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your address at https://www.telge.se by searching for your "
            "street name in the waste collection schedule (Sopbilsschema). Use "
            "the exact address string shown in the autocomplete dropdown, e.g. "
            "'BERGSGATAN 22, SÖDERTÄLJE'."
        ),
    }

    retrieve = HttpGetRetriever(
        url=lambda address, **_: f"{API_URL}/schedule/{_address(address)}"
    )
    parse = parsers.ArgumentGuard(
        parsers.JsonParser(raise_for_status=True),
        argument="address",
        contains='"date"',
        suggestions=retrievers.Suggestions(
            lambda address, **_: (
                f"{API_URL}/autocomplete/{_address(address.split(',')[0])}"
            ),
            pick=_suggestions,
        ),
    )
    transform = JsonTransformer(
        date_key="date",
        type_key=_label,
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        # Several services share a canonical type (Wellpapp and Returpapper,
        # Latrin and Slam); keep Telge's label as the description.
        carry_raw_label=True,
        type_value_map={
            # Four-compartment bin 1 (fortnightly): residual and food waste,
            # coloured glass, hard plastic and paper packaging.
            "Hemsortering (kärl 1)": wt.GENERAL_WASTE,
            # Four-compartment bin 2 (monthly): clear glass, metal packaging,
            # newspapers and plastic packaging.
            "Hemsortering (kärl 2)": wt.RECYCLABLES,
            "Hemsortering": wt.RECYCLABLES,
            "Mat & Restavfall": wt.GENERAL_WASTE,
            "Brännbart avfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Trädgårdsavfall": wt.GARDEN_WASTE,
            "Wellpapp": wt.PAPER,
            "Returpapper": wt.PAPER,
            "Plastförpackningar": wt.PLASTIC,
            "Glas ofärgat": wt.GLASS,
            "Glas färgat": wt.GLASS,
            "Metallförpackningar": wt.METAL,
            # Emptying of a latrine and of a septic tank.
            "Latrin": wt.OTHER,
            "Slam": wt.OTHER,
        },
    )
