"""Consorzio Area Vasta Medio Novarese, Italy.

The consortium publishes one yearly "ecocalendario" PDF per municipality (and
per collection zone in Arona, Borgomanero and Castelletto Sopra Ticino), all
linked from one page as "<Comune> <year> (UFF.)". The source picks the
configured municipality's link by its text with the year dropped, so the
configured name keeps matching next year's calendar.

Each PDF prints three months side by side per page, every day as a line
("1 Lun SECCO", "16 Giov PLASTICA - VETRO") in two columns per month, after a
cover page. Several municipalities' calendars run March to February rather
than January to December; ``preprocessors.PdfMonthBlocks`` dates every month
block by the printed weekdays, so that needs no configuration, and a block
whose weekdays fit no year fails loudly instead of landing in the wrong month.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://www.consorziomedionovarese.it/it-it/rifiuti/rifiuti/calendario"
_PDF_PATTERN = r"/download/[^/]*-(20\d\d)-uff-[^/]*$"

# As listed on the calendar page (link text without "<year> (UFF.)").
_MUNICIPALITIES = (
    "Agrate Conturbia",
    "Ameno",
    "Armeno",
    "Arona (zona C)",
    "Arona (zona D)",
    "Arona (zone A-B)",
    "Boca",
    "Bogogno",
    "Bolzano Novarese",
    "Borgo Ticino",
    "Borgomanero (zona A)",
    "Borgomanero (zona B)",
    "Borgomanero (zona C)",
    "Briga Novarese",
    "Carpignano Sesia",
    "Castelletto Sopra Ticino (zona A)",
    "Castelletto Sopra Ticino (zona B)",
    "Cavaglietto",
    "Cavaglio d'Agogna",
    "Cavallirio",
    "Colazza",
    "Comignago",
    "Cressa",
    "Cureggio",
    "Divignano",
    "Dormelletto",
    "Fara Novarese",
    "Fontaneto d'Agogna",
    "Gargallo",
    "Gattico-Veruno",
    "Ghemme",
    "Gozzano",
    "Grignasco",
    "Invorio",
    "Lesa",
    "Maggiora",
    "Massino Visconti",
    "Meina",
    "Miasino",
    "Nebbiuno",
    "Oleggio Castello",
    "Orta San Giulio",
    "Paruzzaro",
    "Pella",
    "Pettenasco",
    "Pisano",
    "Pogno",
    "Pombia",
    "Prato Sesia",
    "Romagnano Sesia",
    "San Maurizio d'Opaglio",
    "Sizzano",
    "Soriso",
    "Suno",
    "Varallo Pombia",
)

# The rounds as printed in the day cells.
_TYPES = {
    "INDISTINTO": wt.GENERAL_WASTE,
    "SECCO": wt.GENERAL_WASTE,
    "ORGANICO": wt.ORGANIC,
    "UMIDO": wt.ORGANIC,
    "CARTA": wt.PAPER,
    # Cardboard collected from businesses ("ditte"), printed in three forms.
    "CARTONI DITTE": wt.PAPER,
    "CARTONI D.": wt.PAPER,
    "CART.DITTE": wt.PAPER,
    "PLASTICA": wt.PLASTIC,
    "LATTINE": wt.METAL,
    "VETRO": wt.GLASS,
    # "VERDE*": garden waste, a paid service ("* A PAGAMENTO") in most towns.
    "VERDE": wt.GARDEN_WASTE,
}


def _municipality_name(link_text: str) -> str:
    """'Arona (zona C) 2026 (UFF.)' -> 'Arona (zona C)'."""
    return re.sub(r"\s+20\d\d\b.*$", "", link_text)


@final
class Source(BaseSource):
    TITLE = "Consorzio Area Vasta Medio Novarese"
    DESCRIPTION = "Source for Consorzio Area Vasta Medio Novarese (Novara), Italy."
    URL = "https://www.consorziomedionovarese.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.PLASTIC,
        wt.METAL,
        wt.GLASS,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Ameno": {"municipality": "Ameno"},
        "Borgomanero zona A": {"municipality": "Borgomanero (zona A)"},
        "Arona zone A-B": {"municipality": "Arona zone A-B"},
        "Bogogno": {"municipality": "Bogogno"},
    }

    REGIONS = tuple(region(name, municipality=name) for name in _MUNICIPALITIES)

    PARAMS = (municipality("municipality"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your municipality as listed on "
            "https://www.consorziomedionovarese.it/it-it/rifiuti/rifiuti/calendario "
            "without the year, including the zone where there is one, e.g. "
            "'Ameno' or 'Borgomanero (zona A)'."
        ),
        "it": (
            "Inserisci il comune come indicato su "
            "https://www.consorziomedionovarese.it/it-it/rifiuti/rifiuti/calendario "
            "senza l'anno, con la zona dove prevista, ad es. 'Ameno' o "
            "'Borgomanero (zona A)'."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _INDEX_URL,
            pick=retrievers.yearly_links(
                _PDF_PATTERN,
                argument="municipality",
                link_name=_municipality_name,
                # A March-February calendar still holds January and February.
                lookback=1,
            ),
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(
        parsers.PdfTableParser(min_words=100),
        then=preprocessors.PdfMonthBlocks(labels=_TYPES),
    )
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
