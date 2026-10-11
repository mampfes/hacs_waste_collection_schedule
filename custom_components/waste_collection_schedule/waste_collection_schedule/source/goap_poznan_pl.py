from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    dropdown,
    house_number,
    street,
)
from waste_collection_schedule.retrievers import Lookup, Request
from waste_collection_schedule.transformers import ICSTransformer

BASE_URL = "https://web.c-trace.de"
FORM_URL = f"{BASE_URL}/zmgoappoznan-abfallkalender/kalendarzodpadow"

_TYPE_MAP = {
    "rest": wt.GENERAL_WASTE,
    "glas": wt.GLASS,
    "papier": wt.PAPER,
    "plastik": wt.PLASTIC,
    "bio": wt.ORGANIC,
    "sperr": wt.BULKY_WASTE,
}


def _form_url(response, **_):
    """The form URL with the cookieless ASP.NET session id the site mints.

    Requesting the form page without one redirects to a URL that contains a
    fresh ``(S(...))`` segment; a reply that is not a redirect already carries
    a valid one.
    """
    location = response.headers.get("location")
    return f"{BASE_URL}{location}" if location else FORM_URL


@final
class Source(BaseSource):
    TITLE = "GOAP Poznań"
    DESCRIPTION = (
        "Source for the waste collection calendar of GOAP (Związek Międzygminny "
        "Gospodarka Odpadami Aglomeracji Poznańskiej), covering municipalities in "
        "the Poznań agglomeration such as Murowana Goślina, Czerwonak, Swarzędz "
        "and others."
    )
    URL = "https://www.goap.poznan.pl/"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.PAPER,
        wt.PLASTIC,
        wt.ORGANIC,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Huta Pusta 1": {
            "city": "HUTA PUSTA",
            "street": "HUTA PUSTA",
            "house_number": "1",
            "location_type": "Z",
            "building_type": "J",
        },
        "Murowana Goślina, Poznańska 17": {
            "city": "MUROWANA GOŚLINA",
            "street": "POZNAŃSKA",
            "house_number": "17",
        },
    }

    PARAMS = (
        city(),
        street(),
        house_number(),
        dropdown(
            "location_type",
            ["Z", "N", "M", "R"],
            label="Location Type",
            optional=True,
        ),
        dropdown(
            "building_type",
            ["J", "W"],
            label="Building Type",
            optional=True,
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the city, street and house number exactly as the GOAP calendar "
            "writes them (usually upper case, e.g. 'MUROWANA GOŚLINA'). For "
            "villages without named streets the street is often the same as the "
            "city, and a house number may carry a suffix such as '5/A'. Set the "
            "location type (Z inhabited, N uninhabited, M mixed, R recreational) "
            "and building type (J single-family, W multi-family) only if the "
            "address is ambiguous."
        ),
    }

    retrieve = Request(
        lambda form_url, **_: form_url,
        method="POST",
        data=lambda form_url, **p: {
            "posted": "yes",
            "ort": p["city"],
            "strasse": p["street"],
            "hausnr": p["house_number"],
            "objekttyp": p["location_type"] or "",
            "objekttyp2": p["building_type"] or "",
        },
        before=(Lookup(FORM_URL, pick=_form_url, allow_redirects=False),),
    )
    parse = parsers.HtmlParser("#plaene .plan")
    preprocess = preprocessors.HtmlGroupedDates(
        keys=_TYPE_MAP,
        date_pattern=r"(\d{2}\.\d{2}\.\d{4})",
        parse_date=date_parsers.for_format("%d.%m.%Y"),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
