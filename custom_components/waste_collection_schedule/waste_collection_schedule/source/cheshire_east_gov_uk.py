from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, postcode, uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import HtmlTransformer

API = "https://online.cheshireeast.gov.uk/MyCollectionDay/SearchByAjax"

_TYPE_MAP = {
    "general waste": wt.GENERAL_WASTE,
    "mixed recycling": wt.RECYCLABLES,
    "garden waste": wt.GARDEN_WASTE,
}


def _pick_uprn(response, *keys, postcode, name_number, **_) -> str:
    """The first matching address carries its UPRN as ``data-uprn``."""
    link = BeautifulSoup(response.text, "html.parser").find(
        "a", attrs={"class": "get-job-details"}
    )
    if link is None or not link.get("data-uprn"):
        raise SourceArgumentNotFound(
            "name_number", f"{name_number}, {postcode}", "address not found"
        )
    return str(link["data-uprn"])


def _labels(cell) -> list:
    return cell.find_all("label")


def _date(cell) -> str | None:
    """Only a cell with its three labels (day, date, service) is a collection."""
    labels = _labels(cell)
    return labels[1].text if len(labels) > 2 else None


def _type(cell) -> str:
    """A service is named like "Empty Standard General Waste"."""
    text = _labels(cell)[2].text
    for key in _TYPE_MAP:
        if key in text.lower():
            return key
    return text


@final
class Source(BaseSource):
    TITLE = "Cheshire East Council"
    DESCRIPTION = "Source for cheshireeast.gov.uk services for Cheshire East"
    URL = "https://cheshireeast.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "houseUPRN": {"uprn": "100010132073"},
        "houseAddress": {"postcode": "WA16 0AY", "name_number": "3"},
    }

    PARAMS = (
        alternatives(
            [uprn()],
            [postcode("postcode", "name_number")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter either your UPRN (available from "
            "[FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)) OR your "
            "postcode and house number or name."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API}/Search",
                params=lambda postcode=None, name_number=None, **_: {
                    "postcode": postcode,
                    "propertyname": name_number,
                },
                given=lambda uprn=None, **_: uprn,
                pick=_pick_uprn,
            ),
        ),
        url=f"{API}/GetBartecJobList",
        params=lambda key, **_: {"uprn": key},
    )

    parse = parsers.HtmlParser("td.visible-cell")

    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_type,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map=_TYPE_MAP,
    )
