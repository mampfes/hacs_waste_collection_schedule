from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://www.rova.nl/api/waste-calendar/year"


def _query(
    year: int,
    _context,
    *,
    postalcode,
    house_number,
    addition="",
    **_,
) -> dict:
    return {
        "postalcode": str(postalcode).replace(" ", "").upper(),
        "houseNumber": str(house_number).strip(),
        "addition": str(addition or "").strip(),
        "year": year,
    }


@final
class Source(BaseSource):
    TITLE = "Rova"
    DESCRIPTION = "Source for Rova waste collection in the Netherlands."
    URL = "https://www.rova.nl"
    COUNTRY = "nl"
    RAISE_ON_EMPTY = True

    HOWTO: ClassVar[dict] = {
        "en": (
            "Use the same postal code and house number you would enter at "
            "https://www.rova.nl/afvalkalender. If your address has a letter or "
            "addition, provide it in the 'addition' field."
        ),
        "nl": (
            "Gebruik dezelfde postcode en huisnummer als je zou invoeren op "
            "https://www.rova.nl/afvalkalender. Als je adres een letter of "
            "toevoeging heeft, geef deze dan in het 'addition'-veld."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [wt.ORGANIC, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Lemele Lemelerweg 44": {
            "postalcode": "8148PC",
            "house_number": "44",
        },
        "Hardenberg Stationsstraat 1": {
            "postalcode": "7721AA",
            "house_number": "1",
            "addition": "",
        },
    }

    PARAMS = (
        postcode(postcode_field="postalcode", house_field="house_number"),
        text_field("addition", "Addition", default=""),
    )

    retrieve = retrievers.YearlyRetriever(
        fetch=retrievers.Request(_API_URL, params=_query),
    )

    parse = parsers.EachResponse(parsers.JsonParser())

    transform = JsonTransformer(
        date_key="date",
        type_key=lambda record: (record.get("wasteType") or {}).get("title"),
        type_value_map={
            "gft": wt.ORGANIC,
            "pmd": wt.RECYCLABLES,
            "restafval": wt.GENERAL_WASTE,
            "papier": wt.PAPER,
            "glas": wt.GLASS,
            "textiel": wt.TEXTILES,
            "snoeiafval": wt.GARDEN_WASTE,
            "kerstboom": wt.OTHER,
        },
        carry_raw_label=True,
    )
