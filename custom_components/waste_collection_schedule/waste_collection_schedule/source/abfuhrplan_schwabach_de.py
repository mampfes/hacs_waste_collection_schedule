"""City of Schwabach, Germany (abfuhrplan-schwabach.de).

A single-level (street only) deployment of the shared abfuhrplan-*.de
platform, so the whole flow -- address path, 404 walk-up for suggestions and
the ``/getical`` form POST -- is the shared ``AbfuhrplanRetriever``. This
deployment also strips commas out of a street name, which the platform's
``prepare_arg`` takes as ``remove``.
"""

from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.service.AbfuhrplanDe import (
    AbfuhrplanRetriever,
    prepare_arg,
)
from waste_collection_schedule.transformers import ICSTransformer

# Trailing slash is part of the provider's own URL structure; the getical
# endpoint below is requested with a doubled slash to match, matching the
# legacy source's (accidental but working) request shape.
_BASE_URL = "https://www.abfuhrplan-schwabach.de/"


def _prepare_arg(arg: str) -> str:
    return prepare_arg(arg, remove="(),")


@final
class Source(BaseSource):
    TITLE = "Schwabach"
    DESCRIPTION = "Source for the city of Schwabach"
    URL = _BASE_URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Am Alten Friedhof 3, 3a": {"street": "Am Alten Friedhof 3, 3a"},
        "Äußere Rittersbacher Straße": {"street": "Äußere Rittersbacher Straße"},
    }

    PARAMS = (street(field="street"),)

    retrieve = AbfuhrplanRetriever(
        base_url=_BASE_URL, fields=("street",), normalise=_prepare_arg
    )
    parse = IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Restmüllcontainer": wt.GENERAL_WASTE,
            "Papiertonne": wt.PAPER,
            "Gelber Sack": wt.RECYCLABLES,
            "Biotonne": wt.ORGANIC,
            "Biocontainer": wt.ORGANIC,
        }
    )

    def __init__(self, street: str):
        super().__init__(street=_prepare_arg(street))
