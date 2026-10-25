"""Waste collection schedules for Gmina Żukowo (ELWOZ ECO), Poland.

Household calendars are sector PDFs linked from
https://elwozeco.pl/harmonogram/ . Each page is one group of villages; the
collection type is the colour of the day cell.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.service import ElwozEco as elwoz
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://elwozeco.pl/harmonogram/"


@final
class Source(BaseSource):
    TITLE = "Gmina Żukowo (ELWOZ ECO)"
    DESCRIPTION = "Source for Gmina Żukowo (ELWOZ ECO) waste collection."
    URL = "https://elwozeco.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.PAPER,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Skrzeszewo": {"district": "Skrzeszewo"},
    }

    PARAMS = (district("district"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "ELWOZ ECO publishes the Gmina Żukowo household calendars at "
            "https://elwozeco.pl/harmonogram/ (one PDF per sector). Enter the "
            "village name as printed, for example Skrzeszewo. In Żukowo and "
            "Banino the calendar is split by street: enter the street as "
            "printed, including the house-number range when the PDF shows one "
            "(each range is its own round). Żukowo on its own matches the "
            "numbered Żukowo zones and the multifamily (WIELORODZINNE) round, "
            "so the error lists those headings. The same happens for a name "
            "printed on more than one page, such as Barniewice or Dąbrowa. "
            "Przyjaźń on its own is the village calendar; multifamily "
            "buildings in Przyjaźń, Babi Dół and Żukowo use WIELORODZINNE. "
            "Business (Firmy) calendars are not included."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_INDEX_URL, pick=elwoz.residential_pdfs("Żukowo")),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url, timeout=120),
    )
    parse = parsers.EachResponse(
        parsers.PdfWordLayoutParser(min_words=1000, min_vectors=200),
        then=elwoz.PageRecords(),
    )
    preprocess = elwoz.ForDistrict("district")
    transform = ICSTransformer(
        type_value_map={
            elwoz.MIXED: wt.GENERAL_WASTE,
            elwoz.RECYCLING: wt.RECYCLABLES,
            elwoz.GLASS: wt.GLASS,
            elwoz.PAPER: wt.PAPER,
            elwoz.BIO: wt.ORGANIC,
        }
    )
