import re
from datetime import datetime
from typing import ClassVar, final
from zoneinfo import ZoneInfo

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

AJAX_URL = "https://ismaning.de/wp-admin/admin-ajax.php"
_HEADERS = {
    "x-requested-with": "XMLHttpRequest",
    "referer": "https://ismaning.de/umwelt-energie/abfall/abfallkalender/",
}


def _year() -> int:
    # Evaluated on every fetch: Home Assistant reuses the same Source instance,
    # so a year cached at construction would go stale after New Year.
    return datetime.now(ZoneInfo("Europe/Berlin")).year


def _ajax(**fields) -> dict:
    """An admin-ajax POST form; the year is always sent."""
    return {**fields, "year": _year()}


def _pick_street(response, *keys, street, **_) -> tuple[str, str]:
    """``(gebietsnummer, street name)`` of the configured street."""
    streets = re.findall(
        r'<option data-gebietsnummer="(\d+)">([^<]+)</option>', response.text
    )
    if not streets:
        raise SourceArgumentNotFound(
            "street", street, "Es wurden keine Straßen gefunden."
        )
    wanted = str(street).strip()
    if not wanted:
        raise SourceArgumentRequiredWithSuggestions(
            "street", "Bitte wählen Sie Ihre Straße.", [name for _, name in streets]
        )
    for gebiet, name in streets:
        if name.strip().casefold() == wanted.casefold():
            return gebiet, name.strip()
    raise SourceArgumentNotFoundWithSuggestions(
        "street", wanted, [name.strip() for _, name in streets]
    )


def _pick_street_type(response, *keys, **_) -> str:
    """ "1": the street is one area, "2": it is split into house-number ranges."""
    return response.text.strip()


def _needs_number(street_key, street_type, **_) -> bool:
    return street_type == "2"


def _pick_number(response, street_key, street_type, *, street_nr="", **_) -> str:
    options = re.findall(r"<option[^>]*>([^<]+)</option>", response.text)
    numbers = [o.strip() for o in options if o.strip() and o.strip() != "Bitte wählen"]
    wanted = str(street_nr or "").strip()
    if not wanted:
        raise SourceArgumentRequiredWithSuggestions(
            "street_nr", "Diese Straße benötigt eine Hausnummer.", numbers
        )
    if wanted not in numbers:
        raise SourceArgumentNotFoundWithSuggestions("street_nr", wanted, numbers)
    return wanted


def _calendar_data(street_key, street_type, number, **_) -> dict:
    data = _ajax(
        action="ics_non_notification_generation",
        street=street_key[1],
    )
    if number is not None:
        data["hnr"] = number
    return data


def _pick_ics_url(response, street_key, street_type, number, **_) -> str:
    url = response.text.strip()
    if not url.startswith("http"):
        raise SourceArgumentNotFound(
            "street",
            street_key[1],
            "Der Server konnte für diese Auswahl keinen Abfallkalender erstellen.",
        )
    return url


@final
class Source(BaseSource):
    TITLE = "Gemeinde Ismaning – Abfallkalender"
    DESCRIPTION = (
        "Source for the waste collection schedule of the community Ismaning, Germany."
    )
    URL = "https://ismaning.de/umwelt-energie/abfall/abfallkalender/"
    COUNTRY = "de"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@Kufi089"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Am Englischen Garten (ohne Hausnummer)": {"street": "Am Englischen Garten"},
        "Bahnhofstraße 5 (mit Hausnummer)": {
            "street": "Bahnhofstraße",
            "street_nr": "5",
        },
    }

    PARAMS = (
        street("street"),
        house_number("street_nr", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street. If the street requires a house number, enter it "
            "as well (only needed for streets that are split into house-number "
            "ranges; leave empty otherwise)."
        ),
        "de": (
            "Geben Sie Ihre Straße ein. Wenn die Straße eine Hausnummer benötigt, "
            "geben Sie diese ebenfalls an (nur für Straßen erforderlich, die in "
            "Hausnummernbereiche unterteilt sind; ansonsten leer lassen)."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                AJAX_URL,
                method="POST",
                data=lambda **_: _ajax(action="get_streets"),
                headers=_HEADERS,
                pick=_pick_street,
            ),
            Lookup(
                AJAX_URL,
                method="POST",
                data=lambda street_key, **_: _ajax(
                    action="iap_get_first_at_frontend", street=street_key[1]
                ),
                headers=_HEADERS,
                pick=_pick_street_type,
            ),
            Lookup(
                AJAX_URL,
                method="POST",
                data=lambda street_key, street_type, **_: _ajax(
                    action="iap_get_erg_by_second",
                    street=street_key[1],
                    gebietsnummer=street_key[0],
                ),
                headers=_HEADERS,
                when=_needs_number,
                pick=_pick_number,
            ),
            Lookup(
                AJAX_URL,
                method="POST",
                data=_calendar_data,
                headers=_HEADERS,
                pick=_pick_ics_url,
            ),
        ),
        url=lambda street_key, street_type, number, ics_url, **_: ics_url,
        headers=_HEADERS,
        encoding="utf-8",
        raise_for_status=True,
    )
    parse = IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Biotonne": wt.ORGANIC,
            "Papiertonne": wt.PAPER,
            "Gelber Sack": wt.RECYCLABLES,
            "Giftmobil": wt.HAZARDOUS,
            "Giftmobil-Samstag": wt.HAZARDOUS,
            "Giftmobil-Fischerhäuser": wt.HAZARDOUS,
            "Christbaumabholung": wt.GARDEN_WASTE,
            # Community-wide volunteer litter-picking day, not a bulky waste collection.
            "Rama-Dama": wt.OTHER,
        },
        carry_raw_label=True,
    )
