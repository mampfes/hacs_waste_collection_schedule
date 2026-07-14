import re
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Vatten och Miljöresurs"
DESCRIPTION = "Source for Vatten och Miljöresurs waste collection in Jämtland, Sweden."
URL = "https://www.vattenmiljoresurs.se"
COUNTRY = "se"

MUNICIPALITIES = {
    "bracke": "https://www.vattenmiljoresurs.se/bracke/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
    "berg": "https://www.vattenmiljoresurs.se/berg/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
    "harjedalen": "https://www.vattenmiljoresurs.se/harjedalen/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
}

TEST_CASES = {
    "Bräcke - Hantverksgatan 25": {
        "municipality": "bracke",
        "street_address": "Hantverksgatan 25",
    },
    "Berg - Balviken 550, Svenstavik": {
        "municipality": "berg",
        "street_address": "Balviken 550",
    },
    "Härjedalen - Algatan 3, Sveg": {
        "municipality": "harjedalen",
        "street_address": "Algatan 3",
    },
}

EXTRA_INFO = [
    {
        "title": "Bräcke",
        "url": "https://www.vattenmiljoresurs.se/bracke/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
        "country": "se",
        "default_params": {"municipality": "bracke"},
    },
    {
        "title": "Berg",
        "url": "https://www.vattenmiljoresurs.se/berg/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
        "country": "se",
        "default_params": {"municipality": "berg"},
    },
    {
        "title": "Härjedalen",
        "url": "https://www.vattenmiljoresurs.se/harjedalen/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
        "country": "se",
        "default_params": {"municipality": "harjedalen"},
    },
]

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality",
        "street_address": "Street address",
    },
    "de": {
        "municipality": "Gemeinde",
        "street_address": "Straßenadresse",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "One of: bracke, berg, harjedalen",
        "street_address": "Street address as listed on the provider website (e.g. 'Hantverksgatan 25')",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your address on the provider website for your municipality and enter it exactly as shown (street name and number).",
}

# Interval code -> number of matching dates to generate per year
_INTERVAL_WEEKS = {
    "h1": 1,  # every week
    "h2": 2,  # bi-weekly
    "h4": 4,  # every 4 weeks
}

# Weekday code -> Python weekday (Mon=0 ... Sun=6)
_WEEKDAY_MAP = {"1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6}


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _address_matches(search: str, candidate: str) -> bool:
    """Return True if *search* matches a potentially multi-number *candidate* entry."""
    search = _normalize(search)
    candidate = _normalize(candidate)

    if search == candidate:
        return True

    # Compare street names (everything before the first digit)
    candidate_street = re.sub(r"\d.*", "", candidate).strip()
    search_street = re.sub(r"\d.*", "", search).strip()

    if candidate_street != search_street:
        return False

    # Expand number ranges in the candidate entry (e.g. "169 -171" -> {169, 170, 171})
    candidate_numbers: set[str] = set()
    for match in re.findall(r"\d+(?:\s*-\s*\d+)?", candidate):
        if "-" in match:
            start, end = re.split(r"\s*-\s*", match)
            for n in range(int(start), int(end) + 1):
                candidate_numbers.add(str(n))
        else:
            candidate_numbers.add(match.strip())

    search_numbers = re.findall(r"\d+", search)
    return any(n in candidate_numbers for n in search_numbers)


def _collection_dates(freq_code: str) -> list[date]:
    """Convert a frequency code (e.g. 'h222') to a list of upcoming collection dates."""
    if len(freq_code) < 4 or not freq_code.startswith("h"):
        return []

    interval_key = freq_code[:2]  # h1 / h2 / h4
    odd_even = freq_code[2]  # 1 = odd weeks, 2 = even weeks
    weekday_code = freq_code[3]  # 1-7

    if weekday_code not in _WEEKDAY_MAP:
        return []

    target_weekday = _WEEKDAY_MAP[weekday_code]
    interval_weeks = _INTERVAL_WEEKS.get(interval_key)
    if interval_weeks is None:
        return []

    today = date.today()
    results: list[date] = []

    for offset in range(366):
        candidate = today + timedelta(days=offset)
        if candidate.weekday() != target_weekday:
            continue

        week_number = candidate.isocalendar().week

        if interval_key == "h1":
            results.append(candidate)
        elif interval_key == "h2":
            if (odd_even == "1" and week_number % 2 == 1) or (
                odd_even == "2" and week_number % 2 == 0
            ):
                results.append(candidate)
        elif interval_key == "h4":
            # Every 4 weeks: the odd_even digit encodes which week-mod-4 class
            week_mod = week_number % 4
            target_mod = int(odd_even) % 4
            if week_mod == target_mod:
                results.append(candidate)

    return results


class Source:
    def __init__(self, municipality: str, street_address: str):
        municipality = municipality.lower().strip()
        if municipality not in MUNICIPALITIES:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality",
                municipality,
                list(MUNICIPALITIES.keys()),
            )
        self._base_url = MUNICIPALITIES[municipality]
        self._street_address = street_address

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Establish a session cookie by loading the main page, and extract
        # the portlet target ID for the garbage-collection widget.
        r = session.get(
            self._base_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
        )
        r.raise_for_status()

        # Find the portlet target ID by locating the garbage-collection widget element
        # and reading the data-cid attribute from its child container.
        gc_idx = r.text.find("sv-garbage-collection")
        if gc_idx == -1:
            raise ValueError(
                "Could not locate the garbage-collection portlet on the provider page. "
                "The website layout may have changed."
            )
        match = re.search(r'data-cid="([^"]+)"', r.text[gc_idx : gc_idx + 600])
        if not match:
            raise ValueError(
                "Could not extract the portlet target ID from the provider page. "
                "The website layout may have changed."
            )
        target = match.group(1)

        ajax_url = (
            f"{self._base_url}"
            f"?sv.target={target}"
            f"&sv.{target}.route=/allAddresses"
            f"&svAjaxReqParam=ajax"
        )

        r2 = session.get(
            ajax_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json",
                "Referer": self._base_url,
            },
            timeout=20,
        )
        r2.raise_for_status()

        all_addresses = r2.json().get("allAddresses", [])

        # Find the entry matching the requested address
        matched = next(
            (
                entry
                for entry in all_addresses
                if _address_matches(self._street_address, entry.get("hamtstalle", ""))
            ),
            None,
        )

        if matched is None:
            raise SourceArgumentNotFound("street_address", self._street_address)

        freq_code = matched.get("tbfurenhkorlistarad_strtomningsfrekvenskod", "")
        collection_dates = _collection_dates(freq_code)

        return [
            Collection(date=d, t="Hushållsavfall", icon=Icons.GENERAL_WASTE)
            for d in collection_dates
        ]
