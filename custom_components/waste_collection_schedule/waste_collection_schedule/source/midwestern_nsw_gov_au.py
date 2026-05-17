from datetime import date, timedelta

from waste_collection_schedule import Collection

TITLE = "Mid-Western Regional Council"
DESCRIPTION = "Waste collection source for Mid-Western Regional Council NSW"
URL = "https://www.midwestern.nsw.gov.au/"

TEST_CASES = {
    "Mudgee North Monday": {"area": "mudgee_north_monday"},
}

ICON_MAP = {
    "Landfill": "mdi:trash-can",
    "FOGO": "mdi:leaf",
    "Recycling": "mdi:recycle",
    "Paper/Cardboard": "mdi:newspaper",
}

AREAS = {
    "mudgee_north_monday": 0,
    "mudgee_north_thursday": 3,
    "mudgee_south_tuesday": 1,
    "mudgee_south_wednesday": 2,
    "gulgong_monday": 0,
    "gulgong_thursday": 3,
    "kandos_rylstone_friday": 4,
}


class Source:
    def __init__(self, area):
        if area not in AREAS:
            raise ValueError(f"Unknown area: {area}")

        self._area = area
        self._collection_day = AREAS[area]

    def fetch(self):
        entries = []
        today = date.today()

        for i in range(365):
            current = today + timedelta(days=i)

            if current.weekday() != self._collection_day:
                continue

            entries.append(Collection(date=current, t="Landfill"))
            entries.append(Collection(date=current, t="FOGO"))

            # TEMP anchor until we confirm the exact MWRC alternating week pattern.
            # Even ISO weeks = Recycling, odd ISO weeks = Paper/Cardboard.
            if current.isocalendar().week % 2 == 0:
                entries.append(Collection(date=current, t="Recycling"))
            else:
                entries.append(Collection(date=current, t="Paper/Cardboard"))

        return entries