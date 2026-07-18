"""A.R.T. Trier (art-trier.de).

Demonstrates: a static, param-built ICS GET whose feed needs the extended
``IcsParser`` options (``regex`` to trim a fixed prefix off every title,
``split_at`` for a combined round listed as one VEVENT). HttpGetRetriever +
the extended IcsParser + ICSTransformer do all the work; this module only
supplies the URL template (with its district-name transliteration) and the
waste-type map.
"""

import logging
from typing import ClassVar, final
from urllib.parse import quote

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, postcode
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, PAPER, RECYCLABLES

_LOGGER = logging.getLogger(__name__)

_API_URL = "https://www.art-trier.de/ics-feed"
_REMINDER_DAY = "0"  # the event is on the same day as the actual collection
_REMINDER_TIME = "0600"  # any hour of the correct day; the value itself is unused

_SPECIAL_CHARS = str.maketrans(
    {
        " ": "_",
        "ä": "ae",
        "ü": "ue",
        "ö": "oe",
        "ß": "ss",
        "(": None,
        ")": None,
        ",": None,
        ".": None,
    }
)


def _build_url(district: str, zip_code: str) -> str:
    arg = quote(
        district.lower().removeprefix("stadt ").translate(_SPECIAL_CHARS).strip()
    )
    return f"{_API_URL}/{zip_code}:{arg}::@{_REMINDER_DAY}-{_REMINDER_TIME}.ics"


@final
class Source(BaseSource):
    TITLE = "A.R.T. Trier (Deprecated)"
    DESCRIPTION = "Source for waste collection of A.R.T. Trier."
    URL = "https://www.art-trier.de"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Trier": {"zip_code": "54296", "district": "Stadt Trier, Universitätsring"},
        "Schweich": {"zip_code": "54338", "district": "Schweich (inkl. Issel)"},
        "Dreis": {"zip_code": "54518", "district": "Dreis"},
        "Wittlich Marktplatz": {
            "zip_code": "54516",
            "district": "Wittlich, Marktplatz",
        },
        "Wittlich Wengerohr": {"zip_code": "54516", "district": "Wittlich-Wengerohr"},
    }

    PARAMS = (
        postcode(postcode_field="zip_code"),
        district("district"),
    )

    retrieve = HttpGetRetriever(
        url=lambda district, zip_code, **_: _build_url(district, zip_code)
    )
    parse = parsers.IcsParser(
        regex=r"^A.R.T. Abfuhrtermin: (.*)",
        split_at=r" & ",
    )
    transform = ICSTransformer(
        type_value_map={
            "Altpapier": PAPER,
            "Restmüll": GENERAL_WASTE,
            "Gelber Sack": RECYCLABLES,
        }
    )

    def __init__(self, district: str, zip_code: str):
        super().__init__(district=district, zip_code=zip_code)
        _LOGGER.warning(
            "The A.R.T. Trier source is deprecated and might not work with all"
            " addresses anymore. Please use the ICS integration instead: "
            "https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/ics/art_trier_de.md"
        )
