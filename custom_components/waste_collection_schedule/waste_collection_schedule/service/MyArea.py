"""My Area bin-summary cards and optional WebAspx round calendars."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup, Tag

from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.service.WebAspxCollections import CalendarParser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

CALENDAR_HOST = "collections-southnorfolk.azurewebsites.net"


def bins_card(response: Any) -> Tag:
    page = BeautifulSoup(response.text, "html.parser")
    heading = page.find("h3", string="Bins")
    if heading is None or heading.parent is None:
        raise ValueError("My Area response has no Bins card")
    return heading.parent


def calendar_uprn(response: Any) -> str | None:
    link = bins_card(response).find(
        "a", href=lambda href: bool(href and CALENDAR_HOST in href)
    )
    if link is None:
        return None
    match = re.search(r"UPRN=(\d+)", str(link.get("href") or ""))
    return match.group(1) if match else None


class MyAreaParser(Parser["list[dict[str, str]]"]):
    """Prefer the linked calendar over summary dates that can conflate rounds."""

    def __call__(
        self, responses: Any, source: BaseSource | None = None
    ) -> list[dict[str, str]]:
        if len(responses) > 1:
            return CalendarParser()(responses[1], source)
        records = []
        for category in bins_card(responses[0]).select("div.card-text"):
            children = tuple(category.children)
            if len(children) < 4 or not isinstance(children[1], Tag):
                raise ValueError("Malformed My Area bin summary")
            records.append(
                {
                    "date": str(children[3]).strip(),
                    "type": children[1].get_text(strip=True),
                }
            )
        return records
