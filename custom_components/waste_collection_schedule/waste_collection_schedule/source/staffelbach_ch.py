"""Staffelbach (AG), Switzerland (staffelbach.ch).

The municipality publishes its "Entsorgungskalender" as a yearly text PDF
linked from its Entsorgung page: twelve month columns over one sheet (January to
June above, July to December below), each headed by the month name, one row per
day ("13 Di Grüngut"). ``retrievers.yearly_links`` lists every calendar from
this year on, so next year's is read as soon as it is linked, and
``preprocessors.PdfMonthColumns`` bins each row into its month by the headings,
which plain text extraction would interleave.

Besides the kerbside rounds (Kehricht, Grüngut) the calendar marks the opening
days of the fenced Sammelstelle Süd (Wednesday and Saturday); those are not
collections and are not read.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.transformers import ICSTransformer

INDEX_URL = "https://staffelbach.ch/index.php/27/Umwelt_Verkehr_/Entsorgung"

# "/scms/upload/Entsorgungskalender_Staffelbach_2026.pdf"
_PDF_PATTERN = r"Entsorgungskalender[^/]*?(20\d\d)\.pdf$"

_LABELS = ("Kehricht", "Grüngut")


@final
class Source(BaseSource):
    TITLE = "Staffelbach"
    DESCRIPTION = "Source for Staffelbach (AG), Switzerland."
    URL = "https://staffelbach.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {"Staffelbach": {}}

    PARAMS = ()

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.GARDEN_WASTE]

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            INDEX_URL, pick=retrievers.yearly_links(_PDF_PATTERN)
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(
        parsers.PdfTableParser(min_words=300),
        then=preprocessors.PdfMonthColumns(
            labels=_LABELS,
            day_pattern=r"(\d{1,2})\s+[a-z]{2}\b",
            year_pattern=r"Entsorgungskalender\s+(20\d\d)",
        ),
    )
    transform = ICSTransformer(
        type_value_map={
            "Kehricht": wt.GENERAL_WASTE,
            "Grüngut": wt.GARDEN_WASTE,
        },
    )
