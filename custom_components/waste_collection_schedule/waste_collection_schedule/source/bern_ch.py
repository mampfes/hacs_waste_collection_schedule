"""Entsorgung + Recycling Stadt Bern (bern.ch).

Demonstrates ``IcsSessionRetriever`` for a calendar keyed by an opaque per-address
key that the user may either paste in directly or leave the source to find. The
lookup step therefore runs only when no ``key`` was given (``when``): it asks the
official address search for the key and, since that typeahead caps its result
list at 20 entries and so says nothing about whether a house number exists, falls
back to the documented derivation (MD5 of street and number, no separator). The
calendar request then answers an unknown key with HTTP 500, which ``argument``
turns into an error on the field the user actually filled in.

The feed bounds each recurrence with ``UNTIL=<Dec 31>T230000Z``, which for
all-day events is 00:00 local time on Jan 1 and would yield a phantom New Year's
Day collection; ``clip_to_until`` drops it. Its empty ``EXDATE:`` lines are
repaired by the shared ICS conversion.
"""

import hashlib
from typing import Any, ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://bernentsorgung.glue.ch/erb/web"
_SEARCH_URL = f"{_API_URL}/searchAddress"
_ICAL_URL = f"{_API_URL}/ical"


def _search(strasse: str, **_: Any) -> "dict[str, str]":
    return {"query": strasse.strip()}


def _address_key(response: Any, context: "dict[str, Any]") -> "dict[str, str]":
    """The calendar key of the configured address.

    The official search's key where it lists the house number, otherwise the
    documented MD5 derivation.
    """
    strasse = str(context["strasse"]).strip()
    hnr = str(context["hnr"]).strip()
    try:
        addresses = response.json()
    except ValueError:
        addresses = []

    # The endpoint is a typeahead: it matches street name prefixes and can
    # return several streets at once, so keep only the requested street.
    for address in addresses:
        if (
            isinstance(address, dict)
            and str(address.get("street", "")).lower() == strasse.lower()
            and str(address.get("number", "")).lower() == hnr.lower()
            and address.get("key")
        ):
            return {"calendar_key": str(address["key"])}

    return {"calendar_key": hashlib.md5(f"{strasse}{hnr}".encode()).hexdigest().upper()}


@final
class Source(BaseSource):
    TITLE = "Entsorgung + Recycling Stadt Bern"
    DESCRIPTION = "Source for waste collection in the city of Bern, Switzerland."
    URL = "https://www.bern.ch/themen/umwelt-natur-und-energie/abfall-und-recycling"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@sbaerlocher"]

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.PAPER, wt.ORGANIC]

    TEST_CASES: ClassVar[dict] = {
        "Bundesplatz 1 (Bundeshaus)": {"strasse": "Bundesplatz", "hnr": 1},
        "Helvetiaplatz 5 (Historisches Museum)": {"strasse": "Helvetiaplatz", "hnr": 5},
        "Waisenhausplatz 30 (Polizeiwache)": {"strasse": "Waisenhausplatz", "hnr": 30},
        "Key only (Bundesplatz 1)": {"key": "DC46354136EE5531B312A864FA2C4604"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"strasse": "Nirgendwostrasse", "hnr": 1},
        "Unknown key": {"key": "00000000000000000000000000000000"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "de": (
            "Strasse und Hausnummer wie auf "
            "https://bernentsorgung.glue.ch/erb/web/index angeben, z. B. "
            "Strasse 'Bundesplatz' und Hausnummer '1'. Hausnummern mit "
            "Zusatz werden als '3a' angegeben. Alternativ kann der "
            "Schlüssel aus dem iKalender-Link (…/ical?key=…) direkt im Feld "
            "'key' eingetragen werden."
        ),
        "en": (
            "Enter street and house number as shown on "
            "https://bernentsorgung.glue.ch/erb/web/index, e.g. street "
            "'Bundesplatz' and house number '1'. House numbers with a suffix "
            "are written as '3a'. Alternatively, paste the key from the "
            "iCalendar link (…/ical?key=…) directly into the 'key' field."
        ),
    }

    PARAMS = (
        alternatives(
            [street(field="strasse"), house_number(field="hnr")],
            [
                text_field(
                    "key",
                    "Key",
                    coerce=lambda value: str(value).strip().upper(),
                )
            ],
        ),
    )

    retrieve = IcsSessionRetriever(
        steps=[
            {
                "url": _SEARCH_URL,
                "params": _search,
                "when": lambda key=None, **_: not key,
                "extract": _address_key,
            }
        ],
        feed_url=_ICAL_URL,
        feed_params=lambda key=None, calendar_key=None, **_: {
            "key": key or calendar_key
        },
        encoding="utf-8",
        lookahead_month=None,
        argument=lambda key=None, **_: "key" if key else "strasse",
        argument_message="The service does not know this address.",
    )

    parse = IcsFeedsParser(parsers.IcsParser(), clip_to_until=True)

    transform = ICSTransformer(
        type_value_map={
            "Hauskehricht": wt.GENERAL_WASTE,
            "Altpapiersammlung": wt.PAPER,
            # The feed spells this one without the umlaut ("Gruenabfuhr") even
            # though the website shows "Grünabfuhr". ORGANIC is right because
            # Bern collects kitchen and garden organics together.
            "Gruenabfuhr": wt.ORGANIC,
        }
    )
