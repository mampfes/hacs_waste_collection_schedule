"""Shared client for the "abfuhrplan-*.de" waste-calendar platform (DE).

Several German municipalities publish their collection calendar through the
same Neos/Flow application (its form fields are namespaced ``WMIT.MuellAbfuhr``),
reachable at its own ``abfuhrplan-<municipality>.de`` domain. Every deployment
works the same way:

* the address is a URL *path*, one segment per level, lowercased and
  ASCII-folded (``/parsberg/bogenmuehle``, or just ``/marktstrasse`` where the
  municipality is the whole service area);
* an unknown segment 404s the page, and the level above it renders a
  ``li.list-group-item`` list of the valid values at that level, which is where
  the "did you mean" suggestions come from;
* a resolved page carries a "download the calendar" form posting to
  ``/getical``, whose hidden fields (a signed ``__referrer``/``__trustedProperties``
  pair plus a checkbox per waste type) must be echoed back verbatim to get the
  ICS.

:class:`AbfuhrplanRetriever` is the whole flow, so a source on this platform
declares only its base URL and which params make up the path.
"""

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, NoReturn

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import Response, RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


def prepare_arg(arg: str, *, remove: str = "()") -> str:
    """Fold a user-supplied name into the platform's URL-path form.

    Lowercased, spaces hyphenated, umlauts transliterated, and every character
    in ``remove`` dropped. Deployments differ slightly in what they strip, so
    ``remove`` is per-provider: parentheses everywhere, and commas as well on
    the deployments whose street list carries them.
    """
    value = arg.lower().strip().replace(" ", "-")
    for char in remove:
        value = value.replace(char, "")
    return (
        value.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


def parse_list_items(html: str, normalise: Callable[[str], str]) -> list[str]:
    """Read the valid values off a level's ``li.list-group-item`` listing.

    Each item links to the next path segment. The label is used when it folds
    to exactly that segment (so the suggestion reads the way the user would
    type it); where it does not, the segment itself is the only thing that is
    certain to work, so that is suggested instead.
    """
    soup = BeautifulSoup(html, "html.parser")
    elements = []
    for item in soup.select("li.list-group-item"):
        a = item.select_one("a")
        if not a:
            continue
        href = a.get("href")
        if not isinstance(href, str):
            continue
        href_name = href.split("/")[-1]
        if href_name == normalise(item.text.lower().strip()):
            elements.append(item.text.strip())
        else:
            elements.append(href_name)
    return elements


def scrape_getical_form(html: str) -> "dict[str, str | int]":
    """Collect every field of the resolved page's ``/getical`` download form.

    Inputs and buttons are posted back with the value the page gave them (the
    signed referrer/trusted-properties pair plus one checkbox per waste type);
    a ``<select>`` (the reminder lead time) is posted as ``0``. The exact set
    differs from deployment to deployment without documented meaning, so it is
    replayed rather than hardcoded.
    """
    soup = BeautifulSoup(html, "html.parser")
    form = soup.select_one('form[action="/getical"]')
    if not form:
        raise SourceArgumentNotFoundWithSuggestions("street", "", [])

    data: dict = {}
    for input_ in form.select("input") + form.select("button"):
        name = input_.get("name")
        value = input_.get("value")
        if not isinstance(name, str) or not isinstance(value, str):
            continue
        data[name] = value
    for select in form.select("select"):
        name = select.get("name")
        if not isinstance(name, str):
            continue
        data[name] = 0
    return data


class AbfuhrplanRetriever(RetrieverFunc):
    """Resolve the address path, then POST its form for the ICS.

    The pipeline retrieve step for the platform. It GETs the address page,
    scrapes its ``/getical`` form and posts it straight back, returning the raw
    ICS response for ``parsers.IcsParser``.

    When the page 404s it walks back up the path one segment at a time until a
    level renders, and blames the first segment that level did not know about,
    suggesting the values it lists. That is what tells a mistyped street from a
    mistyped municipality: on a two-level deployment a bad street leaves the
    municipality page standing (suggest its streets), while a bad municipality
    404s that too (suggest the municipalities instead).

    Args:
        base_url: the deployment's base URL, used verbatim as the listing page
            for the top level and as the ``/getical`` prefix.
        fields: the ``source.params`` fields making up the path, outermost
            first, already folded by :func:`prepare_arg` in the source's
            ``__init__``.
        normalise: the same folding, for comparing a listing's labels against
            its links (see :func:`parse_list_items`).
    """

    def __init__(
        self,
        *,
        base_url: str,
        fields: Sequence[str],
        normalise: Callable[[str], str] = prepare_arg,
    ):
        if not fields:
            raise ValueError("AbfuhrplanRetriever requires at least one field")
        self._base_url = base_url
        self._fields = tuple(fields)
        self._normalise = normalise

    def _page_url(self, values: Sequence[str]) -> str:
        """The address page for the given path segments (``()`` is the root)."""
        if not values:
            return self._base_url
        return "/".join([self._base_url.rstrip("/"), *values])

    def _raise_unresolved(self, source: "BaseSource", values: list[str]) -> NoReturn:
        """Blame the deepest segment the site could not resolve."""
        for depth in range(len(values) - 1, -1, -1):
            listing = source.session.get(self._page_url(values[:depth]))
            if listing.status_code == 404:
                continue
            listing.raise_for_status()
            raise SourceArgumentNotFoundWithSuggestions(
                self._fields[depth],
                values[depth],
                parse_list_items(listing.text, self._normalise),
            )
        raise SourceArgumentNotFoundWithSuggestions(self._fields[0], values[0], [])

    def __call__(self, source: "BaseSource") -> Response:
        session = source.session
        values = [str(source.params[field]) for field in self._fields]

        page = session.get(self._page_url(values))
        if page.status_code == 404:
            self._raise_unresolved(source, values)
        page.raise_for_status()

        download = session.post(
            f"{self._base_url}/getical", data=scrape_getical_form(page.text)
        )
        download.raise_for_status()
        return download
