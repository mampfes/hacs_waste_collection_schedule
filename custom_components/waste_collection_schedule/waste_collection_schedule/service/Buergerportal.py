"""c-trace "Bürgerportal" citizen portal (buerger-portal-*.azurewebsites.net,
*.buergerportal.digital).

An OData/JSON cascade shared by several German waste-management operators
running the c-trace "Bürgerportal" product: resolve the district (an
``Ort``, optionally narrowed by an ``Ortsteil``) to its id, resolve the
street within that district to its id, then fetch the year's collection
dates for that street (and, where the deployment models it, a specific house
number).

Not to be confused with :mod:`waste_collection_schedule.service.CTrace`, a
different c-trace product (an ICS-calendar download behind an ASP.NET
session-cookie handshake, used by ``c_trace_de.py``). The two share a vendor
name and nothing else: this one is a bespoke per-operator REST API, not an
ICS export.

Each operator is its own Azure Web App (or, for ``biedenkopf``, its own
custom domain) running the same OData model, so only the base URL varies
between them; the request/response shapes are identical. Two schema
generations are live at once across the five deployments: the container
capacity is nested under ``GefaesstarifArt/VolumenObj`` on newer deployments
and ``GefaesstarifArt/Volumen`` on older ones, and a deployment answers with
HTTP 500 rather than an empty result when asked with the wrong one. Since
which generation a given operator runs is not documented anywhere and is not
a property the user can supply, :class:`BuergerportalRetriever` simply tries
the current shape first and falls back to the legacy one on a 500.
"""

import datetime
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

#: Per-operator API base URL. The key is the source's ``operator`` PARAMS value.
BASE_URLS: dict[str, str] = {
    "cochem_zell": "https://buerger-portal-cochemzell.azurewebsites.net/api",
    "alb_donau": "https://buerger-portal-albdonaukreisabfallwirtschaft.azurewebsites.net/api",
    "biedenkopf": "https://biedenkopfmzv.buergerportal.digital/api",
    "bedburg": "https://buerger-portal-bedburg.azurewebsites.net/api",
    "klevestadt": "https://buerger-portal-klevestadt.azurewebsites.net/api",
}

HEADERS = {
    "Accept": "application/json, text/plain;q=0.5",
    "Cache-Control": "no-cache",
}


def _quote_none(value: str | None) -> str:
    """Render an OData string literal, or the ``null`` keyword for ``None``."""
    return "null" if value is None else f"'{value}'"


def _api_base(source: BaseSource) -> str:
    return BASE_URLS[source.params["operator"]]


def resolve_district(source: BaseSource, keys: tuple) -> int:
    """District (``Ort`` + optional ``Ortsteil``) name -> its OData id.

    A LookupChainRetriever step: the first level of the cascade.
    """
    base = _api_base(source)
    response = source.session.get(
        f"{base}/OrteMitOrtsteilen",
        headers=HEADERS,
    )
    response.raise_for_status()
    entries = response.json()["d"]

    district = source.params["district"]
    subdistrict = source.params.get("subdistrict")

    for entry in entries:
        if entry["Ortsname"] == district and entry["Ortsteilname"] == subdistrict:
            return int(entry["OrteId"])

    district_matches = [entry for entry in entries if entry["Ortsname"] == district]
    if district_matches:
        raise SourceArgumentNotFoundWithSuggestions(
            "subdistrict",
            subdistrict,
            [entry["Ortsteilname"] for entry in district_matches],
        )
    raise SourceArgumentNotFoundWithSuggestions(
        "district",
        district,
        sorted({entry["Ortsname"] for entry in entries}),
    )


def resolve_street(source: BaseSource, keys: tuple) -> int:
    """Street name -> its OData id, within the already-resolved district.

    A LookupChainRetriever step: the second level of the cascade.
    """
    (district_id,) = keys
    base = _api_base(source)
    subdistrict = source.params.get("subdistrict")
    response = source.session.get(
        f"{base}/Strassen",
        params={
            "$filter": (
                f"Ort/OrteId eq {district_id} and "
                f"OrtsteilName eq {_quote_none(subdistrict)}"
            ),
            "$orderby": "Name asc",
        },
        headers=HEADERS,
    )
    response.raise_for_status()
    entries = response.json()["d"]

    street = source.params["street"]
    for entry in entries:
        if entry["Name"] == street:
            return int(entry["StrassenId"])

    raise SourceArgumentNotFoundWithSuggestions(
        "street", street, [entry["Name"] for entry in entries]
    )


def _schedule_query(
    district_id: int, street_id: int, number: Any, *, legacy_volume: bool
) -> dict[str, Any]:
    """The ``AbfuhrtermineAbJahr`` query string, in either schema generation."""
    volume_nav = "Volumen" if legacy_volume else "VolumenObj"
    query: dict[str, Any] = {
        "$expand": (
            f"Abfuhrplan,Abfuhrplan/GefaesstarifArt/Abfallart,"
            f"Abfuhrplan/GefaesstarifArt/{volume_nav}"
        ),
        "$orderby": (
            f"Abfuhrplan/GefaesstarifArt/Abfallart/Name,"
            f"Abfuhrplan/GefaesstarifArt/{volume_nav}/VolumenWert"
        ),
        "orteId": district_id,
        "strassenId": street_id,
        "jahr": datetime.date.today().year,
    }
    if number:
        query["hausNr"] = f"'{number}'"
    return query


class BuergerportalRetriever:
    """Resolve district -> street, then fetch that street's collection dates.

    Composes :func:`resolve_district` and :func:`resolve_street` (the
    two-level id cascade) and issues the final ``AbfuhrtermineAbJahr``
    request, retrying once with the legacy container-capacity schema if the
    deployment answers the current one with HTTP 500 (see the module
    docstring). Kept as its own retriever, rather than expressed with
    :class:`~waste_collection_schedule.retrievers.LookupChainRetriever`,
    because the schema fallback needs a second request *of the same
    cascade-resolved URL* rather than a fixed URL template.

    Pair with ``parsers.JsonParser("d")`` and a ``JsonTransformer`` reading
    ``Termin`` (a ``/Date(<ms>)/`` string) and the nested
    ``Abfuhrplan.GefaesstarifArt.Abfallart.Name``.
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def __call__(self, source: BaseSource):
        base = _api_base(source)
        district_id = resolve_district(source, ())
        street_id = resolve_street(source, (district_id,))
        number = source.params.get("number")

        response = source.session.get(
            f"{base}/AbfuhrtermineAbJahr",
            params=_schedule_query(district_id, street_id, number, legacy_volume=False),
            headers=HEADERS,
            timeout=self.timeout,
        )
        if response.status_code == 500:
            response = source.session.get(
                f"{base}/AbfuhrtermineAbJahr",
                params=_schedule_query(
                    district_id, street_id, number, legacy_volume=True
                ),
                headers=HEADERS,
                timeout=self.timeout,
            )
        response.raise_for_status()
        return response
