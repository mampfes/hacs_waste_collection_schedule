"""Dillingen Saar (dillingen-saar.de).

Demonstrates: a static, year-templated ICS GET whose title is truncated at the
first "..." (the feed appends extra detail after it, e.g. "Restmüll
Abfuhr...Behälter 120L"). ``HttpGetRetriever`` + the extended ``IcsParser``
(``regex`` captures everything before the first "...") + ``ICSTransformer`` do
all the work; this module only supplies the URL template and the waste-type
map.

NOTE: the ``service-dillingen-saar.fbo.de`` backend returned 404 for every
path (including its root) when this conversion was verified, both with and
without TLS verification — a pre-existing outage on the legacy source too,
not something this conversion introduced. Live TEST_CASES could not be
confirmed against a live response; the URL/params/regex are carried over
unchanged from the legacy ``fetch()``.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, PAPER, RECYCLABLES

_API_URL = "https://service-dillingen-saar.fbo.de/date/"


def _build_url(street: str) -> str:
    year = datetime.now().year
    # Preserves the legacy double slash after "date" (API_URL already ends in
    # "/", the template adds another) — harmless, and kept for exact parity.
    return f"{_API_URL}/{street}/{year!s}-01-01/+1%20year/"


@final
class Source(BaseSource):
    TITLE = "Dillingen Saar"
    DESCRIPTION = "Source script for waste collection Dillingen Saar"
    URL = "https://www.dillingen-saar.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Am Fischerberg": {"street": "Am Fischerberg"},
        "Odilienplatz": {"street": "Odilienplatz"},
        "Lilienstraße": {"street": "Lilienstraße"},
        "Joseph-Roederer-Straße": {"street": "Joseph-Roederer-Straße"},
    }

    PARAMS = (street("street"),)

    retrieve = HttpGetRetriever(
        url=lambda street, **_: _build_url(street),
        params={"format": "ics", "type": "rm,gs,bio,pa"},
    )
    parse = parsers.IcsParser(regex=r"^(.*?)\.\.\.")
    transform = ICSTransformer(
        type_value_map={
            "Papier Entsorgung": PAPER,
            "Restmüll Abfuhr": GENERAL_WASTE,
            "Tonnen Abfuhr": GENERAL_WASTE,
            "Gelbesäcke Abholung": RECYCLABLES,
        }
    )

    def __init__(self, street: str):
        super().__init__(street=street)
