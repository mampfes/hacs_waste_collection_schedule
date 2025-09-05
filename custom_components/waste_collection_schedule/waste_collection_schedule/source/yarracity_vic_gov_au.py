from datetime import date, timedelta
from waste_collection_schedule import Collection

TITLE = "Yarra City Council (VIC)"
DESCRIPTION = "Yarra bin schedule by zone (weekly rubbish + FOGO; alternating recycling/glass)"
URL = "https://www.yarracity.vic.gov.au/residents/bins-waste-recycling-and-cleansing/recycling-and-rubbish/bin-collection"
TAGS = ["vic", "yarra", "australia"]

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "FOGO": "mdi:leaf",
    "Recycling": "mdi:recycle",
    "Glass": "mdi:glass-fragile",
}

# Seeds for 2025–26, Zone 10
ZONE_CFG = {
    10: {
        "weekday": 4,  # Monday=0 .. Sunday=6; Friday=4
        "fy_start": date(2025, 7, 1),
        "fy_end": date(2026, 6, 30),
        "recycling_seed": date(2025, 7, 4),
        "glass_seed": date(2025, 7, 11),
        "holiday_shifts": {
            date(2025, 12, 26): date(2025, 12, 27),
            date(2026, 4, 3): date(2026, 4, 4),
        },
    }
}


class Source:
    def __init__(self, zone: int = 10):
        if zone not in ZONE_CFG:
            raise ValueError("Unsupported Yarra zone (use 1–10)")
        self.cfg = ZONE_CFG[zone]

    def _weekly_dates(self, start, end):
        d = start + timedelta((self.cfg["weekday"] - start.weekday()) % 7)
        while d <= end:
            yield d
            d += timedelta(days=7)

    def _fortnightly_dates(self, seed, end):
        d = seed
        while d <= end:
            yield d
            d += timedelta(days=14)

    def fetch(self):
        out = []

        # Weekly: rubbish + FOGO
        for d in self._weekly_dates(self.cfg["fy_start"], self.cfg["fy_end"]):
            dd = self.cfg["holiday_shifts"].get(d, d)
            out.append(Collection(dd, "Rubbish", icon=ICON_MAP["Rubbish"]))
            out.append(Collection(dd, "FOGO", icon=ICON_MAP["FOGO"]))

        # Fortnightly: recycling
        for d in self._fortnightly_dates(self.cfg["recycling_seed"], self.cfg["fy_end"]):
            if d >= self.cfg["fy_start"]:
                dd = self.cfg["holiday_shifts"].get(d, d)
                out.append(Collection(dd, "Recycling", icon=ICON_MAP["Recycling"]))

        # Fortnightly: glass
        for d in self._fortnightly_dates(self.cfg["glass_seed"], self.cfg["fy_end"]):
            if d >= self.cfg["fy_start"]:
                dd = self.cfg["holiday_shifts"].get(d, d)
                out.append(Collection(dd, "Glass", icon=ICON_MAP["Glass"]))

        return out
