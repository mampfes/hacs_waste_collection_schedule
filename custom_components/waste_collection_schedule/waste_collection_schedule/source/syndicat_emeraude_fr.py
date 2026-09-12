"""
Syndicat Emeraude (France)

Initial implementation.
"""

import re
import unicodedata
from datetime import date

from dateutil.rrule import FR, MO, MONTHLY, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Syndicat Emeraude (95)"  # Title will show up in README.md and info.md
DESCRIPTION = "Source for 'Syndicat Emeraude' (France)"  # Describe your source
URL = "https://www.syndicat-emeraude.fr/"  # Insert url to service homepage. URL will show up in README.md and info.md
DATA_URL = "https://www.syndicat-emeraude.fr/collecte"  # url used to retrieve data
COUNTRY = "fr"

SOURCE_CODEOWNERS = ["@NightFlowed"]

COMMUNES = [
    "andilly",
    "deuil-la-barre",
    "eaubonne",
    "enghien-les-bains",
    "ermont",
    "franconville",
    "groslay",
    "le-plessis-bouchard",
    "margency",
    "montigny",
    "montlignon",
    "montmagny",
    "montmorency",
    "saint-prix",
    "saint-gratien",
    "sannois",
    "soisy-sous-montmorency",
]

SECTORS = [
    "pavillons",
    "collectifs",
    "ville",
    "hypercentre",
]


def _normalize_name(s: str) -> str:
    """Remove accents, uppercase, and collapse separators for fuzzy name matching."""
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    s = re.sub("[-'‘’]", " ", s.upper())
    return re.sub(r"\s+", " ", s).strip()


COMMUNES_NORMALIZED = {_normalize_name(c): c for c in COMMUNES}
SECTORS_NORMALIZED = {_normalize_name(s): s for s in SECTORS}

EXTRA_INFO = [
    {
        "title": city,
        "url": DATA_URL,
        "default_params": {"commune": city},
    }
    for city in COMMUNES
]

PARAM_TRANSLATIONS = {
    "fr": {
        "commune": "Nom de la commune",
        "sector": "Secteur",
    },
    "en": {
        "commune": "Commune name",
        "sector": "Sector",
    },
    "nl": {
        "commune": "Naam van de gemeente",
        "sector": "Sector",
    },
    "it": {
        "commune": "Nome del comune",
        "sector": "Settore",
    },
}

PARAM_DESCRIPTIONS = {
    "fr": {
        "commune": "Nom de la commune : " + ", ".join(COMMUNES),
        "sector": "Secteur de la commune : " + ", ".join(SECTORS),
    },
    "en": {
        "commune": "Commune name: " + ", ".join(COMMUNES),
        "sector": "Sector of the commune: " + ", ".join(SECTORS),
    },
    "nl": {
        "commune": "Naam van de gemeente: " + ", ".join(COMMUNES),
        "sector": "Sector van de gemeente: " + ", ".join(SECTORS),
    },
    "it": {
        "commune": "Nome del comune: " + ", ".join(COMMUNES),
        "sector": "Settore del comune: " + ", ".join(SECTORS),
    },
}


_WEEKDAYS = {
    "MO": MO,
    "TU": TU,
    "WE": WE,
    "TH": TH,
    "FR": FR,
    "SA": SA,
    "SU": SU,
}

_WEEKDAYS.update(
    {
        "LU": MO,
        "MA": TU,
        "ME": WE,
        "JE": TH,
        "VE": FR,
        "SA": SA,
        "DI": SU,
    }
)

ICON_MAP = {
    "Ordures ménagères": Icons.GENERAL_WASTE,
    "Papiers/Emballages": Icons.RECYCLING,
    "Verre": Icons.GLASS,
    "Végétaux": Icons.GARDEN,
    "Encombrants": Icons.BULKY,
}

# ------------------------- Generate Rules ---------------------------


class Rule:
    def generate(self, start: date, end: date):
        raise NotImplementedError


class WeeklyRule(Rule):
    def __init__(self, weekday: str, months=None):
        self.weekday = weekday
        self.months = months

    def generate(self, start, end):
        kwargs = {
            "freq": WEEKLY,
            "dtstart": start,
            "until": end,
            "byweekday": _WEEKDAYS[self.weekday],
        }
        if self.months:
            kwargs["bymonth"] = self.months
        return [d.date() for d in rrule(**kwargs)]


class MonthlyRule(Rule):
    def __init__(self, weekday: str, nth: int, months=None):
        self.weekday = weekday
        self.nth = nth
        self.months = months

    def generate(self, start, end):
        kwargs = {
            "freq": MONTHLY,
            "dtstart": start,
            "until": end,
            "byweekday": _WEEKDAYS[self.weekday](self.nth),
        }
        if self.months:
            kwargs["bymonth"] = self.months
        return [d.date() for d in rrule(**kwargs)]


class MidMonthlyRule(Rule):
    def __init__(self, weekday: str, months=None):
        self.weekday = weekday
        self.months = months

    def generate(self, start, end):
        kwargs = {
            "freq": MONTHLY,
            "dtstart": start,
            "until": end,
            "byweekday": _WEEKDAYS[self.weekday],
        }

        if self.months:
            kwargs["bymonth"] = self.months

        days = list(rrule(**kwargs))

        by_month = {}
        for d in days:
            by_month.setdefault((d.year, d.month), []).append(d)

        result = []
        for (y, m), values in by_month.items():
            mid = date(y, m, 15)
            best = min(values, key=lambda d: abs((d.date() - mid).days))
            result.append(best.date())

        return sorted(result)


# ------------------------- RULES for each commune and sector ---------------------------

ANDILLY = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("ME")],
        "Verre": [MonthlyRule("LU", 2)],
        "Encombrants": [MonthlyRule("ME", 4, months=[4, 9, 12])],
        "Végétaux": [
            WeeklyRule("ME", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("ME", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("LU"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("ME")],
        "Verre": [MonthlyRule("LU", 2)],
        "Encombrants": [MonthlyRule("ME", 4, months=[4, 9, 12])],
    },
}

DEUIL_LA_BARRE = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("JE")],
        "Papiers/Emballages": [WeeklyRule("VE")],
        "Verre": [MonthlyRule("VE", 3)],
        "Encombrants": [MonthlyRule("ME", 1)],
        "Végétaux": [
            WeeklyRule("ME", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("ME", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("MA"), WeeklyRule("SA")],
        "Papiers/Emballages": [WeeklyRule("VE")],
        "Verre": [MonthlyRule("VE", 3)],
        "Encombrants": [MonthlyRule("ME", 1)],
    },
}

EAUBONNE = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("LU")],
        "Papiers/Emballages": [WeeklyRule("VE")],
        "Verre": [MonthlyRule("LU", 1)],
        "Encombrants": [MonthlyRule("ME", 2)],
        "Végétaux": [
            WeeklyRule("MA", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("MA", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("LU"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("VE")],
        "Verre": [MonthlyRule("LU", 1)],
        "Encombrants": [MonthlyRule("ME", 2)],
    },
}

ENGHIEN_LES_BAINS = {
    "ville": {
        "Ordures ménagères": [WeeklyRule("LU"), WeeklyRule("ME"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("ME")],
        "Verre": [WeeklyRule("ME")],
        "Encombrants": [MonthlyRule("ME", 4)],
        "Végétaux": [],
    },
    "hypercentre": {
        "Ordures ménagères": [
            WeeklyRule("LU"),
            WeeklyRule("MA"),
            WeeklyRule("ME"),
            WeeklyRule("JE"),
            WeeklyRule("VE"),
            WeeklyRule("SA"),
        ],
        "Papiers/Emballages": [WeeklyRule("ME")],
        "Verre": [WeeklyRule("ME")],
        "Encombrants": [MonthlyRule("ME", 4)],
    },
}

ERMONT = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("MA")],
        "Papiers/Emballages": [WeeklyRule("JE")],
        "Verre": [MonthlyRule("VE", 4)],
        "Encombrants": [MonthlyRule("ME", 2)],
        "Végétaux": [WeeklyRule("LU")],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("MA"), WeeklyRule("SA")],
        "Papiers/Emballages": [WeeklyRule("JE")],
        "Verre": [MonthlyRule("VE", 4)],
        "Encombrants": [MonthlyRule("ME", 2)],
    },
}

FRANCONVILLE = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("JE")],
        "Verre": [MonthlyRule("VE", 1)],
        "Encombrants": [
            MonthlyRule("ME", -1, months=[4, 7, 9, 12]),
            MonthlyRule("LU", 1, months=[2]),
        ],
        "Végétaux": [
            WeeklyRule("LU", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("LU", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("LU"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("JE")],
        "Verre": [MonthlyRule("VE", 1)],
        "Encombrants": [MonthlyRule("ME", 3)],
    },
}

GROSLAY = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("LU")],
        "Papiers/Emballages": [WeeklyRule("JE")],
        "Verre": [MonthlyRule("LU", 1)],
        "Encombrants": [MonthlyRule("ME", 3)],
        "Végétaux": [
            WeeklyRule("LU", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("LU", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("LU"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("JE")],
        "Verre": [MonthlyRule("LU", 1)],
        "Encombrants": [MonthlyRule("ME", 3)],
    },
}

LE_PLESSIS_BOUCHARD = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("JE")],
        "Papiers/Emballages": [WeeklyRule("JE")],
        "Verre": [MonthlyRule("LU", 3)],
        "Encombrants": [MonthlyRule("ME", -1, months=[4, 7, 9, 12])],
        "Végétaux": [
            WeeklyRule("JE", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("JE", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("LU"), WeeklyRule("JE")],
        "Papiers/Emballages": [WeeklyRule("JE")],
        "Verre": [MonthlyRule("LU", 3)],
        "Encombrants": [MonthlyRule("ME", -1, months=[4, 7, 9, 12])],
    },
}

MARGENCY = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("ME")],
        "Verre": [MonthlyRule("LU", 2)],
        "Encombrants": [MonthlyRule("VE", 3)],
        "Végétaux": [
            WeeklyRule("ME", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("ME", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("LU"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("ME")],
        "Verre": [MonthlyRule("LU", 2)],
        "Encombrants": [MonthlyRule("VE", 3)],
    },
}

MONTIGNY = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("SA")],
        "Papiers/Emballages": [WeeklyRule("LU")],
        "Verre": [MonthlyRule("LU", 3)],
        "Encombrants": [MonthlyRule("ME", -1, months=[4, 7, 9, 12])],
        "Végétaux": [
            WeeklyRule("LU", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("LU", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("LU"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("LU")],
        "Verre": [MonthlyRule("LU", 3)],
        "Encombrants": [MonthlyRule("ME", 4)],
    },
}

MONTLIGNON = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("LU"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("ME")],
        "Verre": [WeeklyRule("ME")],
        "Encombrants": [MonthlyRule("VE", 3)],
        "Végétaux": [
            WeeklyRule("MA", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("MA", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("LU"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("ME")],
        "Verre": [WeeklyRule("ME")],
        "Encombrants": [MonthlyRule("VE", 3)],
    },
}

MONTMAGNY = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("VE")],
        "Verre": [MonthlyRule("VE", 4)],
        "Encombrants": [MonthlyRule("ME", 2)],
        "Végétaux": [
            WeeklyRule("LU", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("LU", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("LU"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("VE")],
        "Verre": [MonthlyRule("VE", 4)],
        "Encombrants": [MonthlyRule("ME", 2)],
    },
}

MONTMORENCY = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("MA")],
        "Papiers/Emballages": [WeeklyRule("ME")],
        "Verre": [MonthlyRule("VE", 2)],
        "Encombrants": [MonthlyRule("ME", 4)],
        "Végétaux": [
            WeeklyRule("LU", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("LU", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("MA"), WeeklyRule("SA")],
        "Papiers/Emballages": [WeeklyRule("ME")],
        "Verre": [MonthlyRule("VE", 2)],
        "Encombrants": [MonthlyRule("ME", 4)],
    },
}

SAINT_PRIX = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("MA")],
        "Verre": [MonthlyRule("LU", 3)],
        "Encombrants": [MonthlyRule("LU", -1, months=[3, 6, 8, 11])],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("MA"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("MA")],
        "Verre": [MonthlyRule("LU", 3)],
        "Encombrants": [MonthlyRule("LU", -1, months=[3, 6, 8, 11])],
    },
}

SAINT_GRATIEN = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("MA")],
        "Papiers/Emballages": [WeeklyRule("JE")],
        "Verre": [MonthlyRule("LU", 4)],
        "Encombrants": [MonthlyRule("ME", 4)],
        "Végétaux": [
            WeeklyRule("VE", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("VE", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("MA")],
        "Papiers/Emballages": [WeeklyRule("JE")],
        "Verre": [MonthlyRule("LU", 4)],
        "Encombrants": [MonthlyRule("ME", 4)],
    },
}

SANNOIS = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("JE")],
        "Papiers/Emballages": [WeeklyRule("MA")],
        "Verre": [MonthlyRule("LU", 2)],
        "Encombrants": [MonthlyRule("ME", 1)],
        "Végétaux": [
            WeeklyRule("MA", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("MA", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("MA"), WeeklyRule("SA")],
        "Papiers/Emballages": [WeeklyRule("MA")],
        "Verre": [MonthlyRule("LU", 2)],
        "Encombrants": [MonthlyRule("ME", 1)],
    },
}

SOISY_SOUS_MONTMORENCY = {
    "pavillons": {
        "Ordures ménagères": [WeeklyRule("MA")],
        "Papiers/Emballages": [WeeklyRule("MA")],
        "Verre": [MonthlyRule("LU", 4)],
        "Encombrants": [MonthlyRule("ME", 3)],
        "Végétaux": [
            WeeklyRule("LU", months=[1, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            MidMonthlyRule("LU", months=[2, 12]),
        ],
    },
    "collectifs": {
        "Ordures ménagères": [WeeklyRule("MA"), WeeklyRule("VE")],
        "Papiers/Emballages": [WeeklyRule("MA")],
        "Verre": [MonthlyRule("LU", 4)],
        "Encombrants": [MonthlyRule("ME", 3)],
    },
}


RULES = {
    "andilly": ANDILLY,
    "deuil-la-barre": DEUIL_LA_BARRE,
    "eaubonne": EAUBONNE,
    "enghien-les-bains": ENGHIEN_LES_BAINS,
    "ermont": ERMONT,
    "franconville": FRANCONVILLE,
    "groslay": GROSLAY,
    "le-plessis-bouchard": LE_PLESSIS_BOUCHARD,
    "margency": MARGENCY,
    "montigny": MONTIGNY,
    "montlignon": MONTLIGNON,
    "montmagny": MONTMAGNY,
    "montmorency": MONTMORENCY,
    "saint-prix": SAINT_PRIX,
    "saint-gratien": SAINT_GRATIEN,
    "sannois": SANNOIS,
    "soisy-sous-montmorency": SOISY_SOUS_MONTMORENCY,
}

TEST_CASES = {
    f"{commune.upper()}_{sector.upper()}": {
        "commune": commune,
        "sector": sector,
    }
    for commune, sectors in RULES.items()
    for sector in sectors
}

# ------------------------- Source class ---------------------------


class Source:
    def __init__(self, commune: str, sector: str = "pavillons"):

        commune = COMMUNES_NORMALIZED.get(_normalize_name(commune), commune)
        sector = SECTORS_NORMALIZED.get(_normalize_name(sector), sector)

        if not isinstance(commune, str):
            raise SourceArgumentNotFoundWithSuggestions("Commune", commune, COMMUNES)
        if not isinstance(sector, str):
            raise SourceArgumentNotFoundWithSuggestions("Sector", sector, SECTORS)

        if commune not in RULES:
            raise SourceArgumentNotFoundWithSuggestions(
                "Commune", commune, sorted(RULES)
            )

        if sector not in RULES[commune]:
            raise SourceArgumentNotFoundWithSuggestions(
                "Sector", sector, sorted(RULES[commune])
            )

        self._rules = RULES[commune][sector]

    def fetch(self):
        start = date(date.today().year, 1, 1)
        # there is not really a limit, but we will limit to 1 year in the future
        end = date(date.today().year + 1, 12, 31)
        collections = []
        seen = set()
        for waste_type, rules in self._rules.items():
            for rule in rules:
                for d in rule.generate(start, end):
                    # Multiple collections on the same day are supported by using (date, waste_type) as key
                    key = (d, waste_type)
                    if key not in seen:
                        seen.add(key)
                        collections.append(
                            Collection(
                                d,
                                waste_type,
                                ICON_MAP.get(waste_type, Icons.NO_COLLECTION),
                            )
                        )
        collections.sort(key=lambda c: c.date)
        return collections
