"""Region coverage for a source.

A source is one *structure* (its retrieve/parse/transform pipeline plus its
``PARAMS`` schema) applied to one or more *regions*. A single-region source has
an implicit single region; a source that covers several municipalities or
providers under one structure lists them in ``REGIONS``.

Each :class:`Region` is the same structure with specific parameter values, plus
optional display overrides (``url`` / ``country``) for the listing. The
framework uses ``REGIONS`` for the generated README / ``sources.json`` entries
(one discoverable listing per region) and to pre-fill the config form. For very
large external registries (shared platforms with hundreds of providers),
``REGIONS`` may instead be a callable returning the list, so it can be loaded
from a data file rather than written inline.

This is the typed successor to the legacy ``EXTRA_INFO`` dict list: ``params``
is validated against the source's ``PARAMS`` rather than being free-form.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Region:
    """One region a source covers: PARAMS values plus optional display overrides.

    Args:
        title: Display name for the listing (e.g. the municipality).
        params: The source's ``PARAMS`` values that select this region.
        url: Optional listing URL override (defaults to the source's ``URL``).
        country: Optional country-code override (defaults to ``COUNTRY``).
    """

    title: str
    params: dict[str, Any] = field(default_factory=dict)
    url: str | None = None
    country: str | None = None


def region(
    title: str,
    *,
    url: str | None = None,
    country: str | None = None,
    **params: Any,
) -> Region:
    """Declare one region a source covers.

    Keyword args (other than ``url`` / ``country``) are the region's PARAMS
    values, e.g.::

        region("Mulhouse", commune="Mulhouse", quartier="Centre Ville")
        REGIONS = [region(name, commune=name) for name in COMMUNES]
    """
    return Region(title=title, params=params, url=url, country=country)


def from_extra_info(entries: Any) -> list[Region]:
    """Adapt legacy ``EXTRA_INFO`` dicts into :class:`Region` objects.

    A thin compatibility shim so the rest of the toolchain processes the typed
    ``Region`` structure only; the deprecated ``EXTRA_INFO`` dict shape
    (``{title, url?, country?, default_params?}``) is converted at the boundary
    rather than being a second native format.
    """
    if callable(entries):
        entries = entries()
    return [
        Region(
            title=entry.get("title", ""),
            params=entry.get("default_params", {}) or {},
            url=entry.get("url"),
            country=entry.get("country"),
        )
        for entry in (entries or [])
    ]
