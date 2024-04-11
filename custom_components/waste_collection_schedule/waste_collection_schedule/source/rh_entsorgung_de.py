from waste_collection_schedule.source.jumomind_de import Source as JumomindSource

TITLE = "Rhein-Hunsrück Entsorgung (RHE)"
DESCRIPTION = "Source for RHE (Rhein Hunsrück Entsorgung)."
URL = "https://www.rh-entsorgung.de"
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


class Source(JumomindSource):
    def __init__(
        self, city: str, street: str, house_number: int, address_suffix: str = ""
    ):
        super().__init__(
            service_id="rhe",
            city=city,
            street=street,
            house_number=str(house_number) + (address_suffix or ""),
        )
