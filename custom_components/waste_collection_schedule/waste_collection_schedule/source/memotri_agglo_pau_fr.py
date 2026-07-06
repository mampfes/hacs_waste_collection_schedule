import re
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests
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
from waste_collection_schedule import Collection, Icons
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
    "Ordures ménagères": Icons.GENERAL_WASTE,
    "Emballages et papiers": Icons.PAPER,
    "Matières compostables": Icons.ORGANIC,
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

    def _get_csrf_token(self, session: curl_requests.Session) -> str:
        """Get CSRF token from the home page."""
        r = session.get(BASE_URL + "/", timeout=15)
        if r.status_code == 404:
            raise SourceArgumentException(
                "address",
                "The website is temporarily unavailable or blocking automated requests. Please try again later.",
            )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
        if not csrf_input:
            raise SourceArgumentException(
                "address",
                "Unable to retrieve CSRF token from the website. The site may be temporarily unavailable.",
            )
        return csrf_input["value"]

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

        session = curl_requests.Session(impersonate="chrome131")

        csrf_token = self._get_csrf_token(session)

        # Submit form: select2 value format is 'banId&label'
        r = session.post(
            BASE_URL + "/",
            data={
                "csrfmiddlewaretoken": csrf_token,
                "select_adresse": f"{ban_id}&{label}",
            },
            headers={"Referer": BASE_URL + "/"},
            timeout=15,
            allow_redirects=True,
        )
        r.raise_for_status()

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
