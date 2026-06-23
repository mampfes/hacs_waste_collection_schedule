from typing import TYPE_CHECKING

from ..parsers import Parser
from ..retrievers import RetrieverFunc

if TYPE_CHECKING:
    from ..base_source import BaseSource


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# CM City Media exposes a simple JSON dates endpoint keyed by the provider's
# homepage id and realm (with an optional district). That acquisition lives here
# as a retriever:
#
#     retrieve = CMCityMediaRetriever()
#     parse    = CMCityMediaParser()
#
# CMCityMediaRetriever reads hpid / realm / district from source.params and
# fetches on the shared session; CMCityMediaParser returns the schedule items.
# The source resolves each item's German type name onto a canonical WasteType
# via the shared multilingual vocabulary, so no per-region icon table is needed
# (the icon comes from the WasteType).
# --------------------------------------------------------------------------- #

API_URL = "http://slim.cmcitymedia.de/v1/{hpid}/waste/{realm}/dates"


class CMCityMediaRetriever(RetrieverFunc):
    """Fetch the dates feed for the configured hpid / realm (+ optional district)."""

    def __call__(self, source: "BaseSource"):
        params = source.params
        url = API_URL.format(hpid=params["hpid"], realm=params["realm"])
        district = params.get("district")
        return source.session.get(
            url, params={"district": district} if district else None
        )


class CMCityMediaParser(Parser["list[dict]"]):
    """Return the schedule items from the dates response. Does no I/O."""

    def __call__(self, response, source: "BaseSource | None" = None) -> "list[dict]":
        from waste_collection_schedule import response_shape

        data = response.json()
        response_shape.expect(
            isinstance(data, dict)
            and isinstance(data.get("result"), list)
            and len(data["result"]) > 1,
            source_name=response_shape.source_name(source),
            detail="CM City Media response missing result[1]",
            raw=data,
        )
        return data["result"][1]["items"]
