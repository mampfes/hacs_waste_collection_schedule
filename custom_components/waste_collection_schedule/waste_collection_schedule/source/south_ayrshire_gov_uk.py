from datetime import date, datetime, timedelta, timezone
from typing import ClassVar, final
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
from waste_collection_schedule import preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.GossForm import GossJsonParser
from waste_collection_schedule.transformers import RowTransformer

COLLECTION_PAGE_URL = (
    "https://www.south-ayrshire.gov.uk/article/23931/Bin-collection-days"
)


def _page(response, *keys, **params):
    page = BeautifulSoup(response.text, "html.parser")
    form = page.select_one('form[action*="processsubmission"]')
    if form is None:
        raise ValueError("No GOSS collection form found")
    action = str(form.get("action", ""))
    query = parse_qs(urlparse(action).query)
    return (
        urljoin(str(response.url), action),
        {
            "BINDAYS_PAGESESSIONID": query["pageSessionId"][0],
            "BINDAYS_SESSIONID": query["fsid"][0],
            "BINDAYS_NONCE": query["fsn"][0],
            "BINDAYS_VARIABLES": "",
            "BINDAYS_PAGEINSTANCE": "0",
        },
    )


def _dates(record, source):
    if not record.get("success"):
        raise ValueError(f"Collection lookup failed: {record.get('errors', [])}")
    rows = []
    for item in record.get("calArray", []):
        interval = timedelta(days=item["frequency"])
        if interval.days <= 0:
            raise ValueError("Collection frequency must be positive")
        day = (
            datetime.fromisoformat(item["binDate"].replace("Z", "+00:00"))
            .astimezone(timezone.utc)
            .date()
        )
        end = datetime.strptime(item["dtend"], "%Y%m%d").date()
        key = item["bin"].split("/")[0].split()[0]
        while day <= end:
            if day >= date.today():
                rows.append((day, key))
            day += interval
    return rows


@final
class Source(BaseSource):
    TITLE = "South Ayrshire Council"
    DESCRIPTION = "Source for south-ayrshire.gov.uk services for South Ayrshire."
    URL = "https://www.south-ayrshire.gov.uk"
    TEST_CASES: ClassVar[dict] = {
        "4 Thistle Walk, Ayr, KA7 3XH": {"postcode": "KA7 3XH", "uprn": "141030966"}
    }
    COUNTRY = "uk"
    PARAMS = (postcode(), uprn())
    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.GLASS,
        wt.FOOD_WASTE,
    ]
    HOWTO: ClassVar[dict] = {
        "en": "Enter your postcode and the property UPRN from the council's bin collection form. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.Request(
        lambda first, second, **_: second[0],
        method="POST",
        headers={
            "Referer": COLLECTION_PAGE_URL,
            "Origin": "https://www.south-ayrshire.gov.uk",
        },
        data=lambda first, second, uprn, **_: {
            **second[1],
            "BINDAYS_PAGENAME": "PAGE2",
            "BINDAYS_PAGE2_ADDRESSDROPDOWN": str(uprn),
            "BINDAYS_FORMACTION_NEXT": "BINDAYS_PAGE2_FIELD7",
        },
        before=(
            retrievers.Lookup(COLLECTION_PAGE_URL, pick=_page),
            retrievers.Lookup(
                lambda first, **_: first[0],
                method="POST",
                headers={
                    "Referer": COLLECTION_PAGE_URL,
                    "Origin": "https://www.south-ayrshire.gov.uk",
                },
                data=lambda first, postcode, **_: {
                    **first[1],
                    "BINDAYS_PAGENAME": "PAGE1",
                    "BINDAYS_PAGE1_POSTCODE": postcode,
                    "BINDAYS_FORMACTION_NEXT": "BINDAYS_PAGE1_WIZBUTTON",
                },
                pick=_page,
            ),
        ),
    )
    parse = GossJsonParser("PAGE3_1", "FIELD15")
    preprocess = preprocessors.ExplodeList(_dates)
    transform = RowTransformer(
        type_value_map={
            "Blue": wt.RECYCLABLES,
            "Brown": wt.ORGANIC,
            "Green": wt.GENERAL_WASTE,
            "Grey": wt.PAPER,
            "Purple": wt.GLASS,
            "Food": wt.FOOD_WASTE,
        }
    )
