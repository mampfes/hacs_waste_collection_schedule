"""GVU Scheibbs (Gemeindeverband für Umweltschutz im Bezirk Scheibbs), Austria.

The association no longer serves dated HTML pages; it publishes one yearly
"Abfuhrkalender" PDF per member municipality, all linked from its
"Abholtermine" page as "Abfuhrtermine <Gemeinde>". The source picks the
configured municipality's link by its text, so the configured name keeps
matching next year's calendar.

Each PDF prints six months side by side per page, every day as a cell
("15 Do BIO/20 RM"), with a legend to the right of the grid. Most of the
PDFs embed a font without a ``ToUnicode`` map, so pdfminer prints glyph ids
(``(cid:53)(cid:48)`` for "RM"); the glyph ids are the character codes offset
by 29 plus three umlauts and the eszett, which ``_decode`` maps back. The
Scheibbs town calendar was converted with Online2PDF and carries its text in
form XObjects instead, which ``figure_text`` reads.

Organic waste is printed per bin size: "BIO" for the 40-collection bin and
"BIO/20" for the 20-collection bin, in Lackenhof (Gaming) "LA" and "LA 20".
Every 20-collection day is also a 40-collection day, and the day cells print
"BIO/20" for both, so the 40-collection bin is collected on every BIO and
BIO/20 day and the 20-collection bin only on BIO/20 days. ``bio_bin`` and
``lackenhof`` pick the round. The extra general-waste and paper dates "nach
Anmeldung" (R2, P4) only apply to households that registered for them and are
published only with ``additional_collections``. The bin cleaning service (W)
and the Gaming drop-off points (K, L) are not collections and are not read.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, dropdown, municipality
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://scheibbs.umweltverbaende.at/entsorgung-und-termine/abholtermine/"
_PDF_PATTERN = r"/Abfuhrkalender(20\d\d)[^/]*\.pdf$"

# As linked on the index page, without "Abfuhrtermine" and "Stadtgemeinde",
# "St." spelt out as the previous version of this source expected it.
_MUNICIPALITIES = (
    "Gaming",
    "Göstling an der Ybbs",
    "Gresten",
    "Gresten-Land",
    "Lunz am See",
    "Oberndorf an der Melk",
    "Puchenstuben",
    "Purgstall an der Erlauf",
    "Randegg",
    "Reinsberg",
    "Sankt Anton an der Jeßnitz",
    "Sankt Georgen an der Leys",
    "Scheibbs",
    "Steinakirchen am Forst",
    "Wang",
    "Wieselburg",
    "Wieselburg-Land",
    "Wolfpassing",
)

# The legend codes as printed in the day cells. "PRO+SPERR" days are read as
# PRO and SPERR, since labels match whole words.
_TYPES = {
    "RM": wt.GENERAL_WASTE,
    "R2": wt.GENERAL_WASTE,
    "PAP": wt.PAPER,
    "P4": wt.PAPER,
    "V": wt.RECYCLABLES,
    "BIO": wt.ORGANIC,
    "BIO/20": wt.ORGANIC,
    "LA": wt.ORGANIC,
    "LA 20": wt.ORGANIC,
    "STR": wt.GARDEN_WASTE,
    "Christbaum": wt.GARDEN_WASTE,
    "PRO": wt.HAZARDOUS,
    "SPERR": wt.BULKY_WASTE,
}

_BIO_ROUNDS = {
    # (lackenhof, bio_bin) -> the one organic label this household follows.
    (False, "40"): "BIO",
    (False, "20"): "BIO/20",
    (True, "40"): "LA",
    (True, "20"): "LA 20",
}
_ON_REQUEST = {"R2", "P4"}

# Glyph ids of the subset font without a ToUnicode map that are not plain
# character codes offset by 29.
_GLYPHS = {161: "ß", 166: "ä", 184: "ö", 190: "ü"}
_CID = re.compile(r"\(cid:(\d+)\)")


def _decode(text: str) -> str:
    """'(cid:53)(cid:48)' -> 'RM'; text without glyph ids passes unchanged."""

    def glyph(match: re.Match) -> str:
        number = int(match.group(1))
        if number in _GLYPHS:
            return _GLYPHS[number]
        return chr(number + 29) if 3 <= number <= 97 else ""

    return _CID.sub(glyph, text)


def _municipality_name(link_text: str) -> str:
    """'Abfuhrtermine Stadtgemeinde Wieselburg' -> 'Wieselburg'."""
    name = re.sub(r"^\s*Abfuhrtermine\s+(Stadtgemeinde\s+)?", "", link_text)
    return re.sub(r"^St\.\s*", "Sankt ", name)


def _keep(record: tuple, source: "BaseSource | None") -> bool:
    _, label = record
    params = source.params if source is not None else {}
    if label in _ON_REQUEST:
        return bool(params.get("additional_collections"))
    if _TYPES[label] is wt.ORGANIC:
        bio_round = (
            bool(params.get("lackenhof")),
            str(params.get("bio_bin") or "40"),
        )
        return label == _BIO_ROUNDS.get(bio_round)
    return True


@final
class Source(BaseSource):
    TITLE = "GVU Scheibbs"
    DESCRIPTION = (
        "Source for the municipalities of the Gemeindeverband für Umweltschutz "
        "im Bezirk Scheibbs, Austria."
    )
    URL = "https://scheibbs.umweltverbaende.at/"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.HAZARDOUS,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Gaming": {"region": "Gaming"},
        "Gaming, Lackenhof, 20 bio collections": {
            "region": "Gaming",
            "lackenhof": True,
            "bio_bin": "20",
        },
        "Sankt Anton an der Jeßnitz": {"region": "Sankt Anton an der Jeßnitz"},
        "Göstling an der Ybbs": {"region": "Göstling an der Ybbs"},
        "Wieselburg, with additional collections": {
            "region": "Wieselburg",
            "additional_collections": True,
        },
        "Scheibbs": {"region": "Scheibbs"},
    }

    REGIONS = tuple(region(name, region=name) for name in _MUNICIPALITIES)

    PARAMS = (
        municipality("region"),
        dropdown(
            "bio_bin", ["40", "20"], label="Bio bin collections per year", default="40"
        ),
        boolean("lackenhof", label="Lackenhof (Gaming)", default=False),
        boolean(
            "additional_collections",
            label="Additional collections on request (R2, P4)",
            default=False,
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your municipality as linked on "
            "https://scheibbs.umweltverbaende.at/entsorgung-und-termine/abholtermine/ "
            "without 'Abfuhrtermine' and 'Stadtgemeinde', with 'St.' spelt out "
            "as 'Sankt', e.g. 'Gaming' or 'Sankt Anton an der Jeßnitz'. Choose "
            "'20' as bio_bin if your bio bin is emptied 20 times a year (BIO/20) "
            "rather than 40, tick lackenhof in Lackenhof (Gaming), and tick "
            "additional_collections if you registered for the additional "
            "general waste and paper dates (R2, P4). Since the v3 pipeline "
            "migration, waste types use canonical, localised names. Update "
            "filters, automations and customisations using the old labels."
        ),
        "de": (
            "Gib deine Gemeinde so ein, wie sie auf "
            "https://scheibbs.umweltverbaende.at/entsorgung-und-termine/abholtermine/ "
            "verlinkt ist, ohne 'Abfuhrtermine' und 'Stadtgemeinde', mit "
            "'Sankt' statt 'St.', z. B. 'Gaming' oder 'Sankt Anton an der "
            "Jeßnitz'. Wähle bei bio_bin '20', wenn deine Biotonne 20-mal im "
            "Jahr entleert wird (BIO/20) statt 40-mal, aktiviere lackenhof in "
            "Lackenhof (Gaming) und additional_collections, wenn du für die "
            "Zusatztermine Restmüll und Altpapier (R2, P4) angemeldet bist. "
            "Seit der Umstellung auf die v3-Pipeline verwenden Abfallarten "
            "einheitliche, übersetzte Namen. Passe Filter, Automationen und "
            "Anpassungen an, die die alten Bezeichnungen verwenden."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _INDEX_URL,
            pick=retrievers.yearly_links(
                _PDF_PATTERN, argument="region", link_name=_municipality_name
            ),
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(
        parsers.PdfTableParser(
            min_words=100,
            char_margin=1.0,
            decode=_decode,
            figure_text=True,
            # The legend to the right of the December/June column.
            x_range=(0.0, 650.0),
        ),
        then=preprocessors.PdfMonthBlocks(
            labels=_TYPES, weekdays=("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
        ),
    )
    preprocess = preprocessors.RowFilter(_keep)
    transform = ICSTransformer(type_value_map=_TYPES)
