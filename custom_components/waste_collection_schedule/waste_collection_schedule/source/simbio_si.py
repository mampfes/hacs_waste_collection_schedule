import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.preprocessors import (
    Compose,
    DateFields,
    DefaultPreprocessor,
)
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import ICSTransformer


def _next_date(value: str) -> "datetime.date | None":
    """ "četrtek, 1. 10. 2026" as a date; "ni odvoza" (no collection) as None."""
    parts = str(value or "").split(",")
    if len(parts) < 2:
        return None
    return datetime.datetime.strptime(parts[1].strip(), "%d. %m. %Y").date()


@final
class Source(BaseSource):
    TITLE = "Simbio"
    DESCRIPTION = "Source for Simbio."
    URL = "https://www.simbio.si/"
    COUNTRY = "si"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Ljubljanska cesta 1 A": {"street": "Ljubljanska cesta", "house_number": "1 A"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"street": "Nikjer", "house_number": "999"},
    }

    PARAMS = (street(), house_number())

    retrieve = HttpPostRetriever(
        url="https://www.simbio.si/sl/moj-dan-odvoza-odpadkov",
        data=lambda street, house_number, **_: {
            "query": f"{street} {house_number}",
            "action": "simbioOdvozOdpadkov",
        },
    )
    # The search can match the address in several towns; the first match is
    # the best one, as on the council's own page.
    parse = parsers.JsonParser()
    preprocess = Compose(
        DefaultPreprocessor(),
        DateFields(
            fields={
                "next_mko": "Mesani",
                "next_emb": "Embalaza",
                "next_bio": "Bioloski",
            },
            parse_date=_next_date,
        ),
    )
    transform = ICSTransformer(
        type_value_map={
            "Mesani": wt.GENERAL_WASTE,
            "Embalaza": wt.RECYCLABLES,
            "Bioloski": wt.ORGANIC,
        }
    )
