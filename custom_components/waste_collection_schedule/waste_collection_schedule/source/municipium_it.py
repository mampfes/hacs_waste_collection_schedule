import datetime
from difflib import get_close_matches
from typing import ClassVar, final

from waste_collection_schedule import field_terms, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

# Central directory of every municipality on the platform.
CLOUD_URL = "https://cloud.municipiumapp.it"
# The platform WAF rejects the default python-requests User-Agent.
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (waste_collection_schedule)",
}


def _municipality_id(response, *, municipality, **_):
    comuni = response.json()
    wanted = municipality.strip().casefold()
    matches = [
        c
        for c in comuni
        if c["name"].casefold() == wanted
        or f"{c['name']} ({c.get('province_initials')})".casefold() == wanted
    ]
    if not matches:
        names = [c["name"] for c in comuni]
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality",
            municipality,
            get_close_matches(municipality, names, n=5, cutoff=0.4),
        )
    if len(matches) > 1:
        # Same comune name in several provinces: disambiguate by province.
        raise SourceArgAmbiguousWithSuggestions(
            "municipality",
            municipality,
            [f"{c['name']} ({c.get('province_initials')})" for c in matches],
        )
    return matches[0]["id"]


def _subdomain(response, *_, municipality, **__):
    details = response.json()
    subdomain = details.get("subdomain")
    if not subdomain or not details.get("enable_garbage_calendar"):
        raise SourceArgumentNotFoundWithSuggestions("municipality", municipality, [])
    return subdomain


def _calendar_id(response, *_, area=None, **__):
    calendars = response.json()
    if not calendars:
        raise SourceArgumentNotFoundWithSuggestions("area", area, [])
    names = [c["name"] for c in calendars]
    area = None if area is None or str(area).strip() == "" else area

    # Explicit calendar id.
    if isinstance(area, int) or (isinstance(area, str) and area.strip().isdigit()):
        wanted_id = int(area)
        found = next((c for c in calendars if c["id"] == wanted_id), None)
        if found is None:
            # Suggest the zone names: they are valid `area` inputs.
            raise SourceArgumentNotFoundWithSuggestions("area", area, names)
        return found["id"]

    if area is None:
        if len(calendars) == 1:
            return calendars[0]["id"]
        raise SourceArgumentRequiredWithSuggestions(
            "area", "this municipality has more than one collection zone", names
        )

    wanted = area.strip().casefold()
    # Exact match, then unambiguous substring, then fuzzy suggestions.
    found = next((c for c in calendars if c["name"].casefold() == wanted), None)
    if found is None:
        subs = [c for c in calendars if wanted in c["name"].casefold()]
        if len(subs) == 1:
            found = subs[0]
        elif len(subs) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "area", area, [c["name"] for c in subs]
            )
    if found is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "area", area, get_close_matches(str(area), names, n=5, cutoff=0.3) or names
        )
    return found["id"]


def _epoch(days: int) -> int:
    day = datetime.date.today() + datetime.timedelta(days=days)
    # UTC midnight, so the window does not depend on the host's timezone.
    return int(
        datetime.datetime.combine(day, datetime.time(), tzinfo=datetime.UTC).timestamp()
    )


def _window(*_, **__):
    # The calendar endpoint filters events by a [start, end] epoch-second window.
    return {"start": _epoch(-30), "end": _epoch(365)}


def _title(event):
    return (event.get("category") or {}).get("name") or event.get("title") or ""


@final
class Source(BaseSource):
    TITLE = "Municipium"
    DESCRIPTION = (
        "Source for the Municipium app (Maggioli S.p.A.), used by many Italian "
        "municipalities to publish their door-to-door waste collection calendar."
    )
    URL = "https://www.municipiumapp.it"
    COUNTRY = "it"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@fedfus"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.GENERAL_WASTE,
        wt.PLASTIC,
        wt.METAL,
        wt.GLASS,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Serrastretta (CZ) - Zona 2 Migliuso": {
            "municipality": "Serrastretta",
            "area": "Zona 2",
        },
        "Serrastretta (CZ) - by calendar id": {
            "municipality": "Serrastretta",
            "area": 10325,
        },
        "Acate (RG)": {"municipality": "Acate"},
        "Treviglio (BG) - Zona arancione": {
            "municipality": "Treviglio",
            "area": "Zona arancione",
        },
    }

    PARAMS = (
        text_field("municipality", term=field_terms.MUNICIPALITY),
        text_field("area", "Zone / Calendar", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the name of your municipality (comune) as it appears in the "
            "Municipium app. If the municipality has more than one collection zone "
            "(area), the error message will list the available zone names; pass "
            "the one that matches your address as 'area'. A partial name (e.g. "
            "'Zona 2') is enough, or you can pass the numeric calendar id."
        ),
        "it": (
            "Inserisci il nome del tuo comune così come appare nell'app Municipium. "
            "Se il comune ha più di una zona di raccolta (area), il messaggio di "
            "errore elencherà i nomi delle zone disponibili; indica come 'area' "
            "quella che corrisponde al tuo indirizzo. È sufficiente un nome "
            "parziale (es. 'Zona 2'), oppure puoi passare l'id numerico del "
            "calendario."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{CLOUD_URL}/api/v2/municipalities",
                headers=HEADERS,
                pick=_municipality_id,
            ),
            retrievers.Lookup(
                lambda muni_id, **_: (
                    f"{CLOUD_URL}/api/v2/municipalities/show_mobile/{muni_id}"
                ),
                headers=HEADERS,
                pick=_subdomain,
            ),
            retrievers.Lookup(
                lambda muni_id, subdomain, **_: f"https://{subdomain}/api/v2/calendars",
                headers=HEADERS,
                pick=_calendar_id,
            ),
        ),
        url=lambda muni_id, subdomain, calendar_id, **_: (
            f"https://{subdomain}/api/v2/calendars/{calendar_id}"
        ),
        params=_window,
        headers=HEADERS,
        raise_for_status=True,
    )
    parse = parsers.JsonParser()
    transform = JsonTransformer(
        date_key="start",
        type_key=_title,
        type_value_map={
            "umido": wt.ORGANIC,
            "plastica": wt.PLASTIC,
            "carta/cartone": wt.PAPER,
            "secco": wt.GENERAL_WASTE,
            "plastica/lattine": [wt.PLASTIC, wt.METAL],
            "vetro e barattolame": [wt.GLASS, wt.METAL],
            "secco (rsu)": wt.GENERAL_WASTE,
            "secco indifferenziato": wt.GENERAL_WASTE,
        },
    )
