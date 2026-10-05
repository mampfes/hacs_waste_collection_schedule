from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    house_number,
    postcode,
    street,
    text_field,
)
from waste_collection_schedule.field_terms import CITY
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://api.sundsvall.se/Garbage/2281/schedules"


def _query(
    street,
    house_number,
    postal_code,
    city="Sundsvall",
    additional_information=None,
    **_,
):
    params = {
        "street": street,
        "houseNumber": str(house_number),
        "postalCode": str(postal_code),
        "city": city,
    }
    if additional_information:
        params["additionalInformation"] = additional_information
    return params


@final
class Source(BaseSource):
    TITLE = "Mittsverige Vatten & Avfall"
    DESCRIPTION = "Source for Mittsverige Vatten & Avfall (MSVA) waste collection schedule, Sundsvall kommun."
    URL = "https://www.msva.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Västra Radiogatan 18, Sundsvall": {
            "street": "Västra Radiogatan",
            "house_number": "18",
            "postal_code": "85461",
            "city": "Sundsvall",
        },
        "Västra Radiogatan 22, Sundsvall": {
            "street": "Västra Radiogatan",
            "house_number": "22",
            "postal_code": "85461",
            "city": "Sundsvall",
        },
    }

    PARAMS = (
        street("street"),
        house_number("house_number"),
        postcode("postal_code"),
        text_field("city", term=CITY, default="Sundsvall"),
        text_field("additional_information", "Additional information", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the full street address for a property in Sundsvall kommun. "
            "The API only supports Sundsvall (municipality code 2281); Timrå and "
            "Nordanstig addresses are not covered. Use the same street, house "
            "number, postal code and city you would enter on msva.se. "
            "Additional information is a house letter or unit identifier, e.g. "
            "'A'; leave it empty if not applicable."
        ),
        "de": (
            "Geben Sie die vollständige Adresse für ein Grundstück in der "
            "Gemeinde Sundsvall ein. Die API unterstützt nur Sundsvall "
            "(Gemeindecode 2281); Adressen in Timrå und Nordanstig werden nicht "
            "abgedeckt. Zusatzinformation ist eine Hauskennung, z.B. 'A'; leer "
            "lassen, falls nicht zutreffend."
        ),
    }

    retrieve = retrievers.Request(API_URL, params=_query)
    parse = parsers.JsonParser()
    # One facility per property, each carrying its list of next pickups.
    preprocess = preprocessors.ExplodeList("schedules")
    transform = JsonTransformer(
        date_key="nextPickupDate",
        type_key="wasteType",
        type_value_map={
            "WASTE": wt.GENERAL_WASTE,
            "FOOD": wt.FOOD_WASTE,
            "PAPER": wt.PAPER,
            "PLASTIC": wt.RECYCLABLES,
        },
    )
