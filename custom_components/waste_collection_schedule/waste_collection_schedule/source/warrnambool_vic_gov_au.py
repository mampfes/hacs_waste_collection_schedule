from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import Compose, ExplodeList, RequireRecords
from waste_collection_schedule.transformers import RowTransformer

PAGE_URL = "https://www.warrnambool.vic.gov.au/kerbside-bin-collection"
# The address field's own autocomplete, as declared on the page.
AUTOCOMPLETE_URL = (
    "https://www.warrnambool.vic.gov.au/views-autocomplete-filters/"
    "wcc_bins_data/block_1/address/0"
)


def _rounds(row, _source):
    """``Wednesday 04 November - `` / ``Recycling, Glass`` -> one row per bin."""
    date_text = row.select_one(".pickup_date").get_text(" ", strip=True)
    date_text = date_text.rstrip(" -").split(" ", 1)[-1]  # drop the weekday
    labels = row.select_one(".pickup_type").get_text(" ", strip=True)
    return [(date_text, label.strip()) for label in labels.split(",") if label.strip()]


@final
class Source(BaseSource):
    TITLE = "Warrnambool City Council"
    DESCRIPTION = "Source for Warrnambool City Council waste collection."
    URL = "https://www.warrnambool.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Kiama Ave": {"street_address": "3 Kiama Ave WARRNAMBOOL VIC 3280"},
        "Henna St": {"street_address": "13 Henna St WARRNAMBOOL VIC 3280"},
    }
    PARAMS = (street_address("street_address"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            f"Search for your address on {PAGE_URL} and enter it exactly as the "
            "address field suggests it, e.g. 3 Kiama Ave WARRNAMBOOL VIC 3280. Since "
            "the v3 pipeline migration, waste types use canonical, localised names. "
            "Update filters, automations and customisations using the old labels."
        ),
    }
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.ORGANIC,
    ]

    # The council's own bin-day search: the page answers the address with the
    # next two collection days of its zone.
    retrieve = retrievers.Request(
        PAGE_URL, params=lambda street_address, **_: {"address": street_address}
    )
    parse = parsers.HtmlParser(
        "div.bin-dates", require=["#views-exposed-form-wcc-bins-data-block-1"]
    )
    preprocess = Compose(
        RequireRecords(
            argument="street_address",
            suggestions=retrievers.Suggestions(
                AUTOCOMPLETE_URL,
                params=lambda street_address, **_: {"q": street_address},
                pick=lambda response, **_: [item["value"] for item in response.json()],
            ),
            hint=f"Check the address on {PAGE_URL}",
        ),
        ExplodeList(_rounds),
    )
    transform = RowTransformer(
        # The page gives no year and lists the next fortnight only.
        parse_date=date_parsers.nearest_year("%d %B"),
        type_value_map={
            "Landfill": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Glass": wt.GLASS,
            "FOGO": wt.ORGANIC,
        },
    )
