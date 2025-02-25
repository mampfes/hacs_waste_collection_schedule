"""Calendar platform support for Waste Collection Schedule."""

import logging
import uuid
from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from custom_components.waste_collection_schedule.waste_collection_schedule import (
    Collection,
)

# fmt: off
from custom_components.waste_collection_schedule.waste_collection_schedule.collection_aggregator import (
    CollectionAggregator,
)
from custom_components.waste_collection_schedule.waste_collection_schedule.source_shell import (
    SourceShell,
)

from .const import DOMAIN
from .init_ui import WCSCoordinator
from .init_yaml import WasteCollectionApi

# fmt: on

_LOGGER = logging.getLogger(__name__)


class WasteCollectionCalendar(CalendarEntity):
    """Calendar entity class."""

    def __init__(
        self,
        aggregator: CollectionAggregator,
        name: str,
        unique_id: str,
        coordinator: WCSCoordinator | None = None,
        api: WasteCollectionApi | None = None,
        include_types: set[str] | None = None,
        exclude_types: set[str] | None = None,
    ):
        self._api = api
        self._coordinator = coordinator
        self._aggregator = aggregator
        self._name = name
        self._include_types = include_types
        self._exclude_types = exclude_types
        self._unique_id = unique_id
        self._attr_unique_id = unique_id

        if coordinator:
            self._attr_device_info = coordinator.device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()

        if self._coordinator:
            self.async_on_remove(
                self._coordinator.async_add_listener(
                    self._handle_coordinator_update, None
                )
            )

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def name(self):
        """Return entity name."""
        return self._name

    @property
    def event(self):
        """Return next collection event."""
        collections = self._aggregator.get_upcoming(
            count=1,
            include_today=True,
            include_types=self._include_types,
            exclude_types=self._exclude_types,
        )

        if len(collections) == 0:
            return None
        else:
            return self._convert(collections[0])

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return all events within specified time span."""
        events: list[CalendarEvent] = []

        for collection in self._aggregator.get_upcoming(
            include_today=True,
            include_types=self._include_types,
            exclude_types=self._exclude_types,
        ):
            event = self._convert(collection)

            if start_date <= event.start_datetime_local <= end_date:
                events.append(event)

        return events

    def _convert(self, collection: Collection) -> CalendarEvent:
        """Convert an collection into a Home Assistant calendar event."""
        return CalendarEvent(
            summary=collection.type,
            start=collection.date,
            end=collection.date + timedelta(days=1),
            uid=uuid.uuid4(),
        )


def create_calendar_entries(
    shells: list[SourceShell],
    api: WasteCollectionApi | None = None,
    coordinator: WCSCoordinator | None = None,
) -> list[WasteCollectionCalendar]:
    entities: list[WasteCollectionCalendar] = []
    for shell in shells:
        dedicated_calendar_types = shell.get_dedicated_calendar_types()
        for type in dedicated_calendar_types:
            entities.append(
                WasteCollectionCalendar(
                    api=api,
                    coordinator=coordinator,
                    aggregator=CollectionAggregator([shell]),
                    name=shell.get_calendar_title_for_type(type),
                    include_types={shell.get_collection_type_name(type)},
                    unique_id=calc_unique_calendar_id(shell, type),
                )
            )

        entities.append(
            WasteCollectionCalendar(
                api=api,
                coordinator=coordinator,
                aggregator=CollectionAggregator([shell]),
                name=shell.calendar_title,
                exclude_types={
                    shell.get_collection_type_name(type)
                    for type in dedicated_calendar_types
                },
                unique_id=calc_unique_calendar_id(shell),
            )
        )
    return entities


# Config flow setup
async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator: WCSCoordinator = hass.data[DOMAIN][config.entry_id]
    shell = coordinator.shell

    entities = create_calendar_entries([shell], coordinator=coordinator)

    async_add_entities(entities, update_before_add=True)


# YAML setup
async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Set up calendar platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    entities = []

    api: WasteCollectionApi = discovery_info["api"]
    entities = create_calendar_entries(api.shells, api=api)

    async_add_entities(entities)


def calc_unique_calendar_id(shell: SourceShell, type: str | None = None):
    return shell.unique_id + ("_" + type if type is not None else "") + "_calendar"
