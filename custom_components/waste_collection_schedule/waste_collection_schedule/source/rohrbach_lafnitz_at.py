import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Rohrbach an der Lafnitz"
DESCRIPTION = "Source for Rohrbach an der Lafnitz, Austria."
URL = "https://www.rohrbach-lafnitz.at"
COUNTRY = "at"

TEST_CASES: dict[str, dict] = {
    "All waste types": {},
}

ICS_BASE_URL = "https://www.rohrbach-lafnitz.at/system/web/CalendarService.ashx"
ICS_PARAMS = {
    "aqn": (
        "UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4w"
        "LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw="
    ),
    "sprache": "1",
    "gnr": "2371",
}

# Calendar IDs for each waste type
ICS_CALENDARS = {
    "Biomüll": "MjI1MTc2NDk0",
    "Leichtverpackungen": "MjI1MTc2NDg4",
    "Restmüll": "MjI1MTc2NDky",
    "Sperrmüll & Heckenschnitt": "MjI1MTc2NDk2",
}

ICON_MAP = {
    "Biomüll": "mdi:leaf",
    "Leichtverpackungen": "mdi:recycle",
    "Restmüll": "mdi:trash-can",
    "Sperrmüll": "mdi:sofa",
}


class Source:
    def __init__(self):
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        entries: list[Collection] = []

        for waste_type, do_param in ICS_CALENDARS.items():
            params = {**ICS_PARAMS, "do": do_param}
            param_str = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{ICS_BASE_URL}?{param_str}"

            r = requests.get(url, timeout=60)
            r.raise_for_status()

            dates = self._ics.convert(r.text)

            for d in dates:
                icon = None
                for key, value in ICON_MAP.items():
                    if key.lower() in waste_type.lower():
                        icon = value
                        break

                entries.append(Collection(date=d[0], t=waste_type, icon=icon))

        return entries
