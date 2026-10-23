import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, postcode
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.VerintCloud import (
    VerintCloudRetriever,
    VerintStep,
)
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "grey rubbish bin": wt.GENERAL_WASTE,
    "beige recycling bin": wt.PAPER,
    "burgundy plastic bin": wt.RECYCLABLES,
    "burgundy glass bin": wt.GLASS,
    "green garden bin": wt.GARDEN_WASTE,
    "food caddy": wt.FOOD_WASTE,
}


def _address_id(previous, *, postcode, house_number, **_) -> str:
    """The id of the address the property search offers for the house number."""
    addresses = previous.json()["data"]
    if not addresses:
        raise SourceArgumentNotFound("postcode", postcode)
    wanted = str(house_number)
    for address in addresses:
        label = address["label"]
        if label == wanted or label.startswith((f"{wanted} ", f"{wanted},")):
            return address["value"]
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number", wanted, [address["label"] for address in addresses]
    )


def _clean_label(label: str) -> str:
    """``"240L beige recycling bin:"`` -> ``"beige recycling bin"``."""
    return re.sub(r"^\d+L\s+", "", " ".join(label.split()).rstrip(":").strip())


@final
class Source(BaseSource):
    TITLE = "Bolton Council"
    DESCRIPTION = "Source for Bolton Council, UK."
    URL = "https://www.bolton.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_Postcode_Without_Space": {"postcode": "BL52AX", "house_number": "13"},
        "Test_Postcode_With_Space": {"postcode": "BL1 5BQ", "house_number": "14"},
        "Test_House_With_Street_Before_Number": {
            "postcode": "BL1 5XR",
            "house_number": "WOODSLEIGH COPPICE, 2",
        },
    }

    PARAMS = (postcode(), house_number())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and the start of your address as the council's "
            "address list shows it (the house number, or a house name)."
        ),
    }

    retrieve = VerintCloudRetriever(
        "https://bolton.form.uk.empro.verintcloudservices.com/",
        form="es_bin_collection_dates",
        headers={"referer": "https://bolton.form.uk.empro.verintcloudservices.com/"},
        steps=(
            VerintStep(
                "api/widget?action=propertysearch&actionedby=ps_address"
                "&loadform=true&access=citizen&locale=en",
                data=lambda previous, postcode, **_: {"postcode": postcode},
            ),
            # Selecting the address answers with the property's canonical UPRN.
            VerintStep(
                lambda previous, **p: (
                    f"api/setobjectid?objecttype=property&objectid={_address_id(previous, **p)}"
                    "&loaddata=true"
                ),
            ),
            VerintStep(
                "api/custom?action=es_get_bin_collection_dates"
                "&actionedby=uprn_changed&loadform=true&access=citizen&locale=en",
                data=lambda previous, **_: {
                    "uprn": previous.json()["profileData"]["property-UPRN"],
                    "start_date": (
                        datetime.datetime.now() - datetime.timedelta(days=1)
                    ).strftime("%d/%m/%Y"),
                    "end_date": (
                        datetime.datetime.now() + datetime.timedelta(days=365)
                    ).strftime("%d/%m/%Y"),
                },
            ),
        ),
    )
    # The dates come as HTML inside the reply: a block per bin with its name and
    # one list item per collection.
    parse = parsers.HtmlLabelledDates(
        'div[style*="overflow:auto"]',
        label="strong",
        date="ul",
        date_pattern=r"(\d{1,2} [A-Za-z]+ \d{4})",
        all_dates=True,
        from_json_key=("data", "collection_dates"),
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d %B %Y"),
        clean=_clean_label,
        type_value_map=_TYPE_MAP,
    )
