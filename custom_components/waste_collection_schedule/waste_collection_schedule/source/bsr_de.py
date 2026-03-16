import requests
from dataclasses import dataclass
from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "Berliner Stadtreinigungsbetriebe"
DESCRIPTION = "Source for Berliner Stadtreinigungsbetriebe waste collection."
URL = "https://bsr.de"
TEST_CASES = {
    "Hufeland_45a": {
        "schedule_id": "04901100010300413840045A",
    },
    "Marktstr_1": {
        "schedule_id": "049011000105000297900010",
    },
}

ENDPOINT_PICKUPS = "https://umnewforms.bsr.de/p/de.bsr.adressen.app/abfuhrEvents"
FILTERTEMPLATE_PICKUPS = \
    "AddrKey eq '{id}' and " + \
    "DateFrom eq datetime'{year_from}-{month:02d}-01T00:00:00' and " + \
    "DateTo eq datetime'{year_to}-{month:02d}-01T00:00:00'"

@dataclass(frozen=True)
class WasteInfo:
    text: str
    icon: str

WASTE_CATEGORY_MAP: dict[str, WasteInfo] = {
    "BI": WasteInfo("Biogut", "mdi:bio"),
    "HM": WasteInfo("Hausmüll", "mdi:trash-can"),
    "LT": WasteInfo("Laubtonne", "mdi:leaf"),
    "WS": WasteInfo("Wertstoffe", "mdi:recycle"),
    "WB": WasteInfo("Weihnachtsbaum", "mdi:pine-tree"),
}


def get_waste_info(waste_category: str) -> WasteInfo:
    return WASTE_CATEGORY_MAP.get(waste_category, WasteInfo(f"Unbekannter Müll ({waste_category})", "mdi:help-circle"))


class Source:
    def __init__(self, schedule_id: str) -> None:
        self._schedule_id = schedule_id

    def fetch(self) -> list[Collection]:
        now = datetime.now()
        args = {
            "filter": FILTERTEMPLATE_PICKUPS.format(id=self._schedule_id, year_from=now.year, month=now.month, year_to=now.year+1),
        }
        with requests.Session() as pickups_session:
            response_raw = pickups_session.get(ENDPOINT_PICKUPS, params=args)
        response = response_raw.json()
        pickups: list[Collection] = []
        """
        This is one entry in the "dates" dictionary in the response:
        "2025-07-10": [{
            "category": "BI",
            "serviceDay": "DO",
            "serviceDate_actual": "10.07.2025",
            "serviceDate_regular": "10.07.2025",
            "rhythm": "gerade Woche",
            "warningText": "",
            "disposalComp": "BSR"
        }],
        It seems that each entry is a list of pickups. We take the serviceDate_actual as the
        date for the pickup (10.07.2025), not the key (2025-07-10).
        This is the created Collection object:
        Collection{date=2025-07-10, type=Biotonne}
        """
        for date_entry in response["dates"].values():
            for pickup_entry in date_entry:
                pickup_date = datetime.strptime(pickup_entry["serviceDate_actual"], "%d.%m.%Y").date()
                waste_info = get_waste_info(pickup_entry["category"])
                pickup_text = waste_info.text if pickup_entry["disposalComp"] == "BSR" else f"{waste_info.text} ({pickup_entry['disposalComp']})"
                pickups.append(Collection(date=pickup_date, t=pickup_text, icon=waste_info.icon))

        return pickups
