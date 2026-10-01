import datetime
import json
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, municipality, text_field
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.preprocessors import Compose, Deduplicate
from waste_collection_schedule.retrievers import Request
from waste_collection_schedule.transformers import JsonTransformer

_PARSE_BASE = "https://montecospa.it:1337/parse"

# The keys the Monteco website's own calendar page sends to its Parse Server
# backend.
_HEADERS = {
    "X-Parse-Application-Id": "0XUzreSqwbRPAVPzD1aFYLSLGSVafhnVwt2dkwi4",
    "X-Parse-Javascript-Key": "99ffdklUBn0m2azYI44f8ySFPeSGk2FqcvVlE1bC",
    "X-Parse-Master-Key": "99ffdklUBn0m2azYI44f8ySFPeSGk2FqcvVlE1Rq",
}

_TYPE_MAP = {
    "Carta": wt.PAPER,
    "Imballaggi in cartone": wt.PAPER,
    "Frazione organica": wt.ORGANIC,
    "Frazione organica ecomobile": wt.ORGANIC,
    "Plastica": wt.RECYCLABLES,
    "Vetro e metalli": wt.GLASS,
    "Vetro e metalli ecomobile": wt.GLASS,
    "Secco Residuo non riciclabile": wt.GENERAL_WASTE,
    "Rifiuti Ingombranti e RAEE": wt.BULKY_WASTE,
    "Sfalci e potature": wt.GARDEN_WASTE,
    "Abiti usati": wt.TEXTILES,
}


def _where(municipality, zone, user_type, **_) -> dict:
    """The Parse query for this zone's services of this year and the next."""
    year = datetime.date.today().year
    where = {
        "serviceOnline": "1",
        "language": "it",
        "municipality": municipality,
        "serviceZoneName": zone,
        "serviceUserClass": user_type,
        "validityYear": {"$in": [year, year + 1]},
    }
    return {"where": json.dumps(where), "limit": 200}


def _days(records, source):
    """One row per marked day of each service's calendar.

    A record without a waste type is an informational note (put-out times), not
    a collection; a calendar day is a collection when its value is ``"x"``.
    """
    for record in records:
        waste_type = record.get("serviceWasteType")
        if not isinstance(waste_type, dict):
            continue
        name = waste_type.get("name") or "Unknown"
        for day in record.get("serviceCalendar") or []:
            if day.get("value") == "x" and day.get("date"):
                yield {"date": day["date"], "type": name}


@final
class Source(BaseSource):
    TITLE = "Monteco Spa"
    DESCRIPTION = "Source for Monteco Spa waste collection (Puglia, Italy)."
    URL = "https://www.montecospa.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Lecce - zona centro storico (Domestica)": {
            "municipality": "Lecce",
            "zone": "zona_centro_storico",
        },
        "Lecce - zona_a (Non domestica)": {
            "municipality": "Lecce",
            "zone": "zona_a",
            "user_type": "Non domestica",
        },
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.TEXTILES,
    ]

    PARAMS = (
        municipality("municipality"),
        text_field("zone", "Zone"),
        dropdown(
            "user_type",
            ["Domestica", "Non domestica"],
            label="User type",
            default="Domestica",
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.montecospa.it/it/servizi-evoluti?cta=calendario , "
            "click your address on the map, and note the municipality (exactly "
            "as listed on the Monteco website, e.g. 'Lecce') and the zone shown "
            "in the results panel (e.g. 'zona_centro_storico'). The user type "
            "is 'Domestica' (default) or 'Non domestica'."
        ),
        "it": (
            "Visita https://www.montecospa.it/it/servizi-evoluti?cta=calendario , "
            "clicca sul tuo indirizzo sulla mappa e annota il comune (esattamente "
            "come indicato sul sito Monteco, es. 'Lecce') e la zona mostrata nel "
            "pannello dei risultati (es. 'zona_centro_storico'). Il tipo utenza "
            "è 'Domestica' (predefinito) oppure 'Non domestica'."
        ),
    }

    retrieve = Request(
        f"{_PARSE_BASE}/classes/CityService",
        params=_where,
        headers=_HEADERS,
    )
    parse = JsonParser("results")
    preprocess = Compose(_days, Deduplicate(key=lambda row: (row["date"], row["type"])))
    transform = JsonTransformer(
        date_key="date", type_key="type", type_value_map=_TYPE_MAP
    )
