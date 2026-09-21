import datetime
from typing import TYPE_CHECKING, Any

from ..exceptions import SourceArgumentRequired
from ..parsers import Parser
from ..retrievers import RetrieverFunc

if TYPE_CHECKING:
    from ..base_source import BaseSource


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# The abfall.io v3 API is a two-step GraphQL flow: GET "init" with the provider
# key for an apiKey (and the provider's default set of waste types), then POST
# the appointments query to the GraphQL endpoint with that apiKey as a header.
# That acquisition belongs to the platform, so it lives here as a retriever:
#
#     retrieve = AbfallIoGraphQLRetriever()
#     parse    = AbfallIoGraphQLParser()
#
# AbfallIoGraphQLRetriever runs both requests on the shared session and returns
# the GraphQL response; AbfallIoGraphQLParser pulls out data.appointments (and
# raises on a GraphQL error). The source then maps each appointment's waste-type
# name onto a canonical WasteType via the shared multilingual vocabulary.
# --------------------------------------------------------------------------- #

INIT_URL = "https://api.abfall.io"
GQL_URL = "https://widgets.abfall.io/graphql"
HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0"
}

APPOINTMENTS_QUERY = """
query Query($idHouseNumber: ID!, $wasteTypes: [ID], $dateMin: Date, $dateMax: Date, $showInactive: Boolean) {
    appointments(idHouseNumber: $idHouseNumber, wasteTypes: $wasteTypes, dateMin: $dateMin, dateMax: $dateMax, showInactive: $showInactive) {
        date
        wasteType {
            name
        }
    }
}
"""


def _origin_for(source_cls: Any, key: str) -> str | None:
    """Return the website of the region selected by ``key``, if declared.

    Some providers (e.g. KELL GmbH) enforce an Origin allowlist on their key and
    answer 401 to a GraphQL query that carries no matching Origin/Referer. The
    provider's own website is already declared as the region's ``url``.
    Resolved via the class (REGIONS may be a staticmethod, a plain function or a
    list). Keeps the provider registry in the source: this module holds no
    provider list.
    """
    regions: Any = getattr(source_cls, "REGIONS", [])
    if callable(regions):
        regions = regions()
    return next(
        (r.url.rstrip("/") for r in regions if r.url and r.params.get("key") == key),
        None,
    )


def _gql_headers(source_cls: Any, key: str, api_key: str) -> dict:
    headers = {
        **HEADERS,
        "Content-Type": "application/json",
        "x-abfallplus-api-key": api_key,
    }
    origin = _origin_for(source_cls, key)
    if origin:
        headers["Origin"] = origin
        headers["Referer"] = f"{origin}/"
    return headers


_CITIES_QUERY = """
query {
    cities(query: "") { id name idHouseNumber districtsCount appointmentsSupported }
}
"""
_CITY_QUERY = """
query ($id: ID!) {
    city(id: $id) {
        name idHouseNumber districtsCount
        districts { id name idHouseNumber }
        streets { id name idHouseNumber }
    }
}
"""
_DISTRICT_QUERY = """
query ($id: ID!) {
    district(id: $id) { name idHouseNumber streets { id name idHouseNumber } }
}
"""
_STREET_QUERY = """
query ($id: ID!, $idDistrict: ID) {
    street(id: $id) { name idHouseNumber houseNumbers(idDistrict: $idDistrict) { id name } }
}
"""


def list_choices(
    source_cls: Any, key: str, field: str, selections: dict
) -> list[tuple[str, str]]:
    """Walk the abfall.io v3 lookup and return one cascade level as (name, id).

    Levels: ``idCity`` -> ``idDistrict`` -> ``idStreet`` -> ``idHouseNumber``.
    The platform attaches the ``idHouseNumber`` the appointments query needs to
    whichever entity is deepest for that address: a city, a district, a street,
    or a house number of a street. Once a level carries it, the levels below it
    do not apply and return ``[]``, and the ``idHouseNumber`` level offers that
    one id, so the cascade always ends with the value the retriever reads.
    """
    from curl_cffi import requests as cffi_requests

    session = cffi_requests.Session(impersonate="chrome")
    r = session.get(INIT_URL, params={"key": key}, headers=HEADERS)
    if r.status_code != 200:
        return []
    headers = _gql_headers(source_cls, key, r.json()["apiKey"])

    def query(q: str, variables: dict | None = None) -> dict:
        resp = session.post(
            GQL_URL, json={"query": q, "variables": variables or {}}, headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        # Raise rather than return {}: an empty level reads as "not applicable"
        # and would silently skip the rest of the cascade.
        if "errors" in data:
            raise ValueError(f"GraphQL error: {data['errors']}")
        return data.get("data") or {}

    if field == "idCity":
        cities = query(_CITIES_QUERY).get("cities") or []
        return [(c["name"], c["id"]) for c in cities if c.get("appointmentsSupported")]

    id_city = selections.get("idCity")
    if not id_city:
        return []
    city = query(_CITY_QUERY, {"id": str(id_city)}).get("city") or {}
    # (label, idHouseNumber) of the level that settles the address, if any.
    settled = (
        (city["name"], city["idHouseNumber"]) if city.get("idHouseNumber") else None
    )

    if field == "idDistrict":
        if settled or not city.get("districtsCount"):
            return []
        return [(d["name"], d["id"]) for d in city.get("districts") or []]

    parent = city
    id_district = selections.get("idDistrict")
    # Ignore a district left over from another city (a reconfigure that changed
    # idCity keeps the old answer for the levels below it).
    if str(id_district) not in {str(d["id"]) for d in city.get("districts") or []}:
        id_district = None
    if not settled and id_district:
        parent = query(_DISTRICT_QUERY, {"id": str(id_district)}).get("district") or {}
        if parent.get("idHouseNumber"):
            settled = (parent["name"], parent["idHouseNumber"])

    if field == "idStreet":
        if settled:
            return []
        return [(s["name"], s["id"]) for s in parent.get("streets") or []]

    if field != "idHouseNumber":
        return []
    id_street = selections.get("idStreet")
    if not settled and id_street:
        street = (
            query(
                _STREET_QUERY,
                {
                    "id": str(id_street),
                    "idDistrict": str(id_district) if id_district else None,
                },
            ).get("street")
            or {}
        )
        if street.get("idHouseNumber"):
            settled = (street["name"], street["idHouseNumber"])
        else:
            return [(h["name"], h["id"]) for h in street.get("houseNumbers") or []]
    return [(settled[0], str(settled[1]))] if settled else []


class AbfallIoGraphQLRetriever(RetrieverFunc):
    """Resolve the apiKey via the init call, then fetch the appointments.

    Reads ``key`` and ``idHouseNumber`` from ``source.params`` (and an optional
    ``wasteTypes`` filter); when no filter is given the provider's default
    checked waste types are used. Both requests run on the shared session, with
    the region's Origin for providers that allowlist it (see ``_origin_for``).
    """

    def __call__(self, source: "BaseSource"):
        params = source.params
        key = params["key"]
        # The cascade makes every level optional in the form; only this one is
        # needed to fetch, so an address picked short of it fails clearly here.
        if params.get("idHouseNumber") in (None, ""):
            raise SourceArgumentRequired(
                "idHouseNumber", "select your address down to the house number"
            )
        id_house_number = str(params["idHouseNumber"])
        waste_types = params.get("wasteTypes")
        waste_types = [str(w) for w in waste_types] if waste_types else None
        session = source.session

        r = session.get(INIT_URL, params={"key": key}, headers=HEADERS)
        if r.status_code == 401:
            raise ValueError(
                f"API key '{key}' is not valid for the abfall.io v3 GraphQL API. "
                "Please check that you are using the correct key for your provider."
            )
        r.raise_for_status()
        config = r.json()
        api_key = config["apiKey"]

        if waste_types is None:
            waste_types = [
                wt["wasteType"]
                for wt in config["settings"].get("PUB_ABFALLTYPEN", [])
                if wt.get("checked", False)
            ]

        now = datetime.date.today()
        date_max = now + datetime.timedelta(days=365)
        gql_headers = _gql_headers(type(source), key, api_key)
        return session.post(
            GQL_URL,
            json={
                "query": APPOINTMENTS_QUERY,
                "variables": {
                    "idHouseNumber": id_house_number,
                    "wasteTypes": waste_types if waste_types else None,
                    "dateMin": now.isoformat(),
                    "dateMax": date_max.isoformat(),
                    "showInactive": False,
                },
            },
            headers=gql_headers,
        )


class AbfallIoGraphQLParser(Parser["list[dict]"]):
    """Return ``data.appointments`` from the GraphQL response.

    Raises ``ValueError`` if the response carries GraphQL ``errors``. Does no
    I/O, so it runs standalone against a cached response.
    """

    def __call__(self, response, source: "BaseSource | None" = None) -> "list[dict]":
        data = response.json()
        if "errors" in data:
            raise ValueError(f"GraphQL error: {data['errors']}")
        return data.get("data", {}).get("appointments", [])
