"""Landkreis Verden (landkreis-verden.de).

Demonstrates: the Athos "WasteManagementServlet" wizard with an unusual
five-POST shape (rather than the common three): ``CITYCHANGED``,
``STREETCHANGED``, a ``forward`` that selects containers for the typed
house number, then a *second* ``forward`` that instead submits a combined
``Hausnummernwahl`` selection (dropping ``Hausnummer``/``Hausnummerzusatz``),
before the final download. This deployment also sends a fixed custom
``User-Agent`` on every request and never scrapes hidden-state fields from
the servlet (the legacy source built each POST's fields from scratch), so
the wizard's own hidden-input scrape simply contributes nothing extra.

Known gap (documented, not reproduced here, matching the precedent set by
``bielefeld_de``): the legacy source additionally re-fetched a second
calendar year (``Zeitraum: "Jahresübersicht <year+1>"``) when run in
December, merging both years' events. ``AthosWasteManagementRetriever``
runs the wizard's steps exactly once per fetch, so that December-only
second pass is not reproduced.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SERVLET = (
    "https://lkv.landkreis-verden.de/WasteManagementVerden/WasteManagementServlet"
)
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}
_CHECK_MODEL = "com.athos.nl.mvc.abfterm.CheckAbfuhrTermineParameterBusinessCase"
_CONTAINERS = {f"ContainerGewaehlt{suffix}": "on" for suffix in "R4KPGWB"}


@final
class Source(BaseSource):
    TITLE = "Landkreis Verden"
    DESCRIPTION = "Source for Landkreis Verden waste collection."
    URL = "https://www.landkreis-verden.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Achim": {"city": "Achim", "street": "Am Schießstand", "house_number": 10},
        "Blender": {
            "city": "Blender",
            "street": "Buchenweg",
            "house_number": "8",
            "house_number_addition": "a",
        },
        "Riede": {"city": "Riede", "street": "An der Reihe", "house_number": 11},
    }

    PARAMS = (
        city(),
        street(),
        house_number(),
        text_field("house_number_addition", "House number addition", default=""),
    )

    retrieve = AthosWasteManagementRetriever(
        url=_SERVLET,
        headers=_HEADERS,
        initial_params={
            "SubmitAction": "wasteDisposalServices",
            "ApplicationName": "com.athos.nl.mvc.abfterm.AbfuhrTerminModel",
        },
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda city, **_: {
                    "ApplicationName": _CHECK_MODEL,
                    "Ort": city,
                    "Strasse": "",
                    "Hausnummer": "",
                    "Hausnummerzusatz": "",
                    "Zeitraum": f"Jahresübersicht {datetime.now().year}",
                },
            },
            {
                "submit_action": "STREETCHANGED",
                "fields": lambda city, street, **_: {
                    "ApplicationName": _CHECK_MODEL,
                    "Ort": city,
                    "Strasse": street,
                    "Hausnummer": "",
                },
            },
            {
                "submit_action": "forward",
                "fields": lambda city, street, house_number, house_number_addition="", **_: {
                    "ApplicationName": _CHECK_MODEL,
                    **_CONTAINERS,
                    "Ort": city,
                    "Strasse": street,
                    "Hausnummer": house_number,
                    "Hausnummerzusatz": house_number_addition,
                    "Zeitraum": f"Jahresübersicht {datetime.now().year}",
                },
            },
            {
                "submit_action": "forward",
                "fields": lambda city, street, house_number, house_number_addition="", **_: {
                    "ApplicationName": _CHECK_MODEL,
                    **_CONTAINERS,
                    "Ort": city,
                    "Strasse": street,
                    "Hausnummernwahl": f"{house_number}{house_number_addition}",
                    "Zeitraum": f"Jahresübersicht {datetime.now().year}",
                },
                "remove": ("Hausnummer", "Hausnummerzusatz"),
            },
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.nl.mvc.abfterm.AbfuhrTerminModel",
                    **_CONTAINERS,
                    "ICalErinnerung": "keine Erinnerung",
                    "ICalZeit": "06:00 Uhr",
                },
                "remove": ("Ort", "Strasse", "Hausnummernwahl", "Zeitraum"),
            },
        ],
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        # The feed appends a variable frequency suffix to some summaries
        # (e.g. "Restabfallbehaelter 4-woech."); the legacy source's icon
        # lookup used only the first word (``d[1].split()[0]``) for the same
        # reason. Mirror that here so every variant still resolves.
        clean=lambda label: label.split()[0] if label.split() else label,
        type_value_map={
            "Gelber": RECYCLABLES,
            "Restabfallbehaelter": GENERAL_WASTE,
            "Papierbehaelter": PAPER,
            "Kompostbehaelter": ORGANIC,
            "Weihnachtsbaum": GARDEN_WASTE,
        },
    )

    def __init__(
        self,
        city: str,
        street: str,
        house_number: int | str,
        house_number_addition: str = "",
    ) -> None:
        super().__init__(
            city=city,
            street=street,
            house_number=house_number,
            house_number_addition=house_number_addition,
        )
