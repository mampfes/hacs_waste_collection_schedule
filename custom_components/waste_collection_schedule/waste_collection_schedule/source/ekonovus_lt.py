import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
)

TITLE = "Ekonovus"
DESCRIPTION = 'Source for UAB "Ekonovus" waste collection schedule.'
URL = "https://www.ekonovus.lt"

TEST_CASES = {
    "Margirio g. 16, Uzliedziai": {
        "address": "Margirio g. 16",
    },
}

ICON_MAP = {
    "pakuotė": "mdi:recycle",
    "stiklas": "mdi:glass-fragile",
    "komunalinės atliekos": "mdi:trash-can",
    "žaliosios atliekos": "mdi:leaf",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Part of the address as shown in the Ekonovus schedule (e.g. 'Margirio g. 35'). Must be unique enough to match your address.",
    },
}

# Power BI public report API constants
_API_URL = "https://wabi-west-europe-d-primary-api.analysis.windows.net/public/reports/querydata?synchronous=true"
_RESOURCE_KEY = "d86dc3d4-e915-4460-b12e-c925d3ae6c75"
_DATASET_ID = "90015897-045e-4f68-8f83-c40d1fc3bfc2"
_REPORT_ID = "06fc8043-9afa-43d6-88cc-3a1e73aaf964"
_MODEL_ID = 1026609

# Map inventory number code to waste type
_INV_TYPE_MAP = {
    "P": "Pakuotė",
    "S": "Stiklas",
    "K": "Komunalinės atliekos",
    "Z": "Žaliosios atliekos",
    "L": "Komunalinės atliekos",
}


def _waste_type_from_inv(inv_nr: str) -> str:
    """Extract waste type from inventory number like '52-P-45455 (Pakuotė)'."""
    # Try parenthesized name first: "52-P-45455 (Pakuotė)"
    paren_match = re.search(r"\(([^)]+)\)", inv_nr)
    if paren_match:
        return paren_match.group(1)
    # Fall back to code letter: "52-P-45455"
    code_match = re.match(r"\d+-([A-Za-z]+)-", inv_nr)
    if code_match:
        code = code_match.group(1).upper()
        return _INV_TYPE_MAP.get(code, inv_nr)
    return inv_nr


def _build_query(address: str) -> dict:
    """Build the Power BI semantic query payload."""
    return {
        "version": "1.0.0",
        "queries": [
            {
                "Query": {
                    "Commands": [
                        {
                            "SemanticQueryDataShapeCommand": {
                                "Query": {
                                    "Version": 2,
                                    "From": [
                                        {
                                            "Name": "w",
                                            "Entity": "WasteObject",
                                            "Type": 0,
                                        },
                                        {
                                            "Name": "s",
                                            "Entity": "ScheduleDates",
                                            "Type": 0,
                                        },
                                        {
                                            "Name": "t",
                                            "Entity": "Teritorijos konteinerių tvarkaraščiams",
                                            "Type": 0,
                                        },
                                    ],
                                    "Select": [
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "w"}
                                                },
                                                "Property": "Inventorinis nr.",
                                            },
                                            "Name": "WasteObject.reikia",
                                        },
                                        {
                                            "Measure": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "s"}
                                                },
                                                "Property": "Datos",
                                            },
                                            "Name": "ScheduleDates.Datos",
                                        },
                                    ],
                                    "Where": [
                                        {
                                            "Condition": {
                                                "Contains": {
                                                    "Left": {
                                                        "Column": {
                                                            "Expression": {
                                                                "SourceRef": {
                                                                    "Source": "w"
                                                                }
                                                            },
                                                            "Property": "Adresas",
                                                        }
                                                    },
                                                    "Right": {
                                                        "Literal": {
                                                            "Value": f"'{address}'"
                                                        }
                                                    },
                                                }
                                            }
                                        },
                                        {
                                            "Condition": {
                                                "In": {
                                                    "Expressions": [
                                                        {
                                                            "Column": {
                                                                "Expression": {
                                                                    "SourceRef": {
                                                                        "Source": "s"
                                                                    }
                                                                },
                                                                "Property": "Future",
                                                            }
                                                        }
                                                    ],
                                                    "Values": [
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'true'"
                                                                }
                                                            }
                                                        ]
                                                    ],
                                                }
                                            }
                                        },
                                        {
                                            "Condition": {
                                                "In": {
                                                    "Expressions": [
                                                        {
                                                            "Column": {
                                                                "Expression": {
                                                                    "SourceRef": {
                                                                        "Source": "t"
                                                                    }
                                                                },
                                                                "Property": "Rodomas tvarkaraštis",
                                                            }
                                                        }
                                                    ],
                                                    "Values": [
                                                        [{"Literal": {"Value": "'1'"}}]
                                                    ],
                                                }
                                            }
                                        },
                                        {
                                            "Condition": {
                                                "In": {
                                                    "Expressions": [
                                                        {
                                                            "Column": {
                                                                "Expression": {
                                                                    "SourceRef": {
                                                                        "Source": "s"
                                                                    }
                                                                },
                                                                "Property": "OverNextRun",
                                                            }
                                                        }
                                                    ],
                                                    "Values": [
                                                        [{"Literal": {"Value": "true"}}]
                                                    ],
                                                }
                                            }
                                        },
                                        {
                                            "Condition": {
                                                "Not": {
                                                    "Expression": {
                                                        "Comparison": {
                                                            "ComparisonKind": 0,
                                                            "Left": {
                                                                "Column": {
                                                                    "Expression": {
                                                                        "SourceRef": {
                                                                            "Source": "w"
                                                                        }
                                                                    },
                                                                    "Property": "Inventorinis nr.",
                                                                }
                                                            },
                                                            "Right": {
                                                                "Literal": {
                                                                    "Value": "null"
                                                                }
                                                            },
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                    ],
                                },
                                "Binding": {
                                    "Primary": {"Groupings": [{"Projections": [0, 1]}]},
                                    "DataReduction": {
                                        "DataVolume": 4,
                                        "Primary": {"Window": {"Count": 500}},
                                    },
                                    "IncludeEmptyGroups": True,
                                    "Version": 1,
                                },
                                "ExecutionMetricsKind": 1,
                            }
                        }
                    ]
                },
                "QueryId": "",
                "ApplicationContext": {
                    "DatasetId": _DATASET_ID,
                    "Sources": [
                        {"ReportId": _REPORT_ID, "VisualId": "cfba850d0ce48eb9e44d"}
                    ],
                },
            }
        ],
        "cancelQueries": [],
        "modelId": _MODEL_ID,
    }


def _parse_dsr_response(data: dict) -> list[tuple[str, str]]:
    """Parse Power BI DSR response into list of (inventory_nr, dates_csv) tuples."""
    results = []
    try:
        dm0 = data["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"]
    except (KeyError, IndexError):
        return results

    for row in dm0:
        cells = row.get("C", [])
        if len(cells) >= 2:
            inv_nr = str(cells[0])
            dates_str = str(cells[1])
            results.append((inv_nr, dates_str))

    return results


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "X-PowerBI-ResourceKey": _RESOURCE_KEY,
        }

        response = requests.post(
            _API_URL,
            headers=headers,
            json=_build_query(self._address),
        )
        response.raise_for_status()

        data = response.json()
        rows = _parse_dsr_response(data)

        if not rows:
            raise SourceArgumentNotFound("address", self._address)

        entries = []
        for inv_nr, dates_csv in rows:
            waste_type = _waste_type_from_inv(inv_nr)
            icon = ICON_MAP.get(waste_type.lower())

            for date_str in dates_csv.split(","):
                date_str = date_str.strip().rstrip(".")
                if not date_str:
                    continue
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    entries.append(Collection(date=date, t=waste_type, icon=icon))
                except ValueError:
                    continue

        return entries
