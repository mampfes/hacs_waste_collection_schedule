import datetime

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Example Source"
DESCRIPTION = "Source for example waste collection."
URL = None
TEST_CASES = {"Example": {"days": 10}}

# Map your provider's waste-type strings to canonical Icons members.
# See custom_components/waste_collection_schedule/waste_collection_schedule/icons.py
# for the full catalogue.
ICON_MAP = {
    "Type1": Icons.GENERAL_WASTE,
    "Type2": Icons.RECYCLING,
    "Type3": Icons.PAPER,
    "Type4": Icons.BIO_KITCHEN,
    "Type5": Icons.GLASS,
}


class Source:
    def __init__(self, days=20, per_day=2, types=5):
        self._days = days
        self._per_day = per_day
        self._types = types

    def fetch(self):
        now = datetime.datetime.now().date()

        entries = []
        ap_type = 0

        for day in range(self._days):
            for _idx in range(self._per_day):
                waste_type = f"Type{(ap_type % self._types) + 1}"
                entries.append(
                    Collection(
                        now + datetime.timedelta(days=day + 7),
                        waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )
                ap_type = ap_type + 1

        return entries
