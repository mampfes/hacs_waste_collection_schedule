from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer


def _label(li) -> str:
    """The service name: "Next rubbish collection date" -> "rubbish"."""
    heading = li.find("h3")
    if heading is not None:
        text = heading.get_text(strip=True)
    else:
        # The garden waste entry has no heading, just two <strong> elements.
        text = li.find("strong").get_text(strip=True)
    text = text.lower().replace("next", "")
    for noise in ("collection date", "collection"):
        text = text.replace(noise, "")
    return text.strip()


def _date(li) -> str | None:
    """ "Wednesday 7 October 2026": in a <p> below the heading, else the 2nd <strong>."""
    if li.find("h3") is not None:
        paragraph = li.find("p")
        return None if paragraph is None else paragraph.get_text(strip=True)
    strongs = li.find_all("strong")
    return strongs[1].get_text(strip=True) if len(strongs) > 1 else None


@final
class Source(BaseSource):
    TITLE = "Stroud District Council"
    DESCRIPTION = "Source for Stroud District Council."
    URL = "https://stroud.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "GL6+9BW 100120517945": {"postcode": "GL6 9BW", "uprn": 100120517945},
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Use your postcode as the `postcode` argument and your Unique "
            "Property Reference Number (UPRN) as the `uprn` argument. You can "
            "find your UPRN at https://www.findmyaddress.co.uk/."
        ),
    }

    retrieve = HttpGetRetriever(
        "https://www.stroud.gov.uk/my-house",
        params=lambda postcode, uprn, **_: {
            "postcode": postcode.strip(),
            "uprn": str(uprn),
        },
    )
    # The page holds a second, empty template panel: its entries have no date
    # and are skipped.
    parse = parsers.HtmlParser("section.panel-rubbish li")
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_label,
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        skip_unparseable_dates=True,
        type_value_map={
            "rubbish": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "garden waste": wt.GARDEN_WASTE,
            "food waste": wt.FOOD_WASTE,
        },
    )
