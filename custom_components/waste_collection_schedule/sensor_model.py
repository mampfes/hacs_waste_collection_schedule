"""The persisted sensor contract shared by options, devices and YAML."""

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any
from uuid import uuid4

import voluptuous as vol

from .waste_collection_schedule.colors import validate_color
from .waste_collection_schedule.waste_types import ALL_TYPES

STATE_FORMATS = (
    "types_in_days",
    "in_days",
    "relative",
    "date",
    "types",
    "days",
    "custom",
)
DATE_FORMATS = ("dmy", "weekday_dmy", "mdy", "weekday_mdy", "iso", "weekday_iso")
LANGUAGES = ("auto", "en", "de", "fr", "it", "nl", "sl", "da", "fi", "sv", "nb")
KINDS = ("schedule", "days_to", "last_update")
DETAILS_FORMATS = ("upcoming", "appointment_types", "generic", "hidden")


@dataclass
class SensorConfig:
    """One saved sensor; names and display settings never determine identity."""

    name: str
    id: str = field(default_factory=lambda: "c_" + uuid4().hex[:8])
    origin: str = "custom"
    kind: str = "schedule"
    enabled: bool = True
    advanced: bool = False
    types: list[str] = field(default_factory=list)
    exclude_types: list[str] = field(default_factory=list)
    unique_types: bool = False
    count: int | None = None
    leadtime: int | None = None
    event_index: int = 0
    state_format: str = "types_in_days"
    language: str = "en"
    date_format: str = "iso"
    details_format: str = "upcoming"
    value_template: str | None = None
    date_template: str | None = None
    color: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return SENSOR_RECORD_SCHEMA(asdict(self))

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> "SensorConfig":
        return cls(**SENSOR_RECORD_SCHEMA(record))


SENSOR_RECORD_SCHEMA = vol.Schema(
    {
        vol.Required("name"): vol.All(str, vol.Length(min=1)),
        vol.Required("id"): vol.All(str, vol.Match(r"^[a-z0-9_]+$")),
        vol.Optional("origin", default="custom"): str,
        vol.Optional("kind", default="schedule"): vol.In(KINDS),
        vol.Optional("enabled", default=True): bool,
        vol.Optional("advanced", default=False): bool,
        vol.Optional("types", default=list): [str],
        vol.Optional("exclude_types", default=list): [str],
        vol.Optional("unique_types", default=False): bool,
        vol.Optional("count", default=None): vol.Any(
            None, vol.All(int, vol.Range(min=1))
        ),
        vol.Optional("leadtime", default=None): vol.Any(
            None, vol.All(int, vol.Range(min=0))
        ),
        vol.Optional("event_index", default=0): vol.All(int, vol.Range(min=0)),
        vol.Optional("state_format", default="types_in_days"): vol.In(STATE_FORMATS),
        vol.Optional("language", default="en"): vol.In(LANGUAGES),
        vol.Optional("date_format", default="iso"): vol.In(DATE_FORMATS),
        vol.Optional("details_format", default="upcoming"): vol.In(DETAILS_FORMATS),
        vol.Optional("value_template", default=None): vol.Any(None, str),
        vol.Optional("date_template", default=None): vol.Any(None, str),
        vol.Optional("color", default=None): vol.Any(None, validate_color),
    }
)


def catalogue_id(origin: str) -> str:
    if not origin.startswith("type:"):
        return origin
    type_id = origin.removeprefix("type:")
    if all(c in "abcdefghijklmnopqrstuvwxyz0123456789_" for c in type_id):
        return "type_" + type_id
    return "type_x" + sha256(type_id.encode()).hexdigest()[:8]


def migrate_filter(
    value: str, customize: dict, type_ids: set[str] | frozenset[str]
) -> str:
    """Resolve only statically unambiguous canonical names and aliases on ids.

    Provider-label and wildcard customizations remain literal: converting them
    to a category could widen an existing filter to a second bin.
    """
    by_id = {wt.id: wt for wt in ALL_TYPES if wt.id in type_ids}
    if value in by_id or value.startswith("preserved:"):
        return value
    aliases = [key for key, c in customize.items() if c.get("alias") == value]
    if aliases:
        return aliases[0] if len(aliases) == 1 and aliases[0] in by_id else value
    if value in customize:
        return value
    ids = {wt.id for wt in by_id.values() if value in wt.names.values()}
    return next(iter(ids)) if len(ids) == 1 else value
