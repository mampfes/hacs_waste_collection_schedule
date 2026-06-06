import io
import re
import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine, LTRect
from datetime import date
import logging
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "KOSIT EAST"
DESCRIPTION = "Source for KOSIT EAST waste collection."
URL = "https://kositeast.sk"
COUNTRY = "sk"

TEST_CASES = {
    "Adidovce": {"town": "Adidovce"},
    "Andrejová": {"town": "Andrejová"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "town": "Town",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "town": "Town name as displayed on the kositeast.sk website.",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your town on https://kositeast.sk/obyvatelia/harmonogram-zberu-odpadu-v-obciach/ and enter it exactly as it appears in the link.",
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Komunálny odpad": Icons.GENERAL_WASTE,
    "Plasty, VKM, Kovové obaly": Icons.RECYCLING,
    "Sklo": Icons.GLASS,
    "Papier": Icons.PAPER,
    "Jedlé oleje a tuky": Icons.ORGANIC,
    "Nebezpečný odpad": Icons.HAZARDOUS,
}

COLOR_MAP = {
    (1.0, 1.0, 0.0): "Plasty, VKM, Kovové obaly",
    (0.451, 0.89, 0.008): "Sklo",
    (0.584, 0.729, 1.0): "Papier",
    (1.0, 0.702, 0.4): "Jedlé oleje a tuky",
    (0.741, 0.494, 0.984): "Nebezpečný odpad",
    (0.0, 0.0, 0.0): "Komunálny odpad",
}

class Source:
    def __init__(self, town: str):
        self._town = town

    def fetch(self) -> list[Collection]:
        # 1. Fetch main page to get PDF link
        schedule_url = "https://kositeast.sk/obyvatelia/harmonogram-zberu-odpadu-v-obciach/"
        r = requests.get(schedule_url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        pdf_link = None
        for a in soup.find_all("a", href=True):
            if a.text.strip().lower() == self._town.strip().lower() and a['href'].endswith('.pdf'):
                pdf_link = a['href']
                break
        
        if not pdf_link:
            raise SourceArgumentNotFound("town", self._town)
            
        # 2. Download PDF
        r_pdf = requests.get(pdf_link)
        r_pdf.raise_for_status()
        pdf_stream = io.BytesIO(r_pdf.content)
        
        # 3. Parse PDF
        pages = list(extract_pages(pdf_stream))
        if not pages:
            return []
            
        page = pages[0]
        
        lines = []
        rects = []
        
        year = 2024 # fallback
        
        for element in page:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    if isinstance(text_line, LTTextLine):
                        text = text_line.get_text().strip()
                        if text:
                            lines.append({'bbox': text_line.bbox, 'text': text})
                            m = re.search(r"ROK (\d{4})", text)
                            if m:
                                year = int(m.group(1))
            elif isinstance(element, LTRect):
                if 10 < element.width < 15 and 5 < element.height < 10:
                    color = element.non_stroking_color
                    if isinstance(color, (int, float)):
                        color = (color, color, color)
                    elif color is not None:
                        color = tuple(round(c, 3) for c in color)
                    else:
                        color = (0.0, 0.0, 0.0)
                    rects.append({'bbox': element.bbox, 'color': color})
                    
        collections = []
        
        for r_item in rects:
            rx0, ry0, rx1, ry1 = r_item['bbox']
            rcx = (rx0 + rx1) / 2
            rcy = (ry0 + ry1) / 2
            
            col = int((rcx - 40) / 86.6)
            if col < 0 or col > 5:
                continue
                
            is_top = rcy > 485
            month = 1 + col + (0 if is_top else 6)
            
            matched_text = None
            for l in lines:
                lx0, ly0, lx1, ly1 = l['bbox']
                if max(ry0, ly0) < min(ry1, ly1):
                    l_col = int((lx0 - 40) / 86.6)
                    if l_col == col:
                        m = re.search(r"(?:^|[A-Za-zžščťďňľĺáéíóúäô]+\s+)(\d+)\b", l['text'])
                        if m:
                            matched_text = m.group(1)
                            break
            
            if matched_text:
                day = int(matched_text)
                waste_type = COLOR_MAP.get(r_item['color'])
                if waste_type:
                    collections.append(Collection(
                        date=date(year, month, day),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type)
                    ))
                else:
                    _LOGGER.warning(f"Unknown color {r_item['color']} found in schedule")
                    
        return collections
