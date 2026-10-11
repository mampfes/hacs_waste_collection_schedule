from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    boolean,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import Lookup
from waste_collection_schedule.service.OctoberCms import handler, partial_html
from waste_collection_schedule.transformers import RowTransformer

_URL = "https://mohubudapest.hu/hulladeknaptar"


def _options(html: str) -> list[str]:
    """The choices of a select, without its "please choose" first option."""
    return [
        option.decode_contents()
        for option in BeautifulSoup(html, "html.parser").find_all("option")[1:]
    ]


def _street_value(street: str) -> str:
    """The select's value for a street: its last space is written ``---``."""
    return street[::-1].replace(" ", "---", 1)[::-1]


def _streets(response, *_, district, **__) -> list[str]:
    html = partial_html(response, ".publicPlaces", "ajax/publicPlaces")
    if not html or BeautifulSoup(html, "html.parser").find("div", class_="alert"):
        raise SourceArgumentNotFound("district", district)
    return _options(html)


def _house_numbers(response, streets, *_, street, **__) -> list[str]:
    """The house numbers of the chosen street; the street is saved in the session."""
    html = partial_html(response, ".houseNumbers", "ajax/houseNumbers")
    soup = BeautifulSoup(html, "html.parser")
    if (
        response.status_code >= 400
        or not html
        or soup.find("div", class_="alert")
        or soup.find("option", string="Kérem, előbb válasszon közterületet")
    ):
        raise SourceArgumentNotFoundWithSuggestions("street", street, streets)
    return _options(html)


@final
class Source(BaseSource):
    TITLE = "MOHU Budapest"
    DESCRIPTION = "Source script for www.mohubudapest.hu"
    URL = "https://www.mohubudapest.hu"
    COUNTRY = "hu"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_2": {"district": 1114, "street": "Szent Gellért tér", "house_number": 3},
        "Test_3": {"district": 1202, "street": "Bölön utca", "house_number": 5},
    }

    PARAMS = (
        text_field("district", "District (postcode)", coerce=str),
        street(),
        house_number(),
        # Kept so configurations that set it keep loading; certificates are
        # always verified now.
        boolean("verify", default=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose your district (its postcode, e.g. 1114), street and house "
            "number as the calendar at https://www.mohubudapest.hu/hulladeknaptar "
            "writes them. `verify` is no longer used."
        ),
    }

    # The handlers keep their state in the session: the district narrows the street
    # list, the street narrows the house numbers, and the search then answers for
    # the chosen house number.
    retrieve = handler(
        _URL,
        "onSearch",
        "ajax/calSearchResults",
        lambda streets, numbers, house_number, **_: {"houseNumber": house_number},
        before=(
            Lookup(
                handler(
                    _URL,
                    "onSelectDistricts",
                    "ajax/publicPlaces",
                    lambda district, **_: {"district": district},
                ),
                pick=_streets,
            ),
            Lookup(
                handler(
                    _URL,
                    "onSavePublicPlace",
                    "ajax/houseNumbers",
                    lambda streets, street, **_: {"publicPlace": _street_value(street)},
                    raise_for_status=False,
                ),
                pick=_house_numbers,
            ),
        ),
    )
    parse = parsers.HtmlLabelledDates(
        "tr",
        label="td div",
        date="td:nth-of-type(2)",
        date_pattern=r"(\d{4}\.\d{2}\.\d{2})",
        all_labels=True,
        from_json_key=".results",
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y.%m.%d"),
        type_value_map={
            "Kommunális": wt.GENERAL_WASTE,
            "Szelektív": wt.RECYCLABLES,
            "Zöld": wt.GARDEN_WASTE,
        },
    )
