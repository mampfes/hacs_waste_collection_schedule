# Credit where it's due:
# This is based on the elmbridge_gov_uk source

import re
from datetime import date, datetime
from typing import Any, ClassVar, final

from dateutil.parser import parse as _parse_dayfirst_date
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field, uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsDynamicRowsPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

BASE_URL = "https://my.crawley.gov.uk"
INITIAL_URL = f"{BASE_URL}/en/service/check_my_bin_collection"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
AUTH_TEST_URL = f"{BASE_URL}/apibroker/domain/my.crawley.gov.uk"
API_URL = f"{BASE_URL}/apibroker/runLookup"
LOOKUP_ID = "5b4f0ec5f13f4"

# The legacy source (cloned from elmbridge_gov_uk, see credit above) passes
# this Elmbridge tenant hostname as the `hostname` query-string value on the
# isauthenticated call, rather than my.crawley.gov.uk. Every other URL in the
# chain (initial/auth/auth_test/api) is Crawley's own domain -- only this one
# query value differs. Preserved as-is (HTTP-behaviour-preserving conversion);
# flagged for a maintainer to confirm whether it's a genuine shared-tenant
# arrangement or a leftover copy/paste from the elmbridge source.
_AUTH_HOSTNAME = "elmbridge-self.achieveservice.com"

# `rubbishDateCurrent`/`rubbishDateNext`, `recycleDateCurrent`/`recycleDateNext`,
# `greenDateCurrent`/`greenDateNext` -- confirmed against a live response (the
# legacy source's ICON_MAP used long descriptive labels such as "GREENbin
# Garden Waste Collection" that never actually matched these short field-name
# prefixes -- dead code there; the real prefixes are used below instead).
_DATE_KEY_RE = re.compile(r"^(.+?)Date(?:Current|Next)$")


def _parse_dayfirst(*args: str) -> date:
    """dateutil auto-parse with dayfirst=True, matching the legacy source.

    ``date_parsers`` has no dayfirst-aware auto parser, and this module is
    off-limits to change -- a small local parser keeps the exact legacy
    ambiguous-date resolution (DD/MM over MM/DD) without touching it.
    """
    return _parse_dayfirst_date(str(args[-1]).strip(), dayfirst=True).date()


def _form_values(context: dict[str, Any], source: BaseSource) -> dict:
    now = datetime.now()
    usrn = source.params.get("usrn") or "0000"
    return {
        "address": {
            "value": {
                "Address": {
                    "usrn": {"value": usrn},
                    "uprn": {"value": source.params["uprn"]},
                }
            }
        },
        "dayConverted": {"value": now.strftime("%d/%m/%Y")},
        "getCollection": {"value": "true"},
        "getWorksheets": {"value": "false"},
    }


@final
class Source(BaseSource):
    TITLE = "Crawley Borough Council (myCrawley)"
    DESCRIPTION = "Source for Crawley Borough Council (myCrawley)."
    URL = "https://crawley.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Feroners Cl": {"uprn": "100061775179"},
        "Peterborough Road": {"uprn": 100061787552, "usrn": 9700731},
    }

    PARAMS = (uprn(), text_field("usrn", "USRN", optional=True))

    retrieve = AchieveFormsRetriever(
        hostname=_AUTH_HOSTNAME,
        initial_url=INITIAL_URL,
        auth_url=AUTH_URL,
        api_url=API_URL,
        auth_test_url=AUTH_TEST_URL,
        steps=[
            LookupStep(
                LOOKUP_ID,
                section="Address",
                form_values=_form_values,
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    preprocess = AchieveFormsDynamicRowsPreprocessor(
        _DATE_KEY_RE,
        parse_date=_parse_dayfirst,
    )
    transform = RowTransformer(
        parse_date=_parse_dayfirst,
        type_value_map={
            "rubbish": GENERAL_WASTE,
            "recycle": RECYCLABLES,
            "green": GARDEN_WASTE,
        },
    )

    def __init__(self, uprn: str | int, usrn: str | int | None = None):
        super().__init__(uprn=str(uprn), usrn=str(usrn) if usrn else None)
