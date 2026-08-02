"""hausmüll.info, a multi-tenant calendar platform for several German operators.

A hausmüll.info deployment in its "search dialect": the address cascade
(Ort -> Ortsteil -> Straße -> Hausnummer -> Zusatz) runs against one endpoint
per level under ``search/``, each level a fuzzy search that may need retrying
with special characters folded. See ``service/HausmuellInfo.py`` for the
platform.

Every operator in ``SUPPORTED_PROVIDERS`` is preserved as its own ``Region``
(the typed successor to the legacy ``EXTRA_INFO`` list), so none of the towns
this source covers are dropped by the conversion.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    district,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.HausmuellInfo import (
    FromForm,
    HausmuellInfoRetriever,
    Lookup,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

API_URL = "https://{}.hausmuell.info/"

SUPPORTED_PROVIDERS: list = [
    {
        "subdomain": "ebkds",
        "title": "Eigenbetrieb Kommunalwirtschaftliche Dienstleistungen Suhl",
        "url": "https://www.ebkds.de/",
    },
    {
        "subdomain": "erfurt",
        "title": "Stadtwerke Erfurt, SWE",
        "url": "https://www.stadtwerke-erfurt.de/",
    },
    {
        "subdomain": "schmalkalden-meiningen",
        "title": "Kreiswerke Schmalkalden-Meiningen GmbH",
        "url": "https://www.kwsm.de/",
    },
    {
        "subdomain": "ew",
        "title": "Eichsfeldwerke GmbH",
        "url": "https://www.eichsfeldwerke.de/",
    },
    {
        "subdomain": "azv",
        "title": "Abfallwirtschaftszweckverband Wartburgkreis (AZV)",
        "url": "https://www.azv-wak-ea.de/",
    },
    {
        "subdomain": "boerde",
        "title": "Landkreis Börde AöR (KsB)",
        "url": "https://www.ks-boerde.de",
    },
    {
        "subdomain": "asc",
        "title": "Chemnitz (ASR)",
        "url": "https://www.asr-chemnitz.de/",
    },
    {"subdomain": "wesel", "title": "ASG Wesel", "url": "https://www.asg-wesel.de/"},
]

_REJECTED_TEXT = "Bitte geben Sie Ihre Daten korrekt an."


def _clean_label(label: str) -> str:
    """Fix the provider's mojibake and strip the wrapper phrases it adds.

    "Ã¼" is a UTF-8-as-Latin-1 mis-decode of "ü" that survives even after
    forcing the response encoding (a legacy quirk of this provider, kept
    exactly). "Entsorgung:"/"Verschobene Abholung:" are prefix/label noise the
    provider adds around the actual bin name; stripping both (not just the
    former, as the legacy source did only for its icon lookup) means a
    rescheduled collection now resolves to the same canonical type as a
    regular one instead of falling through to a raw "Verschobene Abholung:
    ..." label.
    """
    text = label.replace("Ã¼", "ü").replace("Entsorgung:", "")
    lowered = text.lower()
    marker = "verschobene abholung:"
    idx = lowered.find(marker)
    if idx != -1:
        text = text[:idx] + text[idx + len(marker) :]
    return text.strip()


def _lookup_form(ort: str, ortsteil: str, strasse: str, hausnummer: str, **_) -> dict:
    """The platform's own search form, in the order its page submits it."""
    return {
        "hidden_kalenderart": "privat",
        "input_ort": ort,
        "input_ortsteil": ortsteil,
        "input_str": [strasse, strasse],
        "input_hnr": [hausnummer, hausnummer],
        "ort_id": "0",
        "ortteil_id": "0",
        "str_id": "0",
        "hidden_id_ort": "0",
        "hidden_id_ortsteil": "0",
        "hidden_id_str": "0",
        "hidden_id_hnr": "0",
        "hidden_id_egebiet": "0",
        "hidden_send_btn": "ics",
        "hiddenYear": str(datetime.now().year),
    }


@final
class Source(BaseSource):
    TITLE = "hausmüll.info"
    DESCRIPTION = "Source for hausmüll.info."
    URL = "https://hausmuell.info"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Dietzhausen Am Rain 10 ebkds": {
            "ort": "Dietzhausen",
            "strasse": "Am Rain",
            "hausnummer": 10,
            "subdomain": "ebkds",
        },
        "Adam-Ries-Straße 5, Erfurt": {
            "subdomain": "erfurt",
            "strasse": "Adam-Ries-Straße",
            "hausnummer": "5",
        },
        "schmalkalden-meiningen, Obermaßfeld-Grimmenthal": {
            "subdomain": "schmalkalden-meiningen",
            "ort": "Obermaßfeld-Grimmenthal",
        },
        "schmalkalden-meiningen, Dillstädt": {
            "subdomain": "schmalkalden-meiningen",
            "ort": "Dillstädt",
        },
        "schmalkalden-meiningen Zella-Mehils Benshausen Albrechter Straße": {
            "subdomain": "schmalkalden-meiningen",
            "ort": "Zella-Mehlis",
            "ortsteil": "Benshausen",
            "strasse": "Albrechtser Straße",
        },
        "schmalkalden-meiningen Breitungen, Bußhof": {
            "subdomain": "schmalkalden-meiningen",
            "ort": "Breitungen",
            "ortsteil": "Bußhof",
        },
        "ew, Döringsdorf, Wanfrieder Str.": {
            "subdomain": "ew",
            "ort": "Döringsdorf",
            "strasse": "Wanfrieder Str.",
        },
        "ew, Bernterode (WBS), Hinter den Höfen": {
            "subdomain": "ew",
            "ort": "Bernterode (WBS)",
            "strasse": "Hinter den Höfen",
        },
        "azv, Berka vor dem Hainich": {
            "subdomain": "azv",
            "ort": "Berka vor dem Hainich",
        },
        "azv, Hörselberg-Hainich": {
            "subdomain": "azv",
            "ort": "Hörselberg-Hainich",
            "ortsteil": "Ettenhausen/Nesse",
        },
        "börde, Belsdorf (Altkreis BÖ), Alleringerslebener Straße 15a": {
            "subdomain": "boerde",
            "ort": "Belsdorf (Altkreis BÖ)",
            "strasse": "Alleringerslebener Straße",
            "hausnummer": "15a",
        },
        "chemnitz, Straße des Friedens/Wittgensdorf 2 a": {
            "subdomain": "asc",
            "strasse": "Straße des Friedens/Wittgensdorf",
            "hausnummer": "2 a",
        },
        "wesel Flüren, In der Flürener Heide": {
            "subdomain": "wesel",
            "ort": "Flüren",
            "strasse": "In der Flürener Heide",
        },
    }

    # One structure, many independent operators: preserve every one of
    # SUPPORTED_PROVIDERS as its own Region so none are dropped by the
    # conversion.
    REGIONS = tuple(
        region(p["title"], url=p["url"], subdomain=p["subdomain"])
        for p in SUPPORTED_PROVIDERS
    )

    PARAMS = (
        text_field("subdomain", "Subdomain"),
        district(field="ort", optional=True),
        text_field("ortsteil", "District", optional=True),
        street(field="strasse", optional=True),
        house_number(field="hausnummer", optional=True),
    )

    retrieve = HausmuellInfoRetriever(
        base_url=lambda subdomain, **_: API_URL.format(subdomain),
        form=_lookup_form,
        steps=(
            Lookup(
                field="ort",
                endpoint="search/search_orte.php",
                query={"ort_id": "0"},
                assign=("hidden_id_ort", "ort_id"),
            ),
            Lookup(
                field="ortsteil",
                endpoint="search/search_ortsteile.php",
                query={"ort_id": FromForm("ort_id")},
                assign=("ort_id", "hidden_id_ortsteil"),
                zero_falls_back_to="hidden_id_ort",
                set_input=False,
            ),
            Lookup(
                field="strasse",
                endpoint="search/search_strassen.php",
                query={"str_id": "0", "ort_id": FromForm("ort_id")},
                assign=("hidden_id_str", "str_id"),
                set_input=False,
            ),
            Lookup(
                field="hausnummer",
                endpoint="search/search_hnr.php",
                query={"hnr_id": "0", "str_id": FromForm("str_id")},
                assign=("hidden_id_hnr", "hnr_id"),
            ),
        ),
        area_key="hidden_id_egebiet",
        landing_page=True,
        check_zusatz=True,
        repeat_list_values=True,
        retry_folded=True,
        encoding="utf-8",
        rejected_text=_REJECTED_TEXT,
        rejected_field="subdomain",
        check_lookup_status=False,
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        clean=_clean_label,
        type_value_map={
            "hausmüll": GENERAL_WASTE,
            "restabfall": GENERAL_WASTE,
            "restmüll": GENERAL_WASTE,
            "glass": GLASS,
            "biomüll": ORGANIC,
            "biomüll mit reinigung": ORGANIC,
            "bioabfall mit reinigung": ORGANIC,
            "bioabfall": ORGANIC,
            "papier": PAPER,
            "papier, pappe, karton": PAPER,
            "papier, pappe & kart.": PAPER,
            "pappe, papier & kart.": PAPER,
            "altpapier": PAPER,
            "gelbe tonne": RECYCLABLES,
            "gelber sack": RECYCLABLES,
            "gelber sack / gelbe tonne": RECYCLABLES,
            "leichtverpackungen": RECYCLABLES,
            "leichtstoffverpackungen": RECYCLABLES,
            "grünschnitt": GARDEN_WASTE,
            "schadstoffe": HAZARDOUS,
            "schadstoffmobil": HAZARDOUS,
            "problemmüll": HAZARDOUS,
        },
    )

    def __init__(
        self,
        subdomain: str,
        ort: "str | None" = None,
        ortsteil: "str | None" = None,
        strasse: "str | None" = None,
        hausnummer: "str | int | None" = None,
    ):
        super().__init__(
            subdomain=subdomain,
            ort=ort or "",
            ortsteil=ortsteil or "",
            strasse=strasse or "",
            hausnummer=str(hausnummer) if hausnummer else "",
        )
