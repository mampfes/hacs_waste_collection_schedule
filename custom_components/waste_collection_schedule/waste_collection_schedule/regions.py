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

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Region:
    """One region a source covers: PARAMS values plus optional display overrides.

    Args:
        title: Display name for the listing (e.g. the municipality).
        params: The source's ``PARAMS`` values that select this region.
        url: Optional listing URL override (defaults to the source's ``URL``).
        country: Optional country-code override (defaults to ``COUNTRY``).
        doc_filename: Optional per-region listing doc-link override (defaults
            to the source's own ``/doc/source/<id>.md``). Lets a source whose
            regions are documented on separate pages (e.g. one generated page
            per external provider) point each region's listing at its own doc.
        howto: Optional per-region custom howto override (``{lang: text}``),
            defaulting to the source's own ``HOWTO``/``HOW_TO_GET_ARGUMENTS_DESCRIPTION``.
        source_owners: Optional per-region codeowners override (``["@handle"]``),
            defaulting to the source's own ``SOURCE_CODEOWNERS``.
    """

    title: str
    params: dict[str, Any] = field(default_factory=dict)
    url: str | None = None
    country: str | None = None
    doc_filename: str | None = None
    howto: dict[str, str] | None = None
    source_owners: list[str] | None = None


def region(
    title: str,
    *,
    url: str | None = None,
    country: str | None = None,
    doc_filename: str | None = None,
    howto: dict[str, str] | None = None,
    source_owners: list[str] | None = None,
    **params: Any,
) -> Region:
    """Declare one region a source covers.

    Keyword args (other than ``url`` / ``country`` / ``doc_filename`` /
    ``howto`` / ``source_owners``) are the region's PARAMS values, e.g.::

        region("Mulhouse", commune="Mulhouse", quartier="Centre Ville")
        REGIONS = [region(name, commune=name) for name in COMMUNES]
    """
    return Region(
        title=title,
        params=params,
        url=url,
        country=country,
        doc_filename=doc_filename,
        howto=howto,
        source_owners=source_owners,
    )


REGISTRY_DIR = "doc/regions"


def _registry_path(name: str) -> Path:
    """Where a source's region registry lives, relative to the repo root.

    A seam: the repo root is four levels above this module, which is awkward to
    arrange in a test, so tests replace this rather than the path arithmetic.
    """
    return Path(__file__).resolve().parents[3] / REGISTRY_DIR / f"{name}.yaml"


def from_yaml(
    name: str,
    *,
    expand: str | None = None,
    title: str = "title",
    title_suffix: str | None = None,
    url: str = "url",
    country: str | None = None,
    **param_fields: str,
) -> "Callable[[], list[Region]]":
    """Load a source's regions from ``doc/regions/<name>.yaml``.

    For a platform covering dozens of providers, the registry is data, so keeping
    it as a Python literal means a code change to add a provider and a bespoke
    comprehension in every source that has one. This returns the callable form of
    ``REGIONS``, so the file is read lazily at doc-generation time::

        REGIONS = regions.from_yaml("abfall_io", key="service_id")

    reading a list of mappings::

        - title: Abfallwirtschaft Landkreis Harburg
          url: https://www.landkreis-harburg.de
          service_id: e0dd0aae0e2b0a0a1d1e5cf6c6b5a24d

    ``title``, ``url`` and ``country`` name the keys holding the listing metadata.
    Every other keyword maps a PARAMS field to the key holding its value, so
    ``key="service_id"`` means "the ``key`` param comes from the ``service_id``
    key". ``expand`` names a list-valued key that fans one entry out into a Region
    per element, for a provider serving several municipalities under one id; the
    element becomes each Region's title. ``title_suffix`` names a key whose value
    is then appended in parentheses, so a group of municipalities reached through
    one branded app is labelled once in the data rather than repeated per member.

    **Build-time only.** A HACS install ships ``custom_components/`` and not the
    repo's ``doc/`` tree, so a missing directory yields ``[]`` rather than an
    error, exactly as the ICS YAML listing does. That is safe because ``REGIONS``
    drives the generated README / ``sources.json`` listings, which the config flow
    then reads from JSON. A registry the source needs at *runtime* must not live
    here.
    """

    def load() -> list[Region]:
        path = _registry_path(name)
        if not path.is_file():
            return []

        import yaml

        with open(path, encoding="utf-8") as stream:
            entries = yaml.safe_load(stream) or []

        out: list[Region] = []
        for entry in entries:
            params = {
                field: entry[key] for field, key in param_fields.items() if key in entry
            }
            shared = {
                "url": entry.get(url),
                "country": entry.get(country) if country else None,
            }
            suffix = ""
            if title_suffix and entry.get(title_suffix):
                suffix = f" ({entry[title_suffix]})"
            if expand:
                for element in entry.get(expand, []):
                    out.append(
                        Region(title=f"{element}{suffix}", params=params, **shared)
                    )
            else:
                out.append(
                    Region(title=f"{entry[title]}{suffix}", params=params, **shared)
                )
        return out

    return load


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
