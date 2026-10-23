import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, postcode, uprn
from waste_collection_schedule.transformers import RowTransformer

# Bromsgrove District Council and Redditch Borough Council run a shared waste
# service and both publish the same "BinCollections" web app, one instance per
# council domain.
_DOMAINS = {
    "bromsgrove": "bincollections.bromsgrove.gov.uk",
    "redditch": "bincollections.redditchbc.gov.uk",
}


def _url(council: str = "bromsgrove", **_) -> str:
    return f"https://{_DOMAINS[council]}/BinCollections/Details/"


def _postcode_matches(response, source) -> bool:
    """The page names the postcode of the UPRN: it must be the configured one."""
    found = re.search(r"Bin collection dates for\s+([^<]+?)\s*</h3>", response.text)
    if found is None or source is None:
        return False
    return (
        "".join(found.group(1).split()).upper()
        == "".join(str(source.params["postcode"]).split()).upper()
    )


@final
class Source(BaseSource):
    TITLE = "Bromsgrove & Redditch Councils"
    DESCRIPTION = "Source for the shared bin collection lookup used by Bromsgrove District Council and Redditch Borough Council, UK."
    URL = "https://bromsgrove.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.RECYCLABLES, wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Shakespeare House": {"uprn": "10094552413", "postcode": "B61 8DA"},
        "The Lodge": {"uprn": 10000218025, "postcode": "B60 2AA"},
        "Ceader Lodge": {"uprn": 100120576392, "postcode": "B60 2JS"},
        "Finstall Road": {"uprn": 100120571971, "postcode": "B60 3DE"},
    }

    PARAMS = (
        uprn(),
        postcode(),
        dropdown("council", list(_DOMAINS), label="Council", default="bromsgrove"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) "
            "and enter it with the postcode of the same address. The council is "
            "`bromsgrove` (default) or `redditch`."
        ),
    }

    retrieve = retrievers.Request(
        _url, method="POST", data=lambda uprn, **_: {"UPRN": str(uprn)}
    )

    # An unknown UPRN gets an error page, and a UPRN at another postcode is a
    # mistyped pair either way.
    parse = parsers.ArgumentGuard(
        parsers.HtmlLabelledDates(
            ".collection-container",
            label=".heading",
            date=".collection-details-container",
            date_pattern=r"(\d{1,2} [A-Za-z]+ \d{4})",
            all_dates=True,
        ),
        argument="uprn",
        matches=_postcode_matches,
        hint="check that the UPRN belongs to the postcode and council given",
    )

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map={
            "Green Bin": wt.RECYCLABLES,
            "Grey Bin": wt.GENERAL_WASTE,
            "Brown Bin": wt.GARDEN_WASTE,
        },
    )
