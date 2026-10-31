"""New Forest District Council (England) bin collection dates."""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import HtmlTransformer

# An Ebase "UFS" form: page one takes the postcode, page two lists that
# postcode's addresses (option values are UPRNs), and submitting one shows the
# collections. Each submission goes to the URL keyed by the page's ``ebs``
# token, within the JSESSIONID session the first request opens.
FORM_URL = "https://forms.newforest.gov.uk/ufs/FIND_MY_BIN_BAR.eb"
_STATE_FIELDS = ("formid", "ebs", "formstack")


def _form_state(response, *_, **__) -> dict[str, str]:
    """The page's hidden form state (session token, form stack, page counters)."""
    return retrievers.form_inputs(
        response.text, hidden_only=True, required=_STATE_FIELDS
    )


def _addresses(response, page_one, *, postcode, uprn, **_) -> dict[str, str]:
    """Check the UPRN is one of the postcode's addresses; return page two's state."""
    soup = BeautifulSoup(response.text, "html.parser")
    uprns = [o["value"] for o in soup.select("select option[value]") if o["value"]]
    if not uprns:
        raise SourceArgumentNotFound("postcode", postcode)
    if str(uprn).strip() not in uprns:
        raise SourceArgumentNotFoundWithSuggestions("uprn", uprn, uprns)
    return _form_state(response)


def _submit_postcode(page_one, *, postcode, **_) -> dict[str, str]:
    return {
        **page_one,
        "PAGE:X": "0",
        "PAGE:Y": "0",
        "PAGE:F": "CTID-EBTnjgwK-_",
        "CTRL:JmLqCKl2:_:A": str(postcode).strip(),
        "CTRL:JmLqCKl2:_:B.h": "",
        "HID:inputs": (
            "ICTRL:JmLqCKl2:_:A,ACTRL:JmLqCKl2:_:B.h,ACTRL:EBTnjgwK:_,"
            "APAGE:E.h,APAGE:B.h,APAGE:N.h,APAGE:S.h,APAGE:R.h"
        ),
        "CTRL:EBTnjgwK:_": "Submit",
    }


def _submit_uprn(page_one, page_two, *, uprn, **_) -> dict[str, str]:
    return {
        **page_two,
        "PAGE:X": "0",
        "PAGE:Y": "0",
        "PAGE:F": "",
        "CTRL:KOeKcmrC:_:A": str(uprn).strip(),
        "CTRL:KOeKcmrC:_:B.h": "",
        "HID:inputs": (
            "ICTRL:KOeKcmrC:_:A,ACTRL:KOeKcmrC:_:B.h,ACTRL:QxB4NyYs:_,"
            "ACTRL:Ggx8Z7ze:_,APAGE:E.h,APAGE:B.h,APAGE:N.h,APAGE:S.h,APAGE:R.h"
        ),
        "CTRL:QxB4NyYs:_": "Submit",
    }


def _cells(row) -> list[str]:
    return [td.get_text(strip=True) for td in row.find_all("td", recursive=False)]


@final
class Source(BaseSource):
    TITLE = "New Forest District Council"
    DESCRIPTION = (
        "Source for newforest.gov.uk services for New Forest District Council."
    )
    URL = "https://www.newforest.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "1 Oleander Drive, Totton": {"postcode": "SO40 8XX", "uprn": 100060514912},
        "49 Salisbury Road, Totton": {"postcode": "SO40 3HX", "uprn": "100060518013"},
        "12 Hawkins Close, Ringwood": {"postcode": "BH24 1UQ", "uprn": "100060495458"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "UPRN not at postcode": {"postcode": "SO40 8XX", "uprn": "100060495458"},
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode (e.g. SO40 8XX) and the Unique Property "
            "Reference Number (UPRN) of your property. You can find your UPRN "
            "at https://www.findmyaddress.co.uk/. Since the v3 pipeline "
            "migration, waste types use canonical, localised names. Update "
            "filters, automations and customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.Request(
        lambda page_one, page_two, **_: f"{FORM_URL}?ebz={page_two['ebs']}",
        method="POST",
        before=(
            retrievers.Lookup(FORM_URL, pick=_form_state),
            retrievers.Lookup(
                lambda page_one, **_: f"{FORM_URL}?ebz={page_one['ebs']}",
                method="POST",
                data=_submit_postcode,
                pick=_addresses,
            ),
        ),
        data=_submit_uprn,
    )

    # The "Future collections" table: one row per collection, the date and the
    # container ("Food 23L", "General 180L", "Recycle 240L", "Glass Box").
    parse = parsers.ArgumentGuard(
        parsers.HtmlParser("table[class*=tableContent] tr:has(> td:nth-of-type(2))"),
        argument="uprn",
        contains="tableContent",
    )

    transform = HtmlTransformer(
        date_getter=lambda row: _cells(row)[0],
        type_getter=lambda row: _cells(row)[1].split()[0],
        description_getter=lambda row: _cells(row)[1],
        parse_date=date_parsers.for_format("%A %B %d, %Y"),
        skip_unparseable_dates=True,
        type_value_map={
            "Food": wt.FOOD_WASTE,
            "Garden": wt.GARDEN_WASTE,
            "General": wt.GENERAL_WASTE,
            "Glass": wt.GLASS,
            "Recycle": wt.RECYCLABLES,
        },
    )
