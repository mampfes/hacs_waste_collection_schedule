"""SEAB Biella, Italy.

Demonstrates: the coordinate table-parser path. SEAB publishes a per-municipality
calendar PDF showing six months side-by-side, which plain text extraction
collapses. ``PdfTableParser`` returns each text run with its coordinates grouped
into rows, and ``PdfMonthColumns`` finds the months from the header row, bins
each row's runs into those columns and reads the day number and waste keyword
from each cell. ``ICSTransformer`` maps the Italian labels onto canonical
WasteTypes. All this source declares is the calendar's vocabulary: the round
labels it prints and where it states the year.
"""

from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.parsers import PdfTableParser
from waste_collection_schedule.preprocessors import PdfMonthColumns
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_TYPE_MAP = {
    "INDIFFERENZIATO": GENERAL_WASTE,
    "ORGANICO": ORGANIC,
    "CARTA": PAPER,
    "PLASTICA": RECYCLABLES,
    "VETRO": GLASS,
    "SFALCI": GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "SEAB Biella"
    DESCRIPTION = "Source for SEAB Biella (Italy) waste collection."
    URL = "https://www.seab.biella.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Ailoche": {
            "url": "https://www.seab.biella.it/wp-content/uploads/2026/05/Ailoche-II-semestre.pdf"
        },
        "Andorno Micca": {
            "url": "https://www.seab.biella.it/wp-content/uploads/2026/05/Andorno-Micca-II-semestre.pdf"
        },
    }

    PARAMS = (text_field("url", "Calendar PDF URL"),)

    HOWTO: ClassVar[dict] = {
        "it": (
            "Visita https://www.seab.biella.it/aree-servite, seleziona il tuo "
            "comune e copia il link al file PDF del calendario."
        ),
        "en": (
            "Visit https://www.seab.biella.it/aree-servite, select your "
            "municipality and copy the link to the PDF calendar file."
        ),
    }

    retrieve = HttpGetRetriever(url=lambda url: url)
    parse = PdfTableParser(min_words=50)
    # The cells omit the year; the sheet states it once, in its title.
    preprocess = PdfMonthColumns(
        labels=_TYPE_MAP,
        year_pattern=r"Raccolta rifiuti (\d{4})",
    )

    transform = ICSTransformer(type_value_map=_TYPE_MAP)
