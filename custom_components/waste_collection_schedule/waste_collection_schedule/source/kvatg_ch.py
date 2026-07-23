import io
import logging
import re
from datetime import date, timedelta
from itertools import pairwise
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextContainer, LTTextLine
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "KVA Thurgau"
DESCRIPTION = (
    "Source for KVA Thurgau (Kehrichtverwertungsanlage Thurgau) waste collection, "
    "covering the municipalities of the canton of Thurgau and neighbouring "
    "communities, Switzerland."
)
URL = "https://www.kvatg.ch"
COUNTRY = "ch"

SOURCE_CODEOWNERS = ["@Smn-hns"]

_OVERVIEW_URL = "https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/"

# The KVA plan for Kreuzlingen contains no Kehricht dates — the city publishes
# its own zone plan (a map PDF with a parseable zone/weekday legend) here:
_KREUZLINGEN_ENTSORGUNG_URL = "https://www.kreuzlingen.ch/wir-fuer-sie/entsorgung"

COMMUNITIES = [
    "Affeltrangen",
    "Altnau",
    "Amlikon-Bissegg",
    "Amriswil",
    "Arbon",
    "Basadingen-Schlattingen",
    "Berg",
    "Berlingen",
    "Birwinken",
    "Bischofszell",
    "Bottighofen",
    "Buch",
    "Bürglen",
    "Bussnang",
    "Diessenhofen",
    "Dozwil",
    "Egnach",
    "Erlen",
    "Ermatingen",
    "Eschenz",
    "Felben-Wellhausen",
    "Frauenfeld",
    "Gachnang",
    "Gottlieben",
    "Güttingen",
    "Hauptwil-Gottshaus",
    "Hefenhofen",
    "Hemishofen",
    "Herdern",
    "Hohentannen",
    "Homburg",
    "Hüttlingen",
    "Hüttwilen",
    "Kemmental",
    "Kesswil",
    "Kradolf-Schönenberg",
    "Kreuzlingen",
    "Langrickenbach",
    "Lengwil",
    "Lommis",
    "Märstetten",
    "Mammern",
    "Matzingen",
    "Müllheim",
    "Münsterlingen",
    "Neunforn",
    "Pfyn-Dettighofen",
    "Ramsen",
    "Raperswilen",
    "Roggwil",
    "Romanshorn",
    "Salenstein",
    "Salmsach",
    "Schlatt",
    "Schönholzerswilen",
    "Sommeri",
    "Steckborn",
    "Stein am Rhein",
    "Stettfurt",
    "Sulgen",
    "Tägerwilen",
    "Thundorf",
    "Uesslingen-Buch",
    "Uttwil",
    "Wäldi",
    "Wagenhausen",
    "Warth-Weiningen",
    "Weinfelden",
    "Wigoltingen",
    "Zihlschlacht-Sitterdorf",
]


def EXTRA_INFO():
    return [
        {"title": m, "default_params": {"community": m}, "country": "ch"}
        for m in COMMUNITIES
    ]


CONFIG_FLOW_TYPES = {
    "community": {
        "type": "SELECT",
        "values": COMMUNITIES,
        "multiple": False,
    }
}

TEST_CASES = {
    "Kreuzlingen": {"community": "Kreuzlingen"},
    "Kreuzlingen Zone Ost": {"community": "Kreuzlingen", "zone": "Ost"},
    "Kreuzlingen Kehricht Zentrum": {
        "community": "Kreuzlingen",
        "zone": "Ost",
        "kehricht_zone": "Zentrum",
    },
    "Sulgen": {"community": "Sulgen"},
    "Frauenfeld": {"community": "Frauenfeld"},
    "Bischofszell": {"community": "Bischofszell", "zone": "Bischofszell"},
    "Affeltrangen": {"community": "Affeltrangen"},
    "Arbon Zone 1": {"community": "Arbon", "zone": "Zone 1"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "community": "Community",
        "zone": "Zone / district (optional)",
        "kehricht_zone": "Kehricht zone (Kreuzlingen only, optional)",
    },
    "de": {
        "community": "Gemeinde",
        "zone": "Zone / Abfuhrgebiet (optional)",
        "kehricht_zone": "Kehricht-Zone (nur Kreuzlingen, optional)",
    },
    "it": {
        "community": "Comune",
        "zone": "Zona / area di raccolta (facoltativo)",
        "kehricht_zone": "Zona Kehricht (solo Kreuzlingen, facoltativo)",
    },
    "fr": {
        "community": "Commune",
        "zone": "Zone / secteur de collecte (facultatif)",
        "kehricht_zone": "Zone Kehricht (Kreuzlingen uniquement, facultatif)",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "community": "Community name exactly as listed on the KVA Thurgau "
        "disposal plan page (e.g. 'Kreuzlingen').",
        "zone": "Collection zone or district within the community, if the "
        "disposal plan splits collections by area (e.g. 'Ost' for the "
        "Kreuzlingen green waste district). Leave empty to get all zones; "
        "zoned collections are then suffixed with their zone name. The zone "
        "names are printed left of the date grid in your community's plan on "
        "[kvatg.ch](https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/) — an invalid "
        "value shows a list of the valid names.",
        "kehricht_zone": "Only for Kreuzlingen: household-waste (Kehricht) "
        "zone from the city's own zone plan — 'Süd & Tägerwilen', "
        "'Nord und Ost' or 'Zentrum'. Leave empty to get all three zones. "
        "Which streets belong to which zone is shown on the map [Kehricht, "
        "Abfuhrplan Kreuzlingen](https://www.kreuzlingen.ch/wir-fuer-sie/entsorgung).",
    },
    "de": {
        "community": "Gemeindename genau wie auf der Entsorgungsplan-Seite "
        "der KVA Thurgau aufgeführt (z. B. 'Kreuzlingen').",
        "zone": "Zone bzw. Abfuhrgebiet innerhalb der Gemeinde, falls der "
        "Entsorgungsplan Sammlungen nach Gebiet unterteilt (z. B. 'Ost' für "
        "das Grüngut-Gebiet in Kreuzlingen). Leer lassen für alle Zonen; "
        "zonierte Sammlungen erhalten dann den Zonennamen als Zusatz. Die "
        "Zonennamen stehen links neben dem Datumsraster im Entsorgungsplan "
        "Ihrer Gemeinde auf [kvatg.ch](https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/) "
        "— bei einem ungültigen Wert wird eine Liste der gültigen Namen "
        "angezeigt.",
        "kehricht_zone": "Nur für Kreuzlingen: Kehricht-Abfuhrzone gemäss "
        "dem städtischen Zonenplan — 'Süd & Tägerwilen', 'Nord und Ost' "
        "oder 'Zentrum'. Leer lassen für alle drei Zonen. Welche Strassen "
        "zu welcher Zone gehören, zeigt die Karte [Kehricht, Abfuhrplan "
        "Kreuzlingen](https://www.kreuzlingen.ch/wir-fuer-sie/entsorgung).",
    },
    "it": {
        "community": "Nome del comune esattamente come indicato sulla pagina "
        "dei piani di smaltimento della KVA Thurgau (ad es. 'Kreuzlingen').",
        "zone": "Zona o area di raccolta all'interno del comune, se il piano "
        "di smaltimento suddivide le raccolte per area (ad es. 'Ost' per "
        "l'area del verde di Kreuzlingen). Lasciare vuoto per tutte le zone; "
        "le raccolte zonali riportano poi il nome della zona. I nomi delle "
        "zone si trovano a sinistra della griglia delle date nel piano del "
        "comune su [kvatg.ch](https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/) — "
        "un valore non valido mostra l'elenco dei nomi validi.",
        "kehricht_zone": "Solo per Kreuzlingen: zona di raccolta dei rifiuti "
        "domestici (Kehricht) secondo il piano zonale comunale — "
        "'Süd & Tägerwilen', 'Nord und Ost' o 'Zentrum'. Lasciare vuoto per "
        "tutte e tre le zone. La mappa [Kehricht, Abfuhrplan Kreuzlingen]"
        "(https://www.kreuzlingen.ch/wir-fuer-sie/entsorgung) mostra quali "
        "strade appartengono a quale zona.",
    },
    "fr": {
        "community": "Nom de la commune exactement comme indiqué sur la page "
        "des plans d'élimination de la KVA Thurgau (p. ex. 'Kreuzlingen').",
        "zone": "Zone ou secteur de collecte au sein de la commune, si le "
        "plan d'élimination répartit les collectes par secteur (p. ex. 'Ost' "
        "pour le secteur des déchets verts de Kreuzlingen). Laisser vide pour "
        "toutes les zones ; les collectes zonées portent alors le nom de la "
        "zone. Les noms de zones figurent à gauche de la grille des dates "
        "dans le plan de votre commune sur "
        "[kvatg.ch](https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/) — une valeur "
        "invalide affiche la liste des noms valides.",
        "kehricht_zone": "Uniquement pour Kreuzlingen : zone de collecte des "
        "ordures ménagères (Kehricht) selon le plan de zones de la ville — "
        "'Süd & Tägerwilen', 'Nord und Ost' ou 'Zentrum'. Laisser vide pour "
        "les trois zones. La carte [Kehricht, Abfuhrplan Kreuzlingen]"
        "(https://www.kreuzlingen.ch/wir-fuer-sie/entsorgung) montre quelles "
        "rues appartiennent à quelle zone.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your community on https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/ "
    "and enter its name. If your community's disposal plan splits a collection "
    "by zone (e.g. the green waste districts in Kreuzlingen or the collection "
    "areas in Frauenfeld), you can optionally enter the zone name as printed "
    "in the plan.",
    "de": "Suchen Sie Ihre Gemeinde auf https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/ "
    "und geben Sie deren Namen ein. Falls der Entsorgungsplan Ihrer Gemeinde "
    "eine Sammlung nach Zonen unterteilt (z. B. die Grüngut-Gebiete in "
    "Kreuzlingen oder die Abfuhrgebiete in Frauenfeld), können Sie optional "
    "den Zonennamen wie im Plan gedruckt angeben.",
    "it": "Cerca il tuo comune su https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/ "
    "e inserisci il suo nome. Se il piano di smaltimento del tuo comune "
    "suddivide una raccolta per zone (ad es. le aree del verde a Kreuzlingen "
    "o le zone di raccolta a Frauenfeld), puoi facoltativamente indicare il "
    "nome della zona come stampato nel piano.",
    "fr": "Recherchez votre commune sur https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/ "
    "et saisissez son nom. Si le plan d'élimination de votre commune répartit "
    "une collecte par zones (p. ex. les secteurs de déchets verts à "
    "Kreuzlingen ou les zones de collecte à Frauenfeld), vous pouvez "
    "éventuellement indiquer le nom de la zone tel qu'imprimé dans le plan.",
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Kehricht": Icons.GENERAL_WASTE,
    "Papier/Karton": Icons.PAPER,
    "Papier": Icons.PAPER,
    "Karton": Icons.PAPER,
    "Kleinsperrgut": Icons.BULKY,
    "Grüngut": Icons.ORGANIC,
    "Kunststoff": Icons.PLASTIC_PACKAGING,
    "Häckseldienst": Icons.GARDEN,
    "Metalle": Icons.METAL,
    "Christbaum": Icons.CHRISTMAS_TREE,
}

_MONTH_ABBR = {
    "JAN": 1,
    "FEB": 2,
    "MÄR": 3,
    "APR": 4,
    "MAI": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OKT": 10,
    "NOV": 11,
    "DEZ": 12,
}
_MONTH_FULL = {
    "Januar": 1,
    "Februar": 2,
    "März": 3,
    "April": 4,
    "Mai": 5,
    "Juni": 6,
    "Juli": 7,
    "August": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "Dezember": 12,
}
_WEEKDAYS = {
    "Montag": 0,
    "Dienstag": 1,
    "Mittwoch": 2,
    "Donnerstag": 3,
    "Freitag": 4,
    "Samstag": 5,
    "Sonntag": 6,
}
_WD_RE = "|".join(_WEEKDAYS)

# Holiday-shift lines ("Auffahrt: Freitag, 15.5.2026") must not be mistaken
# for per-zone weekday rules.
_HOLIDAY_WORDS = (
    "Neujahr",
    "Berchtoldstag",
    "Karfreitag",
    "Ostermontag",
    "Auffahrt",
    "Pfingstmontag",
    "Tag der Arbeit",
    "Weihnachten",
    "Stephanstag",
    "Bundesfeier",
    "Verschiebe",
)

# Big left-margin section labels (font size >= 16) own the full-width grids.
_MAJOR_SECTIONS = {
    "KEHRICHT": "Kehricht",
    "PAPIER": "Papier/Karton",
    "KARTON": "Papier/Karton",
    "KLEINSPERRGUT": "Kleinsperrgut",
    "GRÜNGUTABFUHR": "Grüngut",
    "GRÜNABFUHR": "Grüngut",
    "GRÜNGUTSAMMLUNG": "Grüngut",
    "GRÜNGUT": "Grüngut",
    "GRÜNSAMMELTOUR": "Grüngut",
    "KUNSTSTOFFSAMMLUNG": "Kunststoff",
    "KUNSTSTOFF": "Kunststoff",
    "PLASTIKSAMMELTOUR": "Kunststoff",
}
# Smaller sub-block headings; these own the indented mini-grids and the
# inline date notes.
_MINOR_SECTIONS = {
    "HÄCKSELDIENST": "Häckseldienst",
    "METALLE": "Metalle",
    "ALTEISEN": "Metalle",
    "CHRISTBAUM": "Christbaum",
    "KUNSTSTOFFSAMMLUNG": "Kunststoff",
    "KUNSTSTOFF": "Kunststoff",
    "PLASTIKSAMMELTOUR": "Kunststoff",
}

# "22." plain, "8./12.*" compound cell, "9.¹" superscript zone marker,
# "14.5" day with a glued single-digit footnote (Verein reference)
_TOKEN_RE = re.compile(r"(\d{1,2})\.(?:/(\d{1,2})\.)?(\*{1,2}|[¹²³⁴]|\d)?")


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


# ---------------------------------------------------------------------------
# PDF word extraction
# ---------------------------------------------------------------------------


def _extract_words(pdf_stream: io.BytesIO) -> list[dict]:
    """Extract words with coordinates from the (single) plan page."""
    words: list[dict] = []
    for page in extract_pages(pdf_stream):
        for element in page:
            if not isinstance(element, LTTextContainer):
                continue
            for line in element:
                if not isinstance(line, LTTextLine):
                    continue
                chars = [c for c in line if isinstance(c, LTChar)]
                current: list[LTChar] = []
                for c in chars:
                    if current and (
                        c.x0 - current[-1].x1 > max(1.2, 0.35 * c.size)
                        or not c.get_text().strip()
                    ):
                        _flush_word(words, current)
                        current = []
                    if c.get_text().strip():
                        current.append(c)
                _flush_word(words, current)
        break  # all KVA Thurgau plans are single-page
    return words


def _flush_word(words: list[dict], chars: list[LTChar]) -> None:
    if not chars:
        return
    text = "".join(c.get_text() for c in chars).strip()
    if not text:
        return
    words.append(
        {
            "text": text,
            "x0": min(c.x0 for c in chars),
            "x1": max(c.x1 for c in chars),
            "y0": min(c.y0 for c in chars),
            "y": (min(c.y0 for c in chars) + max(c.y1 for c in chars)) / 2,
            "size": max(c.size for c in chars),
        }
    )


def _rows_from_words(words: list[dict]) -> list[dict]:
    """Group words into text rows by baseline, top-to-bottom."""
    rows: dict[float, list[dict]] = {}
    for w in sorted(words, key=lambda w: (round(w["y0"]), w["x0"])):
        key = next((k for k in rows if abs(k - w["y0"]) < 2.5), None)
        if key is None:
            key = w["y0"]
            rows[key] = []
        rows[key].append(w)
    out: list[dict] = []
    for y, ws in rows.items():
        ws.sort(key=lambda w: w["x0"])
        out.append({"y": y, "words": ws, "text": " ".join(w["text"] for w in ws)})
    out.sort(key=lambda r: -r["y"])
    return out


# ---------------------------------------------------------------------------
# Layout analysis
# ---------------------------------------------------------------------------


def _find_year(words: list[dict]) -> int | None:
    text = " ".join(w["text"] for w in sorted(words, key=lambda w: (-w["y0"], w["x0"])))
    m = re.search(r"GÜLTIG AB.{0,25}?(20\d{2})", text)
    return int(m.group(1)) if m else None


def _find_anchors(words: list[dict]) -> list[dict]:
    anchors = []
    for w in words:
        token = w["text"].upper().strip(" /-–")
        major = next(
            (
                s
                for kw, s in _MAJOR_SECTIONS.items()
                if token.startswith(kw) and w["size"] >= 16 and w["x0"] < 150
            ),
            None,
        )
        if major:
            anchors.append({"section": major, "y": w["y"], "x": w["x0"], "major": True})
            continue
        minor = next(
            (
                s
                for kw, s in _MINOR_SECTIONS.items()
                if token.startswith(kw) and w["size"] >= 7
            ),
            None,
        )
        if minor:
            anchors.append(
                {"section": minor, "y": w["y"], "x": w["x0"], "major": False}
            )
    # merge duplicates (the two-line "PAPIER / KARTON" label, repeated headings)
    merged: list[dict] = []
    for a in sorted(anchors, key=lambda a: -a["y"]):
        dup = next(
            (
                m
                for m in merged
                if m["section"] == a["section"]
                and abs(m["y"] - a["y"]) < 40
                and abs(m["x"] - a["x"]) < 60
            ),
            None,
        )
        if dup:
            dup["y"] = (dup["y"] + a["y"]) / 2
        else:
            merged.append(a)
    return merged


def _find_header_rows(words: list[dict]) -> list[dict]:
    """Month-abbreviation rows (JAN..DEZ); at least 2 months on one baseline."""
    month_words = [
        w for w in words if w["text"].rstrip(".*") in _MONTH_ABBR and w["size"] >= 5
    ]
    rows: list[dict] = []
    for w in sorted(month_words, key=lambda w: -w["y0"]):
        row = next((r for r in rows if abs(r["y"] - w["y0"]) < 3), None)
        if row is None:
            rows.append({"y": w["y0"], "months": [w]})
        else:
            row["months"].append(w)
    headers = []
    for row in rows:
        if len(row["months"]) < 2:
            continue
        row["months"].sort(key=lambda w: w["x0"])
        cols = []
        prev_num, offset = 0, 0
        for w in row["months"]:
            num = _MONTH_ABBR[w["text"].rstrip(".*")]
            if num < prev_num:  # "DEZ JAN" wrap -> next year's January column
                offset += 1
            prev_num = num
            cols.append({"x": w["x0"], "month": num, "year_offset": offset})
        gaps = [b["x"] - a["x"] for a, b in pairwise(cols)]
        tol = max(12.0, min(gaps) / 2) if gaps else 18.0
        headers.append({"y": row["y"], "cols": cols, "tol": tol})
    return headers


def _attach_headers(
    headers: list[dict], anchors: list[dict], words: list[dict]
) -> list[dict]:
    """Assign each month-header row to its section label."""

    def score(a: dict, h: dict) -> float:
        dy = abs(a["y"] - h["y"])
        dx = max(0.0, h["cols"][0]["x"] - (a["x"] + 60))
        return dy + 0.15 * dx

    for h in headers:
        cands = [a for a in anchors if abs(a["y"] - h["y"]) < 150]
        # full-width 12-month grids never belong to the right-hand info blocks
        # (Häckseldienst, Metalle, Christbaum) — those only own indented
        # mini-grids
        if len(h["cols"]) >= 12 and h["cols"][0]["x"] < 330:
            grid_owners = [
                a
                for a in cands
                if a["major"]
                or a["section"] not in ("Häckseldienst", "Metalle", "Christbaum")
            ]
            cands = grid_owners or cands
        h["section"] = (
            min(cands, key=lambda a: score(a, h))["section"] if cands else None
        )
        # "Papiersammlung" / "Kartonsammlung" sub-grid labels sit in the
        # zone-label column directly above their month header and override
        # the anchor attachment (e.g. separate paper and cardboard grids).
        sub = " ".join(
            w["text"].lower()
            for w in words
            if 250 < w["x0"] < 360 and 3 < w["y0"] - h["y"] < 45 and w["size"] < 16
        )
        has_papier = bool(re.search(r"\bpapier(sammlung|-)?\b", sub))
        has_karton = bool(re.search(r"\bkarton(sammlung)?\b", sub))
        if has_papier and has_karton:
            h["section"] = "Papier/Karton"
        elif has_papier:
            h["section"] = "Papier"
        elif has_karton:
            h["section"] = "Karton"
    return headers


def _clean_zone_label(label: str) -> str:
    label = re.sub(r"-\s+(?=[a-zäöü])", "", label)  # re-join hyphenated wraps
    label = re.sub(r"\s*,\s*", ", ", label)
    label = re.sub(r"^Sammlung\s+", "", label)
    label = re.sub(rf"\s*:\s*({_WD_RE})\b.*$", "", label)
    # cut glued footnote legends ("... Thurfeld 1 2 TV Bischofszell ...")
    label = re.sub(r"\s\d{1,2}(\s.*)?$", "", label)
    return label.strip(" ,:")


def _find_zone_clusters(
    header: dict, words: list[dict], date_rows_ys: list[float]
) -> list[dict]:
    """Cluster the small labels just left of an indented grid into zones."""
    x_left = header["cols"][0]["x"]
    cand = [
        w
        for w in words
        if x_left - 115 < w["x0"] < x_left - 4
        and header["y"] - 235 < w["y0"] < header["y"] - 2
        and w["text"] not in ("Gebiet", "•")
        and not w["text"].startswith("•")
    ]
    cand.sort(key=lambda w: -w["y0"])
    clusters: list[dict] = []
    for w in cand:
        if clusters and clusters[-1]["ys"][-1] - w["y0"] < 14.5:
            clusters[-1]["words"].append(w)
            clusters[-1]["ys"].append(w["y0"])
        elif re.match(r"[A-ZÄÖÜ]", w["text"]):
            # a new zone label must start with an uppercase word
            clusters.append({"words": [w], "ys": [w["y0"]]})
    zones = []
    for c in clusters:
        yc = sum(c["ys"]) / len(c["ys"])
        # a real zone label must align with at least one date row
        if not any(abs(yc - dy) < 12 for dy in date_rows_ys):
            continue
        label = _clean_zone_label(
            " ".join(
                w["text"] for w in sorted(c["words"], key=lambda w: (-w["y0"], w["x0"]))
            )
        )
        if label:
            zones.append({"label": label, "y": yc})
    return zones


# ---------------------------------------------------------------------------
# Schedule parsing
# ---------------------------------------------------------------------------


def _parse_grids(
    words: list[dict], headers: list[dict], year: int
) -> tuple[list[tuple], list[dict]]:
    """Assign day tokens to (section, zone, date) via the month columns."""
    tokens = [w for w in words if _TOKEN_RE.fullmatch(w["text"]) and w["size"] >= 5]
    # superscript zone legend, e.g. "¹ Nördliche Rebenstrasse / Altstadt"
    legend: dict[str, str] = {}
    for w in words:
        if w["text"][:1] in "¹²³⁴":
            marker = w["text"][0]
            rest = w["text"][1:].strip()
            if not rest:
                same_row = [
                    w2
                    for w2 in words
                    if abs(w2["y0"] - w["y0"]) < 3 and 0 < w2["x0"] - w["x0"] < 250
                ]
                rest = " ".join(
                    x["text"] for x in sorted(same_row, key=lambda x: x["x0"])[:6]
                )
            if rest and marker not in legend and re.match(r"[A-ZÄÖÜ]", rest):
                legend[marker] = rest.strip(" :,")

    results: list[tuple] = []
    gruengut_zones: list[dict] = []
    for h in headers:
        if h["section"] is None:
            continue
        mine = []
        for t in tokens:
            dy = h["y"] - t["y0"]
            if not (3 < dy < 230):
                continue
            if any(
                h2 is not h and 3 < h2["y"] - t["y0"] < dy for h2 in headers
            ):  # a closer header above owns this token
                continue
            col = min(h["cols"], key=lambda c: abs(c["x"] - t["x0"]))
            if abs(col["x"] - t["x0"]) > h["tol"]:
                continue
            mine.append((t, col))
        if mine:
            sizes = sorted(t["size"] for t, _ in mine)
            median = sizes[len(sizes) // 2]
            mine = [(t, c) for t, c in mine if t["size"] >= median - 1.5]
        date_rows = sorted({round(t["y0"]) for t, _ in mine}, reverse=True)
        zones: list[dict] = []
        if h["cols"][0]["x"] > 330:  # indented grids leave room for zone labels
            zones = _find_zone_clusters(h, words, [float(y) for y in date_rows])
            if len(zones) < 2:
                zones = []
        if zones and h["section"] == "Grüngut":
            gruengut_zones.extend(zones)
        zone_tol = 16.0
        if zones:
            ys = sorted(z["y"] for z in zones)
            pitch = min((b - a for a, b in pairwise(ys)), default=28.0)
            zone_tol = max(8.0, min(16.0, pitch / 2))
        for t, col in mine:
            m = _TOKEN_RE.fullmatch(t["text"])
            if m is None:
                continue
            days = [int(m.group(1))] + ([int(m.group(2))] if m.group(2) else [])
            marker = m.group(3) or ""
            zone = None
            if marker in "¹²³⁴" and marker:
                zone = legend.get(marker, f"Zone {'¹²³⁴'.index(marker) + 1}")
            elif zones:
                near = min(zones, key=lambda z: abs(z["y"] - t["y0"]))
                if abs(near["y"] - t["y0"]) < zone_tol:
                    zone = near["label"]
            for day in days:
                try:
                    d = date(year + col["year_offset"], col["month"], day)
                except ValueError:
                    continue
                results.append((h["section"], zone, d))
    return results, gruengut_zones


def _section_band_rows(
    rows: list[dict], anchor: dict, y_above: float, y_below: float
) -> list[dict]:
    return [r for r in rows if anchor["y"] - y_above < r["y"] < anchor["y"] + y_below]


def _parse_kehricht(rows: list[dict], anchors: list[dict]) -> list[tuple[str, str]]:
    """Weekday rules from the Kehricht block; returns [(zone_label, weekday)]."""
    anchor = next((a for a in anchors if a["section"] == "Kehricht"), None)
    if anchor is None:
        return []
    band = _section_band_rows(rows, anchor, y_above=200, y_below=120)
    # re-join wrapped rules ("Abfuhrtag Bischofszell, Halden" /
    # "und Schweizersholz: Dienstag") before matching
    texts: list[str] = []
    for r in band:
        if texts and re.match(r"\s*(?:und\b|[a-zäöü])", r["text"]):
            texts[-1] = texts[-1] + " " + r["text"]
        else:
            texts.append(r["text"])
    pairs = []
    for text in texts:
        for m in re.finditer(
            rf"(?:^|[•●]\s*)?([A-ZÄÖÜ][\w\säöüéè/,()\-]{{0,60}}?):\s*\(?({_WD_RE})\)?",
            text,
        ):
            label, wd = m.group(1).strip(), m.group(2)
            tail = text[m.end() : m.end() + 12]
            if re.match(r"\s*,?\s*\d{1,2}\.", tail):  # holiday shift with a date
                continue
            if any(h.lower() in label.lower() for h in _HOLIDAY_WORDS):
                continue
            label = re.sub(
                r"^(Abfuhrtage?|Abfuhrgebiet|Abfuhrtag|Sammlung)\s*", "", label
            ).strip(" :")
            pairs.append((label, wd))
    seen, out = set(), []
    for label, wd in pairs:
        key = (label.casefold(), wd)
        if key not in seen:
            seen.add(key)
            out.append((label, wd))
    return out


def _parse_kehricht_shifts(rows: list[dict], anchors: list[dict]) -> list[date]:
    """Explicitly listed holiday replacement dates for the Kehricht tour.

    Lines like '• Berchtoldstag: Samstag, 3.1.2026' name the substitute
    collection date for the week of the holiday.
    """
    anchor = next((a for a in anchors if a["section"] == "Kehricht"), None)
    if anchor is None:
        return []
    shifts = []
    for r in _section_band_rows(rows, anchor, y_above=200, y_below=120):
        if not any(h.lower() in r["text"].lower() for h in _HOLIDAY_WORDS):
            continue
        for m in re.finditer(
            rf"(?:{_WD_RE})\s*,?\s*(\d{{1,2}})\.\s*(\d{{1,2}})\.\s*(20\d{{2}})",
            r["text"],
        ):
            try:
                shifts.append(date(int(m.group(3)), int(m.group(2)), int(m.group(1))))
            except ValueError:
                pass
    return shifts


def _parse_weekly_spans(rows: list[dict]) -> list[dict]:
    """Weekly-collection text rules in two flavours.

    'Von Anfang März bis Ende November wöchentliche Sammlung jeden <WD>'
    (Kreuzlingen) and 'Vom 6. März bis 27. November 2026 wöchentlich'
    (Gachnang), optionally followed by cancellations like
    'Die Sammlung vom 3. April (Karfreitag) fällt aus.'
    """
    out = []
    for r in rows:
        m = re.search(r"Von Anfang (\w+) bis Ende (\w+)\s+wöchentliche", r["text"])
        if m and m.group(1) in _MONTH_FULL and m.group(2) in _MONTH_FULL:
            wd = None
            m2 = re.search(rf"jeden\s+({_WD_RE})", r["text"])
            if m2:
                wd = m2.group(1)
            else:  # the weekday usually sits on the following line
                for r2 in rows:
                    if 4 < r["y"] - r2["y"] < 18:
                        m2 = re.search(rf"jeden\s+({_WD_RE})", r2["text"])
                        if m2:
                            wd = m2.group(1)
                            break
            if wd:
                out.append(
                    {
                        "y": r["y"],
                        "start": _MONTH_FULL[m.group(1)],
                        "start_day": None,
                        "end": _MONTH_FULL[m.group(2)],
                        "end_day": None,
                        "weekday": wd,
                        "cancels": [],
                    }
                )
            continue
        m = re.search(
            r"Vom (\d{1,2})\.\s*(\w+) bis (\d{1,2})\.\s*(\w+)(?:\s*20\d{2})?"
            r"\s*wöchentlich",
            r["text"],
        )
        if m and m.group(2) in _MONTH_FULL and m.group(4) in _MONTH_FULL:
            cancels = []
            for r2 in rows:
                if -5 < r["y"] - r2["y"] < 25:
                    for mc in re.finditer(
                        r"vom (\d{1,2})\.\s*(\w+)[^.]*fällt aus",
                        r2["text"],
                        re.IGNORECASE,
                    ):
                        if mc.group(2) in _MONTH_FULL:
                            cancels.append((_MONTH_FULL[mc.group(2)], int(mc.group(1))))
            out.append(
                {
                    "y": r["y"],
                    "start": _MONTH_FULL[m.group(2)],
                    "start_day": int(m.group(1)),
                    "end": _MONTH_FULL[m.group(4)],
                    "end_day": int(m.group(3)),
                    "weekday": None,  # derived from the start date
                    "cancels": cancels,
                }
            )
    return out


def _parse_kw_rule(rows: list[dict], anchors: list[dict], year: int) -> dict | None:
    """Frauenfeld-style 'YYYY: KW 2 / 4 ... / KW 11 – 52' in the Grüngut block."""
    anchor = next((a for a in anchors if a["section"] == "Grüngut"), None)
    if anchor is None:
        return None
    band = _section_band_rows(rows, anchor, y_above=200, y_below=120)
    weeks: list[int] = []
    found = False
    for r in band:
        m = re.search(rf"{year}\s*:\s*(KW[\d\s/–\-KW]*)", r["text"])
        if not m:
            continue
        found = True
        blob = m.group(1)
        # continuation rows just below ("KW 11 – 52" wrapped to its own line)
        for r2 in band:
            if (
                2 < r["y"] - r2["y"] < 25
                and re.match(r"\s*KW[\d\s/–\-]+$", r2["text"])
                and not re.search(r"20\d{2}", r2["text"])
            ):
                blob += " " + r2["text"]
        for rng in re.finditer(r"(\d{1,2})\s*[–\-]\s*(\d{1,2})", blob):
            weeks.extend(range(int(rng.group(1)), int(rng.group(2)) + 1))
        blob_no_rng = re.sub(r"\d{1,2}\s*[–\-]\s*\d{1,2}", "", blob)
        weeks.extend(int(n) for n in re.findall(r"\d{1,2}", blob_no_rng))
        break
    if not found:
        return None
    # zone weekdays: standalone weekday words in the block are the zone-map
    # labels ("Montag-Zone" etc.)
    zone_weekdays = []
    for r in band:
        for w in r["words"]:
            if w["text"] in _WEEKDAYS and w["text"] not in zone_weekdays:
                zone_weekdays.append(w["text"])
    return {"weeks": sorted(set(weeks)), "zone_weekdays": zone_weekdays}


def _parse_inline_dates(
    rows: list[dict], anchors: list[dict], sections_with_grids: set[str], year: int
) -> list[tuple[str, date]]:
    """Concrete dates in the info blocks (Metalle, Häckseldienst, Christbaum)."""
    out = []
    for a in anchors:
        if a["major"] or a["section"] not in ("Metalle", "Häckseldienst", "Christbaum"):
            continue
        if a["section"] in sections_with_grids:
            continue
        for r in _section_band_rows(rows, a, y_above=100, y_below=30):
            if re.search(r"Ausfall|entfällt|[Kk]eine? |verschoben", r["text"]):
                continue
            near = " ".join(
                w["text"] for w in r["words"] if a["x"] - 15 < w["x0"] < a["x"] + 340
            )
            # "22./ 23. 4. 2026" with year, "25. 4. und 24.10." without
            for m in re.finditer(
                r"(\d{1,2})\.\s*(?:/\s*(\d{1,2})\.\s*)?(\d{1,2})\.(?:\s*(20\d{2}))?",
                near,
            ):
                d1, d2, mon, yr = m.groups()
                if not 1 <= int(mon) <= 12:
                    continue
                for dd in (d1, d2):
                    if dd is None:
                        continue
                    try:
                        out.append(
                            (
                                a["section"],
                                date(int(yr) if yr else year, int(mon), int(dd)),
                            )
                        )
                    except ValueError:
                        pass
    return out


# ---------------------------------------------------------------------------
# Date expansion helpers
# ---------------------------------------------------------------------------


def _expand_weekday(year: int, weekday_idx: int) -> list[date]:
    d = date(year, 1, 1)
    d += timedelta(days=(weekday_idx - d.weekday()) % 7)
    out = []
    while d.year == year:
        out.append(d)
        d += timedelta(days=7)
    return out


def _expand_span(year: int, span: dict) -> list[date]:
    start = date(year, span["start"], span["start_day"] or 1)
    if span["end_day"]:
        end = date(year, span["end"], span["end_day"])
    elif span["end"] == 12:
        end = date(year, 12, 31)
    else:
        end = date(year, span["end"] + 1, 1) - timedelta(days=1)
    wd = _WEEKDAYS[span["weekday"]] if span["weekday"] else start.weekday()
    cancelled = {date(year, m, d) for m, d in span["cancels"]}
    d = start + timedelta(days=(wd - start.weekday()) % 7)
    out = []
    while d <= end:
        if d not in cancelled:
            out.append(d)
        d += timedelta(days=7)
    return out


# ---------------------------------------------------------------------------
# Kreuzlingen city Kehricht plan
# ---------------------------------------------------------------------------


def _fetch_kreuzlingen_city_kehricht(year: int) -> set[tuple[str, str | None, date]]:
    """Weekly Kehricht events from the city of Kreuzlingen's own zone plan.

    The plan is a map PDF, but its legend is machine-readable: each zone
    title ("Kreuzlingen Süd & Tägerwilen") sits directly above its weekday
    ("Montag") at the same x position.
    """
    r = requests.get(_KREUZLINGEN_ENTSORGUNG_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    pdf_link = None
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        href = str(a["href"])
        if "kehricht" in text and "abfuhrplan" in text and ".pdf" in href.lower():
            pdf_link = urljoin(_KREUZLINGEN_ENTSORGUNG_URL, href)
            break
    if pdf_link is None:
        raise ValueError("no Kehricht Abfuhrplan link found on kreuzlingen.ch")

    r_pdf = requests.get(pdf_link, timeout=30)
    r_pdf.raise_for_status()
    words = _extract_words(io.BytesIO(r_pdf.content))

    wd_words = sorted(
        (w for w in words if w["text"] in _WEEKDAYS and w["size"] >= 8),
        key=lambda w: w["x0"],
    )
    events: set[tuple[str, str | None, date]] = set()
    for i, wd_w in enumerate(wd_words):
        x_lo = wd_w["x0"] - 5
        x_hi = wd_words[i + 1]["x0"] - 5 if i + 1 < len(wd_words) else float("inf")
        title = " ".join(
            w["text"]
            for w in sorted(words, key=lambda w: w["x0"])
            if x_lo <= w["x0"] < x_hi and 4 < w["y0"] - wd_w["y0"] < 22
        )
        # drop map-marker glyphs (private-use symbols) from the legend text
        title = re.sub(r"[^\w\s&/,.\-]", "", title, flags=re.UNICODE)
        title = re.sub(r"^Kreuzlingen\s*", "", title)
        zone = re.sub(r"\s+", " ", title).strip(" &,") or None
        for d in _expand_weekday(year, _WEEKDAYS[wd_w["text"]]):
            events.add(("Kehricht", zone, d))
    if not events:
        raise ValueError("no zone/weekday legend found in the city Kehricht plan")
    return events


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------


class Source:
    def __init__(
        self,
        community: str,
        zone: str | None = None,
        kehricht_zone: str | None = None,
    ):
        self._community = community
        self._zone = zone
        self._kehricht_zone = kehricht_zone

    def fetch(self) -> list[Collection]:
        pdf_stream = self._download_pdf()
        words = _extract_words(pdf_stream)

        year = _find_year(words)
        if year is None:
            raise ValueError(
                f"Could not determine the schedule year from the PDF for "
                f"'{self._community}'. The plan layout may have changed — "
                "please open an issue."
            )

        rows = _rows_from_words(words)
        anchors = _find_anchors(words)
        headers = _attach_headers(_find_header_rows(words), anchors, words)

        # events: (waste type, zone label or None, date)
        events: set[tuple[str, str | None, date]] = set()

        grid_events, gruengut_zones = _parse_grids(words, headers, year)
        events.update(grid_events)

        # weekly Kehricht rule(s), with explicitly listed holiday shifts
        kehricht = _parse_kehricht(rows, anchors)
        if kehricht:
            weekdays = {wd for _, wd in kehricht}
            kehricht_events = set()
            for label, wd in kehricht:
                zone = label if len(kehricht) > 1 and len(weekdays) > 1 else None
                for d in _expand_weekday(year, _WEEKDAYS[wd]):
                    kehricht_events.add((zone, d))
            for shift in _parse_kehricht_shifts(rows, anchors):
                near = min(
                    kehricht_events,
                    key=lambda e: abs((e[1] - shift).days),
                    default=None,
                )
                if near is not None and abs((near[1] - shift).days) <= 3:
                    kehricht_events.discard(near)
                    kehricht_events.add((near[0], shift))
            for zone, d in kehricht_events:
                events.add(("Kehricht", zone, d))

        # "weekly from March to November" Grüngut spans (e.g. Kreuzlingen)
        for span in _parse_weekly_spans(rows):
            zone = None
            if gruengut_zones:
                near_zone = min(gruengut_zones, key=lambda z: abs(z["y"] - span["y"]))
                if abs(near_zone["y"] - span["y"]) < 20:
                    zone = near_zone["label"]
            for d in _expand_span(year, span):
                events.add(("Grüngut", zone, d))

        # calendar-week Grüngut rule (e.g. Frauenfeld)
        kw = _parse_kw_rule(rows, anchors, year)
        if kw and not kw["zone_weekdays"]:
            _LOGGER.warning(
                "Found a calendar-week Grüngut rule for '%s' but no zone "
                "weekdays — skipping it. The plan layout may have changed.",
                self._community,
            )
        elif kw:
            zone_weekdays = kw["zone_weekdays"]
            for wd in zone_weekdays:
                zone = f"Zone {wd}" if len(zone_weekdays) > 1 else None
                for week in kw["weeks"]:
                    try:
                        d = date.fromisocalendar(year, week, _WEEKDAYS[wd] + 1)
                    except ValueError:
                        continue
                    events.add(("Grüngut", zone, d))

        # inline dates in the info blocks (Metalle street collections etc.)
        sections_with_grids = {t for t, _, _ in grid_events}
        for section, d in _parse_inline_dates(rows, anchors, sections_with_grids, year):
            events.add((section, None, d))

        if not events:
            _LOGGER.warning(
                "No collection dates found in the KVA Thurgau plan for '%s'. "
                "The community may only offer drop-off disposal, or the PDF "
                "layout changed.",
                self._community,
            )

        # Kreuzlingen publishes its Kehricht weekdays only in the city's own
        # zone plan; fetch it in addition to the KVA plan. The city zones are
        # a different system than the Grüngut districts, hence the separate
        # kehricht_zone argument.
        city_events: set[tuple[str, str | None, date]] = set()
        if _normalize(self._community) == "kreuzlingen":
            try:
                city_events = _fetch_kreuzlingen_city_kehricht(year)
            except Exception as e:
                _LOGGER.warning(
                    "Could not fetch the Kreuzlingen city Kehricht plan: %s", e
                )
        if self._kehricht_zone and not city_events:
            raise SourceArgumentNotFoundWithSuggestions(
                "kehricht_zone", self._kehricht_zone, []
            )

        return self._build_collections(events, city_events)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _download_pdf(self) -> io.BytesIO:
        r = requests.get(_OVERVIEW_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        links: dict[str, str] = {}
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if not href.lower().endswith(".pdf"):
                continue
            name = a.get_text(strip=True)
            if name:
                links[name] = href

        wanted = _normalize(self._community)
        pdf_link = next(
            (href for name, href in links.items() if _normalize(name) == wanted), None
        )
        if pdf_link is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "community", self._community, sorted(links) or COMMUNITIES
            )
        pdf_link = urljoin(_OVERVIEW_URL, pdf_link)

        r_pdf = requests.get(pdf_link, timeout=30)
        r_pdf.raise_for_status()
        return io.BytesIO(r_pdf.content)

    @staticmethod
    def _select_zone(
        events: set[tuple[str, str | None, date]],
        wanted_zone: str | None,
        arg_name: str,
    ) -> tuple[set[tuple[str, str | None, date]], bool]:
        """Filter events by a zone argument; returns (events, suffix_zone)."""
        zone_labels = sorted({z for _, z, _ in events if z})
        if not wanted_zone:
            return events, True
        wanted = _normalize(wanted_zone)
        matching = {z for z in zone_labels if wanted == _normalize(z)} or {
            z
            for z in zone_labels
            if re.search(rf"\b{re.escape(wanted)}\b", _normalize(z))
        }
        if not matching:
            raise SourceArgumentNotFoundWithSuggestions(
                arg_name, wanted_zone, zone_labels
            )
        return {(t, z, d) for t, z, d in events if z is None or z in matching}, False

    def _build_collections(
        self,
        events: set[tuple[str, str | None, date]],
        city_events: set[tuple[str, str | None, date]],
    ) -> list[Collection]:
        selected, suffix = self._select_zone(events, self._zone, "zone")
        selected_city, suffix_city = self._select_zone(
            city_events, self._kehricht_zone, "kehricht_zone"
        )

        collections = []
        for part, add_suffix in ((selected, suffix), (selected_city, suffix_city)):
            for t, zone, d in part:
                name = f"{t} ({zone})" if zone and add_suffix else t
                collections.append(Collection(date=d, t=name, icon=ICON_MAP.get(t)))
        collections.sort(key=lambda c: (c.date, c.type))
        return collections
