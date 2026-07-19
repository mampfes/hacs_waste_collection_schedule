from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    service_id,
    street,
)
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.MuellmaxDe import MuellmaxRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

# Demonstrates: a fully declarative source over a stateful platform wizard. The
# Müllmax multi-step form walk lives in the service module as MuellmaxRetriever,
# so this source only declares the pipeline: the final ICS response flows to the
# ordinary IcsParser + ICSTransformer, with the German bin names resolved by the
# shared multilingual vocabulary. One structure covers every Müllmax
# municipality via a callable REGIONS over its own provider registry.


# The provider registry for this one structure: each entry becomes a Region
# (a discoverable listing with its Müllmax service id pre-filled). New providers
# are added here, in the source that owns them.
_PROVIDERS = [
    # AWISTA Düsseldorf ("Dus") removed: the provider switched its backend and the
    # Müllmax form no longer works (upstream #6707, issue #3500).
    # RSAG Rhein-Sieg-Kreis ("Rsa") is covered by the dedicated `rsag_de` source
    # (same Müllmax backend, friendlier city/street config) — see #6553. Entry
    # removed to avoid two listings for the same provider.
    {
        "title": "USB Bochum",
        "url": "https://www.usb-bochum.de/",
        "service_id": "Usb",
    },
    {
        "title": "Abfallwirtschaftsbetriebe Münster",
        "url": "https://www.stadt-muenster.de",
        "service_id": "Awm",
    },
    {
        "title": "Entsorgungsbetrieb Stadt Mainz",
        "url": "https://eb-mainz.de/",
        "service_id": "Ebm",
    },
    {
        "title": "EVS Entsorgungsverband Saar",
        "url": "https://www.evs.de/",
        "service_id": "Evs",
    },
    {
        "title": "Landkreis Gießen",
        "url": "https://www.lkgi.de/",
        "service_id": "Lkg",
    },
    {
        "title": "Stadt Hamm",
        "url": "https://www.hamm.de/",
        "service_id": "Ash",
    },
    {
        "title": "Stadt Darmstadt",
        "url": "darmstadt.de",
        "service_id": "Ead",
    },
    {
        "title": "TBR Remscheid",
        "url": "https://www.tbr-info.de/",
        "service_id": "Tbr",
    },
    {
        "title": "Stadtbildpflege Kaiserslautern",
        "url": "https://www.stadtbildpflege-kl.de/",
        "service_id": "Ask",
    },
    {
        "title": "Stadt Hanau",
        "url": "https://www.hanau.de/",
        "service_id": "His",
    },
    {
        "title": "Stadt Maintal",
        "url": "https://www.maintal.de/",
        "service_id": "Mai",
    },
    {
        "title": "Stadt Haltern am See",
        "url": "https://www.haltern-am-see.de/",
        "service_id": "Hal",
    },
    {
        "title": "Kreisstadt Friedberg",
        "url": "https://www.friedberg-hessen.de/",
        "service_id": "Efb",
    },
]


# Müllmax providers prefix each bin label with a provider code and often a bin
# colour, e.g. "ASH Restmüll-Tonne" or "USB Abfuhr Grau - Restmüll", which stops
# the shared vocabulary from matching. Reduce each label to its core German
# waste term so the map below resolves it; unrecognised labels pass through
# unchanged (resolved by the vocabulary or preserved verbatim).
_TYPE_VALUE_MAP = {
    "restmüll": GENERAL_WASTE,
    "bioabfall": ORGANIC,
    "altpapier": PAPER,
    "wertstoff": RECYCLABLES,
    "grünabfall": GARDEN_WASTE,
    "schadstoff": HAZARDOUS,
}


def _clean(label: str) -> str:
    text = label.lower()
    if "restmüll" in text or "restabfall" in text:
        return "restmüll"
    if "bioabfall" in text or "biotonne" in text:
        return "bioabfall"
    if "altpapier" in text or "papier" in text:
        return "altpapier"
    if "wertstoff" in text or "gelb" in text or "verpack" in text:
        return "wertstoff"
    if "grünab" in text or "grüngut" in text or "grünschnitt" in text:
        return "grünabfall"
    if "umweltmobil" in text or "schadstoff" in text or "problemstoff" in text:
        return "schadstoff"
    return label


@final
class Source(BaseSource):
    TITLE = "Müllmax"
    DESCRIPTION = "Source for Müllmax waste collection."
    URL = "https://www.muellmax.de"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "USB Freiligrathstraße 55": {
            "service": "Usb",
            "mm_frm_str_sel": "Freiligrathstraße",
            "mm_frm_hnr_sel": "44791;Innenstadt;55;",
        },
        "ASH Schäferstraße 49 (plain number)": {
            "service": "Ash",
            "mm_frm_str_sel": "Schäferstraße",
            "mm_frm_hnr_sel": "49",
        },
    }

    PARAMS = (
        service_id("service"),
        city("mm_frm_ort_sel", optional=True),
        street("mm_frm_str_sel", optional=True),
        house_number("mm_frm_hnr_sel", optional=True),
    )

    retrieve = MuellmaxRetriever()
    parse = parsers.IcsParser(min_events=1)
    transform = ICSTransformer(clean=_clean, type_value_map=_TYPE_VALUE_MAP)

    def __init__(
        self,
        service: str,
        mm_frm_ort_sel: str | None = None,
        mm_frm_str_sel: str | None = None,
        mm_frm_hnr_sel: str | None = None,
    ):
        super().__init__(
            service=service,
            mm_frm_ort_sel=mm_frm_ort_sel,
            mm_frm_str_sel=mm_frm_str_sel,
            mm_frm_hnr_sel=mm_frm_hnr_sel,
        )

    @staticmethod
    def REGIONS() -> list[Region]:
        return [
            region(s["title"], url=s["url"], service=s["service_id"])
            for s in _PROVIDERS
        ]
