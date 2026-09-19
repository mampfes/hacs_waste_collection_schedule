import re

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.junker_app import (
    AreaNotFound,
    AreaRequired,
    Junker,
    replace_accents,
)

TITLE = "CIDIU S.p.A."
DESCRIPTION = (
    "Source for CIDIU waste collection services for the north-west Turin province"
)
URL = "https://cidiu.it/"
COUNTRY = "it"

# CIDIU retired its own calendar (cidiu-processer.php) and now publishes the
# schedules through the Junker app, one Junker "municipality" per town, with one
# zone per street or range of street numbers.
TEST_CASES = {
    "Collegno": {
        "city": "COLLEGNO",
        "street": "VIA CONDOVE",
        "street_number": "107",
    },
    "Grugliasco": {
        "city": "GRUGLIASCO",
        "street": "VIALE GRAMSCI",
        "street_number": "18",
    },
    "Rivoli": {
        "city": "RIVOLI",
        "street": "CORSO SUSA",
        "street_number": 124,
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City",
        "street": "Street",
        "street_number": "Street number",
    },
    "it": {
        "city": "Comune",
        "street": "Via",
        "street_number": "Numero civico",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "Town served by CIDIU, e.g. Collegno",
        "street": "Street name without the number",
        "street_number": "Street number",
    },
    "it": {
        "city": "Comune servito da CIDIU, ad esempio Collegno",
        "street": "Nome della via senza il numero civico",
        "street_number": "Numero civico",
    },
}

_RANGE_RE = re.compile(r"(\d+)\s*[a-z]?\s+a\s+(?:civico\s*)?(\d+)")
_EXCEPTION_RE = re.compile(r"tranne\s+(?:civico\s*)?(\d+)")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", replace_accents(text).lower()).strip()


_QUALIFIER_RE = re.compile(r"\s(?=(?:da|pari|dispari|civico)\b|\d)")


def _split_zone_name(zone_name: str) -> tuple[str, str]:
    """Split a Junker zone name into (street, qualifier).

    Junker names its zones like "VIA CONDOVE da civico 2 a civico 124 e da civico
    1 a civico 123" or "CORSO SUSA pari da 2 a 314 dispari da 17 a 315".
    """
    parts = _QUALIFIER_RE.split(_normalize(zone_name), maxsplit=1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def _covers(qualifier: str, number: int) -> bool:
    """Whether a zone qualifier ("da 1 a 15", "pari da 2 a 314", ...) contains `number`."""
    if not qualifier:
        return True
    excluded = {int(m.group(1)) for m in _EXCEPTION_RE.finditer(qualifier)}
    if number in excluded:
        return False
    # Split into segments so that parity words apply to the range that follows
    # them ("pari da 2 a 314 dispari da 17 a 315").
    for segment in re.split(r"(?=\bpari\b|\bdispari\b)", qualifier):
        parity_odd = "dispari" in segment
        parity_even = not parity_odd and "pari" in segment
        for match in _RANGE_RE.finditer(segment):
            low, high = int(match.group(1)), int(match.group(2))
            if not low <= number <= high:
                continue
            if parity_even and number % 2:
                continue
            if parity_odd and not number % 2:
                continue
            return True
    return False


class Source:
    def __init__(self, street, street_number, city):
        self._street = street
        self._street_number = str(street_number)
        self._city = city

    def _find_zone(self, zones: list[tuple[str, int]]) -> str:
        street = _normalize(self._street)
        match = re.match(r"\d+", self._street_number.strip())
        if match is None:
            raise SourceArgumentNotFound(
                "street_number", self._street_number, "Enter a street number."
            )
        number = int(match.group(0))

        parsed = [(name, *_split_zone_name(name)) for name, _id in zones]
        same_street = [
            (name, qualifier) for name, base, qualifier in parsed if base == street
        ]
        if not same_street:
            # Junker often spells the street out in full ("Viale Antonio
            # Gramsci") where CIDIU's old calendar used "VIALE GRAMSCI".
            tokens = set(street.split())
            same_street = [
                (name, qualifier)
                for name, base, qualifier in parsed
                if tokens <= set(base.split())
            ]
        if not same_street:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                sorted({name for name, _id in zones}),
            )

        candidates = [
            name for name, qualifier in same_street if _covers(qualifier, number)
        ]
        if not candidates:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_number", self._street_number, [n for n, _q in same_street]
            )
        if len(candidates) > 1:
            raise SourceArgAmbiguousWithSuggestions("street", self._street, candidates)
        return candidates[0]

    def fetch(self) -> list[Collection]:
        try:
            Junker(self._city, use_embed_url=False).fetch()
        except AreaRequired as e:
            zone = self._find_zone(e.areas)
        except AreaNotFound as e:
            zone = self._find_zone(e.areas)
        else:
            raise ValueError("Expected CIDIU to publish one zone per street")

        return Junker(self._city, area_name=zone, use_embed_url=False).fetch()
