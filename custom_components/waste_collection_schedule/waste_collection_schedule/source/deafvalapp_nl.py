"""De Afvalapp (deafvalapp.nl), used by several Dutch municipalities.

Demonstrates ``IcsSessionRetriever`` for the stateful "submit the address, then
read the calendar back" shape, with ``argument`` blaming the postcode when the
calendar request fails: the first request creates a server-side session tied to
the address (the site always answers it with a redirect, valid address or not),
and the calendar download that follows reads that session. An address the site
cannot resolve makes the *download* answer HTTP 500 ("sessie ongeldig"), so the
failure that names the address is the calendar request's.

The calendar is a rolling window rather than a per-year one, hence
``lookahead_month=None``.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.deafvalapp.nl"
_SESSION_URL = f"{_URL}/calendar/kalender_sessie.jsp"
_ICS_URL = f"{_URL}/calendar/afvalkalender.ics"

# The municipalities served through De Afvalapp: one structure, one listing each.
_MUNICIPALITIES = ("Helmond", "Land van Cuijk", "Boekel", "Maashorst")


def _address_session(
    postcode: str,
    house_number: str,
    house_number_addition: str | None = None,
    **_,
) -> "dict[str, str]":
    return {
        "land": "NL",
        "postcode": postcode.replace(" ", "").upper(),
        "huisnr": house_number,
        "huisnrtoev": (house_number_addition or "").strip(),
    }


@final
class Source(BaseSource):
    TITLE = "De Afvalapp"
    DESCRIPTION = (
        "Source for De Afvalapp, used by several Dutch municipalities "
        "(e.g. Helmond, Land van Cuijk, Boekel, Maashorst)."
    )
    URL = _URL
    COUNTRY = "nl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Maashorst": {"postcode": "5406XP", "house_number": "9"},
        "Helmond": {"postcode": "5701NC", "house_number": 1},
    }

    # The site answers an address it cannot resolve with HTTP 500.
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"postcode": "0000AA", "house_number": "1"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter the same postcode, house number and (optional) house number "
            "addition that you would use at https://www.deafvalapp.nl to look up "
            "your waste collection calendar."
        ),
        "de": (
            "Geben Sie dieselbe Postleitzahl, Hausnummer und (optional) den "
            "Hausnummernzusatz ein, die Sie auch unter https://www.deafvalapp.nl "
            "verwenden würden, um Ihren Abfallkalender abzurufen."
        ),
        "fr": (
            "Saisissez le même code postal, numéro de maison et (facultatif) "
            "complément de numéro que vous utiliseriez sur "
            "https://www.deafvalapp.nl pour consulter votre calendrier de "
            "collecte des déchets."
        ),
        "it": (
            "Inserisci lo stesso CAP, numero civico e (facoltativo) estensione "
            "del numero civico che utilizzeresti su https://www.deafvalapp.nl "
            "per consultare il tuo calendario di raccolta rifiuti."
        ),
    }

    REGIONS = tuple(region(name, url=_URL) for name in _MUNICIPALITIES)

    PARAMS = (
        postcode(postcode_field="postcode", house_field="house_number"),
        text_field("house_number_addition", "House number addition", optional=True),
    )

    retrieve = IcsSessionRetriever(
        steps=[{"url": _SESSION_URL, "params": _address_session}],
        feed_url=_ICS_URL,
        encoding="utf-8",
        lookahead_month=None,
        argument="postcode",
        argument_message=("please check the postcode and house number and try again."),
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer(
        type_value_map={
            "Rest": wt.GENERAL_WASTE,
            "Restafval": wt.GENERAL_WASTE,
            "Gft+e": wt.ORGANIC,
            "GFT": wt.ORGANIC,
            "Papier": wt.PAPER,
            "PBD": wt.RECYCLABLES,
            "PMD": wt.RECYCLABLES,
            "Kerstboom": wt.OTHER,
            "Mobiele Milieustraat": wt.OTHER,
            "Repair Café": wt.OTHER,
        }
    )
