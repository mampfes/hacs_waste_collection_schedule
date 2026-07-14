"""AWISTA Kommunal GmbH (Düsseldorf), Germany.

Demonstrates: a Next.js single-page app whose address search is a React
Server Component "server action", not a documented REST endpoint. Resolving
an address to its calendar UUID means scraping the page for its JS chunk
files, fetching each one to regex out a 40+ hex-character server-action id
tagged ``searchAddressAction`` (several stale ids from older deployments are
usually present alongside the current one), then POSTing the address to that
action id with a ``next-action`` header until one is accepted -- a flow no
configured retriever expresses, so it stays a source-defined ``retrieve``.

The resolved action id is cached on the instance (as the legacy source did),
so a second ``fetch()`` on the same long-lived Source (HA re-polls the same
instance) skips re-scanning the JS bundle.
"""

import json
import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

DOMAIN = "https://www.awista-kommunal.de"
BASE_URL = f"{DOMAIN}/abfallkalender"

_CHUNK_PATH_RE = re.compile(r'src="(/_next/static/chunks/[^"?]+\.js)(?:\?[^"]*)?"')
_ACTION_ID_RE = re.compile(r'"([0-9a-f]{40,})"[\s\S]{0,120}?searchAddressAction')


def _clean_label(label: str) -> str:
    """Strip the service-tier suffix, e.g. "Restmüll (Vollservice)" -> "Restmüll"."""
    return label.split(" (")[0].strip()


@final
class Source(BaseSource):
    TITLE = "AWISTA Kommunal GmbH (Düsseldorf)"
    DESCRIPTION = "Source for AWISTA Kommunal GmbH, Düsseldorf, Germany."
    URL = "https://www.awista-kommunal.de/abfallkalender"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@Zaunei"]

    TEST_CASES: ClassVar[dict] = {
        "Merkurstraße 45": {"street": "Merkurstraße", "house_number": "45"},
        "Freiligrathstraße 19": {"street": "Freiligrathstraße", "house_number": "19"},
        "Sommersstraße 9 (UUID)": {"uuid": "5d1c4832-fd49-4fa7-a4e3-60dbe116cbc0"},
    }

    PARAMS = (
        alternatives(
            [text_field("uuid", "UUID")],
            [street(field="street"), house_number(field="house_number")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide 'street' and 'house_number' as you would type them into "
            "the address search at "
            "https://www.awista-kommunal.de/abfallkalender. Alternatively, "
            "search for your address on that page and copy the UUID from the "
            "browser URL bar (e.g. "
            "https://www.awista-kommunal.de/abfallkalender/<uuid>) into "
            "'uuid'; if 'uuid' is given, the address arguments are ignored."
        ),
    }

    parse = parsers.IcsParser()
    transform = ICSTransformer(
        clean=_clean_label,
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "Bioabfall": ORGANIC,
            "Papier": PAPER,
            "Wertstofftonne": RECYCLABLES,
        },
    )

    def __init__(
        self,
        street: "str | None" = None,
        house_number: "str | None" = None,
        uuid: "str | None" = None,
    ):
        super().__init__(street=street, house_number=house_number, uuid=uuid)
        self._action_candidates: list[str] | None = None
        self._next_action: str | None = None

    def _action_id_candidates(self, session) -> "list[str]":
        if self._action_candidates is not None:
            return self._action_candidates

        page = session.get(BASE_URL, timeout=30)
        page.raise_for_status()

        chunk_paths = _CHUNK_PATH_RE.findall(page.text)

        candidates: list[str] = []
        for path in dict.fromkeys(chunk_paths):
            try:
                chunk = session.get(DOMAIN + path, timeout=30)
                chunk.raise_for_status()
            except Exception:
                continue
            for match in _ACTION_ID_RE.finditer(chunk.text):
                if match.group(1) not in candidates:
                    candidates.append(match.group(1))

        self._action_candidates = candidates
        return candidates

    def _search_address(self, session, action: str, address: str) -> "dict | None":
        response = session.post(
            BASE_URL,
            headers={
                "content-type": "text/plain;charset=UTF-8",
                "accept": "text/x-component",
                "next-action": action,
            },
            data=json.dumps([address]),
            timeout=30,
        )
        if response.status_code != 200:
            return None
        for line in response.text.splitlines():
            if line.startswith("1:"):
                return json.loads(line[2:])
        return None

    def _resolve_uuid(self, session) -> str:
        street_val = self.params["street"]
        house_number_val = self.params["house_number"]
        address = f"{street_val} {house_number_val}"

        candidates = self._action_id_candidates(session)
        if self._next_action and self._next_action in candidates:
            candidates = [self._next_action] + [
                c for c in candidates if c != self._next_action
            ]

        payload: dict | None = None
        for action in candidates:
            payload = self._search_address(session, action, address)
            if payload is not None:
                self._next_action = action
                break

        if payload is None:
            raise SourceArgumentNotFoundWithSuggestions("street", address, [])

        items = payload.get("items") or []
        if not items and payload.get("addressIdForQuery"):
            return payload["addressIdForQuery"]

        if not items:
            raise SourceArgumentNotFoundWithSuggestions("street", address, [])

        return items[0]["id"]

    def retrieve(self, source):
        session = self.session
        uuid = self.params.get("uuid") or self._resolve_uuid(session)
        r = session.get(f"{BASE_URL}/{uuid}/calendar.ics", timeout=30)
        r.raise_for_status()
        return r
