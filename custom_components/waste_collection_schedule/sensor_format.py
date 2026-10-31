"""Semantic state/date rendering without generating Jinja templates."""

from datetime import date
from functools import cache

from babel.dates import format_date

from .sensor_model import LANGUAGES

_TEXT = {
    "en": ("Today", "Tomorrow", "in {n} days", "{types} in {n} days", "on {date}"),
    "de": ("Heute", "Morgen", "in {n} Tagen", "{types} in {n} Tagen", "am {date}"),
    "fr": (
        "Aujourd'hui",
        "Demain",
        "dans {n} jours",
        "{types} dans {n} jours",
        "le {date}",
    ),
    "it": ("Oggi", "Domani", "tra {n} giorni", "{types} tra {n} giorni", "il {date}"),
    "nl": (
        "Vandaag",
        "Morgen",
        "over {n} dagen",
        "{types} over {n} dagen",
        "op {date}",
    ),
    "sl": ("Danes", "Jutri", "čez {n} dni", "{types} čez {n} dni", "{date}"),
    "da": ("I dag", "I morgen", "om {n} dage", "{types} om {n} dage", "den {date}"),
    "fi": (
        "Tänään",
        "Huomenna",
        "{n} päivän kuluttua",
        "{types} {n} päivän kuluttua",
        "{date}",
    ),
    "sv": ("I dag", "I morgon", "om {n} dagar", "{types} om {n} dagar", "den {date}"),
    "nb": ("I dag", "I morgen", "om {n} dager", "{types} om {n} dager", "den {date}"),
}
_DATES = {
    "dmy": "dd.MM.yyyy",
    "weekday_dmy": "EEE, dd.MM.yyyy",
    "mdy": "MM/dd/yyyy",
    "weekday_mdy": "EEE, MM/dd/yyyy",
    "iso": "yyyy-MM-dd",
    "weekday_iso": "EEE, yyyy-MM-dd",
}


def language_for(language: str, ha_language: str) -> str:
    language = ha_language if language == "auto" else language
    base = language.replace("-", "_").split("_")[0].lower()
    return base if base in LANGUAGES and base != "auto" else "en"


def render_date(value, style: str, language: str) -> str:
    if style == "iso":
        return value.isoformat()
    return format_date(value, _DATES[style], locale=language)


@cache
def _prepare_locales():
    for language in LANGUAGES:
        if language != "auto":
            format_date(date(2000, 1, 1), _DATES["weekday_iso"], locale=language)


async def async_prepare_formats(hass):
    """Load Babel's locale data off HA's event loop before rendering callbacks."""
    await hass.async_add_executor_job(_prepare_locales)


def render_state(
    collection, style: str, date_style: str, language: str, separator: str
):
    today, tomorrow, countdown, types_countdown, dated = _TEXT[language]
    values = {"n": collection.daysTo, "types": separator.join(collection.types)}
    if style == "relative":
        return (
            today
            if values["n"] == 0
            else tomorrow
            if values["n"] == 1
            else countdown.format(**values)
        )
    if style == "days":
        return str(values["n"])
    if style == "types":
        return values["types"]
    if style == "date":
        return dated.format(date=render_date(collection.date, date_style, language))
    return (countdown if style == "in_days" else types_countdown).format(**values)
