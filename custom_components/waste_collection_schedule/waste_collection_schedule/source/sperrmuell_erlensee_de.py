import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Erlensee"
DESCRIPTION = "Source for waste collection in Erlensee, Hessen."
URL = "https://sperrmuell.erlensee.de/"
COUNTRY = "de"
TEST_CASES = {
    "Am Rathaus": {"street": "Am Rathaus"},
    "Am Haspel": {"street": "Am Haspel"},
    "Oberhörr (Sandhof / Sonnenhof)": {"street": "Oberhörr (Sandhof / Sonnenhof)"},
}
SOURCE_CODEOWNERS = ["@SgtSeppel"]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": f"Go to {URL} and look up the exact street name in the dropdown.",
    "de": f"Öffnen Sie {URL} und entnehmen Sie den Straßennamen aus der Auswahlliste.",
}

PARAM_TRANSLATIONS = {
    "en": {"street": "Street"},
    "de": {"street": "Straße"},
}

PARAM_DESCRIPTIONS = {
    "en": {"street": "Street name as shown in the dropdown on the website."},
    "de": {"street": "Straßenname wie in der Auswahlliste auf der Website angezeigt."},
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Restmüll (MT)": Icons.GENERAL_WASTE,
    "Erlensee stellt raus": Icons.GENERAL_WASTE,
    "Biotonne": Icons.BIO_KITCHEN,
    "Papier": Icons.PAPER,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Gartenabfälle": Icons.GARDEN,
    "Gartenabfall-Straßensammlung": Icons.GARDEN,
    "Sondermüll": Icons.HAZARDOUS,
    "Weihnachtsbaum-Abholung": Icons.CHRISTMAS_TREE,
}

API_URL = "https://sperrmuell.erlensee.de/"

# "timeframe" option 46 = "6 Monate" (rolling six month window, not year bound)
TIMEFRAME = 46


class Source:
    def __init__(self, street: str) -> None:
        self._street = street
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        r = requests.get(API_URL, params={"type": "reminder"}, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        streets = {}
        select = soup.find("select", {"id": "street"})
        if select:
            for option in select.find_all("option"):
                value = option.get("value")
                if value:
                    streets[option.get_text(strip=True)] = int(value)

        if self._street not in streets:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, list(streets.keys())
            )

        event_ids = [
            int(cb["value"])
            for cb in soup.find_all("input", {"name": "eventType[]"})
            if cb.get("value")
        ]

        data = [
            ("street", streets[self._street]),
            ("timeframe", TIMEFRAME),
            ("download", "ical"),
        ]
        for et in event_ids:
            data.append(("eventType[]", et))

        r = requests.post(
            API_URL,
            params={"type": "reminder"},
            data=data,
            timeout=30,
        )
        r.raise_for_status()

        # summaries look like "Restmüll (MT) (Am Rathaus)": only the trailing
        # street suffix may be removed, the waste type itself can contain "(...)"
        street_suffix = f" ({self._street})"

        entries = []
        for date, waste_type in self._ics.convert(r.text):
            name = waste_type.strip()
            if name.endswith(street_suffix):
                name = name[: -len(street_suffix)].strip()
            entries.append(
                Collection(date, name, ICON_MAP.get(name, Icons.GENERAL_WASTE))
            )

        return entries
