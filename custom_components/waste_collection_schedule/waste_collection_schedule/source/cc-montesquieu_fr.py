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
    # Replace all hyphen/apostrophe variants (U+002D, U+0027, U+2018, U+2019) with a space
    s = re.sub("[-'‘’]", " ", s.upper())
    return re.sub(r"\s+", " ", s).strip()


# Mapping from normalised commune name → canonical commune name from COMMUNES list
COMMUNES_NORMALIZED = {_normalize_commune(c): c for c in COMMUNES}

EXTRA_INFO = [
    {
        "title": city,
        "default_params": {"commune": city},
    }
    for city in COMMUNES
]

TEST_CASES = {commune: {"commune": commune} for commune in COMMUNES}

ICON_MAP = {  # Optional: Dict of waste types and suitable mdi icons
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

BIN_TYPE_MAP = {"Bac d'ordures ménagères": "ordures", "Bac jaune": "recyclage"}

# ### Arguments affecting the configuration GUI ####

PARAM_DESCRIPTIONS = {
    "fr": {
        "commune": "Votre ville de la Communauté de Communes de Montesquieu : "
        + ", ".join(COMMUNES)
    },
    "en": {
        "commune": "Your city of Montesquieu's community: " + ", ".join(COMMUNES),
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "fr": {"commune": "Ville"},
    "en": {"commune": "City"},
    "de": {"commune": "Stadt"},
}
# ### End of arguments affecting the configuration GUI ####


class Source:
    def __init__(self, commune: str):
        self.commune = commune

        if self.commune not in COMMUNES:
            raise SourceArgumentNotFoundWithSuggestions(
                "Commune", self.commune, COMMUNES
            )

    def get_parsed_source(self) -> BeautifulSoup:
        s = requests.Session()
        response = s.get(DATA_URL)
        response.raise_for_status()

        return BeautifulSoup(response.text, "html.parser")

    def fetch(self) -> list[Collection]:
        parsed_source = self.get_parsed_source()
        global_planning = self.get_planning_table(parsed_source)
        city_planning = global_planning[self.commune]

        entries = []  # List that holds collection schedule

        for bin_type in city_planning.keys():
            french_day = city_planning[bin_type]

            collection_day = WEEKDAY_MAP[french_day.strip().lower()]

            for dt in rrule(
                freq=WEEKLY,
                dtstart=date.today(),
                count=20,
                byweekday=collection_day,
            ):
                entries.append(
                    Collection(
                        date=dt.date(),  # Collection date
                        t=bin_type,  # Collection type
                        icon=ICON_MAP.get(bin_type),  # Collection icon
                    )
                )

        global_planning2 = self.get_planning_table_dechets_verts_et_encombrants_pdf(
            parsed_source
        )

        if self.commune in global_planning2:
            city_planning2 = global_planning2[self.commune]
            for bin_type in city_planning2.keys():
                for dt2 in city_planning2[bin_type]:
                    entries.append(
                        Collection(
                            date=dt2,  # Collection date
                            t=bin_type,  # Collection type
                            icon=ICON_MAP.get(bin_type),  # Collection icon
                        )
                    )
        return entries

    def get_planning_table(
        self, parsed_source: BeautifulSoup
    ) -> dict[str, dict[str, str]]:
        tables = parsed_source.select("table")

        planning: dict[str, dict[str, str]] = {}
        for table in tables:
            if str(table).__contains__("ordures ménagères"):
                # thead = table.find('thead')
                table_heads = table.find("thead").find_all("th")
                table_body = table.find("tbody")
                # The source html is malformed. The first <TR> is absent. So we need to select the first 3 TD cells by hands until the source is fixed
                table_datas = table_body.find_all("td")
                ville = table_datas[0].text.strip()
                self.fill_planning(planning, ville, table_heads, table_datas)

                # table_rows = table_body.find_all('tr')
                for t in table_body.find_all("tr"):
                    td = t.select("td")
                    ville = td[0].text.strip()
                    self.fill_planning(planning, ville, table_heads, td)
        return planning

    def fill_planning(self, planning, ville, table_heads, table_datas):
        # HTML may use curly apostrophes; normalise to the canonical COMMUNES key
        canonical = COMMUNES_NORMALIZED.get(_normalize_commune(ville), ville)
        planning[canonical] = {
            table_heads[1].text: table_datas[1].text.strip(),
            table_heads[2].text: table_datas[2].text.strip(),
        }

    def get_planning_table_dechets_verts_et_encombrants_pdf(
        self, parsed_source: BeautifulSoup
    ) -> dict[str, dict[str, list[date]]]:
        """Extract déchets verts and encombrants planning from PDF files linked on the page."""
        # Find PDF links on the page; prefer the most recent year >= current year
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
        layout_text = ""
        for page in pdf_reader.pages:
            layout_text += page.extract_text(extraction_mode="layout")

        return self._parse_pdf_layout(layout_text, best_year)

    def _parse_pdf_layout(
        self, layout_text: str, year: int
    ) -> dict[str, dict[str, list[date]]]:
        """Parse the two-column layout PDF into a commune→waste_type→dates mapping.

        The PDF has a left column (Déchets verts) and a right column (Encombrants).
        Each column contains groups of communes that share collection dates.
        pypdf layout extraction preserves horizontal positions so we can split columns.
        """
        planning: dict[str, dict[str, list[date]]] = {}
        lines = layout_text.split("\n")

        # Locate the column-header line (e.g. "  DÉCHETS VERTS          ENCOMBRANTS")
        # to determine the horizontal split position between the two columns.
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

        left_lines = [line[:split_pos] for line in lines]
        right_lines = [line[split_pos:] for line in lines]

        self._parse_column_groups(left_lines, "Déchets verts", year, planning)
        self._parse_column_groups(right_lines, "Encombrants", year, planning)

        return planning

    def _find_commune_in_line(self, text: str) -> str | None:
        """Return the canonical commune name if any known commune appears in text."""
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
        """Parse one column of the layout text.

        Lines alternate between commune names and dates; blank lines separate
        groups of communes that share the same collection dates.
        All dates accumulated since the last blank are assigned to all communes
        accumulated since the last blank.
        """
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

        commit()  # handle the last group

    def _extract_dates_from_line(self, line: str, year: int) -> list[date]:
        """Extract dates from a text line in format like '1 janvier', '15 février', etc."""
        MOIS_PATTERN = {
            "janvier": "01",
            "fevrier": "02",
            "mars": "03",
            "avril": "04",
            "mai": "05",
            "juin": "06",
            "juillet": "07",
            "aout": "08",
            "septembre": "09",
            "octobre": "10",
            "novembre": "11",
            "decembre": "12",
        }

        dates = []
        for jour_match in re.finditer(
            r"(\d{1,2})\s*([a-zàâäéèêëïîôùûüç]+)", line.lower()
        ):
            jour_str = jour_match.group(1)
            # Normalise accented characters so keys match MOIS_PATTERN
            mois_str = (
                jour_match.group(2)
                .replace("é", "e")
                .replace("è", "e")
                .replace("ê", "e")
                .replace("ë", "e")
                .replace("à", "a")
                .replace("â", "a")
                .replace("ä", "a")
                .replace("ï", "i")
                .replace("î", "i")
                .replace("ô", "o")
                .replace("ù", "u")
                .replace("û", "u")
                .replace("ü", "u")
                .replace("ç", "c")
            )
            if mois_str in MOIS_PATTERN:
                try:
                    jour = int(jour_str)
                    mois = MOIS_PATTERN[mois_str]
                    dates.append(date.fromisoformat(f"{year}-{mois:0>2}-{jour:0>2}"))
                except (ValueError, KeyError):
                    pass

        return dates

