import datetime

import requests
from icalendar import Calendar
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "123abfallkalender"
DESCRIPTION = "Source script for 123abfallkalender.de (Ebsdorfergrund)"
URL = "https://www.123abfallkalender.de/"

EXTRA_INFO = [
    {
        "title": "Beltershausen",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/1-beltershausen",
        "default_params": {
            "district": "Beltershausen",
        },
    },
    {
        "title": "Dreihausen",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/2-dreihausen",
        "default_params": {
            "district": "Dreihausen",
        },
    },
    {
        "title": "Ebsdorf",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/3-ebsdorf",
        "default_params": {
            "district": "Ebsdorf",
        },
    },
    {
        "title": "Frauenberg",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/4-frauenberg",
        "default_params": {
            "district": "Frauenberg",
        },
    },
    {
        "title": "Hachborn",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/5-hachborn",
        "default_params": {
            "district": "Hachborn",
        },
    },
    {
        "title": "Heskem",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/6-heskem",
        "default_params": {
            "district": "Heskem",
        },
    },
    {
        "title": "Ilschhausen",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/7-ilschhausen",
        "default_params": {
            "district": "Ilschhausen",
        },
    },
    {
        "title": "Leidenhofen",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/8-leidenhofen",
        "default_params": {
            "district": "Leidenhofen",
        },
    },
    {
        "title": "Mölln",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/9-molln",
        "default_params": {
            "district": "Mölln",
        },
    },
    {
        "title": "Rauischholzhausen",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/10-rauischholzhausen",
        "default_params": {
            "district": "Rauischholzhausen",
        },
    },
    {
        "title": "Roßberg",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/11-rossberg",
        "default_params": {
            "district": "Roßberg",
        },
    },
    {
        "title": "Wermertshausen",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/12-wermertshausen",
        "default_params": {
            "district": "Wermertshausen",
        },
    },
    {
        "title": "Wittelsberg",
        "url": "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund/13-wittelsberg",
        "default_params": {
            "district": "Wittelsberg",
        },
    },
]

SUPPORTED_DISTRICTS = {
    "Beltershausen": "1-beltershausen",
    "Dreihausen": "2-dreihausen",
    "Ebsdorf": "3-ebsdorf",
    "Frauenberg": "4-frauenberg",
    "Hachborn": "5-hachborn",
    "Heskem": "6-heskem",
    "Ilschhausen": "7-ilschhausen",
    "Leidenhofen": "8-leidenhofen",
    "Mölln": "9-molln",
    "Rauischholzhausen": "10-rauischholzhausen",
    "Roßberg": "11-rossberg",
    "Wermertshausen": "12-wermertshausen",
    "Wittelsberg": "13-wittelsberg",
}

TEST_CASES = {
    "Beltershausen": {"district": "Beltershausen"},
    "Dreihausen": {"district": "Dreihausen"},
    "Ebsdorf": {"district": "Ebsdorf"},
    "Frauenberg": {"district": "Frauenberg"},
    "Hachborn": {"district": "Hachborn"},
    "Heskem": {"district": "Heskem"},
    "Ilschhausen": {"district": "Ilschhausen"},
    "Leidenhofen": {"district": "Leidenhofen"},
    "Mölln": {"district": "Mölln"},
    "Rauischholzhausen": {"district": "Rauischholzhausen"},
    "Roßberg": {"district": "Roßberg"},
    "Wermertshausen": {"district": "Wermertshausen"},
    "Wittelsberg": {"district": "Wittelsberg"},
}

API_URL = "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund"
ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "Altpapier": "mdi:recycle",
    "Gelbe Tonne": "mdi:recycle",
    "MR Sondermüll": "mdi:delete",
    "EBS Sondermüll": "mdi:delete",
    "Praxis GmbH": "mdi:medical-bag",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your district from the list.",
    "de": "Wählen Sie Ihren Ortsteil aus der Liste.",
}

PARAM_DESCRIPTIONS = {"en": {"district": "District"}, "de": {"district": "Ortsteil"}}

PARAM_TRANSLATIONS = {
    "en": {
        "district": "District",
    },
    "de": {
        "district": "Ortsteil",
    },
}


class Source:
    def __init__(self, district: str):
        if district not in SUPPORTED_DISTRICTS:
            raise SourceArgumentNotFoundWithSuggestions(
                "district", district, list(SUPPORTED_DISTRICTS.keys())
            )
        self._slug = SUPPORTED_DISTRICTS[district]

    def fetch(self) -> list[Collection]:
        url = f"{API_URL}/{self._slug}.ics?alert=never"

        r = requests.get(url, timeout=30)
        r.raise_for_status()
        cal = Calendar.from_ical(r.content)

        entries = []

        for event in cal.walk("VEVENT"):
            summary = str(event.get("SUMMARY", "Unbekannt"))
            date = event.get("DTSTART").dt
            if isinstance(date, datetime.datetime):
                date = date.date()
            entries.append(
                Collection(
                    date=date, t=summary, icon=ICON_MAP.get(summary, "mdi:trash-can")
                )
            )

        if not entries:
            raise Exception(f"No entries for district {self._slug}")

        return entries
