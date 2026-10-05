from typing import ClassVar, final

from waste_collection_schedule import date_parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    municipality,
    postcode,
    text_field,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import RowTransformer

API_URL = "https://api.straatbeeld.online/v1/waste-calendar"

# Municipalities known to use this platform. Not exhaustive: any
# "<municipality>.afvalkalender.straatbeeld.online" instance will work,
# these are only used as suggestions if the provided value is not found.
KNOWN_MUNICIPALITIES = ["drimmelen", "geertruidenberg"]


def _municipality(municipality: str, **_) -> str:
    return municipality.strip().lower()


def _postal_code(postal_code: str, **_) -> str:
    return str(postal_code).replace(" ", "").upper()


def _origin(**params) -> str:
    return f"https://{_municipality(**params)}.afvalkalender.straatbeeld.online"


def _body(house_number, house_letter=None, **params) -> dict:
    return {
        "postal_code": _postal_code(**params),
        "house_number": str(house_number),
        "house_letter": house_letter or None,
    }


def _rows(response, source) -> list[tuple[str, str]]:
    """Flatten year -> month -> day -> waste items into (date, waste name) rows."""
    params = source.params
    if response.status_code == 404:
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality", _municipality(**params), KNOWN_MUNICIPALITIES
        )
    if response.status_code == 422:
        raise SourceArgumentNotFound(
            "postal_code",
            f"{_postal_code(**params)} {params['house_number']}",
            "please check the postal code, house number and house letter.",
        )
    response.raise_for_status()

    rows: list[tuple[str, str]] = []
    for months in response.json().get("collections", {}).values():
        for days in months.values():
            for day in days:
                for waste in day.get("data", []):
                    rows.append((day["date"]["formatted"], waste["name"]))
    return rows


@final
class Source(BaseSource):
    TITLE = "Straatbeeld Online"
    DESCRIPTION = (
        "Source for Straatbeeld Online (afvalkalender.straatbeeld.online), "
        "a waste calendar platform used by several Dutch municipalities "
        "(e.g. Gemeente Drimmelen, Gemeente Geertruidenberg)."
    )
    URL = "https://afvalkalender.straatbeeld.online"
    COUNTRY = "nl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Drimmelen, 4926CW 28": {
            "municipality": "drimmelen",
            "postal_code": "4926CW",
            "house_number": "28",
        },
        "Drimmelen, 4926 CW 28 (int house number)": {
            "municipality": "drimmelen",
            "postal_code": "4926 CW",
            "house_number": 28,
        },
    }

    PARAMS = (
        municipality("municipality"),
        postcode("postal_code", "house_number"),
        text_field("house_letter", "House letter/addition", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open your municipality's Straatbeeld Online waste calendar "
            "(e.g. https://drimmelen.afvalkalender.straatbeeld.online), the "
            "'municipality' argument is the first part of that URL "
            "(e.g. 'drimmelen'). Use the same postal code and house number "
            "you would enter on that page. Add a house letter or addition only "
            "when several addresses share the same postal code and house number."
        ),
        "nl": (
            "Open de afvalkalender van je gemeente op Straatbeeld Online "
            "(bijv. https://drimmelen.afvalkalender.straatbeeld.online), het "
            "argument 'municipality' is het eerste deel van die URL "
            "(bijv. 'drimmelen'). Gebruik dezelfde postcode en hetzelfde "
            "huisnummer als op die pagina. Vul een huisletter of toevoeging "
            "alleen in als meerdere adressen dezelfde postcode en hetzelfde "
            "huisnummer hebben."
        ),
    }

    retrieve = retrievers.Request(
        API_URL,
        method="POST",
        json=_body,
        headers=lambda **params: {
            "Origin": _origin(**params),
            "Referer": f"{_origin(**params)}/",
            "Accept": "application/json",
        },
        raise_for_status=False,
    )

    parse = staticmethod(_rows)

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "gft": wt.ORGANIC,
            "papier": wt.PAPER,
            # PBD: plastic, blik (metal) and drink cartons collected together.
            "pbd": wt.RECYCLABLES,
            "plastic": wt.PLASTIC,
            "rest": wt.GENERAL_WASTE,
            "restafval": wt.GENERAL_WASTE,
            "glas": wt.GLASS,
            "textiel": wt.TEXTILES,
            "grofvuil": wt.BULKY_WASTE,
            "kerstboom": wt.OTHER,
            "kca": wt.HAZARDOUS,
            "chemisch": wt.HAZARDOUS,
        },
        carry_raw_label=True,
    )
