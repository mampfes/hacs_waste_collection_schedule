import re
import unicodedata
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "Nantes Métropole"
DESCRIPTION = "Source script for data.nantesmetropole.fr waste collection schedules (Nantes and a few bordering streets in neighbouring communes)"
URL = "https://data.nantesmetropole.fr"
COUNTRY = "fr"

TEST_CASES = {
    "Rue Abbé de l'Epée": {"address": "16 Rue Abbé de l'Epée, Nantes"},
    "Rue du Port Boyer (numbered segment)": {"address": "89 Rue du Port Boyer, Nantes"},
    "Rue du Port Boyer (default segment)": {"address": "40 Rue du Port Boyer, Nantes"},
}

ICON_MAP = {
    "Ordures ménagères": Icons.GENERAL_WASTE,
    "Déchets recyclables": Icons.RECYCLING,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your full street address including the house number and the city name (e.g. '16 Rue Abbé de l'Epée, Nantes').",
    "fr": "Entrez votre adresse complète avec le numéro de rue et le nom de la commune (ex : '16 Rue Abbé de l'Epée, Nantes').",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your street address with house number and city",
    },
    "fr": {
        "address": "Votre adresse postale avec numéro de rue et commune",
    },
}

PARAM_TRANSLATIONS = {
    "en": {"address": "Address"},
    "fr": {"address": "Adresse"},
}

BAN_GEOCODE_URL = "https://api-adresse.data.gouv.fr/search/"
API_URL = "https://data.nantesmetropole.fr/api/records/1.0/search/"
DATASET_ID = "244400404_jours-collectes-dechets-nantes"

# Maps the "city" property returned by the BAN geocoder to the abbreviated
# commune codes used in the dataset (only these communes have records).
COMMUNE_MAP = {
    "nantes": "NANTES",
    "saint-herblain": "ST-HERBLAIN",
    "st-herblain": "ST-HERBLAIN",
    "saint-sebastien-sur-loire": "ST-SEBASTIEN",
    "st-sebastien-sur-loire": "ST-SEBASTIEN",
    "orvault": "ORVAULT",
    "bouguenais": "BOUGUENAIS",
}

FR_WEEKDAYS = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}

BLEU_WASTE_TYPE = "Ordures ménagères"
JAUNE_WASTE_TYPE = "Déchets recyclables"

_NUMBER_RE = re.compile(r"\d+")
_LEADING_NUMBER_RE = re.compile(r"^\s*(\d+)")


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def _parse_weekdays(text):
    """Parse a "*_jour_collecte" field.

    Returns a set of weekday indices (0=Monday), an empty set if the field
    references a public drop-off container ("en colonnes", no fixed day), or
    None if the field just refers back to the "bleu" schedule (TRI'SAC bags).
    """
    if not text:
        return set()
    norm = _strip_accents(text).lower()
    if "colonne" in norm:
        return set()
    if norm.strip().startswith("_") or "voir bac" in norm:
        return None
    days = set()
    for name, idx in FR_WEEKDAYS.items():
        if name in norm:
            days.add(idx)
    return days


def _house_number_matches(obs_text, house_number):
    """Best-effort match of a house number against a free-text French
    "obs_prestation_collecte" description of the street segment it applies to.

    Returns True/False if a decision could be made, or None if the wording
    could not be interpreted.
    """
    if not obs_text or house_number is None:
        return None
    norm = _strip_accents(obs_text).lower()
    numbers = [int(n) for n in _NUMBER_RE.findall(norm)]
    is_odd = "impair" in norm
    is_even = (not is_odd) and re.search(r"(?<!im)pair", norm) is not None
    has_from = "a partir d" in norm
    has_range = " au " in norm and re.search(r"\bdu\b", norm) is not None

    if numbers and not has_from and not has_range:
        # Explicit list of house numbers, e.g. "les numéros 4-6-8".
        return house_number in numbers
    if has_from and numbers:
        threshold = numbers[0]
        if is_odd:
            return house_number % 2 == 1 and house_number >= threshold
        if is_even:
            return house_number % 2 == 0 and house_number >= threshold
        return house_number >= threshold
    if has_range and len(numbers) >= 2:
        lo, hi = numbers[0], numbers[-1]
        if lo > hi:
            lo, hi = hi, lo
        result = lo <= house_number <= hi
        if is_odd:
            result = result and house_number % 2 == 1
        if is_even:
            result = result and house_number % 2 == 0
        return result
    if is_odd:
        return house_number % 2 == 1
    if is_even:
        return house_number % 2 == 0
    return None


class Source:
    def __init__(self, address):
        normalized = address.strip() if isinstance(address, str) else address
        if not normalized:
            raise SourceArgumentRequired("address", "An address is required")
        self._address = normalized

    def fetch(self):
        house_number_match = _LEADING_NUMBER_RE.match(self._address)
        house_number = int(house_number_match.group(1)) if house_number_match else None

        street, city = self._geocode(self._address)

        records = self._search_records(street, city)
        if not records:
            raise SourceArgumentNotFound("address", self._address)

        selected = self._select_records(records, house_number)

        bleu_days = set()
        jaune_days = set()
        jaune_follows_bleu = False
        for record in selected:
            fields = record.get("fields", {})
            record_bleu_days = _parse_weekdays(fields.get("bleu_jour_collecte"))
            record_jaune_raw = _parse_weekdays(fields.get("jaune_jour_collecte"))

            bleu_days |= record_bleu_days
            if record_jaune_raw is None:
                jaune_follows_bleu = True
            else:
                jaune_days |= record_jaune_raw

        if jaune_follows_bleu:
            jaune_days |= bleu_days

        entries = []
        today = date.today()
        # Two years of weekly recurring collection dates. The dataset only
        # exposes the fixed weekday(s) per waste stream, not a full calendar
        # with holiday exceptions.
        for offset in range(730):
            d = today + timedelta(days=offset)
            weekday = d.weekday()
            if weekday in bleu_days:
                entries.append(
                    Collection(
                        date=d,
                        t=BLEU_WASTE_TYPE,
                        icon=ICON_MAP.get(BLEU_WASTE_TYPE),
                    )
                )
            if weekday in jaune_days:
                entries.append(
                    Collection(
                        date=d,
                        t=JAUNE_WASTE_TYPE,
                        icon=ICON_MAP.get(JAUNE_WASTE_TYPE),
                    )
                )

        return entries

    @staticmethod
    def _select_records(records, house_number):
        """Pick the record(s) applicable to the given house number.

        Some streets are split into several segments ("type_collecte" =
        "pluriel") with different collection days depending on the house
        number range. If a segment can be identified with confidence, only
        that segment is used. Otherwise all matching segments are merged
        (best effort), which may over-report collection days for that
        specific address.
        """
        if len(records) == 1:
            return records

        with_obs = [
            r for r in records if r.get("fields", {}).get("obs_prestation_collecte")
        ]
        without_obs = [r for r in records if r not in with_obs]

        if house_number is not None:
            matched = [
                r
                for r in with_obs
                if _house_number_matches(
                    r["fields"].get("obs_prestation_collecte"), house_number
                )
                is True
            ]
            if matched:
                return matched
            if without_obs:
                # Fall back to the segment without any restriction, which
                # acts as the "default" for numbers not called out
                # explicitly by the other segments.
                return without_obs

        # Ambiguous: merge every candidate segment.
        return records

    @classmethod
    def _search_records(cls, street, city):
        commune = (
            COMMUNE_MAP.get(_strip_accents(city).lower().strip()) if city else None
        )

        params = {
            "dataset": DATASET_ID,
            "q": f'libelle:"{street}"',
            "rows": 50,
        }
        if commune:
            params["refine.commune"] = commune

        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        records = data.get("records", [])

        if records:
            return records

        # Retry without the phrase-scoped query, matching client-side on the
        # normalized street name (covers minor formatting differences).
        params = {"dataset": DATASET_ID, "q": street, "rows": 50}
        if commune:
            params["refine.commune"] = commune
        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        target = _strip_accents(street).lower().strip()
        return [
            r
            for r in data.get("records", [])
            if _strip_accents(r.get("fields", {}).get("libelle", "")).lower().strip()
            == target
        ]

    @staticmethod
    def _geocode(address):
        """Geocode the address via the BAN (Base Adresse Nationale) API and
        return the (street, city) it belongs to."""
        try:
            resp = requests.get(
                BAN_GEOCODE_URL,
                params={"q": address, "limit": 1},
                timeout=10,
            )
            resp.raise_for_status()
            features = resp.json().get("features", [])
        except requests.RequestException:
            features = []

        if not features:
            raise SourceArgumentNotFound("address", address)

        props = features[0].get("properties", {})
        street = props.get("street") or props.get("name")
        city = props.get("city")
        if not street or not city:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                address,
                [
                    "Make sure the address includes a street name and the city, "
                    "e.g. '16 Rue Abbé de l'Epée, Nantes'"
                ],
            )
        return street, city
