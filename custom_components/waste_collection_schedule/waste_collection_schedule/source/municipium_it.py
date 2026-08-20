import datetime
from difflib import get_close_matches

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Municipium"
DESCRIPTION = (
    "Source for the Municipium app (Maggioli S.p.A.), used by many Italian "
    "municipalities to publish their door-to-door waste collection calendar."
)
URL = "https://www.municipiumapp.it"
COUNTRY = "it"
SOURCE_CODEOWNERS = ["@fedfus"]

# Central directory of every municipality on the platform.
CLOUD_URL = "https://cloud.municipiumapp.it"

TEST_CASES = {
    "Serrastretta (CZ) - Zona 2 Migliuso": {
        "municipality": "Serrastretta",
        "area": "Zona 2",
    },
    "Serrastretta (CZ) - by calendar id": {
        "municipality": "Serrastretta",
        "area": 10325,
    },
    "Acate (RG)": {
        "municipality": "Acate",
    },
}

# Municipalities on the platform that expose a waste calendar, as (name,
# province). This is only used to advertise coverage in the docs; it does not
# limit which comuni work. The full list must be produced with a throttled scan
# of the /municipalities directory (the platform WAF rate-limits bulk requests),
# via tools/municipium_scan.py before opening the PR. The few below are the ones
# verified end-to-end during development.
COMUNI = [
    ("Serrastretta", "CZ"),
    ("Acate", "RG"),
    ("Affi", "VR"),
    ("Acquanegra Cremonese", "CR"),
    ("Adrara San Rocco", "BG"),
]


def EXTRA_INFO():
    for name, province in COMUNI:
        yield {"title": f"{name} ({province})", "country": "it"}


# Municipium categories vary per municipality; match on a normalised keyword.
ICON_MAP = {
    "umido": Icons.BIO_KITCHEN,
    "organico": Icons.BIO_KITCHEN,
    "secco": Icons.GENERAL_WASTE,
    "indifferenziato": Icons.GENERAL_WASTE,
    "residuo": Icons.GENERAL_WASTE,
    "carta": Icons.PAPER,
    "cartone": Icons.PAPER,
    "vetro": Icons.GLASS,
    "plastica": Icons.PLASTIC_PACKAGING,
    "lattine": Icons.METAL,
    "metallo": Icons.METAL,
    "multimateriale": Icons.RECYCLING,
    "verde": Icons.GARDEN,
    "sfalci": Icons.GARDEN,
    "vegetale": Icons.GARDEN,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter the name of your municipality (comune) as it appears in the "
    "Municipium app. If the municipality has more than one collection zone "
    "(area), the error message will list the available zone names; pass the one "
    "that matches your address as 'area'. A partial name (e.g. 'Zona 2') is "
    "enough, or you can pass the numeric calendar id.",
    "it": "Inserisci il nome del tuo comune cosi come appare nell'app Municipium. "
    "Se il comune ha piu di una zona di raccolta (area), il messaggio di errore "
    "elenchera i nomi delle zone disponibili; indica come 'area' quella che "
    "corrisponde al tuo indirizzo. E sufficiente un nome parziale (es. 'Zona 2'), "
    "oppure puoi passare l'id numerico del calendario.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "The municipality (comune), e.g. 'Serrastretta'.",
        "area": "The collection zone name (or a part of it), or the numeric "
        "calendar id. Only needed when the municipality has more than one zone.",
    },
    "it": {
        "municipality": "Il comune, ad esempio 'Serrastretta'.",
        "area": "Il nome della zona di raccolta (o una parte), oppure l'id "
        "numerico del calendario. Serve solo se il comune ha piu di una zona.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {"municipality": "Municipality", "area": "Zone / Calendar"},
    "it": {"municipality": "Comune", "area": "Zona / Calendario"},
}


def _icon_for(name: str):
    low = name.casefold()
    for key, icon in ICON_MAP.items():
        if key in low:
            return icon
    return None


class Source:
    def __init__(self, municipality: str, area: "str | int | None" = None):
        self._municipality: str = municipality
        self._area = area

    def _find_municipality(self, session: requests.Session) -> dict:
        r = session.get(f"{CLOUD_URL}/api/v2/municipalities")
        r.raise_for_status()
        comuni = r.json()

        wanted = self._municipality.strip().casefold()
        matches = [c for c in comuni if c["name"].casefold() == wanted]
        if not matches:
            names = [c["name"] for c in comuni]
            suggestions = get_close_matches(self._municipality, names, n=5, cutoff=0.4)
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, suggestions
            )
        if len(matches) > 1:
            # Same comune name in several provinces: disambiguate by province.
            labels = [f"{c['name']} ({c.get('province_initials')})" for c in matches]
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, labels
            )

        muni_id = matches[0]["id"]
        r = session.get(f"{CLOUD_URL}/api/v2/municipalities/show_mobile/{muni_id}")
        r.raise_for_status()
        return r.json()

    def _pick_calendar(self, calendars: "list[dict]") -> dict:
        if not calendars:
            raise SourceArgumentNotFoundWithSuggestions("area", self._area, [])

        # Explicit calendar id.
        if isinstance(self._area, int) or (
            isinstance(self._area, str) and self._area.isdigit()
        ):
            wanted_id = int(self._area)
            found = next((c for c in calendars if c["id"] == wanted_id), None)
            if found is None:
                raise SourceArgumentNotFoundWithSuggestions(
                    "area",
                    self._area,
                    [f"{c['name']} (id {c['id']})" for c in calendars],
                )
            return found

        names = [c["name"] for c in calendars]

        if self._area is None:
            if len(calendars) == 1:
                return calendars[0]
            raise SourceArgumentRequiredWithSuggestions(
                "area", "this municipality has more than one collection zone", names
            )

        wanted = self._area.strip().casefold()
        # Exact match, then unambiguous substring, then fuzzy suggestions.
        found = next((c for c in calendars if c["name"].casefold() == wanted), None)
        if found is None:
            subs = [c for c in calendars if wanted in c["name"].casefold()]
            if len(subs) == 1:
                found = subs[0]
        if found is None:
            suggestions = get_close_matches(str(self._area), names, n=5, cutoff=0.3)
            raise SourceArgumentNotFoundWithSuggestions(
                "area", self._area, suggestions or names
            )
        return found

    def fetch(self) -> "list[Collection]":
        session = requests.Session()
        session.headers["Accept"] = "application/json"
        # The platform WAF rejects the default python-requests User-Agent.
        session.headers["User-Agent"] = "Mozilla/5.0 (waste_collection_schedule)"

        details = self._find_municipality(session)
        subdomain = details.get("subdomain")
        if not subdomain or not details.get("enable_garbage_calendar"):
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, []
            )
        api = f"https://{subdomain}/api/v2"

        r = session.get(f"{api}/calendars")
        r.raise_for_status()
        calendar = self._pick_calendar(r.json())

        # The calendar endpoint filters events by a [start, end] epoch-second window.
        today = datetime.date.today()
        start = int(
            datetime.datetime.combine(
                today - datetime.timedelta(days=30), datetime.time()
            ).timestamp()
        )
        end = int(
            datetime.datetime.combine(
                today + datetime.timedelta(days=365), datetime.time()
            ).timestamp()
        )

        r = session.get(
            f"{api}/calendars/{calendar['id']}",
            params={"start": start, "end": end},
        )
        r.raise_for_status()

        entries: list[Collection] = []
        for ev in r.json():
            title = (ev.get("category") or {}).get("name") or ev.get("title")
            date_str = ev.get("start")
            if not title or not date_str:
                continue
            date = datetime.datetime.fromisoformat(date_str).date()
            entries.append(Collection(date=date, t=title, icon=_icon_for(title)))

        return entries
