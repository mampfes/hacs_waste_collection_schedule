import difflib
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.date_parsers import for_format
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import FanOutRetriever, Request, Suggestions
from waste_collection_schedule.transformers import RowTransformer

_API_URL = "https://www.gargzdusvara.eu/ajax.php"

# The API serves one schedule per waste type, selected by this code.
_TYPE_CODES = ("komunalines", "plastikas_popietius", "stiklas", "zaliosios")

# One list of valid locations per waste type; a location can exist for only some.
_LOCATION_LISTS = tuple(
    Suggestions(
        _API_URL,
        method="POST",
        data={"action": "getLocations", "module": "Atliekos", "value": code},
        pick=lambda response, **_: (response.json().get("return") or {}).keys(),
        fallback=[],
    )
    for code in _TYPE_CODES
)


def _dates(responses, source) -> list[tuple[str, str]]:
    """Pair each waste type's dates with its code; a type with no schedule has none.

    ``responses`` arrive in ``_TYPE_CODES`` order. When no type knows the location
    the argument is wrong, and the valid locations are offered.
    """
    rows: list[tuple[str, str]] = []
    matched_any_type = False
    for code, response in zip(_TYPE_CODES, responses, strict=True):
        data = response.json()
        if not data.get("status"):
            continue
        matched_any_type = True
        rows.extend(
            (date, code) for date in (data.get("return") or {}).get("dates") or {}
        )
    if not matched_any_type:
        location = source.params["location"]
        known = sorted({name for lst in _LOCATION_LISTS for name in lst(source)})
        raise SourceArgumentNotFoundWithSuggestions(
            "location",
            location,
            difflib.get_close_matches(location, known, n=5, cutoff=0.5),
        )
    return rows


@final
class Source(BaseSource):
    TITLE = "Gargždų švara"
    DESCRIPTION = (
        "Source for VšĮ 'Gargždų švara' waste collection schedules "
        "(Klaipėda district municipality, Lithuania)."
    )
    URL = "https://www.gargzdusvara.eu"
    COUNTRY = "lt"

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Klemiškės I k.": {"location": "Klemiškės I k."},
        "Gargždų miesto šiaurinė dalis": {
            "location": "Gargždų m. - Aušrupio g., Gargždupio g., Lenktoji g., "
            "Lyros g., Palangos g., Rasos g., Saulažolių g., Vytenio g., "
            "Volungės g., Žibučių g."
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the exact location/street-group name as shown in the "
            "'Pasirinkite vietovę' (select location) dropdown on "
            "https://www.gargzdusvara.eu/atlieku-isvezimo-grafikai/ after picking "
            "any waste type first (e.g. 'Klemiškės I k.'). It must match exactly, "
            "including Lithuanian diacritics."
        ),
    }

    PARAMS = (text_field("location", "Location"),)

    retrieve = FanOutRetriever(
        targets=lambda source, context: _TYPE_CODES,
        fetch=Request(
            _API_URL,
            method="POST",
            data=lambda code, context, location, **_: {
                "action": "getDataAll",
                "module": "Atliekos",
                "lang": "lt",
                "location": location,
                "type": code,
            },
        ),
    )
    parse = staticmethod(_dates)
    transform = RowTransformer(
        parse_date=for_format("%Y-%m-%d"),
        skip_unparseable_dates=True,
        type_value_map={
            "komunalines": wt.GENERAL_WASTE,
            "plastikas_popietius": wt.RECYCLABLES,
            "stiklas": wt.GLASS,
            "zaliosios": wt.GARDEN_WASTE,
        },
    )
