"""Stadt Bielefeld (bielefeld.de).

Demonstrates: the Athos "WasteManagementServlet" wizard with a URL that
migrated host/path (``fallback_url``) and a per-step ``ApplicationName``
override on both the first and last step.

Known gap (documented, not reproduced here): the legacy source additionally
scraped a JS-embedded ``var text = '...'`` blob out of the initial page for
extra ``<input type=radio>`` alternatives, and re-ran the whole wizard once
per radio combination when present (multiple simultaneous facility
submissions for one address). ``AthosWasteManagementRetriever`` does not
special-case that; it always runs the single, common path (no radio
combinations), which is what this source's TEST_CASE address exercises. An
address that genuinely returns multiple radio alternatives would need that
extra fan-out reintroduced, either as a source-level wrapper around this
retriever or as a future engine feature if more Athos deployments turn out to
need it.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SERVLET = "https://anwendungen.bielefeld.de/WasteManagementBielefeldTest/WasteManagementServlet"
# Actual production URL; the servlet above returned 404 for it at conversion
# time and this fallback was substituted, per the legacy source's comment.
_ORIGINAL_SERVLET = (
    "https://anwendungen.bielefeld.de/WasteManagementBielefeld/WasteManagementServlet"
)

_REMINDER_DAY = "keine Erinnerung"  # "keine Erinnerung", "am Vortag", "2/3 Tage vorher"
_REMINDER_TIME = "18:00 Uhr"  # "XX:00 Uhr"


@final
class Source(BaseSource):
    TITLE = "Bielefeld"
    DESCRIPTION = "Source for Stadt Bielefeld."
    URL = "https://bielefeld.de"
    COUNTRY = "de"

    # A wrong street/house number yields an empty Athos schedule; surface it
    # as an error instead of a silently empty calendar (#6943).
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Umweltbetrieb": {"street": "Eckendorfer Straße", "house_number": 57},
    }

    PARAMS = (
        street(),
        house_number(),
        text_field("address_suffix", "Address suffix", default=""),
    )

    retrieve = AthosWasteManagementRetriever(
        url=_SERVLET,
        fallback_url=_ORIGINAL_SERVLET,
        initial_params={"SubmitAction": "wasteDisposalServices"},
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda street, house_number, address_suffix="", **_: {
                    "Ort": street[0],
                    "Strasse": street,
                    "Hausnummer": str(house_number),
                    "Hausnummerzusatz": address_suffix,
                    "ApplicationName": "com.athos.kd.bielefeld.abfuhrtermine.CheckAbfuhrTermineParameterBusinessCase",
                    "ContainerGewaehlt_1": "on",
                    "ContainerGewaehlt_2": "on",
                    "ContainerGewaehlt_3": "on",
                    "ContainerGewaehlt_4": "on",
                },
            },
            {"submit_action": "forward"},
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.kd.bielefeld.abfuhrtermine.AbfuhrTerminModel",
                    "ICalErinnerung": _REMINDER_DAY,
                    "ICalZeit": _REMINDER_TIME,
                },
            },
        ],
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restabfallbehaelter": GENERAL_WASTE,
            "Bioabfallbehaelter": ORGANIC,
            "Papierbehaelter": PAPER,
            "Wertstofftonne": RECYCLABLES,
        }
    )

    def preprocess(self, records, source=None):
        """Drop the calendar's own "Die neue ICal..." announcement VEVENT."""
        return (r for r in records if "Die neue ICal" not in r[1])

    def __init__(self, street: str, house_number: int, address_suffix: str = ""):
        super().__init__(
            street=street, house_number=house_number, address_suffix=address_suffix
        )
