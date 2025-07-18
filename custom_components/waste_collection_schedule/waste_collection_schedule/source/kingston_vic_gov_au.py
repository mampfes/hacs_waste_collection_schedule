from typing import List
from waste_collection_schedule import Collection
from ..service.WhatBinDay import WhatBinDayService, NoOpDeviceKeyStorageManager

TITLE = "City of Kingston"
DESCRIPTION = "Source for City of Kingston (VIC) waste collection."
URL = "https://www.kingston.vic.gov.au"
TEST_CASES = {
    "randomHouse": {
        "street_number": "30C",
        "street_name": "Oakes Avenue",
        "suburb": "CLAYTON SOUTH",
        "post_code": "3169",
    },
    "randomAppartment": {
        "street_number": "1/51",
        "street_name": "Whatley Street",
        "suburb": "CARRUM",
        "post_code": "3197",
    },
    "randomMultiunit": {
        "street_number": "1/1-5",
        "street_name": "Station Street",
        "suburb": "MOORABBIN",
        "post_code": "3189",
    },
}

ICON_MAP = {
    "WasteBin": "mdi:trash-can",
    "RecycleBin": "mdi:recycle",
    "GreenBin": "mdi:leaf",
}

BIN_NAMES = {
    "WasteBin": "General waste (landfill)",
    "RecycleBin": "Recycling",
    "GreenBin": "Food and garden waste",
}

class Source:
    def __init__(self, street_number: str, street_name: str, suburb: str, post_code: str):
        self.street_number = str(street_number)
        self.street_name = str(street_name)
        self.suburb = str(suburb)
        self.post_code = str(post_code)
        
        # Initialize storage manager (will be set up properly when HA context is available)
        self._storage_manager = None
        self._service = None

    def _get_service(self) -> WhatBinDayService:
        """Get or create the WhatBinDay service instance."""
        if self._service is None:
            # Use NoOp storage manager for now
            # TODO: Integrate with HA storage when context is available
            self._storage_manager = NoOpDeviceKeyStorageManager()
            
            # Create service with custom mappings for Kingston
            self._service = WhatBinDayService(
                device_storage_manager=self._storage_manager,
                icon_map=ICON_MAP,
                bin_names=BIN_NAMES,
                app_package="com.socketsoftware.whatbinday.binston"
            )
        
        return self._service

    def fetch(self) -> List[Collection]:
        """Fetch waste collection schedule."""
        service = self._get_service()
        return service.fetch_collections(
            self.street_number,
            self.street_name,
            self.suburb,
            self.post_code,
            state="VIC",
            country="Australia",
            coordinates={"lat": -37.9759, "lng": 145.1350}  # Default Kingston area coordinates
        )
