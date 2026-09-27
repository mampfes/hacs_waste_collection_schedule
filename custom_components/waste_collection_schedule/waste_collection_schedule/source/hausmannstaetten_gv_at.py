from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer


def _text(article, selector: str) -> "str | None":
    found = article.select_one(selector)
    return found.get_text(strip=True) if found is not None else None


def _title(article) -> str:
    # A missing link raises, which HtmlTransformer turns into a skipped row.
    link = article.select_one("a[title]")
    if link is None:
        raise AttributeError("no titled link")
    return str(link["title"])


@final
class Source(BaseSource):
    TITLE = "Hausmannstätten"
    DESCRIPTION = "Source for Hausmannstätten."
    URL = "https://www.hausmannstaetten.gv.at"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    # The district rounds of one stream can fall on the same day.
    IGNORE_DUPLICATES_DEFAULT = True
    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.BULKY_WASTE,
        wt.HAZARDOUS,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Testcase": {},
    }

    PARAMS = ()

    retrieve = HttpGetRetriever(url="https://hausmannstaetten.gv.at/terminkalender")
    # The municipal events calendar's environment tab: one article per
    # collection, its type in the link title, a date and sometimes a time.
    parse = parsers.HtmlParser("#content-tab-umweltkalender div.article")
    transform = HtmlTransformer(
        date_getter=lambda article: _text(article, "span.date"),
        type_getter=_title,
        description_getter=lambda article: _text(article, "span.time"),
        parse_date=date_parsers.for_format("%d.%m.%Y"),
        type_value_map={
            # The municipality's two collection districts (I and II) run their
            # own rounds of the same stream.
            "Bioabfall": wt.ORGANIC,
            "Bioabfall + Reinigung": wt.ORGANIC,
            "Restmüll 1": wt.GENERAL_WASTE,
            "Restmüll I": wt.GENERAL_WASTE,
            "Restmüll II": wt.GENERAL_WASTE,
            "Leicht- und Metallverpackung": wt.RECYCLABLES,
            "Altpapier I": wt.PAPER,
            "Altpapier II": wt.PAPER,
            "Sperrmüll ASZ-Fernitz (Mi)": wt.BULKY_WASTE,
            "Sperrmüll ASZ-Fernitz (Fr)": wt.BULKY_WASTE,
            "Sperrmüll ASZ-Fernitz (Sa)": wt.BULKY_WASTE,
            "Problemstoffsammlung": wt.HAZARDOUS,
        },
        carry_raw_label=True,
    )
