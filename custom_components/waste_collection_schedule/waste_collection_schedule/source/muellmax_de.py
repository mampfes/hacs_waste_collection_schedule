from typing import ClassVar, final

from waste_collection_schedule import parsers, regions
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    service_id,
    street,
)
from waste_collection_schedule.service.MuellmaxDe import MuellmaxRetriever
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a fully declarative source over a stateful platform wizard. The
# Müllmax multi-step form walk lives in the service module as MuellmaxRetriever,
# so this source only declares the pipeline: the final ICS response flows to the
# ordinary IcsParser + ICSTransformer, with the German bin names resolved by the
# shared multilingual vocabulary. One structure covers every Müllmax
# municipality via a callable REGIONS over its own provider registry.


# Müllmax providers prefix each bin label with a provider code and often a bin
# colour, e.g. "ASH Restmüll-Tonne" or "USB Abfuhr Grau - Restmüll", which stops
# the shared vocabulary from matching. Reduce each label to its core German
# waste term so the map below resolves it; unrecognised labels pass through
# unchanged (resolved by the vocabulary or preserved verbatim).
_TYPE_VALUE_MAP = {
    "restmüll": wt.GENERAL_WASTE,
    "bioabfall": wt.ORGANIC,
    "altpapier": wt.PAPER,
    "wertstoff": wt.RECYCLABLES,
    "grünabfall": wt.GARDEN_WASTE,
    "schadstoff": wt.HAZARDOUS,
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

    REGIONS = regions.from_yaml("muellmax_de", service="service_id")
