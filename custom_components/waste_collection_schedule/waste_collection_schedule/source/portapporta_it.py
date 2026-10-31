"""PortAPPorta (Webmapp), Italy: door-to-door collection calendars.

PortAPPorta is the collection app Webmapp runs for several Tuscan operators
(ERSU in Versilia and Lunigiana, ASMIU in Massa, REA around Rosignano Marittimo
and Cecina, ESA on Elba). Its public API (https://portapporta.webmapp.it/api,
open source at https://github.com/webmappsrl/portapporta) lists each operator's
collection zones as GeoJSON and serves the calendar of one zone without a
login, optionally narrowed to one kind of user (domestic, commercial, beach
establishment, ...).

The zone is the user's choice: the API holds only the zone polygons, not the
streets, so the zone is picked by name (the app picks it by locating the
address on a map).
"""

import datetime
from typing import Any, ClassVar, NamedTuple, final

from waste_collection_schedule import (
    config_params,
    date_parsers,
    lookups,
    parsers,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    ExplodeList,
    FlattenGroups,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import RowTransformer

_API = "https://portapporta.webmapp.it/api"

# Operator (company name in the API) -> PortAPPorta company id.
_OPERATORS = {
    "ersu": 1,
    "asmiu": 2,
    "rea": 3,
    "esa": 4,
}

# One year ahead; the API answers the next 14 days when no range is given.
_DAYS_AHEAD = 365

# Trash type slugs, compared case-insensitively. Each operator names its own.
_TYPES: dict[str, Any] = {
    "organico": wt.ORGANIC,
    "carta": wt.PAPER,
    "imballaggi-in-carta-cartone": wt.PAPER,
    "vetro": wt.GLASS,
    "vetro_lattine": wt.GLASS,
    "plastica": wt.PLASTIC,
    "multimateriale": wt.RECYCLABLES,
    "imballaggi e contenitori in plastica e metallo": wt.RECYCLABLES,
    "metallo": wt.METAL,
    "indifferenziato": wt.GENERAL_WASTE,
    "rifiuto urbano residuo": wt.GENERAL_WASTE,
    "rifiuti domestici": wt.GENERAL_WASTE,
    "pannoloni": wt.GENERAL_WASTE,
    "verde": wt.GARDEN_WASTE,
    "sfalci e potature": wt.GARDEN_WASTE,
    "stoffa": wt.TEXTILES,
    "indumenti": wt.TEXTILES,
    "ingombranti": wt.BULKY_WASTE,
    "ingombranti_small": wt.BULKY_WASTE,
    "ingombranti_big": wt.BULKY_WASTE,
    "raee": wt.ELECTRONICS,
    "raee_small": wt.ELECTRONICS,
    "raee_big": wt.ELECTRONICS,
    "pericolosi": wt.HAZARDOUS,
}

# Comuni (as the API names them, "Comune di" dropped) per operator, for the
# documentation only: the zones are always read from the API.
_COMUNI = {
    "ersu": (
        "Aulla",
        "Bagnone",
        "Camaiore",
        "Casola",
        "Comano",
        "Filattiera",
        "Fivizzano",
        "Forte dei Marmi",
        "Fosdinovo",
        "Licciana Nardi",
        "Massarosa",
        "Montignoso",
        "Mulazzo",
        "Pietrasanta",
        "Podenzana",
        "Pontremoli",
        "Seravezza",
        "Stazzema",
        "Tresana",
        "Villafranca",
        "Zeri",
    ),
    "asmiu": ("Massa",),
    "rea": (
        "Casale Marittimo",
        "Castellina Marittima",
        "Castiglioncello",
        "Cecina",
        "Collesalvetti",
        "Guardistallo",
        "Guasticce",
        "Monteverdi Marittimo",
        "Montescudaio",
        "Orciano Pisano",
        "Pomarance",
        "Riparbella",
        "Rosignano Marittimo",
        "Santa Luce",
        "Stagno",
        "Vicarello",
    ),
    "esa": (
        "Campo nell'Elba",
        "Capoliveri",
        "Marciana",
        "Marciana Marina",
        "Portoferraio",
        "Rio",
    ),
}

_DOMESTIC = "domestic"


class _Zone(NamedTuple):
    zone_id: int
    user_type_id: "int | None"


def _comune_name(value: Any) -> str:
    name = str(value or "").strip()
    if name.casefold().startswith("comune di "):
        name = name[len("comune di ") :]
    return name


def _zone_names(label: str, comune: str) -> tuple[str, ...]:
    """The zone's label, and the label without a leading "<comune> - "."""
    names = [label]
    head, sep, tail = label.partition(" - ")
    if sep and lookups.normalize_loose(head) == lookups.normalize_loose(comune):
        names.append(tail)
    return tuple(names)


def _user_type(zone: dict, utenza: "str | None") -> "int | None":
    types = zone.get("availableUserTypes") or []
    if not types:
        return None
    names = {}
    for user_type in types:
        label = user_type.get("label") or {}
        for name in (label.get("it"), label.get("en")):
            if name:
                names[name] = user_type["id"]
    if utenza:
        return lookups.resolve(
            names, utenza, argument="utenza", normalize=lookups.normalize_loose
        )
    domestic = [
        user_type["id"]
        for user_type in types
        if str((user_type.get("label") or {}).get("it", ""))
        .casefold()
        .startswith(_DOMESTIC[:7])
    ]
    if domestic:
        return domestic[0]
    if len(types) == 1:
        return types[0]["id"]
    raise SourceArgumentRequiredWithSuggestions(
        "utenza",
        "the zone has no domestic calendar; choose the kind of user",
        sorted(names),
    )


def _zone(
    response: Any,
    *,
    comune: str,
    zona: "str | None" = None,
    utenza: "str | None" = None,
    **_: Any,
) -> _Zone:
    """The zone (and user type) named by the params in the operator's zones."""
    by_comune: dict[str, list[dict]] = {}
    for feature in response.json().get("features") or []:
        properties = feature.get("properties") or {}
        by_comune.setdefault(_comune_name(properties.get("comune")), []).append(
            properties
        )
    zones = lookups.resolve(
        by_comune,
        _comune_name(comune),
        argument="comune",
        normalize=lookups.normalize_loose,
    )
    if not zona:
        if len(zones) != 1:
            raise SourceArgumentRequiredWithSuggestions(
                "zona",
                "the comune has more than one collection zone",
                sorted(str(zone["label"]) for zone in zones),
            )
        chosen = zones[0]
    else:
        wanted = lookups.normalize_loose(zona)
        matches = [
            zone
            for zone in zones
            if wanted
            in {
                lookups.normalize_loose(name)
                for name in _zone_names(str(zone["label"]), _comune_name(comune))
            }
        ]
        if not matches:
            raise SourceArgumentNotFoundWithSuggestions(
                "zona", zona, sorted(str(zone["label"]) for zone in zones)
            )
        chosen = matches[0]
    return _Zone(int(chosen["id"]), _user_type(chosen, utenza))


def _calendar_params(zone: _Zone, **_: Any) -> dict[str, Any]:
    today = datetime.date.today()
    params: dict[str, Any] = {
        "start_date": today.isoformat(),
        "stop_date": (today + datetime.timedelta(days=_DAYS_AHEAD)).isoformat(),
    }
    if zone.user_type_id is not None:
        params["user_type_id"] = zone.user_type_id
    return params


def _collections(row: Any, _source: Any) -> list[tuple[str, str]]:
    """``(date, entry)`` -> one ``(date, trash type slug)`` per trash type."""
    day, entry = row
    return [
        (day, str(trash_type["slug"]))
        for trash_type in (entry or {}).get("trash_types") or []
    ]


@final
class Source(BaseSource):
    TITLE = "PortAPPorta (ERSU, ASMIU, REA, ESA)"
    DESCRIPTION = (
        "Source for the PortAPPorta app: ERSU (Versilia, Lunigiana), ASMIU "
        "(Massa), REA (Rosignano Marittimo, Cecina) and ESA (Elba)."
    )
    URL = "https://portapporta.webmapp.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.ELECTRONICS,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.HAZARDOUS,
        wt.METAL,
        wt.ORGANIC,
        wt.PAPER,
        wt.PLASTIC,
        wt.RECYCLABLES,
        wt.TEXTILES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "REA Rosignano Nibbiaia": {
            "gestore": "rea",
            "comune": "Rosignano Marittimo",
            "zona": "Gabbro, Nibbiaia e Castelnuovo della Misericordia",
        },
        "REA Montescudaio": {"gestore": "rea", "comune": "Montescudaio"},
        "ASMIU Massa Zona A": {"gestore": "asmiu", "comune": "Massa", "zona": "Zona A"},
        "ERSU Camaiore Lido commercial": {
            "gestore": "ersu",
            "comune": "Camaiore",
            "zona": "Localita Lido di Camaiore",
            "utenza": "Commerciale",
        },
        "ERSU Aulla": {"gestore": "ersu", "comune": "Comune di Aulla"},
        "ESA Marciana Marina": {"gestore": "esa", "comune": "Marciana Marina"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown comune": {"gestore": "rea", "comune": "Nowhere"},
        "Zone required": {"gestore": "asmiu", "comune": "Massa"},
    }

    REGIONS = tuple(
        region(f"{comune} ({gestore.upper()})", gestore=gestore, comune=comune)
        for gestore, comuni in _COMUNI.items()
        for comune in comuni
    )

    PARAMS = (
        config_params.dropdown("gestore", list(_OPERATORS), label="Operator"),
        config_params.municipality("comune"),
        config_params.district("zona", optional=True),
        config_params.text_field("utenza", label="User type", optional=True),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Choose the operator: `ersu` (Versilia and Lunigiana), `asmiu` "
            "(Massa), `rea` (Rosignano Marittimo, Cecina and surroundings) or "
            "`esa` (Elba). Enter your comune as the PortAPPorta app lists it, "
            "e.g. `Rosignano Marittimo`. Where the comune has more than one "
            "collection zone, also enter the zone as named in the app, e.g. "
            "`Gabbro, Nibbiaia e Castelnuovo della Misericordia` (a wrong or "
            "missing zone lists the valid ones). The domestic calendar is used "
            "unless you enter another user type in `utenza`, e.g. "
            "`Commerciale`."
        ),
        "it": (
            "Scegli il gestore: `ersu` (Versilia e Lunigiana), `asmiu` "
            "(Massa), `rea` (Rosignano Marittimo, Cecina e dintorni) o `esa` "
            "(Elba). Inserisci il comune come appare nell'app PortAPPorta, ad "
            "esempio `Rosignano Marittimo`. Se il comune ha più zone di "
            "raccolta, indica anche la zona come nell'app, ad esempio "
            "`Gabbro, Nibbiaia e Castelnuovo della Misericordia` (con una zona "
            "errata o mancante viene mostrato l'elenco). Viene usato il "
            "calendario delle utenze domestiche, salvo indicare un altro tipo "
            "di utenza in `utenza`, ad esempio `Commerciale`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                lambda gestore, **_: f"{_API}/c/{_OPERATORS[gestore]}/zones.geojson",
                pick=lambda response, **params: _zone(response, **params),
            ),
        ),
        url=lambda zone, gestore, **_: (
            f"{_API}/v2/c/{_OPERATORS[gestore]}/calendar/z/{zone.zone_id}"
        ),
        params=_calendar_params,
    )
    parse = parsers.JsonParser("data", "calendar", expected_values={"success": True})
    preprocess = Compose(FlattenGroups(with_key=True), ExplodeList(_collections))
    transform = RowTransformer(
        type_value_map=_TYPES,
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        carry_raw_label=True,
    )
