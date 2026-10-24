from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.service.NemenkomLt import PAGE_URL, NemenkomParser
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Nemenčinės komunalininkas"
    DESCRIPTION = 'Source for UAB "Nemenčinės komunalininkas" (Vilnius district) household waste collection schedule.'
    URL = "https://www.nemenkom.lt"
    TEST_CASES: ClassVar[dict] = {
        "Bajorai, Melisų g.": {"village": "Bajorai", "street": "Melisų g."},
        "Aleksandravas": {"village": "Aleksandravas"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "Open the household waste schedule (XLSX) on https://www.nemenkom.lt/buitiniu-ir-pakuociu-atlieku-surinkimo-grafikas/ and copy the village name from the `Kaimai` column (the part before any brackets). If the village is split by streets, also enter your street exactly as listed in the brackets, e.g. `Melisų g.`."
    }
    COUNTRY = "lt"
    PARAMS = (
        city("village"),
        street(optional=True),
    )

    # The page links the current XLSX schedule; PdfLinkRetriever fetches any
    # linked document, not only PDFs.
    retrieve = PdfLinkRetriever(
        index_url=PAGE_URL,
        pattern=r"\.xlsx$",
        select="first",
        headers={"user-agent": "Mozilla/5.0"},
    )
    parse = NemenkomParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={"Buitinės atliekos": wt.GENERAL_WASTE},
    )
