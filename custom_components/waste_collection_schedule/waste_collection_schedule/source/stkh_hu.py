from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.parsers import PdfTextParser
from waste_collection_schedule.preprocessors import TextGroupedDates
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a text-PDF calendar read by parsers.PdfTextParser and fanned out
# by preprocessors.TextGroupedDates. STKH (Sopron és Térsége, Hungary) publishes
# one PDF per municipality whose text layer is a tabular schedule: each waste-type
# row lists full MM.DD. dates per month, and the calendar year is stated once in
# the heading. The parser returns the page text unchanged, TextGroupedDates splits
# it into one segment per waste-type label and pairs every date in that segment
# with the label, and a plain ICSTransformer maps each Hungarian label onto a
# canonical WasteType. Nothing here is source-specific but the labels and the two
# patterns.
#
# The mixed/residual waste (vegyes) is a fixed weekly recurrence stated only in
# prose ("Vegyes hulladékgyűjtési nap: kedd"), not as dated table rows, so it is
# out of scope here; this source covers the two date-bearing rows (selective and
# green waste) that the text layer pairs explicitly with dates.

# Hungarian table row labels, exactly as printed in the PDF text layer.
_TYPE_VALUE_MAP = {
    "szelektív": wt.RECYCLABLES,
    "zöldhulladék": wt.GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "STKH Sopron és Térsége"
    DESCRIPTION = (
        "Waste collection schedule for municipalities served by STKH "
        "(Sopron és Térsége), Hungary, published as a per-municipality PDF."
    )
    URL = "https://www.stkh.hu"
    COUNTRY = "hu"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@markvp"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Újkér 2026": {
            "url": "https://stkh.hu/wp-content/uploads/2025/12/9472_Ujker_Hulladeknaptar2026.pdf"
        },
    }

    PARAMS = (text_field("url", "Calendar PDF URL"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your municipality's waste calendar (hulladéknaptár) PDF on "
            "https://www.stkh.hu (Szolgáltatásaink), then enter the direct PDF "
            "link as the 'Calendar PDF URL' value."
        ),
    }

    retrieve = HttpGetRetriever(url=lambda url: url)
    parse = PdfTextParser(min_chars=200)

    # A full MM.DD. date cell ("01.26."), and the calendar year printed once in
    # the heading ("2026. évi hulladéknaptár").
    preprocess = TextGroupedDates(
        keys=_TYPE_VALUE_MAP,
        date_pattern=r"\b(?P<month>\d{2})\.(?P<day>\d{2})\.",
        year_pattern=r"(\d{4})\.\s*évi",
    )

    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP)
