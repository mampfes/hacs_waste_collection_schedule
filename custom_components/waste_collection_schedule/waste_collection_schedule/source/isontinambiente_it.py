import datetime
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import HtmlTransformer

# Isontina Ambiente resolves the collection calendar purely from the
# "indirizzo" query parameter: the municipality name in the URL path is only
# used to render the page (title, address dropdown), it does not affect which
# calendar is returned. So any valid municipality slug can be used as the
# request path for every address id in the whole network.
_BASE = "https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/"

_MUNICIPALITIES = (
    ("capriva-del-friuli", "Capriva del Friuli"),
    ("cormons", "Cormons"),
    ("doberdo-del-lago", "Doberdò del Lago"),
    ("dolegna-del-collio", "Dolegna del Collio"),
    ("duino-aurisina", "Duino Aurisina"),
    ("farra-disonzo", "Farra d'Isonzo"),
    ("fogliano-redipuglia", "Fogliano Redipuglia"),
    ("gorizia", "Gorizia"),
    ("gradisca-disonzo", "Gradisca d'Isonzo"),
    ("grado", "Grado"),
    ("mariano-del-friuli", "Mariano del Friuli"),
    ("medea", "Medea"),
    ("monfalcone", "Monfalcone"),
    ("monrupino", "Monrupino"),
    ("moraro", "Moraro"),
    ("mossa", "Mossa"),
    ("romans-disonzo", "Romans d'Isonzo"),
    ("ronchi-dei-legionari", "Ronchi dei Legionari"),
    ("sagrado", "Sagrado"),
    ("san-canzian-disonzo", "San Canzian d'Isonzo"),
    ("san-floriano-del-collio", "San Floriano del Collio"),
    ("san-lorenzo-isontino", "San Lorenzo Isontino"),
    ("san-pier-disonzo", "San Pier d'Isonzo"),
    ("savogna-disonzo", "Savogna d'Isonzo"),
    ("sgonico-zgonik", "Sgonico - Zgonik"),
    ("staranzano", "Staranzano"),
    ("turriaco", "Turriaco"),
    ("villesse", "Villesse"),
)


def _date(dot: Tag) -> datetime.date | None:
    """The day cell's number, with the month and year of the heading above the grid."""
    table = dot.find_parent("table")
    cell = dot.find_parent("td")
    if table is None or cell is None:
        return None
    header = table.find_previous_sibling()
    if isinstance(header, Tag) and header.name != "h3":
        header = header.select_one("h3")
    if not isinstance(header, Tag):
        return None
    month_name, _, year = header.get_text(strip=True).partition(" ")
    month = recurrence.month(month_name)
    if month is None or not year.isdigit():
        return None
    day = cell.get_text(strip=True)
    if not day.isdigit():
        return None
    return datetime.date(int(year), month, int(day))


def _label(dot: Tag) -> str:
    """The legend's name for the dot's colour, falling back to the colour itself."""
    color = next(c for c in dot.get("class", []) if c != "dot")
    table = dot.find_parent("table")
    legend = table.find_next_sibling() if table is not None else None
    if isinstance(legend, Tag):
        for entry in legend.select("div"):
            swatch = entry.select_one("span.dot")
            if swatch is not None and color in swatch.get("class", []):
                return entry.get_text(strip=True)
    return color


@final
class Source(BaseSource):
    TITLE = "Isontina Ambiente"
    DESCRIPTION = (
        "Source for isontina ambiente, serving the municipalities of the Gorizia "
        "province (Italy) and others in the Isontina Ambiente network."
    )
    URL = "https://isontinambiente.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "PIAZZA FURLAN, Ronchi dei Legionari Area B": {"address_id": 1172},
        "VIA DANTE  , Ronchi dei Legionari Area C": {"address_id": 75},
        "VIA GORIZIA  , Ronchi dei Legionari Area F": {"address_id": 147},
        "ANDRONA DELLA PERGOLA, Gorizia Area B": {"address_id": 488},
        "ANDRONA AQUILEIA, Monfalcone Area Monfalcone Ovest": {"address_id": 819},
        "CORTE DEI MAGAZZINI, Cormons Area B": {"address_id": 1145},
        "VIA AVERTO, Grado Area Grado Fossalon Boscat": {"address_id": 1219},
    }

    PARAMS = (location_id("address_id"),)

    REGIONS = tuple(
        region(f"Isontina Ambiente: {name}", url=f"{_BASE}{slug}/")
        for slug, name in _MUNICIPALITIES
    )

    HOWTO: ClassVar[dict] = {
        "en": "Visit <https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/>, pick your municipality from the list, and select your address. The address ID is the number at the end of the URL. e.g. `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/ronchi-dei-legionari/?indirizzo=1172` the address ID is `1172`.",
        "it": "Visita <https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/>, scegli il tuo comune dall'elenco e seleziona il tuo indirizzo. L'ID dell'indirizzo è il numero alla fine dell'URL. es. `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/ronchi-dei-legionari/?indirizzo=1172` l'ID dell'indirizzo è `1172`.",
    }

    retrieve = retrievers.Request(
        f"{_BASE}ronchi-dei-legionari/",
        params=lambda address_id, **_: {"indirizzo": address_id},
    )

    parse = parsers.HtmlParser("table.calendar td div.dot")

    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_label,
        type_value_map={
            "Carta e cartone": wt.PAPER,
            "Organico umido": wt.ORGANIC,
            "Plastica e lattine": wt.RECYCLABLES,
            "Secco residuo": wt.GENERAL_WASTE,
            "Vetro": wt.GLASS,
        },
    )
