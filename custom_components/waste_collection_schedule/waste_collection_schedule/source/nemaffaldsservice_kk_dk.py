import re
from urllib.parse import parse_qs, urlparse

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Nem Affaldsservice (Københavns Kommune)"
DESCRIPTION = "Source for Nem Affaldsservice, the waste collection schedule service of Københavns Kommune (City of Copenhagen), Denmark."
URL = "https://nemaffaldsservice.kk.dk"
COUNTRY = "dk"
TEST_CASES = {
    "Nørrebrogade 10": {"address": "Nørrebrogade 10"},
    "Amagerbrogade 10": {"address": "Amagerbrogade 10"},
    "Rådhuspladsen 1": {"address": "Rådhuspladsen 1"},
}

BASE_URL = "https://nemaffaldsservice.kk.dk"
ADDRESS_LOOKUP_URL = f"{BASE_URL}/WasteHome/AddressByTerm/"
CUSTOMER_LOOKUP_URL = f"{BASE_URL}/WasteHome/SearchCustomerRelation"
CALENDAR_URL = f"{BASE_URL}/Calendar/GetICaldendar"

HEADERS = {"User-Agent": "Mozilla/5.0"}

TOKEN_RE = re.compile(
    r'name="__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"'
)

ICON_MAP = {
    "Restaffald": Icons.GENERAL_WASTE,
    "Madaffald": Icons.BIO_KITCHEN,
    "Bioposer": Icons.BIO_KITCHEN,
    "Papir": Icons.PAPER,
    "Pap": Icons.PAPER,
    "Glas": Icons.GLASS,
    "Metal": Icons.METAL,
    "Plast": Icons.PLASTIC_PACKAGING,
    "Elektronik": Icons.ELECTRONICS,
    "Farligt affald": Icons.HAZARDOUS,
    "Tekstil": Icons.TEXTILE,
    "Storskrald": Icons.BULKY,
    "Haveaffald": Icons.GARDEN,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your address exactly as it appears in Denmark, e.g. "
        "'Nørrebrogade 10'. You can verify the spelling by typing your street "
        "and house number into the search box on "
        "https://nemaffaldsservice.kk.dk/ - if the site offers your address as "
        "an autocomplete suggestion, that exact text is what should be used "
        "here. If the address cannot be found, the resulting error message "
        "will list similar addresses to help you find the correct spelling."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": (
            "Street name and house number, e.g. 'Nørrebrogade 10'. Must match "
            "an address served by Københavns Kommune / Nem Affaldsservice."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    },
}


class Source:
    def __init__(self, address: str):
        self._address: str = address.strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(HEADERS)

        customer_id = self._get_customer_id(session, self._address)

        r = session.get(CALENDAR_URL, params={"customerId": customer_id})
        r.raise_for_status()

        ics = ICS()
        entries = []
        for ev in ics.convert_events(r.text):
            entries.append(
                Collection(
                    ev.date,
                    ev.title,
                    icon=ICON_MAP.get(ev.title),
                )
            )
        return entries

    def _get_customer_id(self, session: requests.Session, address: str) -> str:
        # Resolve/validate the address against the site's own autocomplete
        # endpoint first, so we can offer useful suggestions on a typo/mismatch
        # instead of silently searching for a wrong address.
        suggestions_r = session.get(ADDRESS_LOOKUP_URL, params={"term": address})
        suggestions_r.raise_for_status()
        suggestions = suggestions_r.json() or []

        matched_address = None
        labels = []
        for suggestion in suggestions:
            if not suggestion.get("fullAdress"):
                continue
            label = suggestion.get("label", "")
            labels.append(label)
            if label.lower() == address.lower():
                matched_address = label
                break

        if matched_address is None:
            raise SourceArgumentNotFoundWithSuggestions("address", address, labels)

        home_r = session.get(BASE_URL)
        home_r.raise_for_status()
        token_match = TOKEN_RE.search(home_r.text)
        if token_match is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                address,
                [],
            )
        token = token_match.group(1)

        search_r = session.post(
            CUSTOMER_LOOKUP_URL,
            data={
                "SearchTerm": matched_address,
                "__RequestVerificationToken": token,
            },
        )
        search_r.raise_for_status()

        customer_id = parse_qs(urlparse(search_r.url).query).get("customerId")
        if not customer_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "address", address, [matched_address]
            )

        return customer_id[0]
