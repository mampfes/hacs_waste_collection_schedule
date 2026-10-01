# Credit where it's due:
# This is predominantly a refactoring of the Bristol City Council script from the UKBinCollectionData repo
# https://github.com/robbrad/UKBinCollectionData

import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.preprocessors import Compose, SplitLabels
from waste_collection_schedule.transformers import RowTransformer

API_URL = "https://waste.barnsley.gov.uk/ViewCollection/SelectAddress"


def _rows(records, source=None):
    """Yield ``(date, "Blue, Green")`` from the highlighted next collection and the table rows."""
    for record in records:
        if "highlight-content" in (record.get("class") or []):
            date_text = record.select_one(".ui-bin-next-date").get_text(strip=True)
            label = record.select_one(".ui-bin-next-type").get_text(strip=True)
        else:
            cells = record.find_all("td")
            date_text = cells[0].get_text(strip=True)
            label = cells[1].get_text(strip=True)
        if date_text.lower() == "today":
            yield datetime.date.today(), label
        else:
            yield date_text, label


@final
class Source(BaseSource):
    TITLE = "Barnsley Metropolitan Borough Council"
    DESCRIPTION = "Source for Barnsley Metropolitan Borough Council."
    URL = "https://barnsley.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "S71 1EE 100050671689": {"postcode": "S71 1EE", "uprn": 100050671689},
        "S75 1QF 10032783992": {"postcode": "S75 1QF", "uprn": "10032783992"},
        "test": {"postcode": "S70 3QU", "uprn": 100050607581},
    }

    PARAMS = (postcode("postcode"), uprn("uprn"))

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and your UPRN (available from "
            "[FindMyAddress.co.uk](https://www.findmyaddress.co.uk/))."
        ),
    }

    retrieve = retrievers.HttpPostRetriever(
        API_URL,
        data=lambda postcode, uprn, **_: {
            "personInfo.person1.HouseNumberOrName": "",
            "personInfo.person1.Postcode": f"{postcode}",
            "personInfo.person1.UPRN": f"{uprn}",
            "person1_SelectAddress": "Select address",
        },
    )

    parse = parsers.HtmlParser(".highlight-content, fieldset:nth-of-type(2) tbody tr")

    preprocess = Compose(_rows, SplitLabels(","))

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%A, %B %d, %Y"),
        type_value_map={
            "Grey": wt.GENERAL_WASTE,
            "Green": wt.GARDEN_WASTE,
            "Blue": wt.PAPER,
            "Brown": wt.RECYCLABLES,
        },
    )
