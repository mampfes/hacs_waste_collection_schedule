"""Saubermacher - Komunala, Murska Sobota (Pomurje), Slovenia.

Saubermacher - Komunala collects household waste in Murska Sobota and the
neighbouring Pomurje municipalities. Each municipality's page lists one
yearly calendar PDF per settlement (Murska Sobota town: one per collection
district, "rajon"). The PDFs are DevExpress reports on one template: the
dates ("12.jan", "9.apr-čet" for a moved day) are text in five boxes whose
headings (residual waste, organic waste, packaging, paper, glass) are part of
the background image, so the box a date sits in tells its type.

Each box opens with its collection weekday ("V PONEDELJEK"). A date belongs
to the nearest weekday line above it in the same page half: a long list may
run past its box frame (the Murska Sobota blocks calendar spills packaging
dates into the empty glass box), but never past the next box's weekday line.
Every date is checked against that weekday, or against the weekday printed
after a moved date. The hazardous waste and collection-centre boxes carry no
kerbside dates and are not read.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import (
    lookups,
    parsers,
    recurrence,
    response_shape,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, dropdown
from waste_collection_schedule.transformers import ICSTransformer

_SITE = "https://www.saubermacher-komunala.si"

# Municipalities whose page links settlement calendars -> page slug. (Lendava,
# Puconci and Velika Polana are served too, but publish no calendar PDF.)
_MUNICIPALITIES = {
    "Beltinci": "beltinci",
    "Cankova": "cankova",
    "Črenšovci": "crensovci",
    "Dobrovnik": "dobrovnik-dobronak",
    "Gornji Petrovci": "gornji-petrovci",
    "Grad": "grad",
    "Hodoš": "hodos",
    "Kobilje": "kobilje",
    "Kuzma": "kuzma",
    "Moravske Toplice": "moravske-toplice",
    "Murska Sobota": "murska-sobota",
    "Odranci": "odranci",
    "Rogašovci": "rogasovci",
    "Šalovci": "salovci",
    "Tišina": "tisina",
    "Turnišče": "turnisce",
}

_RESIDUAL = "Ostali odpadki"
_ORGANIC = "Biološki odpadki"
_PACKAGING = "Mešana embalaža"
_PAPER = "Papir"
_GLASS = "Steklo"

# Box position on the template: (right half?, row from the top) -> type.
_BOXES = {
    (False, 0): _RESIDUAL,
    (False, 1): _PACKAGING,
    (False, 2): _GLASS,
    (True, 0): _ORGANIC,
    (True, 1): _PAPER,
}
# Template coordinates (A4 portrait, origin bottom left): the page halves
# split at x 297, the box rows at y 400 and 240.
_HALF_X = 297.0
_ROW_TOPS = (400.0, 240.0)

_WEEKDAY_RE = re.compile(r"^V\s+([^\W\d_]{3})[^\W\d_]*$")
_DATE_RE = re.compile(r"^(\d{1,2})\.([^\W\d_]{3})(?:-([^\W\d_]{3}))?$")
_YEAR_RE = re.compile(r"^20\d\d$")
# "Murska Sobota - rajon 4 - ponedeljek": the link names the weekday too.
_LINK_WEEKDAY_RE = re.compile(
    r"\s*-\s*(?:" + "|".join(recurrence.weekday_names("sl")) + r")\s*$",
    re.IGNORECASE,
)


def _index_url(municipality: str, **_) -> str:
    slug = lookups.resolve(
        _MUNICIPALITIES,
        municipality,
        argument="municipality",
        normalize=lookups.normalize_loose,
    )
    return f"{_SITE}/kje-zbiramo-odpadke/{slug}"


def _link_name(tag) -> str:
    return _LINK_WEEKDAY_RE.sub("", tag.get_text(" ", strip=True))


def _expect(condition: bool, detail: str, source: BaseSource) -> None:
    response_shape.expect(
        condition, source_name=response_shape.source_name(source), detail=detail
    )


def _weekday(name: str) -> "int | None":
    return recurrence.weekday(name.lower(), "sl", abbreviated=True)


def _collections(
    layouts: list[parsers.PdfWordLayout], source: BaseSource
) -> Iterable[tuple[datetime.date, str]]:
    layout = layouts[0]
    years = {w.text for w in layout.lines if _YEAR_RE.match(w.text)}
    _expect(len(years) == 1, f"calendar year not found ({sorted(years)})", source)
    year = int(years.pop())

    # (right half?, y, type, weekday) of every box's weekday line.
    heads: list[tuple[bool, float, str, int]] = []
    for line in layout.lines:
        if not (match := _WEEKDAY_RE.match(line.text)):
            continue
        weekday = _weekday(match[1])
        _expect(weekday is not None, f"unknown weekday line {line.text!r}", source)
        right = line.x > _HALF_X
        row = sum(line.y < top for top in _ROW_TOPS)
        label = _BOXES.get((right, row))
        _expect(label is not None, f"weekday line {line.text!r} off template", source)
        heads.append((right, line.y, label, weekday))  # type: ignore[arg-type]
    _expect(len(heads) >= 3, f"only {len(heads)} waste boxes found", source)

    count = 0
    for word in layout.words:
        if not (match := _DATE_RE.match(word.text)):
            continue
        right = word.x > _HALF_X
        above = [h for h in heads if h[0] == right and h[1] > word.y]
        if not above:
            continue
        _right, _y, label, weekday = min(above, key=lambda h: h[1])
        month = recurrence.month(match[2].lower(), "sl", abbreviated=True)
        _expect(month is not None, f"unknown month in {word.text!r}", source)
        day = datetime.date(year, month, int(match[1]))  # type: ignore[arg-type]
        if match[3]:
            moved = _weekday(match[3])
            _expect(moved is not None, f"unknown weekday in {word.text!r}", source)
            weekday = moved  # type: ignore[assignment]
        _expect(
            day.weekday() == weekday,
            f"{word.text} ({label}) is not on its printed weekday",
            source,
        )
        count += 1
        yield day, label
    _expect(count >= 20, f"only {count} collection dates found", source)


@final
class Source(BaseSource):
    TITLE = "Saubermacher - Komunala"
    DESCRIPTION = (
        "Source for Saubermacher - Komunala (Murska Sobota and Pomurje "
        "municipalities), Slovenia."
    )
    URL = _SITE
    COUNTRY = "si"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Murska Sobota rajon 4": {
            "municipality": "Murska Sobota",
            "district": "Murska Sobota - rajon 4",
        },
        "Murska Sobota bloki": {
            "municipality": "Murska Sobota",
            "district": "Murska Sobota - bloki",
        },
        "Bogojina": {"municipality": "Moravske Toplice", "district": "Bogojina"},
        "Crensovci": {
            "municipality": "Črenšovci",
            "district": "Črenšovci, Žižki, Trnje",
        },
    }

    PARAMS = (
        dropdown("municipality", list(_MUNICIPALITIES), label="Municipality"),
        district(),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Choose your municipality, then enter your settlement exactly as "
            "its calendar is named under 'Urniki odvozov' on the municipality's "
            "page at https://www.saubermacher-komunala.si/kje-zbiramo-odpadke "
            "(e.g. 'Bogojina'). In Murska Sobota town use your district without "
            "the weekday, e.g. 'Murska Sobota - rajon 4' or 'Murska Sobota - "
            "bloki'; the PDF 'Razdelitev mesta Murska Sobota na rajone' shows "
            "the districts."
        ),
        "sl": (
            "Izberite občino in vpišite naselje natanko tako, kot je urnik "
            "poimenovan pod 'Urniki odvozov' na strani občine na "
            "https://www.saubermacher-komunala.si/kje-zbiramo-odpadke "
            "(npr. 'Bogojina'). V mestu Murska Sobota vpišite rajon brez dneva, "
            "npr. 'Murska Sobota - rajon 4' ali 'Murska Sobota - bloki'; rajone "
            "prikazuje PDF 'Razdelitev mesta Murska Sobota na rajone'."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _index_url,
                pick=lookups.link_pick(
                    "district", href=r"/odvoz_odpadkov_[^/]*\.pdf", label=_link_name
                ),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = parsers.PdfWordLayoutParser(min_words=40)
    preprocess = staticmethod(_collections)
    transform = ICSTransformer(
        type_value_map={
            _RESIDUAL: wt.GENERAL_WASTE,
            _ORGANIC: wt.ORGANIC,
            _PACKAGING: wt.RECYCLABLES,
            _PAPER: wt.PAPER,
            _GLASS: wt.GLASS,
        }
    )
