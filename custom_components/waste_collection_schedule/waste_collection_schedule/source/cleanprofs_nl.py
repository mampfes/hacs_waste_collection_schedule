from __future__ import annotations

from datetime import date

from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentExceptionMultiple


TITLE = "CleanProfs"
DESCRIPTION = "Container cleaning schedules provided by CleanProfs."
URL = "https://www.cleanprofs.nl"
COUNTRY = "nl"

API_URL = "https://cleanprofs.jmsdev.nl/api/get-plannings-address"


# For local use this may remain empty.
# For an upstream pull request Waste Collection Schedule requires at least
# one working TEST_CASE.
TEST_CASES = {}


PARAM_TRANSLATIONS = {
    "en": {
        "postal_code": "Postal code",
        "house_number": "House number",
        "suffix": "House number addition",
    },
    "nl": {
        "postal_code": "Postcode",
        "house_number": "Huisnummer",
        "suffix": "Toevoeging",
    },
}


PARAM_DESCRIPTIONS = {
    "en": {
        "postal_code": (
            "Dutch postal code of the address registered with CleanProfs, "
            "for example 1234AB."
        ),
        "house_number": "House number registered with CleanProfs.",
        "suffix": (
            "House number addition, if applicable. "
            "Leave empty when the address has no addition."
        ),
    },
    "nl": {
        "postal_code": (
            "Nederlandse postcode van het adres dat bij CleanProfs "
            "geregistreerd is, bijvoorbeeld 1234AB."
        ),
        "house_number": "Huisnummer dat bij CleanProfs geregistreerd is.",
        "suffix": (
            "Huisnummertoevoeging indien van toepassing. "
            "Laat leeg wanneer er geen toevoeging is."
        ),
    },
}


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the postal code, house number and optional house number "
        "addition of the address registered with CleanProfs."
    ),
    "nl": (
        "Vul de postcode, het huisnummer en eventueel de toevoeging in "
        "van het adres dat bij CleanProfs geregistreerd is."
    ),
}


def _get_icon(product_name: str) -> Icons | None:
    """Return a suitable icon for a CleanProfs product type."""

    product = product_name.strip().upper()

    if product == "GFT":
        return Icons.ORGANIC

    if product in {
        "RST",
        "REST",
        "RESTAFVAL",
    }:
        return Icons.GENERAL_WASTE

    if product in {
        "PBD",
        "PMD",
        "PLASTIC",
    }:
        return Icons.PLASTIC_PACKAGING

    if "GFT" in product:
        return Icons.ORGANIC

    if "REST" in product:
        return Icons.GENERAL_WASTE

    if (
        "PBD" in product
        or "PMD" in product
        or "PLASTIC" in product
    ):
        return Icons.PLASTIC_PACKAGING

    return None


class Source:
    def __init__(
        self,
        postal_code: str,
        house_number: str | int,
        suffix: str = "",
    ):
        self._postal_code = postal_code.replace(" ", "").strip().upper()
        self._house_number = str(house_number).strip()
        self._suffix = str(suffix or "").strip()

    def fetch(self) -> list[Collection]:
        """Fetch container cleaning dates from CleanProfs."""

        response = requests.get(
            API_URL,
            params={
                "zipcode": self._postal_code,
                "house_number": self._house_number,
                "suffix": self._suffix,
            },
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=30,
        )

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as err:
            raise ValueError(
                "CleanProfs returned an invalid JSON response."
            ) from err

        if not isinstance(data, list):
            raise ValueError(
                "CleanProfs returned an unexpected response format."
            )

        if not data:
            raise SourceArgumentExceptionMultiple(
                [
                    "postal_code",
                    "house_number",
                    "suffix",
                ],
                (
                    "CleanProfs returned no cleaning schedule for this "
                    "address. Check the postal code, house number and "
                    "addition and make sure the address is registered "
                    "with CleanProfs."
                ),
            )

        entries: list[Collection] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            product_name = str(
                item.get("product_name") or ""
            ).strip()

            full_date = str(
                item.get("full_date") or ""
            ).strip()

            if not product_name or not full_date:
                continue

            try:
                cleaning_date = date.fromisoformat(full_date)
            except ValueError:
                continue

            entries.append(
                Collection(
                    date=cleaning_date,
                    t=product_name,
                    icon=_get_icon(product_name),
                )
            )

        if not entries:
            raise ValueError(
                "CleanProfs returned data, but no valid cleaning "
                "schedule entries could be parsed."
            )

        return entries