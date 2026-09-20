"""Neunkirchen Siegerland waste calendar (Sitepark IES platform).

A declarative BaseSource pipeline. The shared ``SiteparkIESRetriever`` resolves
the street (and optional Ortsteil) to a pois and returns the raw ICS response;
the shared ``IcsParser`` + ``ICSTransformer`` do the parsing and typing. This
module only declares the municipality's base URL, refid and download params plus
the German-to-canonical waste-type map, so there is no ``retrieve`` override, no
manual request params and no ICON_MAP.

The feed has no way to select a household's actual bin/container choice, so it
lists every residual-waste variant for the street at once: "Restmülltonne"
(bin, ~4-weekly), "Spartonne Restmüll" (reduced bin, same stream on a longer
cycle — a subset of the "Restmülltonne" dates) and "Container Restmüll" (a
separate, non-overlapping schedule for shared containers). All three map to
GENERAL_WASTE; ``carry_raw_label``/``IGNORE_DUPLICATES_DEFAULT`` keep that from
being lossy: the original label survives in ``description`` (so a user can
still tell them apart, or hide the one they don't have via ``customize``), and
— once the "Ignore Duplicate Entries per Day" option is on, which this source
preselects by default — the two entries that would otherwise land on the
exact same day (whenever a "Spartonne" date coincides with its underlying
"Restmülltonne" date) collapse into one instead of showing as a duplicate.
"Container Restmüll" runs on its own dates, so it is never touched by that
merge — an address with both a bin and a container keeps both.
"""

from typing import ClassVar, final

from waste_collection_schedule import field_terms, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select, district
from waste_collection_schedule.service.SiteparkIES import SiteparkIESRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.neunkirchen-siegerland.de"


@final
class Source(BaseSource):
    TITLE = "Neunkirchen Siegerland"
    DESCRIPTION = "Source for 'Abfallkalender Neunkirchen Siegerland'."
    URL = _BASE_URL
    COUNTRY = "de"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]

    TEST_CASES: ClassVar[dict] = {
        "Waldstraße (Altenseelbach)": {"strasse": "Waldstraße (Altenseelbach)"},
        "Altenseelbacher Weg (Neunkirchen)": {
            "strasse": "Altenseelbacher Weg (Neunkirchen)"
        },
    }

    PARAMS = (
        cascading_select(("strasse", field_terms.STREET)),
        district("ort", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Pick your street from the list (shown as 'Street (district)'). "
            "When configuring in YAML, a partial or full street name as shown on "
            "the Neunkirchen Siegerland waste calendar also works (e.g. 'Waldstr' "
            "for 'Waldstraße'). If the "
            "street exists in several districts, add the district (Ortsteil) "
            "shown in parentheses (e.g. 'Neunkirchen')."
        ),
        "de": (
            "Wählen Sie Ihre Straße aus der Liste (Anzeige 'Straße (Ortsteil)'). "
            "In YAML genügt auch ein Teil oder der vollständige Straßenname wie im "
            "Abfallkalender Neunkirchen Siegerland (z.B. 'Waldstr' für "
            "'Waldstraße'). Kommt die Straße in mehreren Ortsteilen vor, "
            "ergänzen Sie den Ortsteil in Klammern (z.B. 'Neunkirchen')."
        ),
    }

    RAISE_ON_EMPTY = True

    # Preselects the "Ignore Duplicate Entries per Day" option (users can
    # still turn it off in the integration's options), which collapses the
    # same-day overlap between "Restmülltonne" and "Spartonne Restmüll" (see
    # module docstring); never touches "Container Restmüll", which runs on
    # its own dates.
    IGNORE_DUPLICATES_DEFAULT = True

    retrieve = SiteparkIESRetriever(
        _BASE_URL,
        refid="3362.1",
        download_params={"kat": "1", "alarm": "0"},
    )

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[str]:
        """Street dropdown for the config flow: every "Street (Ortsteil)" label."""
        return cls.retrieve.street_choices() if field == "strasse" else []

    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Biotonne": wt.ORGANIC,
            "Papiertonne / Papiercontainer": wt.PAPER,
            "Restmülltonne": wt.GENERAL_WASTE,
            "Spartonne Restmüll": wt.GENERAL_WASTE,
            "Container Restmüll": wt.GENERAL_WASTE,
            "Gelbe Tonne": wt.RECYCLABLES,
            "Astschnittsammlung": wt.GARDEN_WASTE,
            "Schadstoffsammlung": wt.HAZARDOUS,
        },
        carry_raw_label=True,
    )
