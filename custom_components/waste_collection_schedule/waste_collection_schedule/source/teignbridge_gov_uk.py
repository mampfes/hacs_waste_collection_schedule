from datetime import datetime
from typing import Any, ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import RowTransformer

_BIN_URL = "https://www.teignbridge.gov.uk/umbraco/surface/bincollection/GetCollections"
_NOT_FOUND = "cannot find any collection details"

_TYPE_MAP = {
    "Food waste container": wt.FOOD_WASTE,
    "Black box": wt.RECYCLABLES,
    "Green box": wt.GLASS,
    "Sack for paper": wt.PAPER,
    "Refuse - black bin": wt.GENERAL_WASTE,
}


def _rows(response: Any, source: BaseSource | None = None) -> list[tuple]:
    """``(date, bin title)`` rows from the collection HTML.

    Each date is an ``h3.binCollectionH3`` (``30 October 2026`` plus a weekday
    span). The following ``div.binInfoContainer`` lists one image title per bin.
    """
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    if _NOT_FOUND in text.lower():
        uprn_value = "" if source is None else source.params.get("uprn", "")
        raise SourceArgumentNotFound(
            "uprn",
            uprn_value,
            "Sorry, but we cannot find any collection details for this property.",
        )

    rows: list[tuple] = []
    for heading in soup.find_all("h3", class_="binCollectionH3"):
        date_text = heading.get_text(strip=True)
        span = heading.find("span", class_="binDayDescriptor")
        if span:
            date_text = date_text.replace(span.get_text(strip=True), "").strip()
        try:
            collected = datetime.strptime(date_text, "%d %B %Y").date()
        except ValueError:
            continue
        container = heading.find_next_sibling("div", class_="binInfoContainer")
        if container is None:
            continue
        for line in container.find_all("div", class_="binInfoLine"):
            image = line.find("img")
            title = image.get("title") if image is not None else None
            if title:
                rows.append((collected, str(title)))
    return rows


@final
class Source(BaseSource):
    TITLE = "Teignbridge District Council"
    DESCRIPTION = "Source for teignbridge.gov.uk waste collection."
    URL = "https://www.teignbridge.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    # UPRN 100040270498 (TQ12 4QQ) answers "cannot find any collection details".
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "EX4 2JR": {"postcode": "EX4 2JR", "uprn": "010032968474"},
    }

    # postcode is not sent. The collection request is keyed by UPRN only.
    # The argument stays so existing configurations keep their field.
    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.teignbridge.gov.uk/recycling-and-waste/forms/"
            "download-your-collection-calendar/, enter your postcode and note "
            "the UPRN from the address dropdown."
        ),
    }

    retrieve = retrievers.Request(
        _BIN_URL,
        params=lambda uprn, **_: {"uprn": str(uprn).strip()},
    )
    parse = staticmethod(_rows)
    transform = RowTransformer(type_value_map=_TYPE_MAP)
