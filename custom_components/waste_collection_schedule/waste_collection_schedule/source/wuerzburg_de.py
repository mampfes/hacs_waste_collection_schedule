from datetime import date, timedelta
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://www.wuerzburg.de/themen/umwelt-klima/vorsorge-entsorgung/abfallkalender/32208.Abfallkalender.html"


def _district_id(response, district=None, street=None, **_):
    if not district and not street:
        raise SourceArgumentRequired("district", "Provide district or street")
    soup = BeautifulSoup(response.text, "html.parser")
    field, value, select = (
        ("street", street, "strlist") if street else ("district", district, "reglist")
    )
    options = soup.select(f"select#{select} option[value]")
    choices = {o.get_text(strip=True): str(o["value"]) for o in options}
    if not choices:
        raise ValueError(f"Würzburg {field} selector is missing")
    if value not in choices:
        raise SourceArgumentNotFoundWithSuggestions(field, value, list(choices))
    return choices[value]


@final
class Source(BaseSource):
    TITLE = "Abfallkalender Würzburg (deprecated)"
    DESCRIPTION = "Deprecated: Use the ICS source instead. Source for waste collection in the city of Würzburg, Germany."
    URL = "https://www.wuerzburg.de"
    TEST_CASES: ClassVar[dict] = {
        "District only": {"district": "Altstadt"},
        "Street only": {"street": "Juliuspromenade"},
        "District + Street": {"district": "Altstadt", "street": "Juliuspromenade"},
        "District + Street diff": {"district": "Altstadt", "street": "Oberer Burgweg"},
    }
    COUNTRY = "de"
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {"street": "zzzznotreal"},
        "Missing location": {},
    }
    PARAMS = (district(optional=True), street(optional=True))
    HOWTO: ClassVar[dict] = {
        "en": "This source remains deprecated; the generic ICS configuration is recommended. Enter district or street exactly as listed on the city calendar. Street takes precedence if both are set. The published event API supplies actual dates and collection pictures. Types now use canonical, localised names; update filters and customisations using old labels."
    }
    retrieve = retrievers.Request(
        _API,
        before=(retrievers.Lookup(_API, pick=_district_id),),
        params=lambda district_id, **_: {
            "_func": "evList",
            "_mod": "events",
            "ev[start]": str(date.today()),
            "ev[end]": str(date.today() + timedelta(days=365)),
            "ev[addr]": district_id,
        },
    )
    parse = parsers.JsonParser("contents")
    preprocess = preprocessors.Compose(
        preprocessors.LogOnce(
            "wuerzburg_de is deprecated; use the Würzburg ICS configuration instead",
            logger=__name__,
        ),
        preprocessors.FlattenGroups(),
    )
    transform = JsonTransformer(
        type_value_map={
            "Bioabfall": wt.ORGANIC,
            "Christbaumabfuhr": wt.GARDEN_WASTE,
            "Gelber Sack": wt.RECYCLABLES,
            "Papier": wt.PAPER,
            "Restmüll": wt.GENERAL_WASTE,
            "Mobile Problemmüll- und Wertstoffsammlung": wt.HAZARDOUS,
            "Problemmüll- und Wertstoffsammlung": wt.HAZARDOUS,
        },
        carry_raw_label=True,
        date_key="start",
        type_key="title",
        parse_date=date_parsers.auto,
        picture_key=lambda event: event.get("thumb", {}).get("url"),
    )
