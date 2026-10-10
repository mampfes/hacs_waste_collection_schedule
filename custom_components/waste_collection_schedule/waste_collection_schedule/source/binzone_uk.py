from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import Compose, ExplodeList
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

# The South & Vale BinDay API returns the property's collection weeks; each
# week lists days ("collection_date": "09/10/2026") and each day the bins
# collected on it ("bin_type": "Recycling"). An unknown UPRN answers "OK" with
# no weeks at all, which RAISE_ON_EMPTY reports.

API_URL = "https://forms.southandvale.gov.uk/api/property/bins/{uprn}"


@final
class Source(BaseSource):
    TITLE = "BinDay (South & Vale)"
    DESCRIPTION = """Consolidated source for waste collection services from:
        South Oxfordshire District Council
        Vale of White Horse District Council
        """
    URL = "https://www.southoxon.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.TEXTILES,
        wt.ELECTRONICS,
        wt.BULKY_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "VOWH": {"uprn": "100120903018"},
        "SO": {"uprn": "100120883950"},
    }

    REGIONS = (
        region(
            "South Oxfordshire District Council", url="https://www.southoxon.gov.uk/"
        ),
        region(
            "Vale of White Horse District Council",
            url="https://www.whitehorsedc.gov.uk/",
        ),
    )

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "An easy way to find your Unique Property Reference Number (UPRN) is by "
            "going to <https://www.findmyaddress.co.uk/> and entering in your "
            "address details."
        ),
    }

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: API_URL.format(uprn=uprn),
        headers={
            "Accept": "application/json",
            "Referer": "https://forms.southandvale.gov.uk/binday.eb",
        },
    )
    parse = parsers.JsonParser(
        "setData",
        "week",
        raise_for_status=True,
        expected_values={"setStatus": "OK"},
    )
    preprocess = Compose(ExplodeList("day"), ExplodeList("bins", into="bin"))
    transform = JsonTransformer(
        date_key="collection_date",
        type_key=lambda record: record["bin"]["bin_type"],
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        # Both bulky-waste services map to BULKY_WASTE; keep the council's
        # label so they stay distinguishable.
        carry_raw_label=True,
        type_value_map={
            "Non-recyclable refuse waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food waste": wt.FOOD_WASTE,
            "Garden Waste subscribers": wt.GARDEN_WASTE,
            "Textiles/Clothes": wt.TEXTILES,
            "Small electricals": wt.ELECTRONICS,
            "Bulky Waste": wt.BULKY_WASTE,
            "Non-Electrical Bulky Waste": wt.BULKY_WASTE,
            "Batteries": wt.OTHER,
        },
    )
