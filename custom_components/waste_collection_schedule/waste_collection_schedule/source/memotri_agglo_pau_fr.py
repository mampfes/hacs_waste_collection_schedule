import hashlib
import re
from datetime import date, timedelta
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from dateutil.rrule import (
    FR,
    MO,
    SA,
    SU,
    TH,
    TU,
    WE,
    WEEKLY,
    rrule,
)
from dateutil.rrule import weekday as RRuleWeekday
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentRequired,
)

TITLE = "Mémotri - Agglomération Pau Béarn Pyrénées"
DESCRIPTION = "Source script for memotri.agglo-pau.fr"
URL = "https://memotri.agglo-pau.fr/"
COUNTRY = "fr"

GEOCODER_URL = "https://api-adresse.data.gouv.fr/search/"
BASE_URL = "https://memotri.agglo-pau.fr"

TEST_CASES = {
    "Pau - Avenue Larribau": {
        "address": "39 avenue larribau 64000 Pau",
    },
    "Idron - Rue de l'Industrie": {
        "address": "2 rue de l'Industrie 64320 Idron",
    },
}

ICON_MAP = {
    "Ordures ménagères": "mdi:trash-can",
    "Emballages et papiers": "mdi:recycle",
    "Matières compostables": "mdi:leaf",
}

WEEKDAY_MAP = {
    "lundi": MO,
    "mardi": TU,
    "mercredi": WE,
    "jeudi": TH,
    "vendredi": FR,
    "samedi": SA,
    "dimanche": SU,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full address including street number, e.g. '39 avenue larribau 64000 Pau'",
    },
    "fr": {
        "address": "Adresse complète avec numéro de rue, ex : '39 avenue larribau 64000 Pau'",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    },
    "fr": {
        "address": "Adresse",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your full address as you would on the memotri.agglo-pau.fr website, including street number, street name, postal code, and city.",
    "fr": "Saisissez votre adresse complète comme sur le site memotri.agglo-pau.fr, avec numéro de rue, nom de rue, code postal et ville.",
}


class Source:
    def __init__(self, address: str):
        normalized_address = address.strip() if isinstance(address, str) else address
        if not normalized_address:
            raise SourceArgumentRequired("address", "A non-empty address is required")
        self._address = normalized_address

    def _resolve_address(self) -> tuple[str, str]:
        """Resolve address to BAN ID (UUID) and label using French gov API."""
        params: dict[str, str | float | int] = {
            "q": self._address,
            "lat": 43.294,
            "lon": -0.370,
            "type": "housenumber",
            "limit": 1,
            "autocomplete": 0,
        }
        r = requests.get(GEOCODER_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        features = data.get("features", [])
        if not features:
            raise SourceArgumentException(
                "address",
                f"No address found for '{self._address}'. "
                "Make sure to include street number, street name, postal code and city.",
            )
        props = features[0]["properties"]
        ban_id = props.get("banId")
        label = props.get("label", self._address)
        if not ban_id:
            raise SourceArgumentException(
                "address",
                f"Address '{label}' was found but has no BAN ID. Try a more specific address.",
            )
        return ban_id, label

    def _solve_challenge(self, session: requests.Session) -> None:
        """Solve BunkerWeb proof-of-work challenge."""
        r = session.get(BASE_URL + "/", timeout=15, allow_redirects=True)
        r.raise_for_status()

        # Check if we already have access (no challenge)
        if "csrfmiddlewaretoken" in r.text or "memotri" in r.text.lower():
            if "Bot Detection" not in r.text:
                return

        # Extract nonce from challenge JavaScript
        nonce_match = re.search(r'digestMessage\("([^"]+)"\+a\.toString\(\)\)', r.text)
        if not nonce_match:
            return  # No challenge found, proceed

        nonce = nonce_match.group(1)

        # Find required prefix length
        prefix_match = re.search(r'startsWith\("(0+)"\)', r.text)
        prefix = prefix_match.group(1) if prefix_match else "0000"

        # Determine an iteration budget based on prefix length, with an upper bound
        max_iterations = min(50_000_000, 10 * (16 ** len(prefix)))

        # Solve proof-of-work
        found = False
        for i in range(max_iterations):
            h = hashlib.sha256((nonce + str(i)).encode()).hexdigest()
            if h.startswith(prefix):
                found = True
                break

        if not found:
            raise RuntimeError(
                "Proof-of-work solution not found within iteration limit"
            )

        # Submit solution
        response = session.post(
            BASE_URL + "/challenge",
            data={"challenge": str(i)},
            headers={"Referer": BASE_URL + "/challenge"},
            timeout=15,
            allow_redirects=True,
        )
        response.raise_for_status()
        if "Bot Detection" in response.text:
            raise RuntimeError("Proof-of-work challenge was not accepted by the server")

    def _parse_schedule(
        self, schedule_text: str
    ) -> list[tuple[RRuleWeekday, bool, bool]]:
        """Parse schedule text into list of (weekday, is_biweekly, is_biweekly_odd) tuples.

        Returns a dateutil.rrule weekday constant, a flag indicating whether it's
        biweekly (odd or even week), and a flag indicating whether it's an odd week.
        """
        text = schedule_text.lower().strip()

        # Remove time-of-day info and extra notes
        # Remove everything after line breaks or special characters
        text = text.split("\n")[0].strip()
        # Remove "matin", "après-midi", "soir"
        text = re.sub(r"\b(matin|après-midi|soir)\b", "", text).strip()

        is_biweekly_odd = "semaine impaire" in text
        is_biweekly_even = "semaine paire" in text
        is_biweekly = is_biweekly_odd or is_biweekly_even

        # Extract weekday
        weekday = None
        for day_name, day_const in WEEKDAY_MAP.items():
            if day_name in text:
                weekday = day_const
                break

        if weekday is None:
            return []

        return [(weekday, is_biweekly, is_biweekly_odd)]

    def fetch(self) -> list[Collection]:
        ban_id, label = self._resolve_address()

        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            }
        )

        self._solve_challenge(session)

        # Fetch collection schedule page
        encoded_label = quote(label, safe="")
        url = f"{BASE_URL}/consignes-tri/{ban_id}/{encoded_label}/"
        r = session.get(url, timeout=15)
        r.raise_for_status()

        if "Bot Detection" in r.text:
            raise SourceArgumentException(
                "address",
                "Unable to bypass bot protection. Please try again later.",
            )

        soup = BeautifulSoup(r.text, "html.parser")
        entries: list[Collection] = []

        # Parse waste collection divs
        divs = soup.find_all("div", class_="memotri")
        if not divs:
            raise SourceArgumentException(
                "address",
                "No waste collection information found for this address. "
                "The address may not be in the Pau agglomeration service area.",
            )

        for div in divs:
            b_tag = div.find("b")
            p_tag = div.find("p", class_="chapo")
            if not b_tag or not p_tag:
                continue

            waste_type = b_tag.text.strip()

            # Get only the direct text of the schedule (first text node)
            schedule_parts = []
            for child in p_tag.children:
                if isinstance(child, str):
                    text = child.strip()
                    if text:
                        schedule_parts.append(text)
                elif child.name == "br":
                    break  # Stop at first <br>
                elif child.name == "span":
                    break  # Stop at warning spans

            schedule_text = " ".join(schedule_parts)
            if not schedule_text:
                continue

            parsed = self._parse_schedule(schedule_text)
            for weekday, is_biweekly, is_odd_week in parsed:
                today = date.today()
                # Generate dates for the next 52 weeks
                all_dates = list(
                    rrule(
                        freq=WEEKLY,
                        dtstart=today - timedelta(days=7),
                        count=54,
                        byweekday=weekday,
                    )
                )

                for dt in all_dates:
                    d = dt.date()
                    if d < today:
                        continue

                    if is_biweekly:
                        iso_week = d.isocalendar()[1]
                        week_is_odd = iso_week % 2 == 1
                        if is_odd_week and not week_is_odd:
                            continue
                        if not is_odd_week and week_is_odd:
                            continue

                    entries.append(
                        Collection(
                            date=d,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )

        return entries
