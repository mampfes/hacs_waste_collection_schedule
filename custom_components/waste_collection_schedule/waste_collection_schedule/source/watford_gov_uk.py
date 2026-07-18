"""Watford Borough Council - Bin Collections.

Watford's AchieveForms lookup chain resolves an "echoAddressPoint" token for
the property (from a UPRN or an already-selected address token), then fetches
a summary row whose "dispHTML" field embeds a rendered HTML fragment (one
``<li class="binItem">`` per bin, with the bin name in an ``<h3>`` and the
next collection date inside a ``<strong>``) rather than structured rows_data --
so the pipeline reads it with parsers.HtmlParser's ``from_json_key``, the same
mechanism used for the OCAPI ``wasteservices`` HTML-in-JSON shape.
"""

import re
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, text_field, uprn
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    LookupStep,
)
from waste_collection_schedule.transformers import HtmlTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Live-verified (2026-07): the standard AchieveForms handshake
# (init_session -> authapi/isauthenticated on the service landing page)
# authenticates watfordbc-self.achieveservice.com without the legacy source's
# regex-scrape of the landing page's embedded `auth-session` value. No
# service-layer change needed.
HOSTNAME = "watfordbc-self.achieveservice.com"
INITIAL_URL = (
    f"https://{HOSTNAME}/en/service/Bin_Collections?accept=yes&consentMessageIds[]=9"
)

LOOKUP_ADDRESS_POINT = "5e57d2f638e6d"
LOOKUP_NEXT_COLLECTIONS = "5e79edf15b2ec"

# The bin name always carries a parenthesised category ("Black bin
# (non-recyclable waste)", "Green Bin (garden waste)", "Blue-lidded bin
# (recycling)", "Brown bin (food waste)"); keying on that phrase is more
# robust than the bin colour/casing, which the legacy source matched loosely.
_CATEGORY_RE = re.compile(r"\(([^)]+)\)")


def _clean_bin_label(label: str) -> str:
    match = _CATEGORY_RE.search(label)
    return (match.group(1) if match else label).strip()


def _date_getter(el: Any) -> "str | None":
    strong = el.select_one("strong")
    return strong.get_text(strip=True) if strong else None


def _type_getter(el: Any) -> str:
    h3 = el.select_one("h3")
    return h3.get_text(strip=True) if h3 else ""


def _address_point_form_values(ctx: dict, source: "BaseSource") -> dict:
    # Preferred argument is uprn; address is the fallback (an already-selected
    # address token from the Watford form), matching the legacy source.
    arg_name = "uprn" if source.params.get("uprn") else "address"
    address_token = source.params.get("address") or source.params.get("uprn")
    uprn_value = source.params.get("uprn") or source.params.get("address")
    ctx["arg_name"] = arg_name
    ctx["address_token"] = str(address_token)
    ctx["uprn_value"] = str(uprn_value).lstrip("0")
    return {
        "echoUprn": {"value": ctx["uprn_value"]},
        "address": {"value": ctx["address_token"]},
    }


def _extract_address_point(response: dict, ctx: dict) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    row = rows.get("0", {}) if isinstance(rows, dict) else {}
    echo_address_point = row.get("echoAddressPoint") if isinstance(row, dict) else None
    if not echo_address_point:
        raise SourceArgumentException(
            ctx["arg_name"],
            "Watford source could not resolve echoAddressPoint for this property token.",
        )
    ctx["echo_address_point"] = echo_address_point


def _collections_form_values(ctx: dict, source: "BaseSource") -> dict:
    return {
        "address": {"value": ctx["address_token"]},
        "echoUprn": {"value": ctx["uprn_value"]},
        "echoAddressPoint": {"value": ctx["echo_address_point"]},
    }


@final
class Source(BaseSource):
    TITLE = "Watford Borough Council"
    DESCRIPTION = "Source for waste collection services for Watford Borough Council"
    URL = "https://www.watford.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "1 Coningsby Drive, Watford": {"uprn": "100080932722"},
    }

    PARAMS = (
        alternatives(
            [uprn()],
            [text_field("address", "Address token", optional=True)],
        ),
    )

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        steps=[
            LookupStep(
                LOOKUP_ADDRESS_POINT,
                section="Address",
                form_values=_address_point_form_values,
                extract=_extract_address_point,
            ),
            LookupStep(
                LOOKUP_NEXT_COLLECTIONS,
                section="Address",
                form_values=_collections_form_values,
            ),
        ],
    )
    parse = HtmlParser(
        "li.binItem",
        from_json_key=("integration", "transformed", "rows_data", "0", "dispHTML"),
    )
    transform = HtmlTransformer(
        date_getter=_date_getter,
        type_getter=_type_getter,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        clean=_clean_bin_label,
        type_value_map={
            "non-recyclable waste": GENERAL_WASTE,
            "garden waste": GARDEN_WASTE,
            "recycling": RECYCLABLES,
            "food waste": FOOD_WASTE,
        },
    )

    def __init__(
        self, uprn: "str | int | None" = None, address: "str | int | None" = None
    ):
        super().__init__(
            uprn=str(uprn).strip() if uprn is not None else None,
            address=str(address).strip() if address is not None else None,
        )
