"""SMOLO a.s. (Třinec), Czech Republic.

The household-waste page links one schedule PDF per year for Třinec
("harmonogram 2026 SKO, BIO, SEP"); the year is in the file name, so
``PdfLinkRetriever`` picks the current one. The PDF is a table of districts
with a collection weekday, which ``service.SmoloSchedule`` reads and expands
into dates for the configured district (and street, where a district appears in
several rows).
"""

from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.service import SmoloSchedule
from waste_collection_schedule.transformers import ICSTransformer

_LANDING_PAGE_URL = (
    "https://www.smolo.cz/sluzby/odpadove-hospodarstvi/informace-pro-domacnosti/"
)


@final
class Source(BaseSource):
    TITLE = "SMOLO a.s. (Třinec)"
    DESCRIPTION = (
        "Source for SMOLO a.s. household waste collection schedule for the town "
        "of Třinec, Czech Republic."
    )
    URL = _LANDING_PAGE_URL
    COUNTRY = "cz"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@jan-tdy"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PLASTIC,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Nebory": {"district": "Nebory"},
        "Karpentná": {"district": "Karpentná"},
        "Stare Mesto Husova": {"district": "Staré Město", "street": "Husova"},
    }

    PARAMS = (district("district"), street("street", optional=True))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open the SMOLO a.s. household-waste page "
            f"({_LANDING_PAGE_URL}) and look up the current 'Třinec - harmonogram' "
            "PDF for the SKO/BIO/SEP schedule. Use the 'ČÁST MĚSTA' (part of "
            "town) column value as the district, e.g. 'Staré Město', 'Lyžbice', "
            "'Nebory' or 'Karpentná'. If your district appears in several rows "
            "with different street lists, also set the street to one street "
            "name from the 'LOKALITA' column."
        ),
    }

    retrieve = retrievers.PdfLinkRetriever(
        index_url=_LANDING_PAGE_URL,
        pattern=r"trinec[^/]*?(20\d\d)[^/]*sko[^/]*bio[^/]*sep[^/]*\.pdf$",
    )
    parse = SmoloSchedule.SmoloScheduleParser()
    preprocess = SmoloSchedule.SmoloScheduleExpander()
    transform = ICSTransformer(
        type_value_map={
            SmoloSchedule.RESIDUAL: wt.GENERAL_WASTE,
            SmoloSchedule.ORGANIC: wt.ORGANIC,
            SmoloSchedule.SORTED: wt.RECYCLABLES,
            SmoloSchedule.SORTED_YELLOW: wt.PLASTIC,
            SmoloSchedule.SORTED_BLUE: wt.PAPER,
        },
    )
