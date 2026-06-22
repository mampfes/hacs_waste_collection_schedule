import datetime
from typing import TYPE_CHECKING

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


class AbfallIoGraphQLRetriever(RetrieverFunc):
    """Resolve the apiKey via the init call, then fetch the appointments.

    Reads ``key`` and ``idHouseNumber`` from ``source.params`` (and an optional
    ``wasteTypes`` filter); when no filter is given the provider's default
    checked waste types are used. Both requests run on the shared session.
    """

    def __call__(self, source: "BaseSource"):
        params = source.params
        key = params["key"]
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
        gql_headers = {
            **HEADERS,
            "Content-Type": "application/json",
            "x-abfallplus-api-key": api_key,
        }
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
