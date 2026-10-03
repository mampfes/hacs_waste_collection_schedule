from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import HtmlTransformer

ADDRESS_API = "https://trsewmllv7.execute-api.eu-west-2.amazonaws.com/dev/address"
COLLECTION_URL = (
    "https://www.herefordshire.gov.uk/rubbish-recycling/check-bin-collection-day"
)


def _pick_uprn(response, *keys, post_code, number, **_) -> str:
    """The lookup answers the OS places of the postcode, each with an ``LPI`` block.

    ``number`` is a house number (``PAO_START_NUMBER``), a house name
    (``PAO_TEXT``, or ``SAO_TEXT`` for a named flat) or the UPRN itself.
    """
    addresses = response.json()
    results = addresses.get("results")
    if addresses.get("error") or not results:
        raise SourceArgumentNotFound("post_code", post_code)

    entered = str(number).strip()
    target = entered.lower()

    def exact(lpi: dict) -> bool:
        return any(
            lpi.get(field) is not None and str(lpi[field]).strip().lower() == target
            for field in ("UPRN", "PAO_TEXT", "PAO_START_NUMBER", "SAO_TEXT")
        )

    matches = [x for x in results if exact(x["LPI"])]
    # A house name that is not cleanly isolated into PAO_TEXT / SAO_TEXT is
    # still found in the full address.
    if not matches and len(target) >= 3:
        matches = [
            x
            for x in results
            if x["LPI"].get("ADDRESS") and target in str(x["LPI"]["ADDRESS"]).lower()
        ]
    if not matches:
        raise SourceArgumentNotFoundWithSuggestions(
            "number",
            entered,
            sorted({x["LPI"]["ADDRESS"] for x in results if x["LPI"].get("ADDRESS")}),
        )
    return matches[0]["LPI"]["UPRN"]


def _label(li) -> str:
    """The service heading above the list, "General rubbish - black bin" -> "General rubbish"."""
    heading = li.find_parent("ul").find_previous_sibling("h3")
    return heading.get_text(strip=True).split(" - ")[0]


def _date_text(li) -> str:
    """ "Wednesday 7 October 2026 (next collection)" -> the date."""
    return li.get_text(strip=True).split("(")[0].strip()


@final
class Source(BaseSource):
    TITLE = "Herefordshire City Council"
    DESCRIPTION = "Source for herefordshire.gov.uk services for hereford"
    URL = "https://herefordshire.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "houseNumber": {"post_code": "hr49js", "number": "52"},
        "uprn": {"post_code": "hr49js", "number": "200002607460"},
    }

    PARAMS = (postcode("post_code", "number"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the postcode and the house number, house name or UPRN "
            "(Unique Property Reference Number) of the property. If your "
            "property only has a name and no number, enter the name; if it is "
            "still not found, the error message lists the full addresses found "
            "for your postcode so you can copy the UPRN or exact wording from "
            "there."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                ADDRESS_API,
                params=lambda post_code, **_: {
                    "postcode": post_code,
                    "type": "standard",
                },
                pick=_pick_uprn,
            ),
        ),
        url=COLLECTION_URL,
        params=lambda key, **_: {"blpu_uprn": key},
    )

    # Every list item under a service heading; the calendar link and the
    # bin-size list share the markup and are skipped for lack of a date.
    parse = parsers.HtmlParser("#binCollectionDetails > ul > li")

    transform = HtmlTransformer(
        date_getter=_date_text,
        type_getter=_label,
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        skip_unparseable_dates=True,
        type_value_map={
            "General rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden waste": wt.GARDEN_WASTE,
        },
    )
