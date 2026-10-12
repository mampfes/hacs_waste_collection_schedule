"""Rybnik, Poland (EKO Sp. z o.o.).

The city publishes its schedules as PDFs under a per-year folder:

* residential and commercial properties: one PDF per district group. Page 1
  lists the zones (Rejon) of the group with their streets; the schedule page
  prints one block per zone (a row per round, a column per month, the days in
  each cell) in the same order, and a footer with the bulky-waste dates.
* multifamily housing: one city-wide PDF with a ruled table whose cells hold
  weekday rules ("środa tydzień nieparzysty"), expanded here over the year.

The current year's PDF is tried first, then the previous year's.
"""

from datetime import date
from typing import Any, ClassVar, final

from waste_collection_schedule import lookups, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    district,
    dropdown,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentRequiredWithSuggestions
from waste_collection_schedule.service.RybnikSchedule import (
    RybnikPdfParser,
    RybnikScheduleReader,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = (
    "https://www.rybnik.eu/fileadmin/user_files/mieszkaj/samorzad/"
    "odpady_komunalne/Harmonogramy_{year}/"
)

# district -> slug in the PDF file name, the zones (Rejon) of its cover table in
# the order of the schedule blocks, and aliases where the footer abbreviates one.
DISTRICT_MAP: dict[str, dict] = {
    "Boguszowice Stare": {
        "slug": "Boguszowice_Stare",
        "zones": [f"Boguszowice Stare {i}" for i in range(1, 6)],
    },
    "Chwalowice / Boguszowice Os. / Klokocin": {
        "slug": "Chwalowice__Boguszowice_Os.__Klokocin",
        "zones": [
            "Chwałowice 1",
            "Chwałowice 2",
            "Boguszowice Osiedle",
            "Kłokocin 1",
            "Kłokocin 2",
        ],
    },
    "Gotartowice": {
        "slug": "Gotartowice",
        "zones": [f"Gotartowice {i}" for i in range(1, 5)],
    },
    "Grabownia / Golejow / Ochojec": {
        "slug": "Grabownia__Golejow__Ochojec",
        "zones": ["Grabownia", "Golejów 1", "Golejów 2", "Ochojec 1", "Ochojec 2"],
    },
    "Ligota": {
        "slug": "Ligota",
        "zones": [f"Ligota-Ligocka Kuźnia {i}" for i in range(1, 5)],
    },
    "Maroko-Nowiny": {
        "slug": "Maroko-Nowiny",
        "zones": [f"Maroko-Nowiny {i}" for i in range(1, 7)],
    },
    "Niedobczyce": {
        "slug": "Niedobczyce",
        "zones": [f"Niedobczyce {i}" for i in range(1, 8)],
    },
    "Niewiadom": {
        "slug": "Niewiadom",
        "zones": [f"Niewiadom {i}" for i in range(1, 5)],
    },
    "Orzepowice / Stodoly / Chwalecice": {
        "slug": "Orzepowice__Stodoly__Chwalecice",
        "zones": [
            "Orzepowice 1",
            "Orzepowice 2",
            "Stodoły",
            "Chwałęcice 1",
            "Chwałęcice 2",
        ],
    },
    "Paruszowiec / Kamien": {
        "slug": "Paruszowiec__Kamien",
        "zones": ["Paruszowiec-Piaski", "Kamień 1", "Kamień 2"],
    },
    "Polnoc": {
        "slug": "Polnoc",
        "zones": [f"Rybnik-Północ {i}" for i in range(1, 6)],
    },
    "Radziejow / Popielow": {
        "slug": "Radziejow__Popielow",
        "zones": ["Radziejów", "Popielów 1", "Popielów 2", "Popielów 3"],
    },
    "Smolna / Zamyslow / Meksyk": {
        "slug": "Smolna__Zamyslow__Meksyk",
        "zones": [
            "Smolna 1",
            "Smolna 2",
            "Zamysłów 1",
            "Zamysłów 2",
            "Zamysłów 3",
            "Meksyk",
        ],
    },
    "Srodmiescie / Wielopole / Kuznia": {
        "slug": "Srodmiescie__Wielopole__Kuznia",
        "zones": [
            "Śródmieście 1",
            "Śródmieście 2",
            "Wielopole 1",
            "Wielopole 2",
            "Kuźnia Rybnicka",
        ],
        "zone_aliases": {"Kuźnia Rybnicka": ["Kuźnia"]},
    },
    "Zebrzydowice": {
        "slug": "Zebrzydowice",
        "zones": [f"Zebrzydowice {i}" for i in range(1, 5)],
    },
}

PROPERTY_TYPES = ["residential", "commercial", "multifamily"]

# The round labels as printed (residential rows and multifamily column headings).
_TYPES = {
    "ZMIESZANE": wt.GENERAL_WASTE,
    "SEGREGOWANE": wt.RECYCLABLES,
    "BIODEGRADOWALNE": wt.ORGANIC,
    "GABARYTY": wt.BULKY_WASTE,
    "PLASTIK": wt.PLASTIC,
    "PAPIER": wt.PAPER,
    "SZKŁO": wt.GLASS,
    "WIELKOGABARYTY": wt.BULKY_WASTE,
    "BIO": wt.ORGANIC,
    # Ash is a winter-only round printed with dashes; not surfaced.
    "POPIOŁY/ŻUŻEL": None,
}


# --- retrieval (pure request shaping) -------------------------------------


def _candidate_years(**_: Any) -> list[int]:
    today = date.today()
    return [today.year, today.year - 1]


def _pdf_url(
    candidate: int, *, property_type: str, district: str | None, **_: Any
) -> str:
    base = _BASE_URL.format(year=candidate)
    if property_type == "multifamily":
        return f"{base}Wielorodzinna_{candidate}.pdf"
    if not district:
        raise SourceArgumentRequiredWithSuggestions(
            "district", "district is required", list(DISTRICT_MAP)
        )
    slug = lookups.resolve(DISTRICT_MAP, district, argument="district")["slug"]
    if property_type == "commercial":
        return f"{base}Firmy{candidate}_{slug}_firmy_{candidate}.pdf"
    return f"{base}zamieszkale{candidate}_{slug}_{candidate}.pdf"


def _is_pdf(response: Any) -> bool:
    return response.status_code == 200 and response.content[:4] == b"%PDF"


@final
class Source(BaseSource):
    TITLE = "Rybnik"
    DESCRIPTION = (
        "Source for Rybnik (Poland) municipal waste collection schedules "
        "provided by EKO Sp. z o.o."
    )
    URL = "https://www.rybnik.eu"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.BULKY_WASTE,
        wt.PLASTIC,
        wt.PAPER,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Paruszowiec-Piaski residential": {
            "district": "Paruszowiec / Kamien",
            "sub_district": "Paruszowiec-Piaski",
            "property_type": "residential",
        },
        "Boguszowice Stare residential (all sub-districts)": {
            "district": "Boguszowice Stare",
            "property_type": "residential",
        },
        "Niedobczyce commercial": {
            "district": "Niedobczyce",
            "property_type": "commercial",
        },
        "Zebrzydowice 1 residential": {
            "district": "Zebrzydowice",
            "sub_district": "Zebrzydowice 1",
            "property_type": "residential",
        },
        "Multifamily Rudzka, Stodoły (odd/even weeks)": {
            "property_type": "multifamily",
            "street": "Rudzka",
            "sub_district": "Stodoły",
        },
        "Multifamily Chabrowa (Maroko-Nowiny)": {
            "property_type": "multifamily",
            "street": "Chabrowa",
        },
    }

    PARAMS = (
        district("district", optional=True),
        text_field("sub_district", "Sub-district (Rejon)", optional=True),
        dropdown(
            "property_type",
            PROPERTY_TYPES,
            label="Property type",
            default="residential",
        ),
        street("street", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose the property type: 'residential' (zamieszkałe), 'commercial' "
            "(firmy/niezamieszkałe) or 'multifamily' (zabudowa wielorodzinna). "
            "For residential and commercial properties enter the district group "
            "(e.g. 'Paruszowiec / Kamien') and optionally the Rejon (zone) from the "
            "left column of the PDF cover table (e.g. 'Kamień 1'); leave it blank "
            "for all zones of the district. The PDFs are on "
            "https://www.rybnik.eu/dla-mieszkancow/odpady-komunalne/. For multifamily "
            "housing enter your street as listed in the 'ULICE' column, and the "
            "'DZIELNICA' value (e.g. 'Stodoły') as sub-district if the street is "
            "listed for several areas."
        ),
    }

    retrieve = retrievers.FirstMatchRetriever(
        candidates=_candidate_years, url=_pdf_url, accept=_is_pdf
    )

    parse = RybnikPdfParser()
    preprocess = RybnikScheduleReader(DISTRICT_MAP)

    transform = ICSTransformer(type_value_map=_TYPES)
