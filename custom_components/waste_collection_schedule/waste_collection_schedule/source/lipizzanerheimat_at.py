from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    city,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import Lookup
from waste_collection_schedule.service.Jolioo import CalendarParser, call
from waste_collection_schedule.transformers import RowTransformer

# The app's key and secret ship inside the Lipizzanerheimat app.
_KEY = "bd75bdbc46162e4995a9"
_SECRET = "2c811f6c8f97eef2ed40"
# Every community of the app, for the calendars-by-name listing.
_ALL_COMMUNITIES = "234|110|110|111|112|241|238|119|113|236|114|237|115|116|117|235"

_TYPE_MAP = {
    "Müll": wt.GENERAL_WASTE,
    "Restmüll": wt.GENERAL_WASTE,
    "Restmüll - 8-wöchentlich": wt.GENERAL_WASTE,
    "Restmüll - 4-wöchentlich": wt.GENERAL_WASTE,
    "Restmüll - 2-wöchentlich": wt.GENERAL_WASTE,
    "Bioabfall": wt.ORGANIC,
    "Biomüll - wöchentlich": wt.ORGANIC,
    "Biomüll": wt.ORGANIC,
    "Biotonne": wt.ORGANIC,
    "Gefäßreinigung Bioabfall": wt.OTHER,
    "Behälterreinigung Bioabfall": wt.OTHER,
    "Sperrmüll": wt.BULKY_WASTE,
    "Spermüll - Alteisenabfuhr": wt.BULKY_WASTE,
    "Glas": wt.GLASS,
    "Altpapier": wt.PAPER,
    "Zwischenabfuhr Altpapier": wt.PAPER,
    "Problemstoffe": wt.HAZARDOUS,
    "Problemstoffübernahme": wt.HAZARDOUS,
    "Metallverpackung": wt.METAL,
    "Metall": wt.METAL,
    "Kunststoffverpackung": wt.PLASTIC,
    "Kunststoff": wt.PLASTIC,
    "Leichtverpackung": wt.PLASTIC,
    "Leicht- und Metallverpackung": wt.RECYCLABLES,
    "Gelber Sack": wt.PLASTIC,
    "Gelber Sack - 6-wöchentlich": wt.PLASTIC,
    "Silofoliensammlung": wt.PLASTIC,
    "Wirtschaftshof": wt.OTHER,
    "MET KKG": wt.OTHER,
    "ASZ": wt.OTHER,
}


def _community_id(response, *_, town, **__) -> str:
    communities = response.json()["data"]
    for community in communities:
        if community["community_title"] == town:
            return community["community_id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "town", town, [c["community_title"] for c in communities]
    )


def _calendar_id(response, *_, street=None, town=None, map_name=None, **__):
    """The calendar of the street in the town, or the one called ``map_name``."""
    data = response.json()["data"]
    if street and town:
        streets = data["street_structure"]
        for item in streets:
            if item["garbage_calendar_street"] == street:
                return item["garbage_calendars_available"][0]
        raise SourceArgumentNotFoundWithSuggestions(
            "street", street, [s["garbage_calendar_street"] for s in streets]
        )
    calendars = data["garbage_calendars"]
    for item in calendars:
        if item["garbage_calendar_title"] == map_name:
            return item["garbage_calendar_id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "map_name", map_name, [c["garbage_calendar_title"] for c in calendars]
    )


@final
class Source(BaseSource):
    TITLE = "APP Lipizzanerheimat"
    DESCRIPTION = "Source for Lipizzanerheimat App"
    URL = "https://www.lipizzanerheimat.at"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.OTHER,
    ]

    REGIONS = (
        region("Bärnbach", url="https://baernbach.gv.at"),
        region("Edelschrott", url="https://www.edelschrott.gv.at"),
        region("Geistthal-Södingberg", url="https://geistthal-soedingberg.at"),
        region("Hirschegg-Pack", url="https://www.hirschegg-pack.gv.at"),
        region("Kainach", url="https://www.kainach.at"),
        region("Köflach", url="https://www.koeflach.at"),
        region("Krottendorf-Gaisfeld", url="https://www.krottendorf-gaisfeld.gv.at"),
        region("Ligist", url="https://www.ligist.gv.at"),
        region("Maria Lankowitz", url="https://www.maria-lankowitz.at"),
        region("Mooskirchen", url="https://www.mooskirchen.at"),
        region("Rosental a.d Kainach", url="https://www.rosental-kainach.at"),
        region(
            "Sankt Martin am Wöllmißberg", url="https://st-martin-woellmissberg.gv.at"
        ),
        region("Söding-Sankt Johann", url="https://www.soeding-st-johann.gv.at"),
        region("Stallhofen", url="https://www.stallhofen.gv.at"),
        region("Voitsberg", url="https://voitsberg.gv.at"),
    )

    TEST_CASES: ClassVar[dict] = {
        "Köflach - Endgasse": {"town": "Köflach", "street": "Endgasse"},
        "Voitsberg - Bahnweg": {"town": "Voitsberg", "street": "Bahnweg"},
        "Köflach - 8580 Köflach 1/7/9/13/30": {
            "map_name": "8580 Köflach 1/7/9/13/30",
        },
        "Voitsberg - Am Hügel": {"town": "Voitsberg", "street": "Am Hügel"},
        "8580 Köflach 1/13/14/30": {"map_name": "8580 Köflach 1/13/14/30"},
    }

    PARAMS = (
        alternatives(
            [city("town"), street()],
            [text_field("map_name", "Calendar Map Name")],
            [text_field("garbage_calendar_id", "Garbage Calendar ID")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open the Lipizzanerheimat app, login or use guest mode, select your "
            "town, go to the garbage calendar view and select the street you want "
            "to get the garbage collection dates for. You can either provide the "
            "calendar name in the lower center, the street name and town as "
            "written in the dropdown or provide the garbage_calendar_id directly."
        ),
        "de": (
            "Öffnen Sie die Lipizzanerheimat-App, melden Sie sich an oder nutzen "
            "Sie den Gastmodus, wählen Sie Ihre Stadt aus, gehen Sie zur Ansicht "
            "des Müllkalenders und wählen Sie die Straße aus, für die Sie die "
            "Müllabfuhrtermine erhalten möchten. Sie können entweder den "
            "Kalendernamen in der unteren Mitte, den Straßennamen und die Stadt, "
            "wie sie im Dropdown-Menü geschrieben sind, oder direkt die "
            "garbage_calendar_id angeben."
        ),
    }

    # 1. the town's community id (only for a street in a town), 2. the calendar
    # id: the street's calendar in that community, the calendar called map_name,
    # or the garbage_calendar_id as given, 3. the calendar.
    retrieve = call(
        _KEY,
        _SECRET,
        "garbagecalendar",
        lambda community_id, calendar_id, **_: {
            "garbage_calendar_id": calendar_id,
            "language": "de",
        },
        before=(
            Lookup(
                call(
                    _KEY,
                    _SECRET,
                    "getcommunities",
                    {"language": "de"},
                ),
                when=lambda *keys, street=None, town=None, **_: bool(street and town),
                pick=_community_id,
            ),
            Lookup(
                call(
                    _KEY,
                    _SECRET,
                    "garbagecalendarindexwithstreets",
                    lambda community_id, **_: {
                        "language": "de",
                        "communities": community_id or _ALL_COMMUNITIES,
                        "garbage_calendar_id": 1,
                    },
                ),
                given=lambda *keys, garbage_calendar_id=None, street=None, town=None, map_name=None, **_: (
                    garbage_calendar_id
                    if garbage_calendar_id and not (street and town) and not map_name
                    else None
                ),
                pick=_calendar_id,
            ),
        ),
    )
    parse = CalendarParser()
    transform = RowTransformer(type_value_map=_TYPE_MAP)
