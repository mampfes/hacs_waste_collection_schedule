from typing import final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import GLASS, PAPER, RECYCLABLES

# Demonstrates: a downloadable open-data CSV consumed end-to-end by the pipeline.
# parsers.CsvParser turns the semicolon-delimited export into dict rows (one row
# per collection event: commune; type; date), so a plain JsonTransformer types
# each row by its `type` column and parses the ISO `date` column. The retriever
# filters server-side to the requested commune via the Opendatasoft `where`
# clause, so only that commune's rows come back.
#
# Tibi (the intercommunale serving the Charleroi region of Wallonia) publishes
# this calendar through the Open Data Wallonie-Bruxelles Opendatasoft portal.
# It covers the two door-to-door selective streams only: PMC (plastics, metals,
# drink cartons) and the combined glass + paper/cardboard day ("V / PC"). That
# combined day is a single export row covering two waste types, so it maps to a
# list of WasteTypes and the pipeline emits one Collection per type on the date.

DATASET_URL = (
    "https://digitalwallonia.opendatasoft.com/api/explore/v2.1/"
    "catalog/datasets/calendrier-des-collectes-2026/exports/csv"
)

# Raw export `type` value -> canonical WasteType(s).
#   "PMC"    = Plastiques, Métaux, Cartons à boissons -> packaging recyclables.
#   "V / PC" = Verre / Papier-Carton, glass and paper/cardboard collected on the
#              same day. Mapping it to a list yields one Collection per type on
#              that date, so both streams are represented faithfully.
_TYPE_MAP = {
    "PMC": RECYCLABLES,
    "V / PC": [GLASS, PAPER],
}


@final
class Source(BaseSource):
    TITLE = "Tibi (Charleroi region)"
    DESCRIPTION = (
        "Selective waste collection schedule for the Tibi intercommunale "
        "(Charleroi region, Wallonia)."
    )
    URL = "https://www.tibi.be"
    COUNTRY = "be"

    TEST_CASES = {
        "Charleroi": {"commune": "Charleroi"},
        "Couillet": {"commune": "Couillet"},
    }

    PARAMS = [text_field("commune", "Commune")]

    HOWTO = {
        "en": (
            "Enter your commune exactly as it appears in the Tibi calendar "
            "(e.g. 'Charleroi', 'Couillet', 'Marcinelle'). Larger municipalities "
            "are split into numbered sectors (e.g. 'Courcelles 1')."
        ),
        "fr": (
            "Indiquez votre commune telle qu'elle figure dans le calendrier "
            "Tibi (ex. 'Charleroi', 'Couillet', 'Marcinelle'). Certaines "
            "communes sont divisées en secteurs numérotés (ex. 'Courcelles 1')."
        ),
    }

    CODEOWNERS = ["@markvp"]

    # An unknown commune yields an empty export rather than an error, so surface
    # that to the user as a bad-argument error instead of a silent empty calendar.
    RAISE_ON_EMPTY = True

    retrieve = retrievers.HttpGetRetriever(
        url=DATASET_URL,
        params=lambda commune, **_: {"where": f'commune="{commune}"'},
    )

    # The export is served with a UTF-8 BOM, which csv.DictReader leaves on the
    # first column name ("﻿commune"). The commune column is filtered
    # server-side and never read by the transformer, so the shape guard checks
    # only the columns actually consumed ("type", "date") to avoid the BOM.
    parse = parsers.CsvParser(delimiter=";", shape=["type", "date"])

    transformer = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map=_TYPE_MAP,
    )

    def __init__(self, commune: str):
        super().__init__(commune=commune)
