"""Normalised name lookups with suggestions-on-miss.

Many sources resolve a user-supplied name (a street, suburb, town or zone) to
some value (a weekday, a zone id, ...) by matching it case-insensitively against
a table parsed from the provider, and raise a helpful "did you mean" error when
it doesn't match. That matching + suggestion boilerplate is identical across
sources, so it lives here.

    weekday = lookups.resolve(town_weekdays, town, argument="town")

For the common "street/town -> weekday -> weekly schedule" pattern, combine this
with ``recurrence.next_weekday`` and a ``Schedule`` in the source's describe().
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from typing import TypeVar

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

V = TypeVar("V")


def normalize_text(value: object) -> str:
    """Casefold, trim, and collapse internal whitespace for tolerant matching."""
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


# Letters NFKD does not decompose into a base letter and an accent.
_UNDECOMPOSED = str.maketrans("łŁđĐøØ", "lLdDoO")


def normalize_loose(value: object) -> str:
    """Like :func:`normalize_text`, but also drop accents and punctuation.

    For names a user types without the diacritics or hyphens the provider
    prints: "Jamno Labusz" matches "Jamno-Łabusz", "Perouges hors cite"
    matches "Pérouges hors cité".
    """
    text = unicodedata.normalize("NFKD", str(value).translate(_UNDECOMPOSED))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[\W_]+", " ", text).strip().casefold()


def resolve(
    mapping: Mapping[str, V],
    value: object,
    *,
    argument: str,
    normalize=normalize_text,
) -> V:
    """Resolve ``value`` against ``mapping`` keys (normalised), else raise.

    Returns ``mapping[key]`` for the key whose normalised form equals the
    normalised ``value``. On no match raises
    :class:`SourceArgumentNotFoundWithSuggestions` naming ``argument`` and
    listing the original keys, so the HA UI shows the valid options.
    """
    wanted = normalize(value)
    for key, result in mapping.items():
        if normalize(key) == wanted:
            return result
    raise SourceArgumentNotFoundWithSuggestions(argument, value, sorted(mapping.keys()))
