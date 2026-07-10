import json
import re
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Östersunds kommun"
DESCRIPTION = "Source for Östersunds kommun waste collection schedule, Sweden."
URL = "https://www.ostersund.se"
COUNTRY = "se"
TEST_CASES = {
    "Återgången 1": {"address": "Återgången 1"},
    "Strandgatan 13": {"address": "Strandgatan 13"},
}

ICON_MAP = {
    "Hushållsavfall": Icons.GENERAL_WASTE,
}

PAGE_URL = "https://www.ostersund.se/bygga-bo-klimat-och-miljo/avfall-och-atervinning/nar-kommer-sopbilen.html"

# Matches every `AppRegistry.registerInitialState('<portletId>', {...});`
# call embedded in the server-rendered page. The waste search widget's
# portlet id is treated as an implementation detail and not hardcoded here;
# instead the correct payload is identified by the presence of the
# "result"/"query" keys, which is more resilient to a future re-deploy of
# the widget under a different portlet id.
STATE_RE = re.compile(
    r"registerInitialState\('[^']+',(\{.*?\})\);",
    re.DOTALL,
)

# Household waste (residual + food waste) is collected together on a fixed
# fortnightly cadence for single-family homes ("Sopbilen hämtar ditt avfall
# var fjortonde dag"). The page only exposes the next pickup date, so future
# occurrences are extrapolated at a 14-day interval.
COLLECTION_INTERVAL_DAYS = 14
NUMBER_OF_COLLECTIONS_TO_GENERATE = 26

WASTE_TYPE = "Hushållsavfall"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to the collection search on ostersund.se, search for your address and copy the street name and house number exactly as shown in the results list, e.g. 'Återgången 1'. Only single-family homes in Östersund kommun are covered; apartment buildings and businesses are not listed.",
    "de": "Öffnen Sie die Abfuhrsuche auf ostersund.se, suchen Sie Ihre Adresse und übernehmen Sie Straßenname und Hausnummer genau wie in der Ergebnisliste angezeigt, z. B. 'Återgången 1'. Es werden nur Einfamilienhäuser in der Gemeinde Östersund unterstützt; Mehrfamilienhäuser und Firmen sind nicht gelistet.",
    "it": "Vai alla ricerca sul sito ostersund.se, cerca il tuo indirizzo e copia via e numero civico esattamente come mostrato nell'elenco dei risultati, ad es. 'Återgången 1'. Sono supportate solo le case unifamiliari nel comune di Östersund; condomini e aziende non sono elencati.",
    "fr": "Rendez-vous sur la recherche de collecte d'ostersund.se, recherchez votre adresse et reprenez le nom de rue et le numéro exactement comme indiqué dans la liste des résultats, par ex. « Återgången 1 ». Seules les maisons individuelles de la commune d'Östersund sont prises en charge ; les immeubles et les entreprises n'y figurent pas.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address including house number, exactly as it appears on ostersund.se, e.g. 'Återgången 1'.",
    },
    "de": {
        "address": "Straßenadresse inkl. Hausnummer, genau wie auf ostersund.se angegeben, z. B. 'Återgången 1'.",
    },
    "it": {
        "address": "Indirizzo stradale con numero civico, esattamente come appare su ostersund.se, ad es. 'Återgången 1'.",
    },
    "fr": {
        "address": "Adresse complète avec numéro, telle qu'elle apparaît sur ostersund.se, par ex. « Återgången 1 ».",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    },
    "de": {
        "address": "Adresse",
    },
    "it": {
        "address": "Indirizzo",
    },
    "fr": {
        "address": "Adresse",
    },
}


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        r = requests.get(PAGE_URL, params={"query": self._address}, timeout=30)
        r.raise_for_status()

        results = None
        for match in STATE_RE.finditer(r.text):
            try:
                payload = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            if "result" in payload and "query" in payload:
                results = payload["result"]
                break

        if results is None:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                message_addition="the schedule page could not be parsed, it may have changed format.",
            )

        wanted = _normalize(self._address)
        match_item = None
        for item in results:
            if _normalize(item.get("address", "")) == wanted:
                match_item = item
                break

        if match_item is None:
            suggestions = [
                f"{item['address'].title()}, {item['zipCode']} {item['city'].title()}"
                for item in results[:10]
            ]
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, suggestions
            )

        next_pickup = match_item.get("nextPickup") or {}
        next_pickup_date = next_pickup.get("nextPickupDate")
        if not next_pickup_date:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                message_addition="no upcoming collection date was returned for this address.",
            )

        next_date = date.fromisoformat(next_pickup_date)

        return [
            Collection(
                date=next_date + timedelta(days=COLLECTION_INTERVAL_DAYS * i),
                t=WASTE_TYPE,
                icon=ICON_MAP.get(WASTE_TYPE),
            )
            for i in range(NUMBER_OF_COLLECTIONS_TO_GENERATE)
        ]
