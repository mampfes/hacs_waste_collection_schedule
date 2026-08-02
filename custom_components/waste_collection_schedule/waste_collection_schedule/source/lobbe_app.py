"""Lobbe App (lobbe.app).

Demonstrates: a four-step ``IcsSessionRetriever`` chain. A three-level cascade
(state -> city -> street, each an AJAX lookup keyed off the previous id) is
followed by one more AJAX call that mints the ICS *download URL*, which the
retriever's feed request then fetches. The chain runs once per calendar year
the schedule can span, so the legacy source's December quirk (also fetch next
year) and its ids-gone-stale retry both come from the retriever: next year is
best-effort, and it re-resolves the ids rather than reusing this year's.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
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


def _pick_id(level: str, argument: str):
    """An ``extract`` matching the user's value against one AJAX dropdown.

    The site answers each lookup with ``[{"id": ..., "text": ...}, ...]``; the
    id and the site's own spelling of the name are both bound into the chain's
    context, because the calendar request wants the pair.
    """

    def extract(response, context) -> dict:
        options = response.json()
        wanted = _make_comparable(context[argument])
        for option in options:
            if _make_comparable(option["text"]) == wanted:
                return {f"{level}_id": option["id"], f"{level}_text": option["text"]}
        raise SourceArgumentNotFoundWithSuggestions(
            argument, context[argument], [option["text"] for option in options]
        )

    return extract


def _ical_request(
    state_id,
    state_text,
    place_id,
    place_text,
    street_id,
    street_text,
    year,
    **_,
) -> dict:
    """Query minting one year's ICS download URL for the resolved address."""
    return {
        "year[id]": 1,
        "year[text]": year,
        "state[id]": state_id,
        "state[text]": state_text,
        "place[id]": place_id,
        "place[text]": place_text,
        "street[id]": street_id,
        "street[text]": street_text,
        **dict.fromkeys(_TYPES, 1),
        "hours": 18,
        "minutes": 0,
        "action": "create_ical",
    }


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

    retrieve = IcsSessionRetriever(
        steps=[
            {
                "url": _API_URL,
                "params": {"action": "state"},
                "extract": _pick_id("state", "state"),
            },
            {
                "url": _API_URL,
                "params": lambda state_id, **_: {"action": "place", "id": state_id},
                "extract": _pick_id("place", "city"),
            },
            {
                "url": _API_URL,
                "params": lambda place_id, **_: {"action": "street", "id": place_id},
                "extract": _pick_id("street", "street"),
            },
            {
                "url": _API_URL,
                "params": _ical_request,
                "extract": lambda response, _: {"ics_url": response.json()["url"]},
            },
        ],
        feed_url=lambda ics_url, **_: ics_url,
    )

    parse = IcsFeedsParser(parsers.IcsParser())

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
