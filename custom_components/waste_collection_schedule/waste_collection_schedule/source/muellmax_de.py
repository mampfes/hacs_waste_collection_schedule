from typing import final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.MuellmaxDe import SERVICE_MAP, MuellmaxRetriever
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a fully declarative source over a stateful platform wizard. The
# Müllmax multi-step form walk lives in the service module as MuellmaxRetriever,
# so this source only declares the pipeline: the final ICS response flows to the
# ordinary IcsParser + ICSTransformer, with the German bin names resolved by the
# shared multilingual vocabulary. One structure covers every Müllmax
# municipality via a callable REGIONS over the platform's SERVICE_MAP.


@final
class Source(BaseSource):
    TITLE = "Müllmax"
    DESCRIPTION = "Source for Müllmax waste collection."
    URL = "https://www.muellmax.de"
    COUNTRY = "de"

    TEST_CASES = {
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

    PARAMS = [
        text_field("service", "Service"),
        text_field("mm_frm_ort_sel", "Ort", optional=True),
        text_field("mm_frm_str_sel", "Straße", optional=True),
        text_field("mm_frm_hnr_sel", "Hausnummer", optional=True),
    ]

    retrieve = MuellmaxRetriever()
    parse = parsers.IcsParser(min_events=1)
    transform = ICSTransformer()

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
            for s in SERVICE_MAP
        ]
