"""Junker app calendars split into one zone per street (or street-number range).

Some Junker municipalities (CIDIU's towns around Turin) list per-street zones
instead of a calendar. A zone is named like ``VIA CONDOVE da civico 2 a civico
124 e da civico 1 a civico 123``, ``CORSO SUSA pari da 2 a 314 dispari da 17 a
315``, ``Viale Bruno Radich 11`` or ``Via Roma civici pari``. The retriever
matches the configured street and house number against those names, then reads
the chosen zone's calendar with the same extraction as ``junker_app``.
"""

import json
import re
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import RetrieverFunc
from waste_collection_schedule.service.junker_app import (
    EVENTS_REGEX,
    PLAIN_URL,
    PLAIN_URL_WITH_AREA,
    ZONE_REGEX,
    _replace_accents,
    _slugify,
)

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_RANGE_RE = re.compile(r"(\d+)\s*[a-z]?\s+a\s+(?:civico\s*)?(\d+)")
_EXCEPTION_RE = re.compile(r"tranne\s+(?:civico\s*)?(\d+)")
_QUALIFIER_WORD_RE = re.compile(
    r"(?:da|dal|a|al|e|civico|civici|pari|dispari|tranne|\d+[a-z]?)"
)

# Specificity of a zone for a house number: a zone named for exactly that number
# beats a range or parity zone, which beats the catch-all zone for the street.
_CATCH_ALL, _RANGE, _EXACT = 0, 1, 2


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", _replace_accents(text).lower()).strip()


def _is_qualifier(words: list[str]) -> bool:
    """Whether trailing words describe house numbers rather than a street name.

    "da vinci" (VIA LEONARDO DA VINCI) or "66 martiri" (PIAZZA 66 MARTIRI) are
    parts of a street name; "11", "da 1 a 15" or "civici pari" are qualifiers.
    """
    return all(_QUALIFIER_WORD_RE.fullmatch(w) for w in words) and any(
        re.fullmatch(r"\d+[a-z]?|pari|dispari", w) for w in words
    )


def _split_zone_name(zone_name: str) -> tuple[str, str]:
    """Split a Junker zone name into (street, qualifier)."""
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


def find_zone(
    street_arg: str, street_number: "str | int", zones: list[tuple[str, int]]
) -> int:
    """Return the id of the zone that covers the configured address."""
    street = _normalize(street_arg)
    number_arg = str(street_number)
    match = re.match(r"\d+", number_arg.strip())
    if match is None:
        raise SourceArgumentNotFound(
            "street_number", number_arg, "Enter a street number."
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
            "street", street_arg, sorted({name for name, _id in zones})
        )

    ranked = [
        (rank, name, id_)
        for name, id_, qualifier in same_street
        if (rank := _match_rank(qualifier, number)) is not None
    ]
    if not ranked:
        raise SourceArgumentNotFoundWithSuggestions(
            "street_number", number_arg, [n for n, _i, _q in same_street]
        )
    best = max(rank for rank, _n, _i in ranked)
    candidates = [(name, id_) for rank, name, id_ in ranked if rank == best]
    if len(candidates) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "street", street_arg, [name for name, _id in candidates]
        )
    return candidates[0][1]


class JunkerStreetRetriever(RetrieverFunc):
    """Resolve a municipality's street zone and return the raw ``events`` list.

    A municipality without zones serves its calendar directly; one with zones
    lists them first, and the zone matching ``street`` / ``street_number`` is
    then requested.
    """

    def __init__(
        self,
        municipality: str = "city",
        street: str = "street",
        street_number: str = "street_number",
    ):
        self.municipality = municipality
        self.street = street
        self.street_number = street_number

    def _fetch(
        self, source: "BaseSource", slug: str, area: "int | None" = None
    ) -> "tuple[str, Any]":
        url = (
            PLAIN_URL_WITH_AREA.format(municipality=slug, area=area)
            if area
            else PLAIN_URL.format(municipality=slug)
        )
        r = source.session.get(url)
        r.raise_for_status()

        zone_match = ZONE_REGEX.search(r.text)
        if zone_match:
            return "zones", [(z["NOME"], z["ID"]) for z in json.loads(zone_match[1])]
        events_match = EVENTS_REGEX.search(r.text)
        if not events_match:
            raise SourceArgumentNotFound(
                self.municipality,
                slug,
                "No events found, the town may be unsupported.",
            )
        return "events", json.loads(events_match[1])

    def __call__(self, source: "BaseSource") -> "list[dict[str, Any]]":
        params = source.params
        city_arg = params[self.municipality]
        street_arg = params[self.street]
        slug = _slugify(city_arg)

        kind, data = self._fetch(source, slug)
        if kind == "zones":
            zone = find_zone(street_arg, params[self.street_number], data)
            kind, data = self._fetch(source, slug, zone)
            if kind == "zones":
                raise SourceArgumentNotFound(
                    self.street, street_arg, "Could not resolve the street zone."
                )
        return data
