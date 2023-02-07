import enum
from datetime import datetime
from homeassistant.const import (
    ATTR_ICON,
    ATTR_ENTITY_PICTURE,
)
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
import requests
from bs4 import BeautifulSoup
import jq

TITLE = "Innherred Renovasjon"
DESCRIPTION = "Source for Innherred renovasjon, Norway"
URL = "https://ir.nt.no"
URL_CALENDAR = "https://innherredrenovasjon.no/tommeplan/{premise_id}/kalender/"
TEST_CASES = {
    "TestcaseI": {
        "premise_id": "5779878e-e9e2-4019-8f0d-d4b132356077",
    },
}


class WasteType(enum.Enum):
    """Represent a waste type"""

    GENERIC = "GENERIC"
    PAPER = "PAPER"
    FOOD = "FOOD"
    PLASTIC = "PLASTIC"
    GLASS_METAL = "GLASS_METAL"

    def __str__(self) -> str:  # pylint: disable=invalid-str-returned
        """Return the event."""
        return self.value


WASTE_TYPES = {
    "Restavfall": WasteType.GENERIC,
    "Papp/papir": WasteType.PAPER,
    "Matavfall": WasteType.FOOD,
    "Plastemballasje": WasteType.PLASTIC,
    "Glass- og metallemballasje": WasteType.GLASS_METAL,
}
ICON_MAP = {
    WasteType.GENERIC: {
        ATTR_ICON: "mdi:trash-can",
        ATTR_ENTITY_PICTURE: "https://innherredrenovasjon.no/wp-content/themes/innherred-renovasjon-2020/images/garbage-disposals/symbol-9991.jpg",
    },
    WasteType.PAPER: {
        ATTR_ICON: "mdi:package-variant",
        ATTR_ENTITY_PICTURE: "https://innherredrenovasjon.no/wp-content/themes/innherred-renovasjon-2020/images/garbage-disposals/symbol-1222.jpg",
    },
    WasteType.FOOD: {
        ATTR_ICON: "mdi:leaf",
        ATTR_ENTITY_PICTURE: "https://innherredrenovasjon.no/wp-content/themes/innherred-renovasjon-2020/images/garbage-disposals/symbol-1111.jpg",
    },
    WasteType.PLASTIC: {
        ATTR_ICON: "mdi:trash-can-outline",
        ATTR_ENTITY_PICTURE: "https://innherredrenovasjon.no/wp-content/themes/innherred-renovasjon-2020/images/garbage-disposals/symbol-4.jpg",
    },
    WasteType.GLASS_METAL: {
        ATTR_ICON: "mdi:bottle-wine-outline",
        ATTR_ENTITY_PICTURE: "https://innherredrenovasjon.no/wp-content/themes/innherred-renovasjon-2020/images/garbage-disposals/symbol-5.jpg",
    },
}


class Source:
    """Waste Collection Source for Innherred Renovasjon"""

    def __init__(self, premise_id):
        self._premise_id = premise_id

    def fetch(self):
        """Fetch fetch"""
        response = requests.get(
            URL_CALENDAR.format(premise_id=self._premise_id),
            headers=self.default_headers,
        )
        soup = BeautifulSoup(response.content, "html.parser")

        items = (
            jq.compile(
                "[. as $m|range(0;$m|length;2)|[{date:($m[.+1]),type: $m[(.)]}]]|add"
            )
            .input(
                [
                    elem.get_text(strip=True)
                    for elem in soup.select(
                        ".gd-calendar__list-item div:not(.gd-calendar__list-item-symbol)"
                    )
                ]
            )
            .first()
        )

        entries = []
        for item in items:
            waste_type = WASTE_TYPES.get(item.get("type"), WasteType.GENERIC)
            waste_icon = ICON_MAP.get(waste_type)
            item_date = f"{item.get('date')}.{datetime.today().year}"
            entries.append(
                Collection(
                    date=datetime.strptime(item_date, "%d.%m.%Y").date(),
                    t=item.get("type"),
                    icon=waste_icon.get(ATTR_ICON),
                    picture=waste_icon.get(ATTR_ENTITY_PICTURE),
                )
            )
        return entries

    @property
    def default_headers(self):
        """Return default headers."""
        return {
            "User-Agent": "Mozilla/5.0",
            "Cache-Control": "max-age=0",
        }
