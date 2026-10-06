import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://your.westlancs.gov.uk/yourwestlancs.aspx"
_POSTBACK = re.compile(r"__doPostBack\s*\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)")
_STATE_FIELDS = ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION")


def _postcode(postcode: str, **_) -> str:
    return postcode.strip().upper()


def _address_form(response, *keys, postcode: str, uprn, **_) -> dict[str, str]:
    """The ASP.NET form body that selects the address with this UPRN."""
    if "no properties found" in response.text.lower():
        raise SourceArgumentNotFound("postcode", postcode)
    soup = BeautifulSoup(response.text, "html.parser")
    grid = soup.find("table", {"id": re.compile("GridView")})
    if not grid:
        raise SourceArgumentNotFound("postcode", postcode)

    wanted = str(uprn)
    for row in grid.find_all("tr"):
        if wanted not in (cell.get_text(strip=True) for cell in row.find_all("td")):
            continue
        link = row.find("a")
        match = _POSTBACK.search(link.get("href", "")) if link else None
        if not match:
            continue
        form = {"__EVENTTARGET": match.group(1), "__EVENTARGUMENT": match.group(2)}
        for field in _STATE_FIELDS:
            element = soup.find("input", {"name": field})
            if element:
                form[field] = element.get("value", "")
        return form
    raise SourceArgumentNotFound("uprn", wanted)


def _label(element) -> str:
    return element.find_parent("tr").find("strong").get_text(strip=True)


def _date(element) -> str:
    return element.get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "West Lancashire Council"
    DESCRIPTION = "Source for West Lancashire Council waste collection schedule."
    URL = "https://westlancs.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Test 1": {"postcode": "WN8 9QR", "uprn": "10012340497"},
        "Test 2": {"postcode": "WN8 9DA", "uprn": "10012357342"},
    }

    PARAMS = (postcode("postcode"), uprn("uprn"))

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                API_URL,
                params=lambda postcode, **_: {"address": _postcode(postcode)},
                pick=_address_form,
            ),
        ),
        url=API_URL,
        params=lambda form, postcode, **_: {"address": _postcode(postcode)},
        method="POST",
        data=lambda form, **_: form,
        raise_for_status=True,
    )
    parse = parsers.HtmlParser("span[id*='lbNext']")
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_label,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        skip_unparseable_dates=True,
        type_value_map={
            "Next refuse collection:": wt.GENERAL_WASTE,
            "Next recycling collection:": wt.RECYCLABLES,
            "Next garden waste collection:": wt.GARDEN_WASTE,
        },
    )
