from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


def _round(label: str) -> str:
    """The round a container belongs to. Stoke names each container ("EMPTY
    BINS MIXED REC 55 BOX", "REC 240 STD"); the round is the code in it."""
    upper = label.upper()
    for code in ("RES", "REC", "ORG"):
        if code in upper:
            return code
    return label


@final
class Source(BaseSource):
    TITLE = "Stoke-on-Trent"
    DESCRIPTION = "Source for Stoke-on-Trent"
    URL = "https://www.stoke.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test1": {"uprn": "3455011383"},
        "Test2": {"uprn": 3455011391},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=(
            "https://www.stoke.gov.uk/jadu/custom/webserviceLookUps/"
            "BarTecWebServices_missed_bin_calendar.php"
        ),
        # The council's UPRNs are twelve digits, zero-padded.
        params=lambda uprn, **_: {"UPRN": str(uprn).zfill(12)},
    )
    parse = parsers.XmlParser(".//BinRound")
    transform = JsonTransformer(
        date_key=lambda round_: (round_.findtext("DateTime") or "")[:10],
        type_key=lambda round_: round_.findtext("Bin") or "",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        clean=_round,
        type_value_map={
            "RES": wt.GENERAL_WASTE,
            "REC": wt.RECYCLABLES,
            "ORG": wt.ORGANIC,
        },
    )
