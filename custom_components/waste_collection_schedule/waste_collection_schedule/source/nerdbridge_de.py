import datetime
from typing import Any

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule import Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Landkreis Northeim (unofficial)"
DESCRIPTION = "Unofficial waste collection schedule for Landkreis Northeim via abfall.nerdbridge.de."
URL = "https://abfall.nerdbridge.de/"
COUNTRY = "de"

TEST_CASES: dict[str, Any] = {
    "Einbeck (Bezirk 2)": {"municipality": "Einbeck (Bezirk 2)"},
    "Bad Gandersheim": {"municipality": "Bad Gandersheim"},
    "Northeim (Bezirk 1)": {"municipality": "Northeim (Bezirk 1)"},
}

ICON_MAP = {
    "Biotonne": Icons.ORGANIC,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Glassammlung": Icons.GLASS,
    "Papiersammlung": Icons.PAPER,
    "Hausmüll": Icons.GENERAL_WASTE,
}

PARAM_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {"municipality": "Municipality"},
    "de": {"municipality": "Ortschaft"},
}

PARAM_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "en": {
        "municipality": "Name of your municipality as shown on https://abfall.nerdbridge.de/"
    },
    "de": {
        "municipality": "Name Ihrer Ortschaft, wie auf https://abfall.nerdbridge.de/ angezeigt"
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION: dict[str, str] = {
    "en": (
        "Go to https://abfall.nerdbridge.de/ and select your municipality. "
        "Use the displayed municipality name as the `municipality` parameter."
    ),
    "de": (
        "Gehen Sie zu https://abfall.nerdbridge.de/ und wählen Sie Ihre Ortschaft aus. "
        "Verwenden Sie den angezeigten Namen als `municipality`-Parameter."
    ),
}

INDEX_URL = "https://abfall.nerdbridge.de/ical/index.json"
DATA_URL = "https://abfall.nerdbridge.de/json/{year}/abfall-nom-{town_id}-{year}.json"

EXTRA_INFO = [
    {
        "title": "Abbecke",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Abbecke"},
    },
    {
        "title": "Ackenhausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Ackenhausen"},
    },
    {
        "title": "Ahlbershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Ahlbershausen"},
    },
    {
        "title": "Ahlshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Ahlshausen"},
    },
    {
        "title": "Albrechtshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Albrechtshausen"},
    },
    {
        "title": "Allershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Allershausen"},
    },
    {
        "title": "Altgandersheim",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Altgandersheim"},
    },
    {
        "title": "Amelith",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Amelith"},
    },
    {
        "title": "Amelsen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Amelsen"},
    },
    {
        "title": "Andershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Andershausen"},
    },
    {
        "title": "Angerstein",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Angerstein"},
    },
    {
        "title": "Asche",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Asche"},
    },
    {
        "title": "Avendshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Avendshausen"},
    },
    {
        "title": "Bad Gandersheim",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Bad Gandersheim"},
    },
    {
        "title": "Bartshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Bartshausen"},
    },
    {
        "title": "Behrensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Behrensen"},
    },
    {
        "title": "Bentierode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Bentierode"},
    },
    {
        "title": "Berka",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Berka"},
    },
    {
        "title": "Berwartshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Berwartshausen"},
    },
    {
        "title": "Beulshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Beulshausen"},
    },
    {
        "title": "Billerbeck",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Billerbeck"},
    },
    {
        "title": "Bishausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Bishausen"},
    },
    {
        "title": "Blankenhagen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Blankenhagen"},
    },
    {
        "title": "Bodenfelde",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Bodenfelde"},
    },
    {
        "title": "Bollensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Bollensen"},
    },
    {
        "title": "Bruchhof",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Bruchhof"},
    },
    {
        "title": "Brunsen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Brunsen"},
    },
    {
        "title": "Brunstein",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Brunstein"},
    },
    {
        "title": "Bühle",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Bühle"},
    },
    {
        "title": "Buensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Buensen"},
    },
    {
        "title": "Clus",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Clus"},
    },
    {
        "title": "Dankelsheim",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Dankelsheim"},
    },
    {
        "title": "Dannhausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Dannhausen"},
    },
    {
        "title": "Dassel",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Dassel"},
    },
    {
        "title": "Dassensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Dassensen"},
    },
    {
        "title": "Deitersen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Deitersen"},
    },
    {
        "title": "Delliehausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Delliehausen"},
    },
    {
        "title": "Denkershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Denkershausen"},
    },
    {
        "title": "Dinkelhausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Dinkelhausen"},
    },
    {
        "title": "Dögerode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Dögerode"},
    },
    {
        "title": "Dörrigsen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Dörrigsen"},
    },
    {
        "title": "Drüber",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Drüber"},
    },
    {
        "title": "Düderode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Düderode"},
    },
    {
        "title": "Eboldshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Eboldshausen"},
    },
    {
        "title": "Echte",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Echte"},
    },
    {
        "title": "Edemissen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Edemissen"},
    },
    {
        "title": "Edesheim",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Edesheim"},
    },
    {
        "title": "Eilensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Eilensen"},
    },
    {
        "title": "Einbeck (Bezirk 1)",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Einbeck (Bezirk 1)"},
    },
    {
        "title": "Einbeck (Bezirk 2)",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Einbeck (Bezirk 2)"},
    },
    {
        "title": "Ellensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Ellensen"},
    },
    {
        "title": "Ellierode (Bad Gandersheim)",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Ellierode (Bad Gandersheim)"},
    },
    {
        "title": "Ellierode (Hardegsen)",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Ellierode (Hardegsen)"},
    },
    {
        "title": "Elvershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Elvershausen"},
    },
    {
        "title": "Elvese",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Elvese"},
    },
    {
        "title": "Erichsburg",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Erichsburg"},
    },
    {
        "title": "Ertinghausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Ertinghausen"},
    },
    {
        "title": "Erzhausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Erzhausen"},
    },
    {
        "title": "Eschershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Eschershausen"},
    },
    {
        "title": "Espol",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Espol"},
    },
    {
        "title": "Fredelsloh",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Fredelsloh"},
    },
    {
        "title": "Fürstenhagen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Fürstenhagen"},
    },
    {
        "title": "Garlebsen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Garlebsen"},
    },
    {
        "title": "Gehrenrode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Gehrenrode"},
    },
    {
        "title": "Gierswalde",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Gierswalde"},
    },
    {
        "title": "Gillersheim",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Gillersheim"},
    },
    {
        "title": "Gladebeck",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Gladebeck"},
    },
    {
        "title": "Goseplack",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Goseplack"},
    },
    {
        "title": "Greene",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Greene"},
    },
    {
        "title": "Gremsheim",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Gremsheim"},
    },
    {
        "title": "Großenrode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Großenrode"},
    },
    {
        "title": "Gut Pinkler",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Gut Pinkler"},
    },
    {
        "title": "Hachenhausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hachenhausen"},
    },
    {
        "title": "Haieshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Haieshausen"},
    },
    {
        "title": "Hallensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hallensen"},
    },
    {
        "title": "Hammenstedt",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hammenstedt"},
    },
    {
        "title": "Hardegsen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hardegsen"},
    },
    {
        "title": "Harriehausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Harriehausen"},
    },
    {
        "title": "Heckenbeck",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Heckenbeck"},
    },
    {
        "title": "Helmscherode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Helmscherode"},
    },
    {
        "title": "Hettensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hettensen"},
    },
    {
        "title": "Hevensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hevensen"},
    },
    {
        "title": "Hillerse",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hillerse"},
    },
    {
        "title": "Hilprechtshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hilprechtshausen"},
    },
    {
        "title": "Hilwartshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hilwartshausen"},
    },
    {
        "title": "Höckelheim",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Höckelheim"},
    },
    {
        "title": "Hohnstedt",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hohnstedt"},
    },
    {
        "title": "Hollenstedt",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hollenstedt"},
    },
    {
        "title": "Holtensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Holtensen"},
    },
    {
        "title": "Holtershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Holtershausen"},
    },
    {
        "title": "Hoppensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hoppensen"},
    },
    {
        "title": "Hullersen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hullersen"},
    },
    {
        "title": "Hunnesrück",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Hunnesrück"},
    },
    {
        "title": "Iber",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Iber"},
    },
    {
        "title": "Imbshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Imbshausen"},
    },
    {
        "title": "Immensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Immensen"},
    },
    {
        "title": "Ippensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Ippensen"},
    },
    {
        "title": "Juliusmühle",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Juliusmühle"},
    },
    {
        "title": "Kalefeld",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Kalefeld"},
    },
    {
        "title": "Kammerborn",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Kammerborn"},
    },
    {
        "title": "Katlenburg",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Katlenburg"},
    },
    {
        "title": "Kirchberg",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Kirchberg"},
    },
    {
        "title": "Kohnsen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Kohnsen"},
    },
    {
        "title": "Kreiensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Kreiensen"},
    },
    {
        "title": "Krimmensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Krimmensen"},
    },
    {
        "title": "Kuventhal",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Kuventhal"},
    },
    {
        "title": "Lagershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Lagershausen"},
    },
    {
        "title": "Langenholtensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Langenholtensen"},
    },
    {
        "title": "Lauenberg",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Lauenberg"},
    },
    {
        "title": "Leinetal",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Leinetal"},
    },
    {
        "title": "Levershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Levershausen"},
    },
    {
        "title": "Lichtenborn",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Lichtenborn"},
    },
    {
        "title": "Lindau",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Lindau"},
    },
    {
        "title": "Lütgenrode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Lütgenrode"},
    },
    {
        "title": "Lüthorst",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Lüthorst"},
    },
    {
        "title": "Lutterbeck",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Lutterbeck"},
    },
    {
        "title": "Lutterhausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Lutterhausen"},
    },
    {
        "title": "Mackensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Mackensen"},
    },
    {
        "title": "Markoldendorf",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Markoldendorf"},
    },
    {
        "title": "Moringen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Moringen"},
    },
    {
        "title": "Müllershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Müllershausen"},
    },
    {
        "title": "Naensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Naensen"},
    },
    {
        "title": "Negenborn",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Negenborn"},
    },
    {
        "title": "Nienhagen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Nienhagen"},
    },
    {
        "title": "Nienover",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Nienover"},
    },
    {
        "title": "Nörten-Hardenberg",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Nörten-Hardenberg"},
    },
    {
        "title": "Northeim (Bezirk 1)",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Northeim (Bezirk 1)"},
    },
    {
        "title": "Northeim (Bezirk 2)",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Northeim (Bezirk 2)"},
    },
    {
        "title": "Odagsen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Odagsen"},
    },
    {
        "title": "Offensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Offensen"},
    },
    {
        "title": "Oldenrode (Kalefeld)",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Oldenrode (Kalefeld)"},
    },
    {
        "title": "Oldenrode (Moringen)",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Oldenrode (Moringen)"},
    },
    {
        "title": "Oldershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Oldershausen"},
    },
    {
        "title": "Olxheim",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Olxheim"},
    },
    {
        "title": "Opperhausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Opperhausen"},
    },
    {
        "title": "Orxhausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Orxhausen"},
    },
    {
        "title": "Osterbruch",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Osterbruch"},
    },
    {
        "title": "Parensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Parensen"},
    },
    {
        "title": "Polier",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Polier"},
    },
    {
        "title": "Portenhagen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Portenhagen"},
    },
    {
        "title": "Relliehausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Relliehausen"},
    },
    {
        "title": "Rengershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Rengershausen"},
    },
    {
        "title": "Rimmerode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Rimmerode"},
    },
    {
        "title": "Rittierode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Rittierode"},
    },
    {
        "title": "Rosenplänter",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Rosenplänter"},
    },
    {
        "title": "Rotenkirchen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Rotenkirchen"},
    },
    {
        "title": "Salzderhelden",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Salzderhelden"},
    },
    {
        "title": "Schachtenbeck",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Schachtenbeck"},
    },
    {
        "title": "Schlarpe",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Schlarpe"},
    },
    {
        "title": "Schnedinghausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Schnedinghausen"},
    },
    {
        "title": "Schönhagen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Schönhagen"},
    },
    {
        "title": "Schoningen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Schoningen"},
    },
    {
        "title": "Sebexen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Sebexen"},
    },
    {
        "title": "Seboldshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Seboldshausen"},
    },
    {
        "title": "Sievershausen (Dassel)",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Sievershausen (Dassel)"},
    },
    {
        "title": "Sievershausen (Einbeck)",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Sievershausen (Einbeck)"},
    },
    {
        "title": "Sohlingen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Sohlingen"},
    },
    {
        "title": "Stöckheim",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Stöckheim"},
    },
    {
        "title": "Strodthagen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Strodthagen"},
    },
    {
        "title": "Stroit",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Stroit"},
    },
    {
        "title": "Sudershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Sudershausen"},
    },
    {
        "title": "Sudheim",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Sudheim"},
    },
    {
        "title": "Sülbeck",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Sülbeck"},
    },
    {
        "title": "Suterode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Suterode"},
    },
    {
        "title": "Thüdinghausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Thüdinghausen"},
    },
    {
        "title": "Tönnieshof",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Tönnieshof"},
    },
    {
        "title": "Trögen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Trögen"},
    },
    {
        "title": "Üssinghausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Üssinghausen"},
    },
    {
        "title": "Uslar",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Uslar"},
    },
    {
        "title": "Vahle",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Vahle"},
    },
    {
        "title": "Vardeilsen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Vardeilsen"},
    },
    {
        "title": "Verliehausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Verliehausen"},
    },
    {
        "title": "Vogelbeck",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Vogelbeck"},
    },
    {
        "title": "Voldagsen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Voldagsen"},
    },
    {
        "title": "Volksen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Volksen"},
    },
    {
        "title": "Volpriehausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Volpriehausen"},
    },
    {
        "title": "Vorwerk Holtensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Vorwerk Holtensen"},
    },
    {
        "title": "Wachenhausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Wachenhausen"},
    },
    {
        "title": "Wahmbeck",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Wahmbeck"},
    },
    {
        "title": "Weddehagen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Weddehagen"},
    },
    {
        "title": "Wellersen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Wellersen"},
    },
    {
        "title": "Wenzen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Wenzen"},
    },
    {
        "title": "Westerhof",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Westerhof"},
    },
    {
        "title": "Wetze",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Wetze"},
    },
    {
        "title": "Wiebrechtshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Wiebrechtshausen"},
    },
    {
        "title": "Wiensen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Wiensen"},
    },
    {
        "title": "Wiershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Wiershausen"},
    },
    {
        "title": "Willershausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Willershausen"},
    },
    {
        "title": "Wolbrechtshausen",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Wolbrechtshausen"},
    },
    {
        "title": "Wolperode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Wolperode"},
    },
    {
        "title": "Wrescherode",
        "url": "https://abfall.nerdbridge.de/",
        "country": "de",
        "default_params": {"municipality": "Wrescherode"},
    },
]


class Source:
    def __init__(self, municipality: str) -> None:
        self._municipality = municipality

    def fetch(self) -> list[Collection]:
        # Fetch the town index to get the id for the requested municipality
        resp = requests.get(INDEX_URL)
        resp.raise_for_status()
        index = resp.json()

        name_to_id: dict[str, str] = {t["name"]: t["id"] for t in index["towns"]}

        if self._municipality not in name_to_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality",
                self._municipality,
                suggestions=list(name_to_id.keys()),
            )

        town_id = name_to_id[self._municipality]
        available_years: list[int] = index.get("years", [])

        today = datetime.date.today()
        years_to_fetch = [today.year]
        if today.year + 1 in available_years:
            years_to_fetch.append(today.year + 1)

        entries: list[Collection] = []
        for year in years_to_fetch:
            url = DATA_URL.format(year=year, town_id=town_id)
            r = requests.get(url)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            data = r.json()

            for item in data.get("dates", []):
                date_str: str = item["date"]
                waste_type: str = item["name"]

                # Parse ISO 8601 date (may include timezone offset)
                dt = datetime.datetime.fromisoformat(date_str)
                collection_date = dt.date()

                icon = None
                for key, val in ICON_MAP.items():
                    if key in waste_type:
                        icon = val
                        break

                entries.append(
                    Collection(date=collection_date, t=waste_type, icon=icon)
                )

        return entries
