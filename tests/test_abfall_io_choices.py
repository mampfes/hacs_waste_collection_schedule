from __future__ import annotations

from bs4 import BeautifulSoup

from custom_components.waste_collection_schedule.waste_collection_schedule.service.AbfallIO import (
    _select_options,
)


def test_select_options_skip_the_form_prompt() -> None:
    """The first <option> is the form's prompt, not a choice (#7489)."""
    soup = BeautifulSoup(
        '<select name="f_id_kommune">'
        '<option value="0">Bitte auswählen...</option>'
        '<option value="2593">Altenberge</option>'
        '<option value="2592">Emsdetten</option>'
        "</select>",
        "html.parser",
    )

    assert _select_options(soup, "f_id_kommune") == [
        ("Altenberge", "2593"),
        ("Emsdetten", "2592"),
    ]


def test_select_options_still_skip_empty_and_minus_one() -> None:
    soup = BeautifulSoup(
        '<select name="f_id_strasse">'
        '<option value="">Leer</option>'
        '<option value="-1">Keine Auswahl</option>'
        '<option value="183730">Alte Ziegelei</option>'
        "</select>",
        "html.parser",
    )

    assert _select_options(soup, "f_id_strasse") == [("Alte Ziegelei", "183730")]
