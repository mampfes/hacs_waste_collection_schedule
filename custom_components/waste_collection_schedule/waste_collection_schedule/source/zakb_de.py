"""Zweckverband Abfallwirtschaft Kreis Bergstraße (zakb.de).

Demonstrates: an Athos "WasteManagementServlet" wizard whose final download
step posts a *fresh* payload rather than the accumulated form state every
other step in this codebase's Athos deployments carries forward (see
AthosWasteManagementRetriever). Expressing that reset through the shared
retriever's declarative ``steps``/``remove`` would need every earlier field
named explicitly; a source-defined retrieve() mirrors the three POSTs
one-for-one instead.
"""

from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    house_number,
    municipality,
    street,
    text_field,
)
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

API_URL = "https://www.zakb.de/online-service/abfallkalender/"


@final
class Source(BaseSource):
    TITLE = "Zweckverband Abfallwirtschaft Kreis Bergstraße"
    DESCRIPTION = "Source for Zweckverband Abfallwirtschaft Kreis Bergstraße."
    URL = "https://www.zakb.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Abtsteinach, Am Hofböhl 1 ": {
            "ort": "Abtsteinach",
            "strasse": "Am Hofböhl",
            "hnr": "1",
            "hnr_zusatz": "",
        },
        "Gorxheimertal, Am Herrschaftswald 10": {
            "ort": "Gorxheimertal",
            "strasse": "Am Herrschaftswald",
            "hnr": "10",
        },
        "Rimbach, Ahornweg 1 B": {
            "ort": "Rimbach",
            "strasse": "Ahornweg",
            "hnr": "1",
            "hnr_zusatz": "B",
        },
        "Zwingenberg, Diefenbachstraße 57": {
            "ort": "Zwingenberg",
            "strasse": "Diefenbachstraße",
            "hnr": 57,
            "hnr_zusatz": "",
        },
        "Bensheim im Bangert 9 a": {
            "ort": "Bensheim",
            "strasse": "Im Bangert",
            "hnr": 9,
            "hnr_zusatz": "A",
        },
    }

    PARAMS = (
        municipality(field="ort"),
        street(field="strasse"),
        house_number(field="hnr"),
        text_field("hnr_zusatz", "House number addition", optional=True),
    )

    def retrieve(self, source):
        session = source.session
        ort = source.params["ort"]
        strasse = source.params["strasse"]
        hnr = str(source.params["hnr"])
        hnr_zusatz = source.params.get("hnr_zusatz") or ""

        r = session.get(API_URL)
        r.raise_for_status()

        args = {
            "aos[Ort]": ort,
            "aos[Strasse]": strasse,
            "aos[Hausnummer]": hnr,
            "aos[Hausnummerzusatz]": hnr_zusatz,
            "aos[CheckBoxRestabfallbehaelter]": "on",
            "aos[CheckBoxRestabfallcontainer]": "on",
            "aos[CheckBoxBioabfallbehaelter]": "on",
            "aos[CheckBoxPapierbehaelter]": "on",
            "aos[CheckBoxPapiercontainer]": "on",
            "aos[CheckBoxGruensperrmuell]": "on",
            "aos[CheckBoxGelber+Sack]": "on",
            "aos[CheckBoxDSD-Container]": "on",
            "submitAction": "CITYCHANGED",
            "pageName": "Lageadresse",
        }
        r = session.post(API_URL, data=args)
        r.raise_for_status()

        args["submitAction"] = "nextPage"
        r = session.post(API_URL, data=args)
        r.raise_for_status()

        return session.post(
            API_URL,
            data={"submitAction": "filedownload_ICAL", "pageName": "Terminliste"},
        )

    parse = IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "restabfallbehaelter": GENERAL_WASTE,
            "restabfallcontainer": GENERAL_WASTE,
            "bioabfallbehaelter": ORGANIC,
            "papierbehaelter": PAPER,
            "papiercontainer": PAPER,
            "gelber sack": RECYCLABLES,
            "gruensperrmuell": GARDEN_WASTE,
        }
    )

    def __init__(self, ort: str, strasse: str, hnr: "str | int", hnr_zusatz: str = ""):
        super().__init__(ort=ort, strasse=strasse, hnr=str(hnr), hnr_zusatz=hnr_zusatz)
