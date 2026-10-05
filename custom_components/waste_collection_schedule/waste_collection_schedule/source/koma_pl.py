import urllib.parse
from typing import ClassVar, final

from waste_collection_schedule import config_params, date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://bok.koma.pl/api"

# Every label the portal lists for a property. "Metale i tworzywa sztuczne"
# (metals and plastics) is one mixed round, so it is RECYCLABLES.
_TYPE_MAP = {
    "Zmieszane": wt.GENERAL_WASTE,
    "Bio": wt.ORGANIC,
    "Odpady zielone": wt.GARDEN_WASTE,
    "Papier": wt.PAPER,
    "Szkło": wt.GLASS,
    "Metale i tworzywa sztuczne": wt.RECYCLABLES,
    "Gabaryty": wt.BULKY_WASTE,
    "Elektro": wt.ELECTRONICS,
}


def _properties_url(gmina: str, miejscowosc: str, ulica: str | None = None, **_) -> str:
    # The API's "prefix" path segment equals the gmina name.
    segments = ["posesje", gmina, gmina, miejscowosc]
    if ulica:
        segments.append(ulica)
    return API_URL + "/" + "/".join(urllib.parse.quote(s.strip()) for s in segments)


def _pick_property(response, *keys, miejscowosc, ulica=None, numer_domu, **_) -> str:
    """The lookup answers one entry per building; take the one with this house number."""
    properties = response.json()
    if not properties:
        if ulica:
            raise SourceArgumentNotFound("ulica", ulica)
        raise SourceArgumentNotFound("miejscowosc", miejscowosc)
    wanted = str(numer_domu).strip().casefold()
    for entry in properties:
        if str(entry.get("numer_domu")).strip().casefold() == wanted:
            return entry["numer_posesji"]
    raise SourceArgumentNotFoundWithSuggestions(
        "numer_domu",
        numer_domu,
        sorted({str(entry.get("numer_domu")) for entry in properties}),
    )


@final
class Source(BaseSource):
    TITLE = "KOMA"
    DESCRIPTION = "Source for KOMA waste collection (e.g. Nowy Dwór Gdański, Poland)."
    URL = "https://koma.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.ELECTRONICS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Nowy Dwór Gdański, Kanałowa 5": {
            "gmina": "Nowy Dwór Gdański",
            "miejscowosc": "Nowy Dwór Gdański",
            "ulica": "Kanałowa",
            "numer_domu": "5",
        },
        "Nowy Dwór Gdański, Kanałowa 4/1": {
            "gmina": "Nowy Dwór Gdański",
            "miejscowosc": "Nowy Dwór Gdański",
            "ulica": "Kanałowa",
            "numer_domu": "4/1",
        },
    }

    PARAMS = (
        config_params.municipality(field="gmina"),
        config_params.city(field="miejscowosc"),
        config_params.street(field="ulica", optional=True),
        config_params.house_number(field="numer_domu"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://koma.pl/harmonogram-odpadow/ and step through the "
            "dropdowns (Wybierz Miasto -> miejscowość -> ulica -> numer domu) to "
            "find the exact spelling of your commune (gmina), town, street and "
            "house number. Leave the street empty for towns without streets."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _properties_url,
                pick=_pick_property,
            ),
        ),
        url=f"{API_URL}/apiharmonogram",
        params=lambda key, gmina, **_: {"value": f"{gmina.strip()}/{key}"},
    )

    parse = parsers.JsonParser("odbior")

    transform = JsonTransformer(
        date_key="data",
        type_key="typ",
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        skip_unparseable_dates=True,
    )
