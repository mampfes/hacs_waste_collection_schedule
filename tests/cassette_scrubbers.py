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
import re
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


def _chesterfield_gov_uk(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Keep only the Aura ``context`` of the Lightning Out bootstrap (~450 KB)."""
    for interaction in interactions:
        if interaction["url"].endswith(".app"):
            context = _json(interaction)["auraConfig"]["context"]
            _set_json(interaction, {"auraConfig": {"context": context}})


def _afvalstoffendienst_nl(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Keep only the waste streams the calendars refer to (each carries an SVG)."""
    used = {
        entry["afvalstroom_id"]
        for interaction in interactions
        if "/kalender/" in interaction["url"]
        for entry in _json(interaction)
    }
    for interaction in interactions:
        if interaction["url"].endswith("/afvalstromen"):
            _set_json(interaction, [s for s in _json(interaction) if s["id"] in used])


def _cem_ambiente_it(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Keep only the configured municipality and street of the two index lists.

    ``listComuni`` carries every municipality's full profile (~400 KB) and
    ``listVie`` every street; the schedule request is the only thing a replay
    needs besides the two rows that resolve the arguments.
    """
    wanted = {"listComuni": args["city"], "listVie": args["street"]}
    for interaction in interactions:
        endpoint = interaction["url"].rsplit("/", 1)[-1]
        if endpoint in wanted:
            data = _json(interaction)
            name = str(wanted[endpoint]).strip().casefold()
            data["body"] = [
                row for row in data["body"] if str(row["nome"]).casefold() == name
            ]
            _set_json(interaction, data)


def _czystyregion_pl(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Cut each page of the cascade (~250 KB of site chrome apiece) to what is read.

    The form page keeps its CSRF token, the commune dropdown and the ``regiony``
    list, the result page its schedule table, the schedule page its ``events``.
    """
    patterns = (
        r'name="_token" value="[^"]*"',
        r'id="gminy"[^>]*>.*?</select>',
        r"var regiony = \[.*?\];",
        r'<table id="harmonogramy".*?</table>',
        r"events:\s*JSON\.parse\(`.*?`\)",
    )
    for interaction in interactions:
        text = base64.b64decode(interaction["content_b64"]).decode("utf-8")
        kept = [
            match.group(0)
            for pattern in patterns
            for match in [re.search(pattern, text, re.S)]
            if match
        ]
        raw = "<html><body>" + "\n".join(kept) + "</body></html>"
        interaction["content_b64"] = base64.b64encode(raw.encode("utf-8")).decode(
            "ascii"
        )


_PLAIN_DAY = re.compile(
    r'\s*<td data-date="[^"]*" class="(?![^"]*highlighted)[^"]*">\d+</td>'
)


def _gmina_sroda_slaska_pl(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Drop the calendar cells that are not collection days, and page chrome."""
    for interaction in interactions:
        html = base64.b64decode(interaction["content_b64"]).decode("utf-8")
        html = _PLAIN_DAY.sub("", html)
        html = re.sub(r"[^\n]*data:image/[^\n]*\n", "", html)
        html = re.sub(r'<ul class="nav-bar vertical">.*?</ul>', "", html, flags=re.S)
        html = re.sub(r"<script.*?</script>", "", html, flags=re.S)
        interaction["content_b64"] = base64.b64encode(html.encode("utf-8")).decode(
            "ascii"
        )


def _smiecioplan_pl(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Drop the ICS export's reminder alarms and events before the recording day."""
    day = today.replace("-", "")
    for interaction in interactions:
        if not interaction["url"].endswith("/export/ics"):
            continue
        text = base64.b64decode(interaction["content_b64"]).decode("utf-8")
        text = re.sub(r"BEGIN:VALARM.*?END:VALARM\r?\n", "", text, flags=re.S)
        text = re.sub(
            r"BEGIN:VEVENT(?:(?!END:VEVENT).)*?DTSTART;VALUE=DATE:(\d{8})"
            r"(?:(?!END:VEVENT).)*?END:VEVENT\r?\n",
            lambda m: m.group(0) if m.group(1) >= day else "",
            text,
            flags=re.S,
        )
        interaction["content_b64"] = base64.b64encode(text.encode("utf-8")).decode(
            "ascii"
        )


def _valorlux_lu(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Keep only the configured commune of the all-communes calendar (~80 KB)."""
    for interaction in interactions:
        if interaction["url"].endswith("/api/calendar/all"):
            cities = _json(interaction)["cities"]
            commune = args["commune"]
            _set_json(interaction, {"cities": {commune: cities[commune]}})


def _potsdam_de(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Keep only the configured street of the 17 MB all-streets page data."""

    def norm(value: Any) -> str:
        return str(value or "").lower().strip()

    for interaction in interactions:
        if not interaction["url"].endswith("page-data.json"):
            continue
        payload = _json(interaction)
        dbapi = payload["result"]["data"]["dbapi"]
        region = dbapi["allRegionen"][0]["regionen"][0]
        region["ortsteile"] = [
            {
                **district,
                "strassen": [
                    street
                    for street in district["strassen"]
                    if norm(street["name"]) == norm(args["strasse"])
                ],
            }
            for district in region["ortsteile"]
            if norm(district["name"]) == norm(args["ortsteil"])
        ]
        dbapi["allFeiertage"] = []
        _set_json(interaction, payload)


SCRUBBERS: dict[str, Scrubber] = {
    "potsdam_de": _potsdam_de,
    "valorlux_lu": _valorlux_lu,
    "smiecioplan_pl": _smiecioplan_pl,
    "afvalstoffendienst_nl": _afvalstoffendienst_nl,
    "cem_ambiente_it": _cem_ambiente_it,
    "czystyregion_pl": _czystyregion_pl,
    "gmina_sroda_slaska_pl": _gmina_sroda_slaska_pl,
    "sica_lu": _sica_lu,
    "chesterfield_gov_uk": _chesterfield_gov_uk,
}


def for_case(
    module_name: str, args: dict[str, Any], today: str
) -> Callable[[list[dict]], None] | None:
    """The scrubber for one test case of ``module_name``, if it has one."""
    scrubber = SCRUBBERS.get(module_name)
    if scrubber is None:
        return None
    return lambda interactions: scrubber(interactions, args, today)
