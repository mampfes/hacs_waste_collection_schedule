import json
import re

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

from ..service.ICS import ICS

TITLE = "AWISTA Kommunal GmbH (Düsseldorf)"
DESCRIPTION = "Source for AWISTA Kommunal GmbH, Düsseldorf, Germany."
URL = "https://www.awista-kommunal.de/abfallkalender"
COUNTRY = "de"

TEST_CASES = {
    "Merkurstraße 45": {"street": "Merkurstraße", "house_number": "45"},
    "Freiligrathstraße 19": {"street": "Freiligrathstraße", "house_number": "19"},
    "Sommersstraße 9 (UUID)": {"uuid": "5d1c4832-fd49-4fa7-a4e3-60dbe116cbc0"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Provide your 'street' and 'house_number' as you would type them into the "
        "address search at https://www.awista-kommunal.de/abfallkalender. "
        "Alternatively, search for your address on that page and copy the UUID "
        "from the browser URL bar (e.g. "
        "https://www.awista-kommunal.de/abfallkalender/<uuid>) into the 'uuid' "
        "argument; if 'uuid' is given, the address arguments are ignored."
    ),
    "de": (
        "Geben Sie 'street' (Straße) und 'house_number' (Hausnummer) so an, wie Sie "
        "sie in die Adresssuche auf "
        "https://www.awista-kommunal.de/abfallkalender eingeben würden. "
        "Alternativ können Sie Ihre Adresse auf dieser Seite suchen und die UUID aus "
        "der Adresszeile des Browsers kopieren (z. B. "
        "https://www.awista-kommunal.de/abfallkalender/<uuid>) und als Argument "
        "'uuid' angeben; wird 'uuid' angegeben, werden die Adressargumente ignoriert."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street",
        "house_number": "House number",
        "uuid": "UUID (optional)",
    },
    "de": {
        "street": "Straße",
        "house_number": "Hausnummer",
        "uuid": "UUID (optional)",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name, e.g. 'Merkurstraße'.",
        "house_number": "House number, e.g. '45'.",
        "uuid": "Pre-resolved address UUID. If set, the address lookup is skipped.",
    },
    "de": {
        "street": "Straßenname, z. B. 'Merkurstraße'.",
        "house_number": "Hausnummer, z. B. '45'.",
        "uuid": "Vorab aufgelöste Adress-UUID. Wenn gesetzt, entfällt die Adresssuche.",
    },
}

SOURCE_CODEOWNERS = ["@Zaunei"]

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Bioabfall": Icons.BIO_KITCHEN,
    "Papier": Icons.PAPER,
    "Wertstofftonne": Icons.RECYCLING,
}

DOMAIN = "https://www.awista-kommunal.de"
BASE_URL = f"{DOMAIN}/abfallkalender"


class Source:
    def __init__(
        self,
        street: str | None = None,
        house_number: str | None = None,
        uuid: str | None = None,
    ):
        self._street = street
        self._house_number = house_number
        self._uuid = uuid
        self._next_action: str | None = None
        self._action_candidates: list[str] | None = None
        self._ics = ICS()

        if not uuid and not (street and house_number):
            raise SourceArgumentRequired(
                "street",
                "either 'uuid' or both 'street' and 'house_number' must be provided.",
            )

    def _action_id_candidates(self, session: requests.Session) -> list[str]:
        """Scrape candidate Next.js server-action ids from the page's JS chunks.

        The bundles contain several 40+ hex strings tagged ``searchAddressAction``
        (the current id plus stale ones from older builds), so we collect every
        candidate rather than trusting the first match and let the caller
        validate which one the live deployment actually accepts.
        """
        if self._action_candidates is not None:
            return self._action_candidates

        page = session.get(BASE_URL, timeout=30)
        page.raise_for_status()

        # Script tags carry a `?dpl=<deployment>` query suffix, so match the
        # `.js` path and allow (and discard) the trailing query string.
        chunk_paths = re.findall(
            r'src="(/_next/static/chunks/[^"?]+\.js)(?:\?[^"]*)?"', page.text
        )

        candidates: list[str] = []
        for path in dict.fromkeys(chunk_paths):
            try:
                chunk = session.get(DOMAIN + path, timeout=30)
                chunk.raise_for_status()
            except requests.RequestException:
                continue

            for match in re.finditer(
                r'"([0-9a-f]{40,})"[\s\S]{0,120}?searchAddressAction', chunk.text
            ):
                if match.group(1) not in candidates:
                    candidates.append(match.group(1))

        self._action_candidates = candidates
        return candidates

    def _search_address(
        self, session: requests.Session, action: str, address: str
    ) -> dict | None:
        """Run the address search for one action id.

        Returns the parsed payload if ``action`` is honored by the live
        deployment, or ``None`` if the id is stale/invalid so the caller can
        fall through to the next candidate.
        """
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

    def _resolve_uuid(self, session: requests.Session) -> str:
        address = f"{self._street} {self._house_number}"

        candidates = self._action_id_candidates(session)
        # Prefer an id already validated on a previous fetch of this instance.
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
            raise RuntimeError(
                "Could not find a working searchAddressAction id at "
                f"{BASE_URL}; the site layout may have changed."
            )

        items = payload.get("items") or []
        if not items and payload.get("addressIdForQuery"):
            return payload["addressIdForQuery"]

        if not items:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                address,
                [],
            )

        return items[0]["id"]

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        uuid = self._uuid or self._resolve_uuid(session)

        response = session.get(f"{BASE_URL}/{uuid}/calendar.ics", timeout=30)
        response.raise_for_status()

        dates = self._ics.convert(response.text)

        entries: list[Collection] = []
        for d, summary in dates:
            # Summaries look like "Restmüll (Vollservice)"; strip the service-tier suffix.
            waste_type = summary.split(" (")[0].strip()
            icon = ICON_MAP.get(waste_type)
            entries.append(Collection(d, waste_type, icon=icon))

        return entries
