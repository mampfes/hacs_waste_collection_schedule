from typing import ClassVar, final

from waste_collection_schedule import field_terms
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select, text_field
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.AppAbfallplusDe import (
    SUPPORTED_SERVICES,
    AppAbfallplusParser,
    AppAbfallplusRetriever,
    discover_choices,
)
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

# Declarative source over the "Apps by Abfall+" platform. The whole live wizard
# (token, Bundesland -> Landkreis -> Kommune -> Bezirk -> Straße -> Hausnummer
# cascade, validate, struktur download) and the XML interpretation live in the
# service as AppAbfallplusRetriever + AppAbfallplusParser, so this source only
# declares the pipeline. The transformer maps each German category name onto a
# canonical WasteType via the shared multilingual vocabulary.
#
# There is no static region registry on this platform: regions are discovered
# live. The config cascade is expressed with config_params.cascading_select;
# get_choices(field, selections) delegates to the service's discover_choices,
# which replays the same wizard to list one level's options. The provider
# registry below (which app id serves which area, collected offline) drives the
# discoverable README / sources.json listings only; it pre-fills the app id, and
# the rest of the cascade is resolved live.


@final
class Source(BaseSource):
    TITLE = "Apps by Abfall+"
    DESCRIPTION = "Source for Apps by Abfall+."
    URL = "https://www.abfallplus.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    # The transformer resolves each app's open-ended German labels through the shared
    # multilingual vocabulary, so any canonical type may appear.
    # The platform's provider labels are open-ended; these are the canonical
    # types the shared vocabulary resolves. Anything else is preserved verbatim.
    WASTE_TYPES: ClassVar[list] = [
        GENERAL_WASTE,
        ORGANIC,
        PAPER,
        RECYCLABLES,
        GARDEN_WASTE,
        HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "de.k4systems.abfallappnf Ahrenviöl alle Straßen": {
            "app_id": "de.k4systems.abfallappnf",
            "city": "Ahrenviöl",
            "strasse": "Alle Straßen",
        },
        "de.albagroup.app Braunschweig Hauptstraße 7A  ": {
            "app_id": "de.albagroup.app",
            "city": "Braunschweig",
            "strasse": "Hauptstraße",
            "hnr": "7A",
        },
        "de.k4systems.bonnorange Auf dem Hügel": {
            "app_id": "de.k4systems.bonnorange",
            "city": "A",  # First letter of street required
            "strasse": "Auf dem Hügel",
            "hnr": 6,
        },
        "de.ucom.abfallavr Brühl Habichtstr. 4A": {
            "app_id": "de.ucom.abfallavr",
            "strasse": "Habichtstr.",
            "hnr": "4A",
            "city": "Brühl",
        },
        "de.k4systems.abfallappwug Bergen hauptstr. 1": {
            "app_id": "de.k4systems.abfallappwug",
            "strasse": "Alle Straßen",
            "city": "Bergen",
        },
        "de.k4systems.abfallappcux Wurster Nordseeküste Aakweg Alle Hausnummern": {
            "app_id": "de.k4systems.abfallappcux",
            "strasse": "Aakweg",
            "hnr": "Alle Hausnummern",
            "city": "Wurster Nordseeküste",
        },
        "de.abfallwecker Mutzschen, Am Lindigt 1": {
            "app_id": "de.abfallwecker",
            "city": "Dahlen",
            "strasse": "Hauptstraße",
            "hnr": 2,
            "bundesland": "Sachsen",
            "landkreis": "Landkreis Nordsachsen",
        },
        "de.k4systems.leipziglk Brandis Brandis": {
            "app_id": "de.k4systems.leipziglk",
            "city": "Brandis",
            "bezirk": "Brandis",
        },
        "de.k4systems.leipziglk Machern Machern": {
            "app_id": "de.k4systems.leipziglk",
            "city": "Machern",
            "bezirk": "Machern",
            "strasse": "alle Straßen",
        },
        "de.k4systems.lkgoettingen, Abfallwirtschaft Altkreis Göttingen,  Adelebsen, Alle Straßen": {
            "app_id": "de.k4systems.lkgoettingen",
            "landkreis": "Abfallwirtschaft Altkreis Göttingen",
            "city": "Adelebsen",
            "strasse": "Alle Straßen",
            "bezirk": "Adelebsen",
        },
    }

    PARAMS = (
        text_field("app_id", "App ID"),
        cascading_select(
            ("bundesland", field_terms.STATE),
            ("landkreis", field_terms.COUNTY),
            ("city", field_terms.MUNICIPALITY),
            ("bezirk", field_terms.DISTRICT),
            ("strasse", field_terms.STREET),
            ("hnr", field_terms.HOUSE_NUMBER),
        ),
    )

    retrieve = AppAbfallplusRetriever()
    parse = AppAbfallplusParser()
    transform = JsonTransformer(date_key="date", type_key="category")

    def __init__(
        self,
        app_id: str,
        strasse: str | None = None,
        hnr: str | int | None = None,
        bezirk: str | None = None,
        city: str | None = None,
        bundesland: str | None = None,
        landkreis: str | None = None,
    ):
        super().__init__(
            app_id=app_id,
            strasse=strasse,
            hnr=hnr,
            bezirk=bezirk,
            city=city,
            bundesland=bundesland,
            landkreis=landkreis,
        )

    @staticmethod
    def REGIONS() -> list[Region]:
        regions: list[Region] = []
        for app_id, services in SUPPORTED_SERVICES.items():
            for service in services:
                regions.append(region(service, app_id=app_id, city=service))
        return regions

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[tuple[str, str]]:
        """Options for one cascade level given the levels chosen so far.

        Implements config_params.cascading_select. Delegates to the service's
        live discovery, which walks the AbfallPlus wizard for the given app id.
        """
        app_id = selections.get("app_id")
        if not app_id:
            return []
        return discover_choices(str(app_id), field, selections)
