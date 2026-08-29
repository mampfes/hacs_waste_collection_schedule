import io
import re
from typing import ClassVar
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pdfminer.layout import LTPage, LTTextContainer, LTTextLine
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.source.kositeast_sk import COLOR_MAP as EAST_COLOR_MAP
from waste_collection_schedule.source.kositeast_sk import Source as KositEastSource

TITLE = "KOSIT WEST"
DESCRIPTION = "Source for KOSIT WEST waste collection."
URL = (
    "https://kositwest.sk/sluzby/zber-komunalneho-odpadu-a-triedenych-zloziek-z-obci-"
    "a-samosprav/harmonogramy-zberu-odpadu-v-obciach/"
)
COUNTRY = "sk"

SOURCE_CODEOWNERS = ["@mynameisdominik"]

TEST_CASES = {
    "Vieska": {"town": "Vieska"},
    "Sap": {"town": "Sap"},
    "Michal na Ostrove": {"town": "Michal na Ostrove"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "town": "Town",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "town": "Town name as displayed on the kositwest.sk website.",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your town on the KOSIT WEST website and enter it exactly as it appears in the link.",
}


class Source(KositEastSource):
    _MAX_RECT_WIDTH = 0.04
    _N_MONTH_COLS = 3
    _N_MONTH_ROWS = 4
    _MATCH_HORIZONTAL_OVERLAP = True
    _COLOR_MAP: ClassVar[dict[tuple, str]] = {
        **EAST_COLOR_MAP,
        (0.573, 0.816, 0.314): "Sklo",
        (0.557, 0.663, 0.859): "Papier",
    }
    _IGNORED_COLORS: ClassVar[set[tuple]] = {(1.0, 1.0, 1.0)}

    @staticmethod
    def _extract_year(page: LTPage) -> int | None:
        for element in page:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    if isinstance(text_line, LTTextLine):
                        match = re.search(r"\b(20\d{2})\b", text_line.get_text())
                        if match:
                            return int(match.group(1))
        return None

    def _download_pdf(self) -> io.BytesIO:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        pdf_link: str | None = None
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if not isinstance(href, str):
                continue
            if anchor.get_text(
                strip=True
            ).lower() == self._town.strip().lower() and href.lower().endswith(".pdf"):
                pdf_link = href
                break

        if pdf_link is None:
            raise SourceArgumentNotFound("town", self._town)

        pdf_response = requests.get(urljoin(URL, pdf_link), timeout=30)
        pdf_response.raise_for_status()
        return io.BytesIO(pdf_response.content)
