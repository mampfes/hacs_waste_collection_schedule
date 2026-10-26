from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import field_terms as ft
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id, text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)
from waste_collection_schedule.transformers import RowTransformer


def _query(id=None, uprn=None, **_):
    if id is None or str(id).strip() == "":
        if uprn is not None:
            raise SourceArgumentNotFound(
                "uprn",
                uprn,
                "the former Bryson UPRN lookup has been retired. Select your property at https://antrimandnewtownabbey.gov.uk/binchecker/ and configure the Id from its URL as id; the council checker includes recycling.",
            )
        raise SourceArgumentRequired(
            "id",
            "select your property in the council bin checker and use the Id from its URL",
        )
    return {"Id": str(id).strip(), "size": 20}


def _rows(element, source):
    date = element.select_one("p.date")
    if date is None:
        raise ValueError("A council collection record has no printed date")
    return [
        (date.get_text(strip=True), item.get_text(strip=True))
        for item in element.select("li")
        if item.get_text(strip=True)
    ]


@final
class Source(BaseSource):
    TITLE = "Antrim and Newtownabbey"
    DESCRIPTION = "Dated refuse, brown-bin and recycling collections from the council bin checker."
    URL = "https://antrimandnewtownabbey.gov.uk"
    COUNTRY = "uk"
    TEST_CASES: ClassVar[dict] = {
        "uprn + id": {"id": 1456, "uprn": 185354344},
        "id_str": {"id": "1145"},
        "Recycling on a separate weekday": {"id": 58105},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Former UPRN-only lookup": {"uprn": "185405500"},
        "Missing property ID": {},
    }
    PARAMS = (
        location_id("id", optional=True),
        text_field("uprn", term=ft.UPRN, optional=True),
    )
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]
    RAISE_ON_EMPTY = True
    HOWTO: ClassVar[dict] = {
        "en": "Search your address at https://antrimandnewtownabbey.gov.uk/binchecker/ and copy the Id from the selected property's URL into id. The council now publishes dated recycling collections alongside refuse and brown-bin collections. UPRN-only configurations must be updated to this council ID because the old Bryson lookup has been retired; with id configured, the old uprn argument is unnecessary. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.Request(
        "https://antrimandnewtownabbey.gov.uk/binchecker/", params=_query
    )
    parse = parsers.HtmlParser("div.feature-box.bins", require=["div.feature-box.bins"])
    preprocess = preprocessors.ExplodeList(_rows)
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%a %d %b, %Y"),
        type_value_map={
            "Black bins": wt.GENERAL_WASTE,
            "Brown bins": wt.ORGANIC,
            "Wheelie boxes": wt.RECYCLABLES,
            "Kerbside Recycling": wt.RECYCLABLES,
        },
    )
