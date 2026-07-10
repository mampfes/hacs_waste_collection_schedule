import re
import unicodedata
from datetime import date

import requests
from bs4 import BeautifulSoup
from dateutil.rrule import FR, MO, MONTHLY, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Coeur d'Yvelines"
DESCRIPTION = "Source script for coeur-yvelines.fr"
URL = "https://www.coeur-yvelines.fr/"
DATA_URL = (
    "https://www.coeur-yvelines.fr/environnement/calendriers-de-collecte-des-dechets/"
)
COUNTRY = "fr"

# commune -> internal id used by the "commune" query parameter on DATA_URL
COMMUNES = {
    "Auteuil-le-Roi": 2,
    "Autouillet": 3,
    "Bazoches-sur-Guyonne": 4,
    "Behoust": 5,
    "Beynes": 1,
    "Boissy-sans-Avoir": 6,
    "Flexanville": 7,
    "Galluis": 8,
    "Gambais": 9,
    "Garancières": 10,
    "Goupillières": 11,
    "Grosrouvre": 12,
    "Jouars-Pontchartrain": 13,
    "La Queue-lez-Yvelines": 14,
    "Le Tremblay-sur-Mauldre": 15,
    "Les Mesnuls": 16,
    "Marcq": 17,
    "Mareil-le-Guyon": 18,
    "Méré": 19,
    "Millemont": 20,
    "Montfort-l'Amaury": 21,
    "Neauphle-le-Château": 22,
    "Neauphle-le-Vieux": 23,
    "Saint-Germain-de-la-Grange": 24,
    "Saint-Rémy-l'Honoré": 25,
    "Saulx-Marchais": 26,
    "Thiverval-Grignon": 27,
    "Thoiry": 28,
    "Vicq": 29,
    "Villiers-le-Mahieu": 30,
    "Villiers-Saint-Frédéric": 31,
}


def _normalize(s: str) -> str:
    """Remove accents, lower-case, and collapse separators for fuzzy matching."""
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    s = re.sub(r"[-'‘’]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


COMMUNES_NORMALIZED = {_normalize(c): c for c in COMMUNES}

EXTRA_INFO = [
    {
        "title": commune,
        "url": URL,
        "default_params": {"commune": commune},
    }
    for commune in COMMUNES
]

TEST_CASES = {commune: {"commune": commune} for commune in COMMUNES}

ICON_MAP = {
    "Déchets ménagers": Icons.GENERAL_WASTE,
    "Déchets végétaux": Icons.GARDEN,
    "Emballages et papiers": Icons.RECYCLING,
    "Encombrants": Icons.BULKY,
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
# Order in which the "jours" checkboxes are rendered on the page (Mon..Sun).
WEEKDAY_ORDER = [MO, TU, WE, TH, FR, SA, SU]

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
        "commune": "Votre commune de la Communauté de Communes Cœur d'Yvelines : "
        + ", ".join(COMMUNES)
    },
    "en": {
        "commune": "Your municipality within Coeur d'Yvelines: " + ", ".join(COMMUNES),
    },
    "de": {
        "commune": "Ihre Gemeinde in Coeur d'Yvelines: " + ", ".join(COMMUNES),
    },
}

PARAM_TRANSLATIONS = {
    "fr": {"commune": "Commune"},
    "en": {"commune": "Municipality"},
    "de": {"commune": "Gemeinde"},
}


class Source:
    def __init__(self, commune: str):
        normalized = _normalize(commune)
        canonical = COMMUNES_NORMALIZED.get(normalized)
        if canonical is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", commune, list(COMMUNES)
            )
        self.commune = canonical
        self._commune_id = COMMUNES[canonical]

    def get_parsed_source(self) -> BeautifulSoup:
        response = requests.get(DATA_URL, params={"commune": self._commune_id})
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def fetch(self) -> list[Collection]:
        soup = self.get_parsed_source()

        year = date.today().year
        heading = soup.find("h2", string=re.compile(r"Calendrier\s+\d{4}"))
        if heading:
            m = re.search(r"\d{4}", heading.get_text())
            if m:
                year = int(m.group())

        entries: list[Collection] = []
        for block in soup.select("div.semaine"):
            title_tag = block.find("h3")
            periode_tag = block.find("p", class_="periode")
            jours_div = block.find("div", class_="jours")
            if not title_tag or not periode_tag or not jours_div:
                continue

            bin_type = title_tag.get_text(strip=True)
            periode_text = periode_tag.get_text(strip=True)

            spans = jours_div.find_all("span")
            checked_weekdays = [
                WEEKDAY_ORDER[i]
                for i, span in enumerate(spans)
                if "checked" in (span.get("class") or []) and i < len(WEEKDAY_ORDER)
            ]

            for collection_date in self._dates_for_period(
                periode_text, year, checked_weekdays
            ):
                entries.append(
                    Collection(
                        date=collection_date,
                        t=bin_type,
                        icon=ICON_MAP.get(bin_type),
                    )
                )

        return entries

    @staticmethod
    def _dates_for_period(
        periode_text: str, year: int, checked_weekdays: list
    ) -> list[date]:
        normalized = _normalize(periode_text)

        # No fixed schedule: collection is arranged by online appointment.
        if "rendez vous" in normalized:
            return []

        if not checked_weekdays:
            return []

        # "Les derniers mardis des mois pairs" -> last matching weekday of
        # every even month of the year.
        if "derniers" in normalized and "mois pairs" in normalized:
            matched_weekday = None
            for name, weekday_obj in WEEKDAY_MAP.items():
                if name in normalized:
                    matched_weekday = weekday_obj
                    break
            if matched_weekday is None:
                matched_weekday = checked_weekdays[0]
            dates = []
            for month in (2, 4, 6, 8, 10, 12):
                if month == 12:
                    month_end = date(year, 12, 31)
                else:
                    month_end = date(year, month + 1, 1)
                dates.extend(
                    dt.date()
                    for dt in rrule(
                        freq=MONTHLY,
                        dtstart=date(year, month, 1),
                        until=month_end,
                        byweekday=matched_weekday,
                        bysetpos=-1,
                        count=1,
                    )
                )
            return dates

        # "Du 24 mars au 1 décembre" / "Tous les jeudis du 2 avril au 10
        # décembre" -> weekly recurrence on the checked weekday(s) within the
        # given date range.
        range_match = re.search(
            r"du\s+(\d{1,2})(?:er)?\s+([a-zàâäéèêëïîôùûüç]+)"
            r"\s+au\s+(\d{1,2})(?:er)?\s+([a-zàâäéèêëïîôùûüç]+)",
            periode_text.lower(),
        )
        if range_match:
            start_day, start_month_str, end_day, end_month_str = range_match.groups()
            start_month = MOIS_MAP.get(_normalize(start_month_str))
            end_month = MOIS_MAP.get(_normalize(end_month_str))
            if start_month and end_month:
                try:
                    start_date = date(year, start_month, int(start_day))
                    end_date = date(year, end_month, int(end_day))
                except ValueError:
                    return []
                return [
                    dt.date()
                    for dt in rrule(
                        freq=WEEKLY,
                        dtstart=start_date,
                        until=end_date,
                        byweekday=checked_weekdays,
                    )
                ]

        # Explicit one-off dates, e.g. "Les mardis 19 mai et 17 novembre",
        # "Le mardi 5 mai" or "Le 10 mars et 8 septembre".
        if re.search(r"\d", periode_text):
            dates = []
            for m in re.finditer(
                r"(\d{1,2})(?:er)?\s+([a-zàâäéèêëïîôùûüç]+)", periode_text.lower()
            ):
                month = MOIS_MAP.get(_normalize(m.group(2)))
                if month:
                    try:
                        dates.append(date(year, month, int(m.group(1))))
                    except ValueError:
                        pass
            return dates

        # "Toute l'année" and anything else unrecognized (e.g. hamlet-specific
        # exceptions) fall back to a weekly recurrence for the whole year on
        # the checked weekday(s), which reflects the schedule for the large
        # majority of residents of the commune.
        return [
            dt.date()
            for dt in rrule(
                freq=WEEKLY,
                dtstart=date(year, 1, 1),
                until=date(year, 12, 31),
                byweekday=checked_weekdays,
            )
        ]
