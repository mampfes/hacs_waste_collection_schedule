import re

from waste_collection_schedule import (  # type: ignore[attr-defined]
    Collection,
    Icons,
)
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.junker_app import (
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

# Junker's labels mapped back onto the ones CIDIU's own calendar used, so that
# switching to Junker does not rename the waste types users filter on.
TYPE_MAP = {
    "General waste collection": ("Indifferenziato", Icons.GENERAL_WASTE),
    "Organic waste": ("Organico", Icons.BIO_KITCHEN),
    "Paper": ("Carta", Icons.PAPER),
    "Plastic": ("Plastica", Icons.RECYCLING),
    "Glass/Cans": ("Vetro e lattine", Icons.GLASS),
}

_RANGE_RE = re.compile(r"(\d+)\s*[a-z]?\s+a\s+(?:civico\s*)?(\d+)")
_EXCEPTION_RE = re.compile(r"tranne\s+(?:civico\s*)?(\d+)")
_QUALIFIER_WORD_RE = re.compile(
    r"(?:da|dal|a|al|e|civico|civici|pari|dispari|tranne|\d+[a-z]?)"
)

# Specificity of a zone for a house number: a zone named for exactly that number
# beats a range or parity zone, which beats the catch-all zone for the street.
_CATCH_ALL, _RANGE, _EXACT = 0, 1, 2


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", replace_accents(text).lower()).strip()


def _is_qualifier(words: list[str]) -> bool:
    """Whether trailing words describe house numbers rather than a street name.

    "da vinci" (VIA LEONARDO DA VINCI) or "66 martiri" (PIAZZA 66 MARTIRI) are
    parts of a street name; "11", "da 1 a 15" or "civici pari" are qualifiers.
    """
    return all(_QUALIFIER_WORD_RE.fullmatch(w) for w in words) and any(
        re.fullmatch(r"\d+[a-z]?|pari|dispari", w) for w in words
    )


def _split_zone_name(zone_name: str) -> tuple[str, str]:
    """Split a Junker zone name into (street, qualifier).

    Junker names its zones like "VIA CONDOVE da civico 2 a civico 124 e da civico
    1 a civico 123", "CORSO SUSA pari da 2 a 314 dispari da 17 a 315",
    "Viale Bruno Radich 11" or "Via Roma civici pari".
    """
    words = _normalize(zone_name).replace("(", " ").replace(")", " ").split()
    for i in range(1, len(words)):
        if _is_qualifier(words[i:]):
            return " ".join(words[:i]), " ".join(words[i:])
    return " ".join(words), ""


def _match_rank(qualifier: str, number: int) -> int | None:
    """Specificity with which a zone qualifier covers `number`, None if it doesn't."""
    if not qualifier:
        return _CATCH_ALL
    excluded = {int(m.group(1)) for m in _EXCEPTION_RE.finditer(qualifier)}
    if number in excluded:
        return None
    if not _RANGE_RE.search(qualifier):
        if "pari" in qualifier:  # "civici pari" / "civici dispari", no numbers
            odd = "dispari" in qualifier
            return _RANGE if bool(number % 2) == odd else None
        # A bare number: the zone is dedicated to that house number.
        listed = {int(n) for n in re.findall(r"\d+", qualifier)}
        return _EXACT if number in listed else None
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
            return _RANGE
    return None


class Source:
    def __init__(self, street, street_number, city):
        self._street = street
        self._street_number = str(street_number)
        self._city = city

    def _find_zone(self, zones: list[tuple[str, int]]) -> int:
        """Return the id of the zone that covers the configured address."""
        street = _normalize(self._street)
        match = re.match(r"\d+", self._street_number.strip())
        if match is None:
            raise SourceArgumentNotFound(
                "street_number", self._street_number, "Enter a street number."
            )
        number = int(match.group(0))

        parsed = [(name, id_, *_split_zone_name(name)) for name, id_ in zones]
        same_street = [
            (name, id_, qualifier)
            for name, id_, base, qualifier in parsed
            if base == street
        ]
        if not same_street:
            # Junker often spells the street out in full ("Viale Antonio
            # Gramsci") where CIDIU's old calendar used "VIALE GRAMSCI".
            tokens = set(street.split())
            same_street = [
                (name, id_, qualifier)
                for name, id_, base, qualifier in parsed
                if tokens <= set(base.split())
            ]
        if not same_street:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                sorted({name for name, _id in zones}),
            )

        ranked = [
            (rank, name, id_)
            for name, id_, qualifier in same_street
            if (rank := _match_rank(qualifier, number)) is not None
        ]
        if not ranked:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_number", self._street_number, [n for n, _i, _q in same_street]
            )
        best = max(rank for rank, _n, _i in ranked)
        candidates = [(name, id_) for rank, name, id_ in ranked if rank == best]
        if len(candidates) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "street", self._street, [name for name, _id in candidates]
            )
        return candidates[0][1]

    def fetch(self) -> list[Collection]:
        try:
            # Towns without per-street zones return their calendar right away.
            collections = Junker(self._city, use_embed_url=False).fetch()
        except AreaRequired as e:
            zone_id = self._find_zone(e.areas)
            collections = Junker(self._city, area=zone_id, use_embed_url=False).fetch()

        entries = []
        for c in collections:
            label, icon = TYPE_MAP.get(c.type, (c.type, c.icon))
            entries.append(Collection(date=c.date, t=label, icon=icon))
        return entries
