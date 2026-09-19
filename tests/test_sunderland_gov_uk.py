import os
import sys
from unittest.mock import patch

import pytest

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
            "waste_collection_schedule",
        )
    )
)

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.source import sunderland_gov_uk

ADDRESS_HTML = """
<form action="/process">
  <select name="BINCOLLECTIONCHECKERNEWV3_ADDRESSSEARCH_SCCLISTOFADDRESSES">
    <option value="1">1 Example Road</option>
    <option value="2">17 Sutherland Drive</option>
  </select>
</form>
"""


@patch.object(sunderland_gov_uk.Source, "_lookup_postcode")
@patch.object(sunderland_gov_uk.Source, "_submit_address")
@patch.object(sunderland_gov_uk.Source, "_extract_form_data", return_value={})
@patch.object(
    sunderland_gov_uk.Source, "_extract_result", return_value={"schedules": []}
)
def test_fetch_submits_matching_address(
    extract_result,
    extract_form_data,
    submit_address,
    lookup_postcode,
):
    lookup_postcode.return_value.text = ADDRESS_HTML
    source = sunderland_gov_uk.Source(
        postcode="SR4 8RJ",
        address=" 17  SUTHERLAND DRIVE ",
    )

    assert source.fetch() == []
    submit_address.assert_called_once_with(
        ADDRESS_HTML,
        "2",
        "17 Sutherland Drive",
    )


def test_fetch_raises_suggestion_for_malformed_address_response():
    source = sunderland_gov_uk.Source(
        postcode="SR4 8RJ",
        address="17 Sutherland Drive",
    )

    with patch.object(source, "_lookup_postcode") as lookup_postcode:
        lookup_postcode.return_value.text = (
            "<html><body>unexpected response</body></html>"
        )

        with pytest.raises(SourceArgumentNotFoundWithSuggestions) as error:
            source.fetch()

    assert error.value.argument == "postcode"
    assert list(error.value.suggestions) == []
