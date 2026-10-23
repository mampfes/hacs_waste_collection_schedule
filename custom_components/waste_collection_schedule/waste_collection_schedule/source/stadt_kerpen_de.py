from typing import ClassVar, final

from waste_collection_schedule import field_terms
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.config_params import cascading_select, waste_types
from waste_collection_schedule.source.abfall_io import Source as AbfallIOSource
from waste_collection_schedule.transformers import ICSTransformer

# Kerpen's waste collection is run by Schönmackers, whose MüllALARM service is
# the abfall.io platform. This is the same structure as abfall_io with the key
# and kommune pinned to Kerpen, so it subclasses the abfall.io pipeline source
# and only overrides metadata, the params the user still has to supply, and
# __init__. PINNED_PARAMS feeds the fixed values back into the config flow's
# cascade so the district, street and house-number dropdowns still populate.
# Kerpen's form requires a district (f_id_bezirk) before it lists any streets.

_KEY = "e5543a3e190cb8d91c645660ad60965f"
_KOMMUNE = 3703


@final
class Source(AbfallIOSource):
    TITLE = "Stadt Kerpen"
    DESCRIPTION = "Source for waste collection services in Kerpen."
    URL = "https://www.stadt-kerpen.de"
    COUNTRY = "de"

    # Empty, not omitted: the abfall.io parent lists its own registry, which this
    # pinned source must not inherit. The source entry itself is the listing.
    REGIONS = ()

    TEST_CASES: ClassVar[dict] = {
        # The ids the config flow's district -> street -> house number cascade
        # stores (Amselweg 1, Bezirk Kerpen). The former case
        # (f_id_strasse "3703amselweg", f_id_strasse_hnr "19409") never pointed
        # at Kerpen: abfall.io resolves the export by the house-number id alone,
        # and 19409 is Pützdorfer Straße 67 in Aldenhoven.
        "Amselweg 1 (Bezirk Kerpen)": {
            "f_id_bezirk": "9739",
            "f_id_strasse": "184953",
            "f_id_strasse_hnr": "184953",
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open the MüllALARM web app at "
            "https://www.schoenmackers.de/kommunen/muellalarm-app/, choose Kerpen, "
            "then enter your street and house number with the browser's network "
            "tab open. The form data of the requests to api.abfall.io carries the "
            "f_id_strasse and f_id_strasse_hnr values. The kommune id is already "
            "set to Kerpen."
        ),
        "de": (
            "Öffnen Sie die MüllALARM Web-App unter "
            "https://www.schoenmackers.de/kommunen/muellalarm-app/, wählen Sie "
            "Kerpen und geben Sie Straße und Hausnummer bei geöffnetem Netzwerk-Tab "
            "des Browsers ein. In den Formulardaten der Anfragen an api.abfall.io "
            "stehen die Werte für f_id_strasse und f_id_strasse_hnr. Die ID der "
            "Kommune ist für Kerpen bereits vorgegeben."
        ),
    }

    # The key and kommune are fixed for Kerpen, so they are not user params.
    PARAMS = (
        cascading_select(
            ("f_id_bezirk", field_terms.DISTRICT),
            ("f_id_strasse", field_terms.STREET),
            ("f_id_strasse_hnr", field_terms.HOUSE_NUMBER),
        ),
        waste_types("f_abfallarten"),
    )

    PINNED_PARAMS: ClassVar[dict] = {"key": _KEY, "f_id_kommune": _KOMMUNE}

    # Declared explicitly: defining transform below would otherwise make
    # BaseSource derive WASTE_TYPES from its one-entry map alone.
    WASTE_TYPES: ClassVar[list] = AbfallIOSource.WASTE_TYPES

    # Schönmackers' local name for Kerpen's bundled green cuttings collection,
    # which the shared vocabulary does not alias.
    transform = ICSTransformer(
        type_value_map={"Grünbündel": wt.GARDEN_WASTE},
    )

    def __init__(
        self,
        f_id_strasse: int | str,
        f_id_strasse_hnr: int | str | None = None,
        f_id_bezirk: int | str | None = None,
        f_abfallarten: list[int] | None = None,
    ):
        super().__init__(
            key=_KEY,
            f_id_kommune=_KOMMUNE,
            f_id_bezirk=f_id_bezirk,
            f_id_strasse=f_id_strasse,
            f_id_strasse_hnr=f_id_strasse_hnr,
            f_abfallarten=f_abfallarten,
        )
