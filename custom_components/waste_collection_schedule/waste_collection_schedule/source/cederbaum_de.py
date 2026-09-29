import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.preprocessors import (
    ArgumentLookup,
    Compose,
    ExplodeList,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

# The page lists every street as a <select> option (value = index) and holds the
# dates of all streets in one inline script, ``var rate = ["d.m.Y,d.m.Y", ...]``,
# one comma list per street index.
_RATE_RE = re.compile(r"var rate = \[(.*?)\];", re.DOTALL)


def _street_dates(html: str, source) -> dict[str, dict]:
    """Map each street name to the list of its collection dates."""
    match = _RATE_RE.search(html)
    if not match:
        return {}
    rates = [text.strip('"') for text in match.group(1).split('","')]
    table: dict[str, dict] = {}
    for option in BeautifulSoup(html, "html.parser").select("select option"):
        value = str(option.get("value"))
        if not value.isdigit() or int(value) >= len(rates):
            continue
        table[option.get_text().strip()] = {"dates": rates[int(value)].split(",")}
    return table


@final
class Source(BaseSource):
    TITLE = "Cederbaum Braunschweig"
    DESCRIPTION = "Cederbaum Braunschweig Paperimüll"
    URL = "https://www.cederbaum.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.PAPER]

    TEST_CASES: ClassVar[dict] = {
        "Hans-Sommer-Str": {"street": "Hans-Sommer-Str."},
        "Adolfstr 31-42": {"street": "Adolfstr. 31-42"},
        "Am Schwarzen Berge": {"street": "am Schwarzen Berge "},
    }

    PARAMS = (street(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street exactly as it is listed on "
            "https://www.cederbaum.de/blaue-tonne/ (e.g. 'Adolfstr. 31-42')."
        ),
        "de": (
            "Gib die Straße genau so ein, wie sie auf "
            "https://www.cederbaum.de/blaue-tonne/ aufgeführt ist "
            "(z. B. 'Adolfstr. 31-42')."
        ),
    }

    retrieve = HttpGetRetriever("https://www.cederbaum.de/blaue-tonne/")
    parse = parsers.TextParser()
    preprocess = Compose(
        ArgumentLookup(_street_dates, argument="street"),
        ExplodeList("dates", into="date"),
    )
    transform = JsonTransformer(
        date_key="date",
        type_key=lambda record: "Paper",
        type_value_map={"Paper": wt.PAPER},
        parse_date=date_parsers.for_format("%d.%m.%Y"),
    )
