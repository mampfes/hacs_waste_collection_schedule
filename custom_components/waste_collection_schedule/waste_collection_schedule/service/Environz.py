"""The Environz ``nextservicedate`` API behind New Zealand councils' bin apps.

Central Otago and Dunedin (and other Environz customers) share one Azure
function per council, ``environz-api.azurewebsites.net/api/<council>/nextservicedate``,
guarded by a per-council key that the councils' own apps ship. One GET per
address answers with the next year of collections, one ``route<CODE>`` key per
round holding ``{index: "dd/mm/yyyy"}``; a round the address does not have is
``null`` or empty, and an unknown address is a 400.
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from waste_collection_schedule import response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import HttpGetRetriever

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

# The three-letter round codes of the ``route<CODE>`` keys.
TYPE_VALUE_MAP = {
    "REF": wt.GENERAL_WASTE,
    "REC": wt.RECYCLABLES,
    "GLA": wt.GLASS,
    "FOD": wt.FOOD_WASTE,
    "ORG": wt.ORGANIC,
    "GRN": wt.GARDEN_WASTE,
}


def normalise_address(address: Any) -> str:
    """The API writes a unit range "2/90 Harbour Terrace"; the app shows "2 - 90 ..."."""
    text = str(address).strip()
    parts = text.split("-")
    if len(parts) > 1 and parts[0].strip().isdigit():
        parts = [parts[0].strip() + "/" + parts[1].strip(), *parts[2:]]
    return "-".join(parts)


def next_service_date_retriever(council: str, key: str) -> HttpGetRetriever:
    """The year of collections for the ``address`` param, from ``council``."""
    return HttpGetRetriever(
        url=f"https://environz-api.azurewebsites.net/api/{council}/nextservicedate",
        params=lambda address, **_: {
            "code": key,
            "address": normalise_address(address),
            "endDate": (datetime.now() + timedelta(days=365)).strftime("%d/%m/%Y"),
            "postcode": "",
        },
        headers={"user-agent": "Mozilla/5.0"},
    )


class RoutesParser(Parser["list[dict[str, str]]"]):
    """One ``{"type", "date"}`` record per date of each ``route<CODE>`` key."""

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[dict[str, str]]":
        if response.status_code == 400:
            address = source.params.get("address") if source else None
            raise SourceArgumentNotFound(
                argument="address",
                value=normalise_address(address),
                message_addition="make sure the address matches one that has a schedule in the council's bin app.",
            )
        response.raise_for_status()
        data = response.json()
        response_shape.expect(
            isinstance(data, dict),
            source_name=response_shape.source_name(source),
            detail="nextservicedate reply is not a mapping of routes",
            raw=response.text,
        )
        return [
            {"type": key.removeprefix("route").strip(), "date": date}
            for key, dates in data.items()
            if key.startswith("route") and dates
            for date in dates.values()
        ]
