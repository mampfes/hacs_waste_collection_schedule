from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.JaduBinCollections import strip_ordinal
from waste_collection_schedule.transformers import RowTransformer

API_URL = "https://maps.monmouthshire.gov.uk/localinfo.aspx"

_NEAREST_YEAR = date_parsers.nearest_year("%A %d %B")


def _collapse(text: str) -> str:
    """Whitespace runs (the page wraps its text mid-phrase) to single spaces."""
    return " ".join(text.split())


def _date(text: str):
    """ "Tuesday 6th\\n October" -> the date, the year being the nearest to today."""
    return _NEAREST_YEAR(strip_ordinal(_collapse(text)))


def _label(text: str) -> str:
    return _collapse(text).removesuffix(" (pay to use service)")


@final
class Source(BaseSource):
    TITLE = "Monmouthshire Council"
    DESCRIPTION = "Source for Monmouthshire Council, UK."
    URL = "https://www.monmouthshire.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.OTHER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "200000952833": {"uprn": 200000952833},
        "10033354474": {"uprn": 10033354474},
        "10033351693": {"uprn": 10033351693},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting "
            "[Find My Address](https://www.findmyaddress.co.uk) and entering "
            "in your address details."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(
        url=API_URL,
        params=lambda uprn, **_: {"action": "SetAddress", "UniqueId": uprn},
    )

    # One box per round, its name in the <h4> and its next date in the <strong>.
    # An unknown UPRN is answered with an ordinary page without the property
    # details, so the marker tells a bad UPRN from a property with no rounds.
    parse = parsers.ArgumentGuard(
        parsers.HtmlLabelledDates(
            'div[aria-label="Waste Collections"] div.waste',
            label="h4",
            date="strong",
            parse_date=_date,
        ),
        argument="uprn",
        contains="Unique Property Reference Number (UPRN):",
        hint=(
            "the UPRN is invalid or outside the Monmouthshire Council area; "
            "make sure your address returns entries on the council website"
        ),
    )

    transform = RowTransformer(
        clean=_label,
        type_value_map={
            "Household rubbish bag": wt.GENERAL_WASTE,
            "Red & purple recycling bags": wt.RECYCLABLES,
            "Blue food bin": wt.FOOD_WASTE,
            "Green Glass Box": wt.GLASS,
            # No canonical type for nappy and hygiene waste; the raw label is
            # carried so the user still sees which collection it is.
            "Yellow nappy & hygiene waste bag": wt.OTHER,
            "Garden Waste Bins": wt.GARDEN_WASTE,
        },
        carry_raw_label=True,
    )
