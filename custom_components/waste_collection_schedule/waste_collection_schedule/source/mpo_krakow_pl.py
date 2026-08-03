"""MPO Kraków, Poland.

Composes: :class:`~waste_collection_schedule.service.KiedyWywoz.SchedulePdfRetriever`
(the city's schedule is served by the kiedywywoz.pl platform, whose street and
building index is walked with the city's own token) and
:class:`~waste_collection_schedule.preprocessors.TextDatedBlocks` (the PDF is a
diary: a weekday, the date, then the rounds collected that day, one per line).
``ICSTransformer`` maps the Polish labels onto canonical WasteTypes.
"""

from typing import ClassVar, final

from waste_collection_schedule import config_params
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import PdfTextParser
from waste_collection_schedule.preprocessors import TextDatedBlocks
from waste_collection_schedule.service.KiedyWywoz import SchedulePdfRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_TOKEN = "OkkxhC6b9etJBAq7WTHJ0LhIglO18sip"

# One dated block: "<weekday>\n<day> <month>" then its stacked round names, up
# to the next such heading or the end of the document.
_BLOCK_PATTERN = (
    r"\w+\n(?P<day>\d+)\s(?P<month>\w+)\n"
    r"(?P<labels>[\w\s\-]+?)(?=\n\w+\n\d+\s\w+|$)"
)

# The PDF's only statement of which year it covers.
_YEAR_PATTERN = r"Data generowania:\s(\d{4})-\d{2}-\d{2}"


@final
class Source(BaseSource):
    TITLE = "MPO Kraków"
    DESCRIPTION = "Source script for MPO Kraków"
    URL = "https://harmonogram.mpo.krakow.pl/"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Romanowicza 1 DM": {"street_name": "Romanowicza", "building_number": "1 DM"},
        "Na Wrzosach 43 DJ": {"street_name": "Na Wrzosach", "building_number": "43 DJ"},
        "Świtezianki 7 DB": {"street_name": "Świtezianki", "building_number": "7 DB"},
        "Przewóz 40d DW": {"street_name": "Przewóz", "building_number": "40d DW"},
    }

    PARAMS = (
        config_params.street(field="street_name"),
        config_params.house_number(field="building_number"),
    )

    retrieve = SchedulePdfRetriever(token=_TOKEN)
    parse = PdfTextParser(min_chars=100)

    # A round the shared vocabulary does not know keeps its printed text, so the
    # labels are folded to sentence case for a tidy sensor name.
    preprocess = TextDatedBlocks(
        block_pattern=_BLOCK_PATTERN,
        year_pattern=_YEAR_PATTERN,
        normalise=str.capitalize,
    )

    transform = ICSTransformer(
        type_value_map={
            "Zmieszane": GENERAL_WASTE,
            "Szkło": GLASS,
            "Papier": PAPER,
            "Tworzywa sztuczne": RECYCLABLES,
            "Bio": ORGANIC,
            "Zielone": GARDEN_WASTE,
            "Choinki": GARDEN_WASTE,
        }
    )

    def __init__(self, street_name: str, building_number: str) -> None:
        super().__init__(
            street_name=street_name.strip().title(),
            building_number=building_number.strip().upper(),
        )
