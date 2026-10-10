from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer

# The Abfuhrkalender page (about 1.7 MB) carries the whole district's calendar
# as inline script tables:
#   tblStrassen        streets: StrassenId, Strasse, Gemeinde (the village)
#   tblStrassenGruppen street -> collection group (GruppenId, StrassenId)
#   tblTermine         dates: Datum (YYYY-MM-DD), GruppenId, Muellart
#   tblMuellarten      waste types: MuellId -> Art
# The street is matched by name, narrowed by the village when given; a street
# found in several villages needs the village.

API_URL = "https://www.awb-bir.de/Service/(0)Abfuhrkalender/"

_TABLES = ("tblStrassen", "tblStrassenGruppen", "tblTermine", "tblMuellarten")


def _key(value) -> str:
    return str(value or "").strip().lower()


def _rows(tables, source):
    street_name = source.params["street"] if source else ""
    city_name = source.params.get("city") if source else None
    streets = tables["tblStrassen"]

    matches = [s for s in streets if _key(s["Strasse"]) == _key(street_name)]
    if not matches:
        # Suggest the village's streets; all streets when no (known) village.
        in_city = [s for s in streets if _key(s["Gemeinde"]) == _key(city_name)]
        raise SourceArgumentNotFoundWithSuggestions(
            "street",
            street_name,
            sorted(
                {s["Strasse"] for s in (in_city if city_name and in_city else streets)}
            ),
        )
    if city_name:
        in_city = [s for s in matches if _key(s["Gemeinde"]) == _key(city_name)]
        if not in_city:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", city_name, sorted({s["Gemeinde"] for s in matches})
            )
        matches = in_city
    cities = sorted({s["Gemeinde"] for s in matches})
    if len(cities) > 1:
        raise SourceArgAmbiguousWithSuggestions("city", city_name, cities)

    street_ids = {s["StrassenId"] for s in matches}
    group_ids = {
        g["GruppenId"]
        for g in tables["tblStrassenGruppen"]
        if g["StrassenId"] in street_ids
    }
    names = {w["MuellId"]: w["Art"] for w in tables["tblMuellarten"]}
    for termin in tables["tblTermine"]:
        name = names.get(termin["Muellart"])
        if termin["GruppenId"] in group_ids and name:
            yield termin["Datum"], name


@final
class Source(BaseSource):
    TITLE = "AWB Birkenfeld"
    DESCRIPTION = "Source for AWB Birkenfeld (Abfallwirtschaftsbetrieb Landkreis Birkenfeld), Germany"
    URL = "https://www.awb-bir.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.HAZARDOUS,
    ]

    # Every case records the whole 1.7 MB calendar page, so only one case is
    # active, the one passing both street and village. The others were checked
    # live during the pipeline migration and stay here for manual runs.
    TEST_CASES: ClassVar[dict] = {
        "Reichenbach, Auf dem Schoß": {
            "street": "Auf dem Schoß",
            "city": "Reichenbach",
        },
        # "Hahnweiler, Falkenweg": {"street": "Falkenweg", "city": "Hahnweiler"},
        # "Horbruch, Im Kätz": {"street": "Im Kätz", "city": "Horbruch"},
        # "unique street without city": {"street": "Auf dem Schoß"},
    }

    PARAMS = (street(), city(optional=True))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit the AWB Birkenfeld waste calendar page "
            "<https://www.awb-bir.de/Service/(0)Abfuhrkalender/> and search for "
            "your street. Use the exact street name (and, if it occurs in more "
            "than one village, the Ortsgemeinde) as shown in the search results."
        ),
        "de": (
            "Besuchen Sie die Abfuhrkalender-Seite der AWB Birkenfeld "
            "<https://www.awb-bir.de/Service/(0)Abfuhrkalender/> und suchen Sie "
            "nach Ihrer Straße. Verwenden Sie den Straßennamen (und, falls dieser "
            "in mehreren Gemeinden vorkommt, die Ortsgemeinde) genau wie in den "
            "Suchergebnissen angezeigt."
        ),
    }

    retrieve = HttpGetRetriever(url=API_URL)
    parse = parsers.JsVarParser(*_TABLES)
    preprocess = staticmethod(_rows)
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Restabfall": wt.GENERAL_WASTE,
            "Altpapier": wt.PAPER,
            "Gelber Sack": wt.RECYCLABLES,
            "Problemabfälle": wt.HAZARDOUS,
        },
    )
