import re
import unicodedata
from datetime import date
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from pypdf import PdfReader
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Communauté de Communes de Montesquieu"  # Title will show up in README.md and info.md
DESCRIPTION = "Source script for cc-montesquieu.fr"  # Describe your source
URL = "https://www.cc-montesquieu.fr/"  # Insert url to service homepage. URL will show up in README.md and info.md
DATA_URL = "https://www.cc-montesquieu.fr/vivre/dechets/collectes-des-dechets"  # url used to retrieve data
COUNTRY = "fr"

COMMUNES = [
    "Ayguemorte-les-Graves",
    "Beautiran",
    "Cabanac-et-Villagrains",
    "Cadaujac",
    "Castres-Gironde",
    "Isle Saint-Georges",
    "La Brède",
    "Léognan",
    "Martillac",
    "Saint-Médard-d'Eyrans",
    "Saint-Morillon",
    "Saint-Selve",
    "Saucats",
]


def _normalize_commune(s: str) -> str:
    """Remove accents, uppercase, and collapse separators for fuzzy name matching."""
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    s = re.sub("[-'‘’]", " ", s.upper())
    return re.sub(r"\s+", " ", s).strip()


COMMUNES_NORMALIZED = {_normalize_commune(c): c for c in COMMUNES}

EXTRA_INFO = [
    {
        "title": city,
        "url": URL,
        "default_params": {"commune": city},
    }
    for city in COMMUNES
]

TEST_CASES = {commune: {"commune": commune} for commune in COMMUNES}

ICON_MAP = {
    "Bac d'ordures ménagères": "mdi:trash-can",
    "Bac jaune": "mdi:recycle",
    "Déchets verts": "mdi:leaf",
    "Encombrants": "mdi:dump-truck",
}

WEEKDAY_MAP = {
    "lundi": MO,
    "mardi": TU,
    "mercredi": WE,
    "jeudi": TH,
    "vendredi": FR,
    "samedi": SA,
    "dimanche": SU,
}

MOIS_MAP = {
    "janvier": 1,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "decembre": 12,
}

PARAM_DESCRIPTIONS = {
    "fr": {
        "commune": "Votre ville de la Communauté de Communes de Montesquieu : "
        + ", ".join(COMMUNES)
    },
    "en": {
        "commune": "Your city of Montesquieu's community: " + ", ".join(COMMUNES),
    },
}

PARAM_TRANSLATIONS = {
    "fr": {"commune": "Ville"},
    "en": {"commune": "City"},
    "de": {"commune": "Stadt"},
}


class Source:
    def __init__(self, commune: str):
        self.commune = commune
        if self.commune not in COMMUNES:
            raise SourceArgumentNotFoundWithSuggestions(
                "Commune", self.commune, COMMUNES
            )

    def get_parsed_source(self) -> BeautifulSoup:
        response = requests.get(DATA_URL)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def fetch(self) -> list[Collection]:
        parsed_source = self.get_parsed_source()
        city_planning = self.get_planning_table(parsed_source)[self.commune]

        entries = [
            Collection(date=dt.date(), t=bin_type, icon=ICON_MAP.get(bin_type))
            for bin_type, french_day in city_planning.items()
            for dt in rrule(
                freq=WEEKLY,
                dtstart=date.today(),
                count=20,
                byweekday=WEEKDAY_MAP[french_day.strip().lower()],
            )
        ]

        pdf_planning = self.get_planning_table_dechets_verts_et_encombrants_pdf(
            parsed_source
        )
        for bin_type, dates in pdf_planning.get(self.commune, {}).items():
            entries.extend(
                Collection(date=dt, t=bin_type, icon=ICON_MAP.get(bin_type))
                for dt in dates
            )

        return entries

    def get_planning_table(
        self, parsed_source: BeautifulSoup
    ) -> dict[str, dict[str, str]]:
        planning: dict[str, dict[str, str]] = {}
        for table in parsed_source.select("table"):
            if "ordures ménagères" not in str(table):
                continue
            thead = table.find("thead")
            table_body = table.find("tbody")
            if not thead or not table_body:
                continue
            table_heads = thead.find_all("th")
            # The source HTML is malformed: the first <TR> is absent, so handle
            # the orphan TDs before the first proper <TR> manually.
            table_datas = table_body.find_all("td")
            self._fill_planning(
                planning, table_datas[0].text.strip(), table_heads, table_datas
            )
            for row in table_body.find_all("tr"):
                td = row.select("td")
                self._fill_planning(planning, td[0].text.strip(), table_heads, td)
        return planning

    @staticmethod
    def _fill_planning(planning, ville, table_heads, table_datas):
        canonical = COMMUNES_NORMALIZED.get(_normalize_commune(ville), ville)
        planning[canonical] = {
            table_heads[1].text: table_datas[1].text.strip(),
            table_heads[2].text: table_datas[2].text.strip(),
        }

    def get_planning_table_dechets_verts_et_encombrants_pdf(
        self, parsed_source: BeautifulSoup
    ) -> dict[str, dict[str, list[date]]]:
        """Extract déchets verts and encombrants planning from PDF files linked on the page."""
        current_year = date.today().year
        best_url = None
        best_year = 0

        for a_tag in parsed_source.find_all("a", href=True):
            href = str(a_tag["href"])
            m = re.search(
                r"PLANNING-DECHETS-VERTS-ENCOMBRANTS-(\d{4})\.pdf",
                href,
                re.IGNORECASE,
            )
            if m:
                pdf_year = int(m.group(1))
                if pdf_year >= current_year and pdf_year > best_year:
                    best_year = pdf_year
                    best_url = href

        if not best_url:
            return {}

        response = requests.get(best_url, timeout=10)
        response.raise_for_status()

        pdf_reader = PdfReader(BytesIO(response.content))
        layout_text = "".join(
            page.extract_text(extraction_mode="layout") for page in pdf_reader.pages
        )

        return self._parse_pdf_layout(layout_text, best_year)

    def _parse_pdf_layout(
        self, layout_text: str, year: int
    ) -> dict[str, dict[str, list[date]]]:
        planning: dict[str, dict[str, list[date]]] = {}
        lines = layout_text.split("\n")

        # Locate the column-header line to determine the horizontal split position.
        split_pos = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("DÉCHETS VERTS") and "ENCOMBRANTS" in line:
                # Subtract a small buffer so commune names starting just left of
                # the header are still captured in the right column.
                split_pos = line.index("ENCOMBRANTS") - 4
                break

        if split_pos is None:
            return planning

        self._parse_column_groups(
            [line[:split_pos] for line in lines], "Déchets verts", year, planning
        )
        self._parse_column_groups(
            [line[split_pos:] for line in lines], "Encombrants", year, planning
        )

        return planning

    @staticmethod
    def _find_commune_in_line(text: str) -> str | None:
        norm = _normalize_commune(text)
        for norm_commune, commune in COMMUNES_NORMALIZED.items():
            if norm_commune in norm:
                return commune
        return None

    def _parse_column_groups(
        self,
        lines: list[str],
        waste_type: str,
        year: int,
        planning: dict,
    ) -> None:
        current_communes: list[str] = []
        current_dates: list[date] = []

        def commit() -> None:
            if current_communes and current_dates:
                for commune in current_communes:
                    planning.setdefault(commune, {}).setdefault(waste_type, []).extend(
                        current_dates
                    )

        for line in lines:
            stripped = line.strip()
            if not stripped:
                commit()
                current_communes = []
                current_dates = []
                continue

            commune = self._find_commune_in_line(stripped)
            if commune and commune not in current_communes:
                current_communes.append(commune)

            current_dates.extend(self._extract_dates_from_line(stripped, year))

        commit()

    @staticmethod
    def _extract_dates_from_line(line: str, year: int) -> list[date]:
        dates = []
        for m in re.finditer(r"(\d{1,2})\s*([a-zàâäéèêëïîôùûüç]+)", line.lower()):
            mois_str = "".join(
                c
                for c in unicodedata.normalize("NFD", m.group(2))
                if unicodedata.category(c) != "Mn"
            )
            mois = MOIS_MAP.get(mois_str)
            if mois:
                try:
                    dates.append(date(year, mois, int(m.group(1))))
                except ValueError:
                    pass
        return dates
