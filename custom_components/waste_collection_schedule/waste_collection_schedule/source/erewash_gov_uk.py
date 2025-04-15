from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Erewash Borough Council"
DESCRIPTION = "Source for erewash.gov.uk services for Erewash Borough Council, UK."
URL = "https://www.erewash.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": "100030126659"},
    "Test_002": {"uprn": "100030154311"},
    "Test_003": {"uprn": "100030118783"},
}
ICON_MAP = {
    "recycling-collection-service": "mdi:recycle",
    "garden-waste-collection-service": "mdi:leaf",
    "domestic-waste-collection-service": "mdi:trash-can",
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION: dict = {
    "en": "an easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
}
PARAM_TRANSLATIONS: dict = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}
PARAM_DESCRIPTIONS: dict = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()

        """
        There are two valid urls:
        URL + "/bbd-whitespace/one-year-collection-dates" -- this returns Christmas and New Year dates with no indication which is going to be used.
        URL + "/bbd-whitespace/one-year-collection-dates-without-christmas" -- this exclude Christmas and New Year dates.
        The website says Christmas and New Year dates will be publicised via the website & socials closer to year end.
        I've opted for the first one as it returns more dates.
        If that causes year-end bug reports on GitHub, the alternative can be implemented.
        """

        r = s.get(
            URL + "/bbd-whitespace/one-year-collection-dates",
            # URL + "/bbd-whitespace/one-year-collection-dates-without-christmas"
            params={"uprn": self._uprn, "_wrapper_format": "drupal_ajax"},
            timeout=30,
        )
        r.raise_for_status()

        entries = []

        for _, data in r.json()[0]["settings"]["collection_dates"].items():
            for collection in data:
                entries.append(
                    Collection(
                        date=datetime.fromtimestamp(
                            int(collection["timestamp"])
                        ).date(),
                        t=collection["service"],
                        icon=ICON_MAP.get(collection["service-identifier"]),
                    )
                )

        return entries
