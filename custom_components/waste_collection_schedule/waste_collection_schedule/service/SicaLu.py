"""The SICA app backend (``dashboard.sicaapp.lu``) of the Luxembourg syndicate.

Two public JSON endpoints under ``/api/api/app``: ``/community`` lists the
served communes (a syndicate such as "Community Mamer" carries its communes as
``children``), and ``/pickup-date`` lists every enabled collection of *all*
communes, each tagged with its ``community_id``. The feed cannot be filtered
server side, so :class:`SicaParser` reads both responses, resolves the
configured commune to its id and keeps that commune's collections.
"""

from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import FanOutRetriever, Request

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

API_URL = "https://dashboard.sicaapp.lu/api/api/app"
COMMUNITY_URL = f"{API_URL}/community"
PICKUP_URL = f"{API_URL}/pickup-date"
HEADERS = {"User-Agent": "SicaAPP", "Accept": "application/json"}

#: the commune list first, then the collections of every commune
retriever = FanOutRetriever(
    targets=lambda source, context: [COMMUNITY_URL, PICKUP_URL],
    fetch=Request(lambda url, context, **_: url, headers=HEADERS),
)


class SicaParser(Parser["list[dict[str, Any]]"]):
    """The enabled collection entries of the configured commune."""

    def __init__(self, argument: str = "municipality"):
        self.argument = argument

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[dict[str, Any]]":
        community_response, pickup_response = response
        communities = community_response.json()
        if not isinstance(communities, dict):
            raise ValueError(f"Unexpected data type: {type(communities)}")
        entries = pickup_response.json()
        if not isinstance(entries, list):
            raise ValueError(f"Unexpected data type: {type(entries)}")

        ids: dict[str, int] = {
            item["name"]["en"].lower(): item["id"]
            for community in communities.get("data", [])
            for item in [community, *community.get("children", [])]
            if not item["isDisabled"] and not item.get("children", [])
        }
        wanted = str(source.params[self.argument] if source else "").lower()
        community_id = ids.get(wanted)
        if not community_id:
            raise SourceArgumentNotFoundWithSuggestions(
                self.argument, wanted, list(ids.keys())
            )
        return [
            entry
            for entry in entries
            if not entry["isDisabled"] and entry["community_id"] == community_id
        ]
