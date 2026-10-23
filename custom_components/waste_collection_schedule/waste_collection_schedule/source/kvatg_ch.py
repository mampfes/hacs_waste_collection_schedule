"""KVA Thurgau disposal plans (kvatg.ch), one PDF per municipality."""

from collections.abc import Iterable
from datetime import date
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, municipality, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.regions import region
from waste_collection_schedule.service import KvaThurgau as kva
from waste_collection_schedule.service.ICS import IcsEvent
from waste_collection_schedule.transformers import ICSTransformer

_OVERVIEW_URL = "https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/"

# The KVA plan for Kreuzlingen contains no Kehricht dates: the city publishes
# its own zone plan (a map PDF with a parseable zone/weekday legend) here.
_CITY_URL = "https://www.kreuzlingen.ch/wir-fuer-sie/entsorgung"

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


def _targets(source: BaseSource, plan_url: str) -> list[str]:
    """The plan PDF, plus Kreuzlingen's city page that links its Kehricht plan."""
    targets = [plan_url]
    if kva.normalize(source.params["community"]) == "kreuzlingen":
        targets.append(_CITY_URL)
    return targets


def plan_rows(documents: list[list[dict]], source: BaseSource) -> Iterable[IcsEvent]:
    """Events of the community plan (and Kreuzlingen's city Kehricht plan)."""
    params = source.params
    year, events = kva.plan_events(documents[0], params["community"])
    city_events = (
        kva.city_kehricht_events(documents[1], year) if len(documents) > 1 else set()
    )
    kehricht_zone = params.get("kehricht_zone")
    if kehricht_zone and not city_events:
        raise SourceArgumentNotFoundWithSuggestions("kehricht_zone", kehricht_zone, [])

    selected, _ = kva.select_zone(events, params.get("zone"), "zone")
    selected_city, _ = kva.select_zone(city_events, kehricht_zone, "kehricht_zone")
    rows: list[tuple[date, str, str | None]] = [
        (d, t, zone) for t, zone, d in (*selected, *selected_city)
    ]
    for d, t, zone in sorted(rows, key=lambda r: (r[0], r[1], r[2] or "")):
        yield IcsEvent(date=d, title=t, location=zone, description=None)


@final
class Source(BaseSource):
    TITLE = "KVA Thurgau"
    DESCRIPTION = (
        "Source for KVA Thurgau (Kehrichtverwertungsanlage Thurgau) waste collection, "
        "covering the municipalities of the canton of Thurgau and neighbouring "
        "communities, Switzerland."
    )
    URL = "https://www.kvatg.ch"
    COUNTRY = "ch"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@Smn-hns"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.PLASTIC,
        wt.METAL,
    ]

    TEST_CASES: ClassVar[dict] = {
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

    PARAMS = (
        municipality("community"),
        district("zone", optional=True),
        text_field("kehricht_zone", "Kehricht zone (Kreuzlingen only)", optional=True),
    )

    REGIONS = tuple(region(name, community=name) for name in COMMUNITIES)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Find your community on https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/ "
            "and enter its name. If your community's disposal plan splits a collection "
            "by zone (e.g. the green waste districts in Kreuzlingen or the collection "
            "areas in Frauenfeld), you can optionally enter the zone name as printed "
            "in the plan; an invalid value shows a list of the valid names. Only for "
            "Kreuzlingen, kehricht_zone selects the household-waste zone of the "
            "city's own zone plan ('Süd & Tägerwilen', 'Nord und Ost' or 'Zentrum'); "
            "leave it empty to get all three."
        ),
        "de": (
            "Suchen Sie Ihre Gemeinde auf https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/ "
            "und geben Sie deren Namen ein. Falls der Entsorgungsplan Ihrer Gemeinde "
            "eine Sammlung nach Zonen unterteilt (z. B. die Grüngut-Gebiete in "
            "Kreuzlingen oder die Abfuhrgebiete in Frauenfeld), können Sie optional "
            "den Zonennamen wie im Plan gedruckt angeben; bei einem ungültigen Wert "
            "wird eine Liste der gültigen Namen angezeigt. Nur für Kreuzlingen wählt "
            "kehricht_zone die Kehricht-Zone des städtischen Zonenplans ('Süd & "
            "Tägerwilen', 'Nord und Ost' oder 'Zentrum'); leer lassen für alle drei."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_OVERVIEW_URL, pick=kva.plan_link),
        targets=_targets,
        fetch=retrievers.Request(
            lambda target, plan_url, link=None, **_: link or target,
            before=(
                retrievers.Lookup(
                    lambda target, plan_url, **_: target,
                    pick=kva.city_plan_link,
                    when=lambda target, plan_url, **_: target == _CITY_URL,
                ),
            ),
        ),
    )
    parse = parsers.EachResponse(kva.PlanWordsParser())
    preprocess = staticmethod(plan_rows)
    transform = ICSTransformer(
        type_value_map={
            "Kehricht": wt.GENERAL_WASTE,
            "Papier/Karton": wt.PAPER,
            "Papier": wt.PAPER,
            "Karton": wt.PAPER,
            "Kleinsperrgut": wt.BULKY_WASTE,
            "Grüngut": wt.ORGANIC,
            "Kunststoff": wt.PLASTIC,
            "Häckseldienst": wt.GARDEN_WASTE,
            "Metalle": wt.METAL,
            "Christbaum": wt.GARDEN_WASTE,
        }
    )
