import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(
    str(Path(__file__).parents[1] / "custom_components" / "waste_collection_schedule")
)

from waste_collection_schedule.source import swale_gov_uk


class Response:
    def __init__(self, html: str, url: str = "https://swale.gov.uk/check-your-bin-day"):
        self.content = html.encode()
        self.url = url

    def raise_for_status(self) -> None:
        return None


class Session:
    def __init__(self, responses: list[Response]):
        self.responses = iter(responses)
        self.calls: list[tuple[str, str, dict[str, str] | None]] = []

    def get(self, url: str, params=None):
        self.calls.append(("get", url, params))
        return next(self.responses)

    def post(self, url: str, data=None):
        self.calls.append(("post", url, data))
        return next(self.responses)


INITIAL_FORM = """
<html><input type="hidden" name="token" value="token-one">
<form action="/lookup" method="post">
  <input type="hidden" name="SQ_FORM_999_PAGE" value="1">
  <input type="hidden" name="state" value="first-state">
  <label for="postcode">Enter your postcode</label>
  <input id="postcode" name="q999:q1">
  <input type="submit" name="submit_999" value="Choose Your Address">
</form></html>
"""

UPRN_FORM = """
<html><input type="hidden" name="token" value="token-two">
<form action="/lookup" method="post">
  <input type="hidden" name="SQ_FORM_999_PAGE" value="2">
  <input type="hidden" name="state" value="second-state">
  <label for="address">Choose your address</label>
  <select id="address" name="q999:q2"><option value="[redacted]">Address</option></select>
  <input type="submit" name="submit_999" value="Get Bin Days">
</form></html>
"""

RESULTS = """
<html>
  <strong id="SBC-YBD-collectionDate">Friday, 8 August</strong>
  <div id="SBCFirstBins"><li>blue bin</li><li>food waste</li></div>
  <div id="FutureCollections"><p>Friday, 15 August</p></div>
  <ul id="FirstFutureBins"><li>green bin</li></ul>
</html>
"""


def fetch_with(responses: list[Response]) -> tuple[list, Session]:
    session = Session(responses)
    with (
        patch.object(swale_gov_uk.requests, "Session", return_value=session),
        patch.object(swale_gov_uk, "sleep"),
    ):
        entries = swale_gov_uk.Source("[redacted]", "AA1 1AA").fetch()
    return entries, session


def test_fetch_preserves_dynamic_form_state_and_parses_results() -> None:
    entries, session = fetch_with(
        [Response(INITIAL_FORM), Response(UPRN_FORM), Response(RESULTS)]
    )

    assert [(entry.date, entry.type) for entry in entries] == [
        (date(date.today().year, 8, 8), "Recycling"),
        (date(date.today().year, 8, 8), "Food"),
        (date(date.today().year, 8, 15), "Refuse"),
    ]
    assert session.calls == [
        ("get", swale_gov_uk.API_URL, None),
        (
            "post",
            "https://swale.gov.uk/lookup",
            {
                "token": "token-one",
                "SQ_FORM_999_PAGE": "1",
                "state": "first-state",
                "q999:q1": "AA1 1AA",
                "submit_999": "Choose Your Address",
            },
        ),
        (
            "post",
            "https://swale.gov.uk/lookup",
            {
                "token": "token-two",
                "SQ_FORM_999_PAGE": "2",
                "state": "second-state",
                "q999:q2": "[redacted]",
                "submit_999": "Get Bin Days",
            },
        ),
    ]


def test_fetch_rejects_cloudflare_challenge() -> None:
    challenge = "<html><title>Just a moment...</title>challenges.cloudflare.com</html>"

    with pytest.raises(ValueError, match="Cloudflare challenge"):
        fetch_with([Response(challenge)])


def test_fetch_rejects_postcode_validation() -> None:
    validation = Response(
        "<html><div class='sq-form-error'>Invalid postcode</div></html>"
    )

    with pytest.raises(
        ValueError, match="postcode submission returned a validation error"
    ):
        fetch_with([Response(INITIAL_FORM), validation])


def test_fetch_rejects_uprn_validation() -> None:
    validation = Response(
        "<html><div class='sq-form-error'>Invalid address</div></html>"
    )

    with pytest.raises(ValueError, match="UPRN submission returned a validation error"):
        fetch_with([Response(INITIAL_FORM), Response(UPRN_FORM), validation])


def test_fetch_rejects_missing_postcode_control() -> None:
    missing_control = """
    <form action="/lookup" method="post">
      <input type="hidden" name="SQ_FORM_999_PAGE" value="1">
      <input type="submit" name="submit_999" value="Choose Your Address">
    </form>
    """

    with pytest.raises(ValueError, match="missing its postcode control"):
        fetch_with([Response(missing_control)])


def test_fetch_rejects_returned_form() -> None:
    with pytest.raises(ValueError, match="input form instead of results"):
        fetch_with(
            [Response(INITIAL_FORM), Response(UPRN_FORM), Response(INITIAL_FORM)]
        )
