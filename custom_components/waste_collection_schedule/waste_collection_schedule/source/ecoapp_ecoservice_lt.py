import datetime
from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import Compose, RequireRecords
from waste_collection_schedule.transformers import JsonTransformer

SCHEDULES_PAGE_URL = "https://ecoservice.lt/grafikai/"
# The schedule search on the page is a Power BI "publish to web" report. Its
# embed token (``view?r=``) carries this resource key; the report page itself
# names the cluster that serves it (``clusterAssignmentRecord``), and the API
# host is that cluster's ``-api`` name, exactly as the report viewer builds it.
RESOURCE_KEY = "6689ce06-85f4-4c23-baf0-318c087fd486"
API_HOST = "https://wabi-west-europe-d-primary-api.analysis.windows.net"
MODELS_URL = (
    f"{API_HOST}/public/reports/{RESOURCE_KEY}/modelsAndExploration"
    "?preferReadOnlySession=true"
)
QUERY_URL = f"{API_HOST}/public/reports/querydata?synchronous=true"
HEADERS = {"Accept": "application/json", "X-PowerBI-ResourceKey": RESOURCE_KEY}

_ENTITY = "InventoryDays"
_ID_COLUMN = "Inventorinis numeris"
_DATE_COLUMN = "Date"

# The report has no waste-type column. The inventory number's middle letter is
# the container's stream (13-L-115261, 13-P-505460, 13-S-500496, 13-Z-001848,
# the three Vilnius containers of one household plus a green-waste bin).
_STREAMS = {
    "L": wt.GENERAL_WASTE,
    "P": wt.RECYCLABLES,
    "S": wt.GLASS,
    "Z": wt.GARDEN_WASTE,
}


def _container_ids(value):
    """'13-L-115261, 13-P-505460' or a YAML list -> clean inventory numbers."""
    items = value if isinstance(value, (list, tuple)) else str(value or "").split(",")
    cleaned = (str(item).strip().replace('"', "").replace("'", "") for item in items)
    return [item for item in cleaned if item]


def _model(response, **_):
    """The ids the query must name: the report's model, dataset and report."""
    data = response.json()
    model = data["models"][0]
    return {
        "modelId": model["id"],
        "DatasetId": model["dbName"],
        "ReportId": data["exploration"]["reportId"],
    }


def _column(name):
    return {
        "Column": {"Expression": {"SourceRef": {"Source": "i"}}, "Property": name},
        "Name": f"{_ENTITY}.{name}",
    }


def _query(model, waste_object_ids, **_):
    """The report's own semantic query: every date of the given containers."""
    values = [[{"Literal": {"Value": f"'{oid}'"}}] for oid in waste_object_ids]
    query = {
        "Version": 2,
        "From": [{"Name": "i", "Entity": _ENTITY, "Type": 0}],
        "Select": [_column(_ID_COLUMN), _column(_DATE_COLUMN)],
        "Where": [
            {
                "Condition": {
                    "In": {
                        "Expressions": [{"Column": _column(_ID_COLUMN)["Column"]}],
                        "Values": values,
                    }
                }
            }
        ],
    }
    return {
        "version": "1.0.0",
        "queries": [
            {
                "Query": {
                    "Commands": [
                        {
                            "SemanticQueryDataShapeCommand": {
                                "Query": query,
                                "Binding": {
                                    "Primary": {"Groupings": [{"Projections": [0, 1]}]},
                                    "DataReduction": {
                                        "DataVolume": 3,
                                        "Primary": {"Window": {"Count": 30000}},
                                    },
                                    "Version": 1,
                                },
                            }
                        }
                    ]
                },
                "QueryId": "",
                "ApplicationContext": {
                    "DatasetId": model["DatasetId"],
                    "Sources": [{"ReportId": model["ReportId"]}],
                },
            }
        ],
        "cancelQueries": [],
        "modelId": model["modelId"],
    }


def _rows(response, source=None):
    """Decode the report's compressed data shape into ``{id, date}`` rows.

    Each row lists only the columns that changed: bit ``i`` of ``R`` marks
    column ``i`` as repeated from the row before, and a text column holds an
    index into its ``ValueDicts`` list. Dates are epoch milliseconds (UTC).
    """
    data = response.json()["results"][0]["result"]["data"]["dsr"]["DS"][0]
    dictionaries = data.get("ValueDicts", {})
    rows = []
    schema: list = []
    previous: list = []
    for row in (data.get("PH") or [{}])[0].get("DM0", []):
        schema = row.get("S", schema)
        values = list(row.get("C", []))
        repeated = row.get("R", 0)
        current = [
            previous[i] if repeated >> i & 1 else values.pop(0)
            for i in range(len(schema))
        ]
        previous = current
        oid, stamp = (
            dictionaries[column["DN"]][value] if "DN" in column else value
            for column, value in zip(schema, current, strict=True)
        )
        day = datetime.datetime.fromtimestamp(stamp / 1000, datetime.UTC).date()
        rows.append({"id": oid, "date": day})
    return rows


def _stream(row):
    parts = str(row["id"]).split("-")
    return parts[1] if len(parts) == 3 else str(row["id"])


@final
class Source(BaseSource):
    TITLE = "Ecoservice atliekos"
    DESCRIPTION = 'Source for UAB "Ecoservice".'
    URL = "https://ecoservice.lt/"
    COUNTRY = "lt"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Jono Glaubico g. 10-1 (Vilnius)": {
            "waste_object_ids": "'13-L-115261', 13-P-505460,13-S-500496"
        },
        "Parko g. 1 (Pilies I k.)": {"waste_object_ids": "94-L-002776"},
        "D. Poškos g. 26 (Vilnius)": {"waste_object_ids": ["13-Z-001848"]},
    }
    PARAMS = (
        text_field(
            "waste_object_ids",
            "Container inventory numbers",
            coerce=_container_ids,
        ),
    )
    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the inventory number printed on the side of each container, "
            "separated by commas, e.g. 13-L-115261, 13-P-505460. You can check them "
            f"in the schedule search on {SCHEDULES_PAGE_URL}. Since the v3 pipeline "
            "migration, waste types use canonical, localised names. Update filters, "
            "automations and customisations using the old labels."
        ),
    }
    WASTE_TYPES: ClassVar[list] = list(_STREAMS.values())

    retrieve = retrievers.Request(
        QUERY_URL,
        method="POST",
        headers=HEADERS,
        json=_query,
        before=(retrievers.Lookup(MODELS_URL, headers=HEADERS, pick=_model),),
    )
    parse = staticmethod(_rows)
    preprocess = Compose(
        RequireRecords(
            argument="waste_object_ids",
            hint=f"Check the inventory numbers in the schedule search on {SCHEDULES_PAGE_URL}",
        ),
    )
    transform = JsonTransformer(
        date_key="date",
        type_key=_stream,
        type_value_map=_STREAMS,
    )
