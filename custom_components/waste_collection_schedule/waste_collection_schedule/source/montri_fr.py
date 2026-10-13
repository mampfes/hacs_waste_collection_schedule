from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street_address, text_field
from waste_collection_schedule.field_terms import POSTCODE
from waste_collection_schedule.service.MontriCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Montri"
    DESCRIPTION = "Source for Montri, a French waste collection schedule platform used by several intercommunal waste-management syndicates (e.g. SICOVAD around Épinal)."
    URL = "https://montri.fr"
    COUNTRY = "fr"
    TEST_CASES: ClassVar[dict] = {
        "6 Place Georges Boizot, Dinozé": {
            "postal_code": "88000",
            "city_name": "Dinozé",
            "address": "6 Place Georges Boizot",
        },
        "2 Place Georges Clémenceau, Épinal": {
            "postal_code": "88000",
            "city_name": "Épinal",
            "address": "2 place georges clémenceau",
        },
        "30 La Ville Es Nouvelle, Iffendic": {
            "postal_code": "35750",
            "city_name": "Iffendic",
            "address": "30 La Ville Es Nouvelle",
        },
    }
    PARAMS = (
        text_field("postal_code", term=POSTCODE),
        city("city_name"),
        street_address(),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "householdtrash": wt.GENERAL_WASTE,
            "recyclable": wt.RECYCLABLES,
            "Emballages recyclables": wt.RECYCLABLES,
            "glass": wt.GLASS,
            "paper": wt.PAPER,
            "organic": wt.ORGANIC,
            "bulky": wt.BULKY_WASTE,
        },
    )
