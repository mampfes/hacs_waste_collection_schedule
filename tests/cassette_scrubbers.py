"""Per-source trimming of a cassette at record time.

Some providers answer with one feed for every customer and offer no way to ask
for less (``sica_lu``'s ``/pickup-date`` lists every commune's collections,
about 7 MB). Recording that verbatim makes a multi-megabyte cassette per test
case. A scrubber registered here is run by ``record_fixtures.py`` on the live
interactions before they are written, and cuts such a response down to what the
test case actually reads, so re-recording reproduces the same trimmed cassette.

A scrubber only *removes* records from a recorded response; it never edits or
invents one. Register one only for a feed that cannot be filtered server side.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Callable
from typing import Any

Scrubber = Callable[[list[dict], dict[str, Any], str], None]


def _json(interaction: dict) -> Any:
    return json.loads(base64.b64decode(interaction["content_b64"]))


def _set_json(interaction: dict, value: Any) -> None:
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    interaction["content_b64"] = base64.b64encode(raw.encode("utf-8")).decode("ascii")


def _sica_lu(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Keep the configured commune's collections from the recording day on."""
    wanted = str(args["municipality"]).lower()
    ids = {
        item["name"]["en"].lower(): item["id"]
        for interaction in interactions
        if interaction["url"].endswith("/community")
        for community in _json(interaction).get("data", [])
        for item in [community, *community.get("children", [])]
        if not item["isDisabled"] and not item.get("children", [])
    }
    for interaction in interactions:
        if interaction["url"].endswith("/pickup-date"):
            _set_json(
                interaction,
                [
                    entry
                    for entry in _json(interaction)
                    if not entry["isDisabled"]
                    and entry["community_id"] == ids.get(wanted)
                    and entry["date"][:10] >= today
                ],
            )


SCRUBBERS: dict[str, Scrubber] = {
    "sica_lu": _sica_lu,
}


def for_case(
    module_name: str, args: dict[str, Any], today: str
) -> Callable[[list[dict]], None] | None:
    """The scrubber for one test case of ``module_name``, if it has one."""
    scrubber = SCRUBBERS.get(module_name)
    if scrubber is None:
        return None
    return lambda interactions: scrubber(interactions, args, today)
