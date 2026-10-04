import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, municipality
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import RowTransformer

API_URL = "https://www.gojer.at/service/abfuhrkalender.html"
CITY_URL = "https://www.gojer.at/ortausgemeinde.html"

# The calendar form's checkboxes; the page only lists the selected services.
_SERVICES = {
    "bio": "Bioabfall",
    "haus": "Hausmüll",
    "plastik": "Plastikflaschen",
    "papier": "Altpapier",
    "altstoff": "Altstoffsammelzentrum",
}


def _same(a: str, b: str) -> bool:
    for char in (" ", ",", ".", "_", "-"):
        a = a.replace(char, "")
        b = b.replace(char, "")
    return a.lower() == b.lower()


def _municipality_value(response, *_, municipality, **__) -> str:
    """The select's option value for the municipality, given as value or text."""
    select = BeautifulSoup(response.text, "html.parser").select_one(
        "select#gemeindewahl"
    )
    options = {
        option["value"]: option.get_text(strip=True)
        for option in (select.select("option") if select else [])
        if option.get("value") not in (None, "", "base")
    }
    for value, text in options.items():
        if _same(value, str(municipality)) or _same(text, str(municipality)):
            return value
    raise SourceArgumentNotFoundWithSuggestions(
        "municipality", municipality, list(options.values())
    )


def _city_name(response, *_, city, **__) -> str:
    """The town's name as the provider spells it."""
    names = [
        option.get_text(strip=True)
        for option in BeautifulSoup(response.text, "html.parser").select("option")
    ]
    for name in names:
        if _same(name, str(city)):
            return name
    raise SourceArgumentNotFoundWithSuggestions("city", city, names)


def _rows(rows, source) -> list[tuple[str, str]]:
    """``(date, label)``; a row without a date continues the previous row's date."""
    result = []
    current = ""
    for row in rows:
        cells = row.select("td")
        if len(cells) < 2:
            continue
        found = re.search(r"\d{2}\.\d{2}\.\d{2}", cells[0].get_text())
        if found:
            current = found[0]
        if not current:
            continue
        for span in cells[1].select("span"):
            span.decompose()
        result.append((current, cells[1].get_text(strip=True)))
    return result


@final
class Source(BaseSource):
    TITLE = "GOJER"
    DESCRIPTION = "Source for GOJER."
    URL = "https://www.gojer.at/"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Ruden Kleindiex": {"municipality": "Ruden", "city": "Kleindiex"},
        "Frantschach-St. Gertraud": {
            "municipality": "Frantschach-St. Gertraud",
            "city": "Trum-und Prössinggraben",
        },
        "St. Kanzian am Klopeiner See, Vesielach": {
            "municipality": "St. Kanzian am Klopeiner See",
            "city": "Vesielach",
        },
    }

    PARAMS = (municipality(), city())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your municipality and town on "
            "https://www.gojer.at/service/abfuhrkalender.html and enter both "
            "names as shown there."
        ),
        "de": (
            "Wähle Gemeinde und Ort auf "
            "https://www.gojer.at/service/abfuhrkalender.html und trage beide "
            "Namen so ein, wie sie dort angezeigt werden."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(API_URL, pick=_municipality_value),
            retrievers.Lookup(
                CITY_URL,
                params=lambda municipality_value, **_: {"choice": municipality_value},
                pick=_city_name,
            ),
        ),
        url=API_URL,
        params=lambda municipality_value, city_name, **_: {
            "gemeindewahl": municipality_value,
            "ortswahl": city_name,
            **_SERVICES,
        },
        raise_for_status=True,
    )
    parse = parsers.HtmlParser("tr.mitBorder, tr.ohneBorder")
    preprocess = staticmethod(_rows)
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d.%m.%y"),
        type_value_map={
            "Bioabfall": wt.ORGANIC,
            "Hausmüll": wt.GENERAL_WASTE,
            "Altpapier": wt.PAPER,
            "Leicht- und Metallverpackungen": wt.RECYCLABLES,
            "Altstoffsammelzentrum": wt.OTHER,
        },
        carry_raw_label=True,
    )
