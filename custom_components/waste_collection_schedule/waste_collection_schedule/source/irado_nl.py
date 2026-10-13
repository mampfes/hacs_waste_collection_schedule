import datetime
import re
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://www.irado.nl/afvalkalender"
POSTCODE_PATTERN = re.compile(r"^(\d{4})\s*([A-Za-z]{2})$")


def _address_form(
    postcode: str = "", house_number: str = "", suffix: str = "", **_
) -> dict[str, str]:
    """The address form the calendar page itself posts."""
    match = POSTCODE_PATTERN.match(str(postcode).strip())
    if not match:
        raise SourceArgumentNotFound(
            "postcode",
            postcode,
            "postcode must consist of 4 digits followed by 2 letters, e.g. 3131VX",
        )
    return {
        "appointment_zipcode": match.group(1),
        "appointment_zipcode_suffix": match.group(2).upper(),
        "appointment_housenumber": str(house_number).strip(),
        "appointment_housenumber_suffix": (suffix or "").strip(),
        "wsa_calendar": "4498794404",
    }


def _address_known(response, postcode: str = "", house_number: str = "", **_) -> bool:
    """Irado answers an unknown address with an error message in the page."""
    if "form-error-message" in response.text:
        raise SourceArgumentNotFound(
            "postcode/house_number",
            f"{postcode} {house_number}",
            "this combination of postcode and house number is not known by Irado. "
            "Please verify it at https://www.irado.nl/afvalkalender",
        )
    return True


def _date(entry: Tag) -> datetime.date:
    """The collection date: day cell inside a month grid under a year heading."""
    grid = entry.find_parent("div", class_="av-cal")
    month = recurrence.month(grid.select_one(".avk-cal-header").get_text(strip=True))
    year = grid.find_previous("div", class_="avk-year").get_text(strip=True)
    day = entry.find_parent("span", class_="pickup-day").select_one(".d-number")
    return datetime.date(int(year), month, int(day.get_text(strip=True)))


def _type(entry: Tag) -> str:
    for cls in entry.get("class", []):
        if cls.startswith("pickup-part-"):
            return cls[len("pickup-part-") :]
    return ""


@final
class Source(BaseSource):
    TITLE = "Irado"
    DESCRIPTION = (
        "Source for Irado waste collection services, covering Vlaardingen, Schiedam, "
        "Maassluis, Capelle aan den IJssel and Voorne aan Zee (Netherlands)."
    )
    URL = "https://www.irado.nl"
    COUNTRY = "nl"

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Zwanensingel_no_suffix": {"postcode": "3136GZ", "house_number": "7"},
        "Platanendreef_with_suffix": {
            "postcode": "3137CN",
            "house_number": "2",
            "suffix": "A",
        },
    }

    PARAMS = (
        postcode(house_field="house_number"),
        text_field("suffix", "House number suffix", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the postcode (e.g. 3131VX) and house number you would use at "
            "https://www.irado.nl/afvalkalender"
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    # Posting the address stores it in the session; the year view then shows it.
    retrieve = retrievers.Request(
        API_URL,
        params={"view": "year"},
        before=[
            retrievers.Lookup(
                API_URL, method="POST", data=_address_form, pick=_address_known
            )
        ],
    )

    # Days of the neighbouring months are padded in as "inactive" cells and
    # shown again, active, in their own month.
    parse = parsers.HtmlParser(
        ".av-cal .day.active .pickup-part",
        require=[".av-cal", ".avk-year"],
    )

    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_type,
        type_value_map={
            "restafval": wt.GENERAL_WASTE,
            "gft": wt.ORGANIC,
            "papier": wt.PAPER,
            "pmd": wt.RECYCLABLES,
        },
    )
