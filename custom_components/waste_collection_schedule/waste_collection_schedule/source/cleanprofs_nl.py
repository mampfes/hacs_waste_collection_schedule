from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, postcode, text_field
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://cleanprofs.jmsdev.nl/api/get-plannings-address"


_TYPE_MAP = {
    "GFT": wt.ORGANIC,
    "RST": wt.GENERAL_WASTE,
    "Duo": wt.GENERAL_WASTE,
    "PLC": wt.RECYCLABLES,
}


@final
class Source(BaseSource):
    TITLE = "CleanProfs"
    DESCRIPTION = "Container cleaning schedules provided by CleanProfs."
    URL = "https://www.cleanprofs.nl"
    COUNTRY = "nl"

    SOURCE_CODEOWNERS: ClassVar[list] = ["@BjornWill"]

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "CleanProfs Wateringen": {
            "postcode": "2291PG",
            "house_number": "12",
        }
    }

    PARAMS = (
        postcode(),
        house_number(),
        text_field("suffix", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the postcode, house number and optional house-number "
            "addition of an address registered with CleanProfs."
        ),
        "nl": (
            "Vul de postcode, het huisnummer en eventueel de toevoeging in "
            "van een adres dat bij CleanProfs geregistreerd is."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.Request(
        API_URL,
        params=lambda postcode, house_number, suffix="", **_: {
            "zipcode": postcode.replace(" ", "").upper(),
            "house_number": str(house_number).strip(),
            "suffix": str(suffix or "").strip(),
        },
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )

    parse = parsers.JsonParser()

    transform = JsonTransformer(
        date_key="full_date",
        type_key="product_name",
        type_value_map=_TYPE_MAP,
    )
