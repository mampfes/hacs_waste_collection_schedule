import re
import unicodedata
from typing import Any, ClassVar, final

from waste_collection_schedule import parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    RequireRecords,
    WeekdayRecurrence,
)
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BAN_URL = "https://api-adresse.data.gouv.fr/search/"
_API_URL = "https://data.nantesmetropole.fr/api/records/1.0/search/"
_DATASET_ID = "244400404_jours-collectes-dechets-nantes"

_BLEU = "Ordures ménagères"
_JAUNE = "Déchets recyclables"

# Maps the "city" the BAN geocoder returns to the abbreviated commune codes of
# the dataset (only these communes have records).
_COMMUNE_MAP = {
    "nantes": "NANTES",
    "saint-herblain": "ST-HERBLAIN",
    "st-herblain": "ST-HERBLAIN",
    "saint-sebastien-sur-loire": "ST-SEBASTIEN",
    "st-sebastien-sur-loire": "ST-SEBASTIEN",
    "orvault": "ORVAULT",
    "bouguenais": "BOUGUENAIS",
}

_NUMBER_RE = re.compile(r"\d+")
_LEADING_NUMBER_RE = re.compile(r"^\s*(\d+)")


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def _geocoded(response, *_, address, **__) -> tuple[str, str]:
    """The (street, city) the BAN geocoder resolves the address to."""
    features = response.json().get("features", [])
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


def _query(street_city: tuple[str, str], **_) -> dict[str, Any]:
    street, city = street_city
    params: dict[str, Any] = {
        "dataset": _DATASET_ID,
        "q": f'libelle:"{street}"',
        "rows": 50,
    }
    commune = _COMMUNE_MAP.get(_strip_accents(city).lower().strip())
    if commune:
        params["refine.commune"] = commune
    return params


def _days(text: str | None) -> str | None:
    """The weekdays a ``*_jour_collecte`` field names, as ``"a/b"``.

    An empty string means a public drop-off container ("en colonnes", no fixed
    day); ``None`` means the field refers back to the "bleu" schedule (TRI'SAC
    bags).
    """
    if not text:
        return ""
    norm = _strip_accents(text).lower()
    if "colonne" in norm:
        return ""
    if norm.strip().startswith("_") or "voir bac" in norm:
        return None
    return "/".join(
        word
        for word in re.findall(r"[a-z]+", norm)
        if recurrence.weekday(word) is not None
    )


def _house_number_matches(obs_text: str | None, house_number: int | None):
    """Best-effort match of a house number against the free-text French
    "obs_prestation_collecte" describing which part of a street a record covers.

    True/False if decided, None if the wording could not be interpreted.
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
        lo, hi = sorted((numbers[0], numbers[-1]))
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


def _select_records(records: list[dict], house_number: int | None) -> list[dict]:
    """The record(s) applicable to the house number.

    A street can be split into segments ("pluriel") with different days per
    house number range. A segment identified with confidence wins; otherwise
    the segment without restriction, otherwise all segments are merged.
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
            return without_obs
    return records


def _schedule(records: list[dict], source: BaseSource) -> list[dict[str, str]]:
    """One ``{bleu, jaune}`` weekday record for the selected street segment(s)."""
    match = _LEADING_NUMBER_RE.match(source.params["address"])
    house_number = int(match.group(1)) if match else None
    bleu: list[str] = []
    jaune: list[str] = []
    follows_bleu = False
    for record in _select_records(list(records), house_number):
        fields = record.get("fields", {})
        bleu.append(_days(fields.get("bleu_jour_collecte")) or "")
        day = _days(fields.get("jaune_jour_collecte"))
        if day is None:
            follows_bleu = True
        else:
            jaune.append(day)
    if follows_bleu:
        jaune.extend(bleu)
    return [{"bleu": "/".join(bleu), "jaune": "/".join(jaune)}]


@final
class Source(BaseSource):
    TITLE = "Nantes Métropole"
    DESCRIPTION = (
        "Source script for data.nantesmetropole.fr waste collection schedules "
        "(Nantes and a few bordering streets in neighbouring communes)"
    )
    URL = "https://data.nantesmetropole.fr"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Rue Abbé de l'Epée": {"address": "16 Rue Abbé de l'Epée, Nantes"},
        "Rue du Port Boyer (numbered segment)": {
            "address": "89 Rue du Port Boyer, Nantes"
        },
        "Rue du Port Boyer (default segment)": {
            "address": "40 Rue du Port Boyer, Nantes"
        },
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full street address including the house number and the "
            "city name (e.g. '16 Rue Abbé de l'Epée, Nantes')."
        ),
        "fr": (
            "Entrez votre adresse complète avec le numéro de rue et le nom de la "
            "commune (ex : '16 Rue Abbé de l'Epée, Nantes')."
        ),
    }

    # The dataset publishes only the fixed weekday(s) per stream, not a calendar,
    # so the dates are projected two years ahead.
    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                _BAN_URL,
                params=lambda address, **_: {"q": address, "limit": 1},
                pick=_geocoded,
            ),
        ),
        url=_API_URL,
        params=_query,
        raise_for_status=True,
    )
    parse = parsers.JsonParser("records")
    preprocess = Compose(
        RequireRecords(argument="address"),
        _schedule,
        WeekdayRecurrence(day={"bleu": _BLEU, "jaune": _JAUNE}, count=104),
    )
    transform = ICSTransformer(
        type_value_map={_BLEU: wt.GENERAL_WASTE, _JAUNE: wt.RECYCLABLES}
    )
