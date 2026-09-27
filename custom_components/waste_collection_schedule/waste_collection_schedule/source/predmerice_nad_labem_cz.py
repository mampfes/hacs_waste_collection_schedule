from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Předměřice nad Labem"
    DESCRIPTION = "Source for Předměřice nad Labem, Czech Republic."
    URL = "https://www.predmericenl.cz/odpady"
    COUNTRY = "cz"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@ArzykDev"]
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Předměřice nad Labem": {},
    }

    PARAMS = ()

    retrieve = HttpGetRetriever(url="https://www.predmericenl.cz/odpady")
    # One table per waste type: its catalogue code and name in the third row
    # ("200301 Směsný komunální odpad"), then every collection date.
    parse = parsers.HtmlLabelledDates(
        "table.svozovy_plan",
        label="tr:nth-of-type(3) > td",
        date=":scope",
        date_pattern=r"\d{2}\.\d{2}\.\d{4}",
        parse_date=date_parsers.for_format("%d.%m.%Y"),
        all_dates=True,
    )
    transform = RowTransformer(
        clean=lambda label: label.split(maxsplit=1)[-1],
        type_value_map={
            "Směsný komunální odpad": wt.GENERAL_WASTE,
            "Plasty": wt.RECYCLABLES,
            "Papír a lepenky": wt.PAPER,
        },
    )
