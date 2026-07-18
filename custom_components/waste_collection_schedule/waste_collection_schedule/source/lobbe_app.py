"""Lobbe App (lobbe.app).

Demonstrates: a three-level cascade (state -> city -> street, each an AJAX
lookup keyed off the previous id) that then requests an ICS *download URL*
(one more AJAX call) before finally fetching the calendar itself. That's more
hops than ``TwoStepRetriever`` models, so ``retrieve`` is a source-defined
override; it also reproduces the legacy source's December quirk (also fetch
next year's calendar) and its ids-gone-stale retry for that second fetch.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    ELECTRONICS,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://lobbe.app/wp-admin/admin-ajax.php"
_TYPES = {"gelber", "biobfall", "restabfall", "altpapier", "additional_types"}

_PLACES = {
    "Hessen": [
        "Allendorf",
        "Bad Arolsen",
        "Battenberg",
        "Bromskirchen",
        "Burgwald",
        "Diemelsee",
        "Diemelstadt",
        "Edertal",
        "Frankenau",
        "Hatzfeld",
        "Korbach",
        "Lichtenfels",
        "Rosenthal",
        "Twistetal",
        "Vöhl",
        "Willingen",
    ],
    "Nordrhein-Westfalen": [
        "Altena",
        "Altenbeken",
        "Arnsberg",
        "Bad Berleburg",
        "Bad Driburg",
        "Bad Wünnenberg",
        "Balve",
        "Bestwig",
        "Borchen",
        "Borgentreich",
        "Brakel",
        "Breckerfeld",
        "Brilon",
        "Büren",
        "Delbrück",
        "Eslohe",
        "Hallenberg",
        "Halver",
        "Hemer",
        "Iserlohn",
        "Kierspe",
        "Lichtenau",
        "Marienmünster",
        "Marsberg",
        "Medebach",
        "Meinerzhagen",
        "Menden",
        "Meschede",
        "Nachrodt-Wiblingwerde",
        "Olsberg",
        "Plettenberg",
        "Rüthen",
        "Schalksmühle",
        # "Schmallenberg", # Listed but is not the current service provider
        "Steinheim",
        "Sundern",
        "Warburg",
        "Warstein",
        "Werdohl",
        "Willebadessen",
        "Winterberg",
    ],
}


def _make_comparable(s: str) -> str:
    return (
        s.lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("str.", "straße")
        .replace("ß", "ss")
        .replace(".", "")
        .replace(",", "")
    )


def _get_id(
    session, action: str, compare_to: str, param_name: str, params=None
) -> tuple[int, str]:
    params = {"action": action, **(params or {})}
    r = session.get(_API_URL, params=params)
    r.raise_for_status()
    data = r.json()
    original_compare_to = compare_to
    compare_to = _make_comparable(compare_to)
    for d in data:
        if _make_comparable(d["text"]) == compare_to:
            return d["id"], d["text"]

    raise SourceArgumentNotFoundWithSuggestions(
        param_name, original_compare_to, [d["text"] for d in data]
    )


def _resolve_ids(
    session, state: str, city: str, street: str
) -> tuple[int, str, int, str, int, str]:
    state_id, state_name = _get_id(session, "state", state, "state")
    city_id, city_name = _get_id(session, "place", city, "city", {"id": state_id})
    street_id, street_name = _get_id(
        session, "street", street, "street", {"id": city_id}
    )
    return state_id, state_name, city_id, city_name, street_id, street_name


def _fetch_year(session, year: int, ids: tuple[int, str, int, str, int, str]) -> str:
    state_id, state_name, city_id, city_name, street_id, street_name = ids
    params = {
        "year[id]": 1,
        "year[text]": year,
        "state[id]": state_id,
        "state[text]": state_name,
        "place[id]": city_id,
        "place[text]": city_name,
        "street[id]": street_id,
        "street[text]": street_name,
        **dict.fromkeys(_TYPES, 1),
        "hours": 18,
        "minutes": 0,
        "action": "create_ical",
    }
    r = session.get(_API_URL, params=params)
    r.raise_for_status()
    ics_url = r.json()["url"]

    r = session.get(ics_url)
    r.raise_for_status()
    return r.text


def _extra_info():
    return [
        region(city, state=state, city=city)
        for state, cities in _PLACES.items()
        for city in cities
    ]


@final
class Source(BaseSource):
    TITLE = "Lobbe App"
    DESCRIPTION = "Source for Lobbe App."
    URL = "https://lobbe.app/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Hessen Diemelsee Am Breuschelt": {
            "state": "Hessen",
            "city": "Diemelsee",
            "street": "Am Breuschelt",
        },
        "Nordrhein-Westfalen Meschede Alte Henne": {
            "state": "Nordrhein-Westfalen",
            "city": "Meschede",
            "street": "Alte Henne",
        },
        "Nordrhein-Westfalen Willebadessen Ächternstraße": {
            "state": "Nordrhein-Westfalen",
            "city": "Willebadessen",
            "street": "Ächternstraße",
        },
    }

    PARAMS = (
        text_field("state", label="State"),
        text_field("city", label="City"),
        text_field("street", label="Street"),
    )

    REGIONS = _extra_info

    RAISE_ON_EMPTY = True

    def retrieve(self, source):
        state = source.params["state"]
        city = source.params["city"]
        street = source.params["street"]
        ids = _resolve_ids(source.session, state, city, street)

        now = datetime.now()
        texts = [_fetch_year(source.session, now.year, ids)]
        if now.month != 12:
            return texts

        try:
            texts.append(_fetch_year(source.session, now.year + 1, ids))
        except Exception:
            try:
                ids = _resolve_ids(source.session, state, city, street)
                texts.append(_fetch_year(source.session, now.year + 1, ids))
            except Exception:
                pass
        return texts

    def parse(self, response, source=None):
        entries = []
        for text in response:
            entries.extend(ICS().convert(text))
        return entries

    transform = ICSTransformer(
        type_value_map={
            "Restabfall": GENERAL_WASTE,
            "Bioabfall": ORGANIC,
            "Altpapier": PAPER,
            "Gelber Sack / Wertstofftonne": RECYCLABLES,
            "Elektroschrott": ELECTRONICS,
        }
    )

    def __init__(self, state: str, city: str, street: str):
        super().__init__(state=state, city=city, street=street)
