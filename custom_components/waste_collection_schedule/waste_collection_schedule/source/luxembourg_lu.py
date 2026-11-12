from typing import ClassVar, final

from waste_collection_schedule import date_parsers, field_terms, regions, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select
from waste_collection_schedule.retrievers import detached_source
from waste_collection_schedule.service import DataPublicLu
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Luxembourg (all communes)"
    DESCRIPTION = (
        "National waste collection calendars for every Luxembourg commune, "
        "published as open data on data.public.lu. Choose a commune, then a "
        "locality and street when that commune splits its schedule."
    )
    URL = "https://data.public.lu"
    COUNTRY = "lu"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.ELECTRONICS,
        wt.HAZARDOUS,
        wt.METAL,
        wt.TEXTILES,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Beaufort": {"commune": "Beaufort"},
        "Reisdorf": {"commune": "Reisdorf"},
        "Pétange - Pétange, Rue Michel Rodange": {
            "commune": "Pétange",
            "localite": "Pétange",
            "rue": "Rue Michel Rodange",
        },
        "Bech - specific street": {
            "commune": "Bech",
            "localite": "Bech",
            "rue": "Am Biirk",
        },
        "Pétange - Rodange": {
            "commune": "Pétange",
            "localite": "Rodange",
            "rue": "Rue Willy Huberty",
        },
    }

    # Build-time listing only (doc/ is not shipped in a HACS install). Fetch and
    # the config-flow dropdowns read the live CSV, so a renamed commune does not
    # break the source; it only leaves the generated listing stale until the
    # registry is refreshed.
    REGIONS = regions.from_yaml("luxembourg_lu", commune="commune")

    PARAMS = (
        cascading_select(
            ("commune", field_terms.MUNICIPALITY),
            ("localite", field_terms.DISTRICT),
            ("rue", field_terms.STREET),
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search for your commune in the source list (each commune is listed "
            "on its own) or pick Luxembourg (all communes). The form then "
            "offers a dropdown for the commune, and - only when that commune "
            "splits its schedule - for the locality and the street. Values must "
            "match the open data set on data.public.lu (accents, the 'Rue ' "
            "prefix). A missing or wrong value still lists the valid ones."
        ),
    }

    retrieve = retrievers.Request(DataPublicLu.CSV_URL, timeout=60)
    parse = DataPublicLu.CalendarParser()

    # Cached for the process so the config flow does not download the national
    # CSV once per cascade level. Fetch itself always goes through ``retrieve``.
    _choice_rows: ClassVar[list[dict[str, str]] | None] = None

    @classmethod
    def _calendar_rows(cls) -> list[dict[str, str]]:
        if cls._choice_rows is None:
            response = cls.retrieve(detached_source())
            cls._choice_rows = DataPublicLu.parse_rows(response)
        return cls._choice_rows

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[str]:
        """Options for one cascade level, from the live national CSV.

        A level whose commune (or locality) does not split further returns
        ``[]`` and is skipped by the config-flow wizard. The parser's
        suggestion errors remain the fallback for YAML and mistyped values.
        """
        rows = cls._calendar_rows()
        commune = str(selections.get("commune") or "").strip()
        if commune:
            rows = DataPublicLu.matching_rows(rows, "Commune", commune)
        if field == "commune":
            return DataPublicLu.column_options(rows, "Commune")
        if field == "localite":
            return (
                DataPublicLu.column_options(rows, "Localité", keep_blank=True)
                if commune
                else []
            )
        loc_options = DataPublicLu.column_options(rows, "Localité", keep_blank=True)
        localite = str(selections.get("localite") or "").strip()
        if loc_options and not localite:
            # Street names can repeat across localities (e.g. Rue Michel
            # Rodange in both Pétange and Rodange); wait for the locality.
            return []
        if localite:
            rows = DataPublicLu.matching_rows(
                rows, "Localité", localite, keep_blank=True
            )
        if field == "rue":
            return (
                DataPublicLu.column_options(
                    rows,
                    "Rue",
                    keep_blank=True,
                    wildcard=DataPublicLu.ALL_STREETS,
                )
                if commune
                else []
            )
        return []

    transform = JsonTransformer(
        date_key="Date",
        type_key="Type de collecte",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "Biodéchets": wt.ORGANIC,
            "Conteneur pour déchets ménagers": wt.GENERAL_WASTE,
            "Déchets ménagers en mélange": wt.GENERAL_WASTE,
            "Déchets de verdure": wt.GARDEN_WASTE,
            "Arbres de Noël": wt.GARDEN_WASTE,
            "Déchets d'équipements électriques et électroniques": wt.ELECTRONICS,
            "Déchets d’équipements électriques et électroniques": wt.ELECTRONICS,
            "Déchets encombrants": wt.BULKY_WASTE,
            "Déchets encombrants en vrac": wt.BULKY_WASTE,
            "Déchets recyclables": wt.RECYCLABLES,
            "Valorlux": wt.RECYCLABLES,
            "Ferraille": wt.METAL,
            "Papier/Carton": wt.PAPER,
            "Papier/Carton (commerces)": wt.PAPER,
            "Papier/Carton – 40L": wt.PAPER,
            "SuperDrecksKëscht": wt.HAZARDOUS,
            "Verre": wt.GLASS,
            "Verre (commerces)": wt.GLASS,
            "Verre – 40L": wt.GLASS,
            "Vieux bois": wt.OTHER,
            "Vieux vêtements": wt.TEXTILES,
        },
    )
