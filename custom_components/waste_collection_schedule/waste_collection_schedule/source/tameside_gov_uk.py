from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://public.tameside.gov.uk/forms/bin-dates.asp"


def _postcode(value) -> str:
    return str(value).upper().strip().replace(" ", "")


def _date(img) -> str:
    """The calendar is a table per year, a row per month and a cell per day."""
    year = img.find_parent("fieldset", class_="year").find("h3").get_text(strip=True)
    month = img.find_parent("tr", class_="month").find("td", class_="month")
    day = img.find_parent("td", class_="day").find("div", class_="day")
    # "14th": the suffix sits in its own span.
    return f"{next(day.strings).strip()} {month.get_text(strip=True)} {year}"


def _label(img) -> str:
    """``brown_bin_Icon`` -> ``Brown bin``."""
    return img["alt"].replace("_Icon", "").replace("_", " ").capitalize()


@final
class Source(BaseSource):
    TITLE = "Tameside Metropolitan Borough Council"
    DESCRIPTION = (
        "Source for tameside.gov.uk, Tameside Metropolitan Borough Council, UK"
    )
    URL = "https://www.tameside.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.PAPER, wt.OTHER]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "M34 6AG", "uprn": "100011601683"},
        "Test_002": {"postcode": "ol5 9jl", "uprn": "100011548952"},
        "Test_003": {"postcode": "SK148JP", "uprn": 100011573345},
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and your UPRN, which you can find at "
            "[FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)."
        ),
    }

    retrieve = retrievers.Request(
        API_URL,
        method="POST",
        data=lambda postcode, uprn, **_: {
            "F03_I01_SelectAddress": f"{uprn}-{_postcode(postcode)}",
            "AdvanceSearch": "Continue",
            "F01_I02_Postcode": _postcode(postcode),
            "F01_I03_Street": "",
            "F01_I04_Town": "",
            "history": ",1,3,",
        },
    )

    parse = parsers.HtmlParser("fieldset.year img.binIcon")

    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_label,
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map={
            "Green bin": wt.GENERAL_WASTE,
            "Blue bin": wt.PAPER,
            "Brown bin": wt.OTHER,
            "Black bin": wt.OTHER,
        },
        carry_raw_label=True,
    )
