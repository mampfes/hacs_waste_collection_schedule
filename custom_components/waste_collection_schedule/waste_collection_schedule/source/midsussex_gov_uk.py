"""Mid Sussex District Council bin collection dates (Whitespace portal)."""

import re
from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    house_number,
    postcode,
    street,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import HtmlTransformer

# The Whitespace "MOP" portal: the start page hands out a Track token, the
# address search (seq=2) lists matching properties as links, and a property's
# link (seq=3) shows its collections, one <ul class="displayinlineblock"> per
# collection: icon, date (DD/MM/YYYY), service name.
BASE_URL = "https://waste.services.midsussex.gov.uk/"
START_URL = urljoin(BASE_URL, "mop.php")


def _number(params: dict) -> str:
    return (params.get("number") or params.get("house_number") or "").strip()


def _track(response, *_, **__) -> str:
    """The session's Track token from the start page's links."""
    track = re.search(r"Track=([^&\"']+)", response.text)
    if track is None:
        raise ValueError("Mid Sussex portal did not hand out a Track token")
    return track.group(1)


def _search(track, **params) -> dict[str, str]:
    return {
        "address_name_number": _number(params),
        "address_street": (params.get("street") or "").strip(),
        "street_town": "",
        "address_postcode": (params.get("postcode") or "").strip(),
    }


def _property(response, track, **params) -> str:
    """The schedule link of the listed property matching the house name/number."""
    links = BeautifulSoup(response.text, "html.parser").select("a.app-subnav__link")
    wanted = _number(params).upper()
    for link in links:
        if wanted in link.get_text(strip=True).upper():
            return urljoin(BASE_URL, link["href"])
    argument = "number" if params.get("number") else "house_number"
    raise SourceArgumentNotFoundWithSuggestions(
        argument, _number(params), [link.get_text(strip=True) for link in links]
    )


@final
class Source(BaseSource):
    TITLE = "Mid Sussex District Council (Whitespace WRP)"
    DESCRIPTION = "Source script for midsussex.gov.uk"
    URL = "https://www.midsussex.gov.uk/waste-and-recycling/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test Case 1: 23 High Street": {
            "number": "23",
            "street": "HIGH STREET",
            "postcode": "RH17 6TB",
        },
        "Test Case 2: Hapstead Hall": {
            "number": "HAPSTEAD HALL",
            "street": "HIGH STREET",
            "postcode": "RH17 6TB",
        },
        "Test Case 3: The Gardeners Arms": {
            "number": "THE GARDENERS ARMS",
            "street": "SELSFIELD ROAD",
            "postcode": "RH17 6TJ",
        },
    }

    PARAMS = (
        postcode(),
        street(),
        # ``house_number`` is the older name of ``number``; both still work.
        alternatives([house_number("number")], [house_number("house_number")]),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your property's postcode, street name and house name or "
            "number (or business name) as they appear in the council's "
            "collection search. Since the v3 pipeline migration, waste types "
            "use canonical, localised names. Update filters, automations and "
            "customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.Request(
        lambda track, schedule, **_: schedule,
        before=(
            retrievers.Lookup(START_URL, pick=_track),
            retrievers.Lookup(
                lambda track, **_: f"{START_URL}?serviceID=A&Track={track}&seq=2",
                method="POST",
                data=_search,
                pick=_property,
            ),
        ),
    )

    parse = parsers.HtmlParser("ul.displayinlineblock")

    transform = HtmlTransformer(
        date_getter=lambda ul: ul.select("li")[1].p.get_text(strip=True),
        type_getter=lambda ul: ul.select("li")[2].p.get_text(strip=True).upper(),
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "DOMESTIC FOOD WASTE SERVICE": wt.FOOD_WASTE,
            "DOMESTIC RECYCLING WASTE COLLECTION SERVICE": wt.RECYCLABLES,
            "DOMESTIC REFUSE WASTE COLLECTION SERVICE": wt.GENERAL_WASTE,
            "DOMESTIC GARDEN WASTE SERVICE": wt.GARDEN_WASTE,
        },
    )
