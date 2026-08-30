import re
import unicodedata
from datetime import date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Clisson Sèvre et Maine Agglo"
DESCRIPTION = (
    "Source for Clisson Sèvre et Maine Agglo, the inter-municipal authority "
    "responsible for waste collection in 18 municipalities of the "
    "Loire-Atlantique department, France."
)
URL = "https://environnement.clissonsevremaine.fr"
COUNTRY = "fr"

SOURCE_CODEOWNERS = ["@JeyMuller"]

CALENDAR_URL = (
    "https://environnement.clissonsevremaine.fr"
    "/dechets/collecte-des-dechets/calendrier-des-collectes"
)
CATEGORY_ARG = "tx_calendarize_calendar[customSearch][category]"
MONTH_ARG = "tx_calendarize_calendar[month]"
YEAR_ARG = "tx_calendarize_calendar[year]"

# Number of months fetched, starting with the current one. The integration
# refreshes once a day by default, so this stays well within reason.
MONTHS_TO_FETCH = 12

# Only used to advertise every municipality in the documentation and in the
# configuration UI. The actual identifiers are always resolved live from the
# drop-down on the website, so a renumbering upstream cannot break the source.
COMMUNES = [
    "Aigrefeuille-sur-Maine",
    "Boussay",
    "Château-Thébaud",
    "Clisson",
    "Clisson, rue Saint-Antoine",
    "Gétigné - zone A",
    "Gétigné - zone B",
    "Gorges",
    "Haute-Goulaine",
    "La Haye-Fouassière - Zone A",
    "La Haye-Fouassière - Zone B",
    "La Planche",
    "Maisdon-sur-Sèvre - zone 1",
    "Maisdon-sur-Sèvre - zone 2",
    "Maisdon-sur-Sèvre - zone 3",
    "Monnières",
    "Remouillé",
    "Saint-Hilaire-de-Clisson - Zone A",
    "Saint-Hilaire-de-Clisson - Zone B",
    "Saint-Lumine-de-Clisson - Zone A",
    "Saint-Lumine-de-Clisson - Zone B",
    "St-Fiacre-sur-Maine",
    "Vieillevigne",
]

EXTRA_INFO = [
    {
        "title": commune,
        "url": URL,
        "default_params": {"commune": commune},
    }
    for commune in COMMUNES
]

# A representative subset: a plain municipality, a zoned one, the street that
# has its own round, and a three-zone municipality. Every entry costs
# MONTHS_TO_FETCH requests, so testing all 23 zones would hammer the website.
TEST_CASES = {
    "Gorges": {"commune": "Gorges"},
    "Maisdon-sur-Sèvre - zone 1": {"commune": "Maisdon-sur-Sèvre - zone 1"},
    "La Haye-Fouassière - Zone B": {"commune": "La Haye-Fouassière - Zone B"},
    "Clisson, rue Saint-Antoine": {"commune": "clisson, rue saint-antoine"},
}

ICON_MAP = {
    "ordures menageres": Icons.GENERAL_WASTE,
    "emballages": Icons.PLASTIC_PACKAGING,
}
DEFAULT_ICON = Icons.GENERAL_WASTE

PARAM_TRANSLATIONS = {
    "en": {"commune": "Municipality"},
    "fr": {"commune": "Commune"},
}
PARAM_DESCRIPTIONS = {
    "en": {
        "commune": (
            "Your municipality, exactly as listed in the drop-down menu on the "
            "collection calendar page, e.g. 'Maisdon-sur-Sèvre - zone 1'."
        )
    },
    "fr": {
        "commune": (
            "Votre commune, telle qu'elle apparaît dans la liste déroulante de "
            "la page du calendrier des collectes, par exemple "
            "'Maisdon-sur-Sèvre - zone 1'."
        )
    },
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        f"Open {CALENDAR_URL} and pick your municipality in the drop-down menu. "
        "Use the wording shown there. Some municipalities are split into "
        "several collection zones; the maps at the end of the downloadable PDF "
        "calendars tell you which zone your street belongs to."
    ),
    "fr": (
        f"Ouvrez {CALENDAR_URL} et choisissez votre commune dans la liste "
        "déroulante. Reprenez le libellé affiché. Certaines communes sont "
        "découpées en plusieurs zones de collecte ; les cartes situées à la fin "
        "des calendriers PDF téléchargeables indiquent la zone de votre rue."
    ),
}

FRENCH_MONTHS = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]

# The waste type is spelled out in the calendar legend as "Collecte des
# ordures ménagères" / "Collecte des emballages". Trim the lead-in so the
# sensors read "Ordures ménagères" and "Emballages".
COLLECTION_PREFIX = re.compile(r"^collecte\s+(?:des?|du|de\s+la|de\s+l')\s+", re.I)


def _normalize(value: str) -> str:
    """Lowercase, strip accents and reduce punctuation to single spaces."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", without_accents.lower()).strip()


class Source:
    def __init__(self, commune: str):
        self._commune: str = commune.strip()

    def _get_categories(self, session: requests.Session) -> dict[str, str]:
        """Map every municipality label of the drop-down to its category id."""
        r = session.get(CALENDAR_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        select = soup.find("select", attrs={"name": CATEGORY_ARG})
        if select is None:
            raise Exception("Could not find the municipality selector on the page")

        return {
            option.get_text(strip=True): option["value"]
            for option in select.find_all("option")
            if option.get("value")
        }

    def _parse_month(
        self, session: requests.Session, category: str, year: int, month: int
    ) -> list[Collection]:
        params = {CATEGORY_ARG: category, YEAR_ARG: year, MONTH_ARG: month}
        r = session.get(CALENDAR_URL, params=params, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Guard against the website ignoring the month/year arguments, which
        # would otherwise yield the same month over and over again.
        header = soup.find(id="month-header")
        expected = _normalize(f"{FRENCH_MONTHS[month - 1]} {year}")
        if header is None or expected not in _normalize(
            header.get_text(" ", strip=True)
        ):
            return []

        # The legend maps a CSS colour prefix to a human readable waste type.
        legend: dict[str, str] = {}
        for span in soup.select("#month-legend span[class*=_catheader_text]"):
            for css_class in span.get("class", []):
                if css_class.endswith("_catheader_text"):
                    label = COLLECTION_PREFIX.sub("", span.get_text(strip=True))
                    legend[css_class.removesuffix("_catheader_text")] = (
                        label[:1].upper() + label[1:]
                    )

        entries: list[Collection] = []
        for day_cell in soup.select("td.day.hasEvents"):
            classes = day_cell.get("class", [])
            if "not-current-month" in classes:
                continue
            day = int(day_cell.get_text(strip=True))

            # A single day can carry several collections, one CSS colour each.
            for css_class in classes:
                if not css_class.endswith("_catheader_bullet"):
                    continue
                colour = css_class.removesuffix("_catheader_bullet")
                if colour not in legend:
                    continue
                waste_type = legend[colour]
                entries.append(
                    Collection(
                        date=date(year, month, day),
                        t=waste_type,
                        icon=ICON_MAP.get(_normalize(waste_type), DEFAULT_ICON),
                    )
                )
        return entries

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        categories = self._get_categories(session)
        wanted = _normalize(self._commune)
        category = next(
            (
                value
                for label, value in categories.items()
                if _normalize(label) == wanted
            ),
            None,
        )
        if category is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", self._commune, sorted(categories)
            )

        today = date.today()
        entries: list[Collection] = []
        for offset in range(MONTHS_TO_FETCH):
            month_index = today.month - 1 + offset
            entries += self._parse_month(
                session, category, today.year + month_index // 12, month_index % 12 + 1
            )

        if not entries:
            raise Exception(
                f"No collection found for {self._commune}, "
                "the website layout may have changed"
            )
        return entries
