from typing import final

from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.regions import region
from waste_collection_schedule.source.jumomind_de import Source as JumomindSource

# Rhein-Hunsrück Entsorgung runs on Jumomind (service id "rhe"). This is the
# same structure as jumomind_de, pinned to the "rhe" service and exposing a
# friendlier address form (an explicit house-number suffix), so it subclasses
# the Jumomind pipeline source and only overrides metadata + __init__.


@final
class Source(JumomindSource):
    TITLE = "Rhein-Hunsrück Entsorgung (RHE)"
    DESCRIPTION = "Source for RHE (Rhein Hunsrück Entsorgung)."
    URL = "https://www.rh-entsorgung.de"
    COUNTRY = "de"

    REGIONS = [region("Rhein-Hunsrück Entsorgung (RHE)", url=URL)]

    TEST_CASES = {
        "Horn": {
            "city": "Rheinböllen",
            "street": "Erbacher Straße",
            "house_number": 13,
            "address_suffix": "A",
        },
        "Bärenbach": {
            "city": "Bärenbach",
            "street": "Schwarzener Straße",
            "house_number": 10,
        },
    }

    # service_id is fixed to "rhe", so it is not a user param here. The optional
    # address_suffix is folded into the house number before the parent runs.
    PARAMS = [
        text_field("city", "Ort"),
        text_field("street", "Straße"),
        text_field("house_number", "Hausnummer"),
        text_field("address_suffix", "Hausnummerzusatz", optional=True),
    ]

    def __init__(
        self, city: str, street: str, house_number: int, address_suffix: str = ""
    ):
        super().__init__(
            service_id="rhe",
            city=city,
            street=street,
            house_number=str(house_number) + (address_suffix or ""),
        )
