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
from collections.abc import Callable, Mapping
from typing import Any, TypeVar
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

V = TypeVar("V")


def normalize_text(value: object) -> str:
    """Casefold, trim, and collapse internal whitespace for tolerant matching."""
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


# Letters NFKD does not decompose into a base letter and an accent, and
# ligatures a user types as two letters ("Goeulzin" for "Gœulzin").
_UNDECOMPOSED = str.maketrans(
    {
        **dict(zip("łŁđĐøØ", "lLdDoO", strict=True)),
        "œ": "oe",
        "Œ": "OE",
        "æ": "ae",
        "Æ": "AE",
        "ß": "ss",
    }
)


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


_YEAR = re.compile(r"(?<!\d)20\d{2}(?!\d)")


def link_pick(
    argument: str,
    *,
    href: str = r"\.pdf(?:$|[?#])",
    selector: str = "a[href]",
    attribute: str = "href",
    label: Callable[[Tag], str] | None = None,
    newest: bool = False,
) -> Callable[..., str]:
    """A ``Lookup`` pick: the link on an index page named like a source param.

    For the provider that lists one calendar per municipality (or zone) on an
    index page, each a link whose text is the name::

        retrieve = retrievers.LookupChainRetriever(
            steps=(retrievers.Lookup(INDEX_URL, pick=lookups.link_pick("commune")),),
            url=lambda pdf_url, **_: pdf_url,
        )

    The param is compared with :func:`normalize_loose` (case, accents and
    punctuation ignored); a miss raises
    :class:`SourceArgumentNotFoundWithSuggestions` listing every name found. The
    link is returned absolute, resolved against the page's URL.

    Args:
        argument: the source param holding the name.
        href: regex the link's URL must match (default: a PDF).
        selector: CSS selector for the candidate links.
        attribute: the attribute holding the URL; ``"value"`` with
            ``selector="select option"`` reads a drop-down of communes.
        label: ``callable(tag) -> name`` for a link not named by its own text
            (a card whose heading is a sibling); defaults to the link text.
        newest: when several links share a name (this season's calendar and
            last season's), keep the one whose text and URL name the latest
            year rather than the first.
    """
    pattern = re.compile(href, re.IGNORECASE)

    def pick(response: Any, *_keys: Any, **params: Any) -> str:
        soup = BeautifulSoup(response.text, "html.parser")
        links: dict[str, str] = {}
        latest: dict[str, int] = {}
        for tag in soup.select(selector):
            url = tag.get(attribute)
            if not isinstance(url, str) or not pattern.search(url):
                continue
            name = (label(tag) if label else tag.get_text(" ", strip=True)).strip()
            if not name:
                continue
            year = max(
                (int(y) for y in _YEAR.findall(f"{tag.get_text(' ')} {url}")),
                default=0,
            )
            if name not in links or (newest and year > latest[name]):
                links[name] = urljoin(str(response.url), url)
                latest[name] = year
        value = params.get(argument)
        return resolve(links, value, argument=argument, normalize=normalize_loose)

    return pick
