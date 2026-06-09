import datetime
import io
import re

import requests
from pypdf import PdfReader
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "SEAB Biella"
DESCRIPTION = "Source for SEAB Biella (Italy) waste collection."
URL = "https://www.seab.biella.it"
COUNTRY = "it"

TEST_CASES = {
    "Ailoche": {
        "url": "https://www.seab.biella.it/wp-content/uploads/2026/05/Ailoche-II-semestre.pdf"
    },
    "Andorno Micca": {
        "url": "https://www.seab.biella.it/wp-content/uploads/2026/05/Andorno-Micca-II-semestre.pdf"
    },
}

MONTH_NAMES = {
    "GENNAIO": 1,
    "FEBBRAIO": 2,
    "MARZO": 3,
    "APRILE": 4,
    "MAGGIO": 5,
    "GIUGNO": 6,
    "LUGLIO": 7,
    "AGOSTO": 8,
    "SETTEMBRE": 9,
    "OTTOBRE": 10,
    "NOVEMBRE": 11,
    "DICEMBRE": 12,
}

# Mapping of waste types in the PDF to icons
WASTE_TYPES = {
    "INDIFFERENZIATO": {"icon": "mdi:trash-can"},
    "ORGANICO": {"icon": "mdi:leaf"},
    "CARTA": {"icon": "mdi:package-variant"},
    "PLASTICA": {"icon": "mdi:recycle"},
    "VETRO": {"icon": "mdi:glass-fragile"},
    "SFALCI": {"icon": "mdi:leaf"},
}

PARAM_DESCRIPTIONS = {
    "it": {
        "url": "URL del file PDF del calendario (es. https://www.seab.biella.it/wp-content/uploads/2026/05/Ailoche-II-semestre.pdf)",
    },
    "en": {
        "url": "URL of the PDF calendar file (e.g., https://www.seab.biella.it/wp-content/uploads/2026/05/Ailoche-II-semestre.pdf)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "url": "URL",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "it": "Visita https://www.seab.biella.it/aree-servite, seleziona il tuo comune e copia il link al file PDF del calendario.",
    "en": "Visit https://www.seab.biella.it/aree-servite, select your municipality and copy the link to the PDF calendar file.",
}


class Source:
    def __init__(self, url):
        self._url = url

    def fetch(self):
        response = requests.get(self._url, timeout=10)
        response.raise_for_status()

        reader = PdfReader(io.BytesIO(response.content))

        # Extract full text to find the year
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()

        year_match = re.search(r"Raccolta rifiuti (\d{4})", full_text)
        year = int(year_match.group(1)) if year_match else datetime.date.today().year

        entries = []
        for page in reader.pages:
            page_text = page.extract_text(extraction_mode="layout")
            lines = page_text.splitlines()

            # Find months on this page and their horizontal positions
            month_configs = []
            for line in lines:
                line_upper = line.upper()
                for m_name, m_num in MONTH_NAMES.items():
                    if m_name in line_upper:
                        for match in re.finditer(re.escape(m_name), line_upper):
                            month_configs.append(
                                {"name": m_name, "num": m_num, "pos": match.start()}
                            )
                if month_configs:
                    break

            if not month_configs:
                continue

            month_configs.sort(key=lambda x: x["pos"])

            for line in lines:
                # Find all potential day entries in the line: "NN aaa" where NN is 1-2 digits and aaa is 3 letters
                matches = list(re.finditer(r"(\d{1,2})\s+[a-z]{3}", line.lower()))
                if not matches:
                    continue

                # The first match gives us the day number for this line
                day_num = int(matches[0].group(1))

                # Determine which months on this page SHOULD have this day number
                valid_months = []
                for m_conf in month_configs:
                    try:
                        datetime.date(year, m_conf["num"], day_num)
                        valid_months.append(m_conf)
                    except ValueError:
                        # Day doesn't exist in this month (e.g., Feb 30)
                        pass

                # Match each found date entry to a valid month in order
                for i in range(min(len(matches), len(valid_months))):
                    m_conf = valid_months[i]
                    start_pos = matches[i].start()
                    # Chunk goes until the next match or end of line
                    end_pos = (
                        matches[i + 1].start() if i + 1 < len(matches) else len(line)
                    )
                    chunk_upper = line[start_pos:end_pos].upper()

                    # Check for waste types in the current cell
                    for w_type, w_info in WASTE_TYPES.items():
                        if w_type in chunk_upper:
                            try:
                                date = datetime.date(year, m_conf["num"], day_num)
                                entries.append(
                                    Collection(
                                        date, w_type.capitalize(), w_info["icon"]
                                    )
                                )
                            except ValueError:
                                pass

        return entries
