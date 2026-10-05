from datetime import date
from unittest.mock import Mock

from waste_collection_schedule.source.nice_cotedazur_fr import Source

HTML = """<div class='collecte--block commune'><h2 class='entry-title'>Nice</h2><div class='entry-content'>Collecte des ordures ménagères : lundi et jeudi. Collecte sélective : mercredi.</div></div>"""


def test_nice_fixed_days():
    source = Source({"municipality": "Nice"})
    source._start_date, source._end_date = date(2026, 10, 5), date(2026, 10, 11)
    source._request = Mock()
    source._request.get.return_value.text = HTML
    source._request.get.return_value.raise_for_status = Mock()
    result = source.fetch()
    assert [item.date for item in result] == [date(2026, 10, 5), date(2026, 10, 8)]


def test_phase_one_excludes_alternating_municipalities():
    source = Source({"municipality": "Bairols"})
    source._request = Mock()
    source._request.get.return_value.text = "<div class='collecte--block commune'><h2 class='entry-title'>Bairols</h2><div class='entry-content'>mercredi, en alternance</div></div>"
    source._request.get.return_value.raise_for_status = Mock()
    source._start_date, source._end_date = date(2026, 10, 5), date(2026, 10, 11)
    assert source.fetch() == []
