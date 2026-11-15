"""Bamberg (City/Stadt) (stadt.bamberg.de).

Athos "WasteManagementServlet" wizard, the plain German shape: one
field-setting step (city/street/house number, ``Ort`` derived from the
street's first letter like ``zke_sb_de``), one container-selection step
(all nine ``ContainerGewaehlt_N`` slots), one download step with an
explicit ``ApplicationName`` override -- the legacy source hardcodes that
value rather than relying on a re-scrape, so this shape needed no
adjustment for the retriever's single-scrape mechanic (contrast
``zke_sb_de``/``zaw_sr_de``, which did).

The year is a ``Zeitraum`` radio (``Jahresübersicht <year>``) that the legacy
source never sent (the line setting it was commented out), so the server's
preselection wins -- and from autumn on that is next year, which leaves
every collection until the end of the current year missing. ``iterate_field``
runs the wizard once per offered year instead, as ``zke_sb_de`` does.

Not independently live-verified: ``ebbweb.stadt.bamberg.de`` was
unreachable (connection timeout) from the environment this conversion was
done in, for both the legacy source and this one, so the field names/steps
and ``type_value_map`` follow the legacy source's own logic
(``ICON_MAP.get(label.split()[0])``) rather than an observed live
``SUMMARY`` string. Verify against TEST_CASES before relying on this in
production.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer

_SERVLET = (
    "https://ebbweb.stadt.bamberg.de/WasteManagementBamberg/WasteManagementServlet"
)


@final
class Source(BaseSource):
    TITLE = "Bamberg (City/Stadt)"
    DESCRIPTION = "Source for Bamberg (City/Stadt)."
    URL = "https://www.stadt.bamberg.de"
    COUNTRY = "de"

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Gartenstraße 2": {
            "street": "Gartenstraße",
            "house_number": 2,
        },
        "Egelseestraße 41b": {
            "street": "Egelseestraße",
            "house_number": 114,
            "address_suffix": "a",
        },
    }

    PARAMS = (
        street(),
        house_number(),
        text_field("address_suffix", "Address suffix", default=""),
    )

    retrieve = AthosWasteManagementRetriever(
        url=_SERVLET,
        initial_params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        iterate_field="Zeitraum",
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda street, house_number, address_suffix="", **_: {
                    "Ort": street[0].upper(),
                    "Strasse": street,
                    "Hausnummer": str(house_number),
                    "Hausnummerzusatz": address_suffix,
                },
            },
            {
                "submit_action": "forward",
                "fields": lambda **_: {
                    f"ContainerGewaehlt_{i}": "on" for i in range(1, 10)
                },
            },
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.nl.mvc.abfterm.AbfuhrTerminModel",
                },
            },
        ],
    )
    parse = parsers.EachResponse(parsers.IcsParser())
    transform = ICSTransformer(
        clean=lambda label: label.split()[0],
        type_value_map={
            "restmuell": wt.GENERAL_WASTE,
            "biomuell": wt.ORGANIC,
            "papier": wt.PAPER,
            "gelber": wt.RECYCLABLES,
        },
    )
