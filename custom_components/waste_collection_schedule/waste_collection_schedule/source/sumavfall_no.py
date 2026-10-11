from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "Restavfall": wt.GENERAL_WASTE,
    "Matavfall": wt.FOOD_WASTE,
    "Papp/papir": wt.PAPER,
    "Plastemballasje": wt.PLASTIC,
    "Glas-emballasje": wt.GLASS,
    "Metallemballasje": wt.METAL,
    # Older wordings of the combined rounds.
    "Papp & Plast": [wt.PAPER, wt.PLASTIC],
    "Glass- og metallemballasje": [wt.GLASS, wt.METAL],
}


@final
class Source(BaseSource):
    TITLE = "SUM Avfall (Sunnfjord og Ytre Sogn Miljøverk IKS)"
    DESCRIPTION = (
        "Source script for sumavfall.no - Sunnfjord og Ytre Sogn Miljøverk IKS"
    )
    URL = "https://www.sumavfall.no"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.PLASTIC,
        wt.GLASS,
        wt.METAL,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Blåbærlia 16": {"address": "blåbærlia-16"},
    }

    PARAMS = (text_field("address", "Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "The address slug as it appears in the calendar URL "
            "(`https://www.sumavfall.no/tommekalender?adresse=...`), "
            "e.g. 'blåbærlia-16' or 'storgata-1'."
        ),
    }

    retrieve = HttpGetRetriever(
        url="https://www.sumavfall.no/tommekalender",
        params=lambda address, **_: {"adresse": address},
    )
    # One <li> per collection day: the date as DD.MM.YYYY and one span per
    # round collected that day.
    parse = parsers.HtmlLabelledDates(
        "details li",
        label="span.text-lg",
        date="div.flex",
        date_pattern=r"(\d{2}\.\d{2}\.\d{4})",
        all_labels=True,
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d.%m.%Y"),
        clean=lambda label: label.strip().rstrip(","),
        type_value_map=_TYPE_MAP,
    )
