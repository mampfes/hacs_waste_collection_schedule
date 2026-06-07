from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import coords
from waste_collection_schedule.transformers import KeyValueTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)


class Source(BaseSource):
    TITLE = "Stirling"
    DESCRIPTION = "Source for Stirling."
    URL = "https://www.stirling.wa.gov.au"
    COUNTRY = "au"
    API_URL = "https://www.stirling.wa.gov.au/bincollectioncheck/getresult"

    TEST_CASES = {
        "-31.9034183 115.8320855": {"lat": -31.9034183, "lon": 115.8320855},
        "-31.878331, 115.815553": {"lat": "-31.8783052", "lon": "115.8157741"},
    }

    PARAMS = [coords(lat="lat", lon="lon")]

    transformer = KeyValueTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "red": GENERAL_WASTE,
            "green": ORGANIC,
            "greenverge": GARDEN_WASTE,
            "yellow": RECYCLABLES,
        },
    )

    def __init__(self, lat: float, lon: float):
        if isinstance(lat, str):
            lat = float(lat)
        if isinstance(lon, str):
            lon = float(lon)
        self._headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "configid": "7c833520-7b62-4228-8522-fb1a220b32e8",
            "form": "57753bab-f589-44d7-8934-098b6d5c572f",
            "fields": f"{lon},{lat}",
            "apikeylookup": "Bin Day",
            "Origin": self.URL,
            "Referer": f"{self.URL}/waste-and-environment/waste-and-recycling/bin-collections",
        }
