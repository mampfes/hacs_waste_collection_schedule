"""Kirklees Council - Manage your bins.

Kirklees runs its own AchieveForms lookup chain: a postcode lookup returns the
addresses at that postcode (keyed by UPRN), a property-type lookup resolves
the council's internal "GovDeliveryCategorye" for the chosen UPRN, a
token-validation call sets that category on the session, and a final lookup
returns the actual collection dates. Each call after the first reuses (and
extends) the same "Search" form section, so the chain is expressed as four
LookupSteps threaded through a shared context dict.
"""

from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field, uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Live-verified (2026-07): the standard AchieveForms handshake
# (init_session -> authapi/isauthenticated, using the un-prefixed service path
# below verbatim, without the legacy source's separate apibroker/domain
# warm-up GET) authenticates my.kirklees.gov.uk. No service-layer change
# needed.
HOSTNAME = "my.kirklees.gov.uk"
INITIAL_URL = f"https://{HOSTNAME}/service/Bins_and_recycling___Manage_your_bins"

LOOKUP_ADDRESS = "58049013ca4c9"  # postcode -> address list (keyed by UPRN)
LOOKUP_PROP_TYPE = "659c2c2386104"  # UPRN -> GovDeliveryCategorye / PropertyType
LOOKUP_UPRN_VALID = "631615c4bd3b7"  # set session validatedUPRN token
LOOKUP_COLLECTIONS = "65e08e60b299d"  # UPRN -> bin collection dates


def _address_form_values(ctx: dict, source: "BaseSource") -> dict:
    ctx["uprn"] = source.params["uprn"]
    ctx["postcode"] = source.params["postcode"]
    return {"Postcode": {"value": source.params["postcode"]}}


def _extract_address(response: dict, ctx: dict) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    if not isinstance(rows, dict):
        rows = {}
    target_uprn = ctx["uprn"]
    if target_uprn not in rows:
        raise SourceArgumentNotFoundWithSuggestions(
            "uprn", target_uprn, list(rows.keys())
        )
    row = rows[target_uprn]
    ctx["prop_ref"] = row.get("PropertyReference", "")
    ctx["house"] = row.get("Premise", "")
    ctx["street"] = row.get("Street", "")
    ctx["town"] = row.get("Town", "")
    ctx["full_addr"] = row.get("display", "")


def _extract_prop_type(response: dict, ctx: dict) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    gov_cat = ""
    prop_type = "Residential"
    if isinstance(rows, dict) and rows:
        first = next(iter(rows.values()))
        gov_cat = first.get("GovDeliveryCategorye", "")
        prop_type = first.get("PropertyType", "Residential") or "Residential"
    ctx["gov_cat"] = gov_cat
    ctx["prop_type"] = prop_type


def _search_section(ctx: dict, *, include_prop_type: bool) -> dict:
    """Build the "Search" form section, mirroring browser state after address
    selection. Kirklees' later lookups are tolerant of every field being sent
    under one flat section (live-verified), so the "Your bins" fields a real
    browser sends as a sibling section are simply added onto this one by the
    caller instead."""
    section: dict[str, Any] = {
        "PowerSuite_Available": {"value": "True"},
        "PowerSuite_Available1": {"value": "True"},
        "productName": {"value": "Self"},
        "uprn2": {"value": ctx["uprn"]},
        "validatedUPRN": {"value": ctx["uprn"]},
        "suppliedUPRN": {"value": ctx["uprn"]},
        "uprnFinal": {"value": ctx["uprn"]},
        "validPropertyFlag": {"value": "yes"},
        "sSection": {"value": "1"},
        "flatOrSubBuildingFinal": {"value": ""},
        "houseFinal": {"value": ctx["house"]},
        "streetFinal": {"value": ctx["street"]},
        "townFinal": {"value": ctx["town"]},
        "postcodeFinal": {"value": ctx["postcode"]},
        "fullAddressFinal": {"value": ctx["full_addr"]},
        "customerAddress": {
            "value": {
                "Section 1": {
                    "searchForAddress": {"value": "yes"},
                    "Postcode": {"value": ctx["postcode"]},
                    "List": {"value": ctx["uprn"]},
                    "House": {"value": ctx["house"]},
                    "Street": {"value": ctx["street"]},
                    "Town": {"value": ctx["town"]},
                    "UPRN": {"value": ctx["uprn"]},
                    "PropertyReference": {"value": ctx["prop_ref"]},
                    "postcode": {"value": ""},
                    "house": {"value": ""},
                    "flat": {"value": ""},
                    "street": {"value": ""},
                    "town": {"value": ""},
                    "fullAddress": {"value": ctx["full_addr"]},
                    "lengthPostCode": {"value": str(len(ctx["postcode"]))},
                }
            }
        },
    }
    if include_prop_type:
        section["binsPropertyType"] = {
            "value": {
                "Section 1": {
                    "PropertyType": {"value": ctx["prop_type"]},
                    "GovDeliveryCategorye": {"value": ctx["gov_cat"]},
                }
            }
        }
        section["GovDeliveryCategorye"] = {"value": ctx["gov_cat"]}
        section["PropertyType"] = {"value": ctx["prop_type"]}
    return section


def _collections_form_values(ctx: dict, source: "BaseSource") -> dict:
    section = _search_section(ctx, include_prop_type=True)
    today = date.today()
    section["NextCollectionFromDate"] = {
        "value": (today - timedelta(days=7)).strftime("%d/%m/%Y")
    }
    section["NextCollectionToDate"] = {
        "value": (today + timedelta(days=28)).strftime("%d/%m/%Y")
    }
    return section


@final
class Source(BaseSource):
    TITLE = "Kirklees Council"
    DESCRIPTION = (
        "Source for waste collections for Kirklees Council (my.kirklees.gov.uk)"
    )
    URL = "https://www.kirklees.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Midgebottom House": {"uprn": "83074265", "postcode": "HD9 7HA"},
        "HD8 8NA test": {"uprn": "83194785", "postcode": "HD8 8NA"},
    }

    PARAMS = (
        postcode(),
        uprn(),
        text_field(
            "predict",
            "Predict future collections",
            default="false",
            optional=True,
        ),
    )

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        steps=[
            LookupStep(
                LOOKUP_ADDRESS,
                form_values=_address_form_values,
                extract=_extract_address,
            ),
            LookupStep(
                LOOKUP_PROP_TYPE,
                section="Search",
                form_values=lambda ctx, source: _search_section(
                    ctx, include_prop_type=False
                ),
                extract=_extract_prop_type,
            ),
            LookupStep(
                LOOKUP_UPRN_VALID,
                section="Search",
                form_values=lambda ctx, source: _search_section(
                    ctx, include_prop_type=True
                ),
            ),
            LookupStep(
                LOOKUP_COLLECTIONS,
                section="Search",
                form_values=_collections_form_values,
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    transform = RowTransformer(
        type_value_map={
            "grey wheelie bin": GENERAL_WASTE,
            "green wheelie bin": RECYCLABLES,
            "brown wheelie bin": GARDEN_WASTE,
            "blue wheelie bin": RECYCLABLES,
        },
    )

    def __init__(self, uprn: str | int, postcode: str, predict: str | bool = False):
        pc = postcode.strip().upper().replace(" ", "")
        normalised_postcode = pc[:-3] + " " + pc[-3:] if len(pc) >= 5 else pc
        super().__init__(
            uprn=str(uprn),
            postcode=normalised_postcode,
            predict=str(predict).strip().lower() in {"true", "yes", "1"},
        )

    def preprocess(
        self, rows: Any, source: "BaseSource | None" = None
    ) -> "Iterable[tuple[Any, str]]":
        values: Iterable[Any]
        if isinstance(rows, dict):
            values = rows.values()
        elif isinstance(rows, list):
            values = rows
        else:
            return
        predict = bool(self.params.get("predict"))
        for row in values:
            if not isinstance(row, dict):
                continue
            date_str = row.get("NextCollectionDate")
            label = row.get("label") or row.get("ServiceItemName")
            if not date_str or not label:
                continue
            try:
                base_date = date_parsers.auto(str(date_str))
            except (ValueError, TypeError):
                continue
            dates = [base_date]
            if predict:
                # Kirklees residential collections are fortnightly; mirrors the
                # legacy source's 365-day look-ahead window.
                dates.extend(
                    base_date + timedelta(days=14 * i) for i in range(1, 365 // 14)
                )
            for collection_date in dates:
                yield collection_date, str(label)
