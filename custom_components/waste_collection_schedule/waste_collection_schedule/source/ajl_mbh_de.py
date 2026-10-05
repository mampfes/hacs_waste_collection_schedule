import re
from datetime import date
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import field_terms, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import RowTransformer

BASE_URL = "https://www.ajl-mbh.de/abfallkalender/entsorgungstermine"


def _argument(value):
    return value if isinstance(value, int) else str(value).strip()


def _streets(root):
    result = {}
    for option in root.select("select#street option"):
        value = option.get("value", "")
        if value and value != "-1" and value.isdigit():
            result[option.get_text(strip=True)] = int(value)
    return result


def _match(options, field, value):
    for label, identifier in options.items():
        if label.casefold() == value.casefold():
            return identifier
    raise SourceArgumentNotFoundWithSuggestions(field, value, list(options))


def _town_id(response, *, town, **_):
    root = BeautifulSoup(response.text, "html.parser")
    towns = {}
    for anchor in root.select("a.stadtbutton"):
        match = re.search(r"town=(\d+)", anchor.get("href", ""))
        name = anchor.get("name", "").strip()
        if match and name:
            towns[name] = int(match[1])
    return _match(towns, "town", town)


def _street_id(response, *_, street, **kwargs):
    return _match(
        _streets(BeautifulSoup(response.text, "html.parser")), "street", street
    )


def _calendar_params(town_id, street_id=None, **_):
    params = {"year": date.today().year, "town": town_id}
    if street_id is not None:
        params["street"] = street_id
    return params


def _events(roots, source):
    root = roots[0]
    heading = root.select_one("h2.ajl-green")
    year_match = re.search(r"\d{4}", heading.get_text()) if heading else None
    year = int(year_match[0]) if year_match else date.today().year
    calendar = root.select_one("div#calenderview")
    if calendar is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", str(source.params.get("street")), list(_streets(root))
        )
    rows = []
    for category in calendar.select("div.cat"):
        inner = category.find("div", class_=re.compile(r"^cat-"))
        heading = inner.find("h3") if inner else None
        if heading is None:
            continue
        for day in inner.select(".dayprint"):
            match = re.search(r"(\d{1,2})\.(\d{2})\.", day.get_text(strip=True))
            if match:
                try:
                    collection_date = date(year, int(match[2]), int(match[1]))
                except ValueError:
                    continue
                rows.append((collection_date, heading.get_text(strip=True)))
    return rows


@final
class Source(BaseSource):
    TITLE = "AJL - Abfallwirtschaftsgesellschaft Jerichower Land mbH"
    DESCRIPTION = (
        "Source for AJL - Abfallwirtschaftsgesellschaft Jerichower Land mbH, Germany."
    )
    URL = "https://www.ajl-mbh.de"
    COUNTRY = "de"
    TEST_CASES: ClassVar[dict] = {
        "Biederitz (no street)": {"town": "Biederitz"},
        "Burg, Fliederweg": {"town": "Burg", "street": "Fliederweg"},
        "Biederitz by ID": {"town": 98},
        "Burg by ID with street ID": {"town": 154, "street": 313},
    }
    RAISE_ON_EMPTY = True

    PARAMS = (
        text_field("town", term=field_terms.MUNICIPALITY, coerce=_argument),
        text_field("street", term=field_terms.STREET, optional=True, coerce=_argument),
    )
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown town": {"town": "__unknown_town__"},
        "Street required": {"town": "Burg"},
    }
    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.PAPER,
        wt.ORGANIC,
        wt.GENERAL_WASTE,
        wt.BULKY_WASTE,
        wt.HAZARDOUS,
        wt.GARDEN_WASTE,
    ]
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                BASE_URL,
                pick=_town_id,
                given=lambda town, **_: town if isinstance(town, int) else None,
            ),
            retrievers.Lookup(
                BASE_URL,
                params=_calendar_params,
                pick=_street_id,
                given=lambda *_, street=None, **kwargs: (
                    street if isinstance(street, int) else None
                ),
                when=lambda *_, street=None, **kwargs: street is not None,
            ),
        ),
        url=BASE_URL,
        params=_calendar_params,
        raise_for_status=True,
    )
    parse = parsers.HtmlParser("html")
    preprocess = staticmethod(_events)
    transform = RowTransformer(
        type_value_map={
            "Gelbe Tonne": wt.RECYCLABLES,
            "Papier": wt.PAPER,
            "Biomüll": wt.ORGANIC,
            "Restmüll": wt.GENERAL_WASTE,
            "Sperrmüll": wt.BULKY_WASTE,
            "Schadstoffmobil": wt.HAZARDOUS,
            "Weihnachtsbaum": wt.GARDEN_WASTE,
        },
        carry_raw_label=True,
    )
