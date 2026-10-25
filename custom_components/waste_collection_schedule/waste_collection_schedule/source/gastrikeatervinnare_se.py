from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Gästrike Återvinnare"
DESCRIPTION = "Source for Gästrike Återvinnare waste collection"
URL = "https://gastrikeatervinnare.se/"
COUNTRY = "se"
TEST_CASES = {
    "Police Sandviken": {"street": "Bryggargatan 6", "city": "Sandviken"},
}

SEARCH_REMOVED = (
    "Gästrike Återvinnare has removed its public collection day search; the "
    "days are now only shown on Mina sidor (https://minasidor.gastrikeatervinnare.se) "
    "after login. This source can no longer fetch them. Version 3.0.0 of Waste "
    "Collection Schedule reads Mina sidor with your customer number and password."
)


class Source:
    def __init__(self, street, city):
        self._street = street
        self._city = city

    def fetch(self) -> list[Collection]:
        raise SourceArgumentException("street", SEARCH_REMOVED)
