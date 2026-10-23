import uuid
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)
from waste_collection_schedule.transformers import JsonTransformer

# The Omrin Afvalapp backend: an anonymous login by address answers an access
# token, which the GraphQL endpoint takes as a bearer token.
_API = "https://api.omrinafvalapp.nl"

_CALENDAR_QUERY = """
query FetchCalendar {
  fetchCalendar {
    id
    date
    description
    type
    containerType
    placingTime
    state
  }
}
"""

# Dates the backend leaves unset carry this value.
_SENTINEL_DATE = "0001-01-01T00:00:00"


def _postal_code(postal_code: str) -> str:
    return postal_code.replace(" ", "").upper()


def _house_number(house_number) -> int:
    try:
        return int(house_number)
    except (TypeError, ValueError) as exc:
        raise SourceArgumentException(
            "house_number", "House number must be numeric."
        ) from exc


def _suffix(suffix) -> str:
    return (suffix or "").strip()


def _login_body(*_keys, postal_code, house_number, suffix=None, **_) -> dict:
    postal = _postal_code(postal_code)
    number = _house_number(house_number)
    extension = _suffix(suffix)
    return {
        "Email": None,
        "Password": None,
        "PostalCode": postal,
        "HouseNumber": number,
        "HouseNumberExtension": extension,
        # The app registers a device per install; one id per address keeps the
        # request reproducible.
        "DeviceId": str(uuid.uuid5(uuid.NAMESPACE_URL, f"omrin:{postal}{number}")),
        "Platform": "iOS",
        "AppVersion": "4.0.3.273",
        "OsVersion": "iPhone15,3 26.2.1",
    }


def _access_token(response, *_keys, **_) -> str:
    payload = response.json()
    if not payload.get("success"):
        raise SourceArgumentNotFound(
            "postal_code",
            f"Omrin could not find this address: {payload.get('errors') or 'unknown error'}",
        )
    return payload["data"]["accessToken"]


def _is_dated(record, _source=None) -> bool:
    return bool(record.get("date")) and record["date"] != _SENTINEL_DATE


@final
class Source(BaseSource):
    TITLE = "Omrin"
    DESCRIPTION = "Source for Omrin waste collection schedules."
    URL = "https://www.omrin.nl"
    COUNTRY = "nl"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Weme 3, Ermelo": {
            "postal_code": "3851MA",
            "house_number": "3",
            "suffix": "",
        },
    }

    PARAMS = (
        postcode(postcode_field="postal_code", house_field="house_number"),
        text_field("suffix", "House number suffix", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the postcode, house number and, if you have one, the house "
            "number suffix of your address, as in the Omrin Afvalapp."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.PAPER]

    retrieve = retrievers.Request(
        f"{_API}/graphql",
        method="POST",
        json={"query": _CALENDAR_QUERY},
        headers=lambda token, **_: {
            "Content-Type": "application/json",
            "User-Agent": "GraphQL.Client/6.1.0.0",
            "Authorization": f"Bearer {token}",
        },
        before=(
            retrievers.Lookup(
                f"{_API}/api/auth/login",
                method="POST",
                json=_login_body,
                headers={
                    "User-Agent": "Omrin.Afvalapp.Client/1.0",
                    "Accept": "application/json",
                },
                pick=_access_token,
            ),
        ),
    )

    parse = parsers.JsonParser("data", "fetchCalendar")
    preprocess = preprocessors.Compose(
        preprocessors.RowFilter(_is_dated),
        preprocessors.Deduplicate(key=lambda record: (record["date"], record["type"])),
    )
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "GFT": wt.ORGANIC,
            "PAPIER": wt.PAPER,
            "PMD": wt.RECYCLABLES,
            "RESTAFVAL": wt.GENERAL_WASTE,
            "Sortibak": wt.GENERAL_WASTE,
        },
    )
