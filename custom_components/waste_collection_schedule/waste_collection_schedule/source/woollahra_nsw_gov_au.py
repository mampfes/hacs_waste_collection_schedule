from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Woollahra Municipal Council (NSW)"
DESCRIPTION = "Source for Woollahra Municipal Council rubbish collection."
URL = "https://www.woollahra.nsw.gov.au/"
DEEPLINK = f"{URL}Services/Rubbish-and-recycling/Find-your-rubbish-and-scheduled-clean-up-service-dates"
TEST_CASES = {
    "13 Paddington Street Paddington": {
        "address": "13 Paddington Street PADDINGTON NSW 2021",
    },
    "22 Oxford Street Paddington": {
        "address": "22 Oxford Street PADDINGTON NSW 2021",
    },
}

PAGE_LINK = "/$b9015858-988c-48a4-9473-7c193df083e4$/Services/Rubbish-and-recycling/Find-your-rubbish-and-scheduled-clean-up-service-dates"

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "referer": DEEPLINK,
    "x-requested-with": "XMLHttpRequest",
}

ICON_MAP = {
    "general waste": Icons.GENERAL_WASTE,
    "green waste": Icons.ORGANIC,
    "recycling": Icons.RECYCLING,
    "clean": Icons.BULKY,
}

_CONFIG = OpenCitiesConfig(
    domain=URL.rstrip("/"),
    page_link=PAGE_LINK,
    headers=HEADERS,
    use_curl_cffi=True,
    warm_up_url=DEEPLINK,
    icon_keywords=ICON_MAP,
    # Woollahra mixes a recurring problem-waste promo tile into the same
    # response as real dated collections. It is not a kerbside collection.
    exclude_types=("Recycle problem waste",),
)


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        entries = self._client.fetch(address=self._address)

        # Preserve the source's historic canonical labels for seasonal clean-ups.
        for entry in entries:
            lowered = entry.type.lower()
            for season in ("spring", "summer", "winter"):
                if season in lowered and "clean" in lowered:
                    entry.set_type(f"{season.title()} Clean-Up")
                    entry.set_icon(Icons.BULKY)
                    break

        return entries
