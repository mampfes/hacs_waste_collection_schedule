"""Calendar platform support for Waste Collection Schedule."""

import logging
from datetime import datetime, timedelta, time, tzinfo

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

# fmt: off
from custom_components.waste_collection_schedule.waste_collection_schedule.collection_aggregator import \
    CollectionAggregator
from custom_components.waste_collection_schedule.waste_collection_schedule.source_shell import \
    SourceShell

# fmt: on

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up calendar platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    entities = []

    api = discovery_info["api"]

    tz = dt_util.get_time_zone(hass.config.time_zone) if hass.config.time_zone is not None else None

    for shell in api.shells:
        dedicated_calendar_types = shell.get_dedicated_calendar_types()
        for type in dedicated_calendar_types:
            entities.append(
                WasteCollectionCalendar(
                    api=api,
                    aggregator=CollectionAggregator([shell]),
                    name=shell.get_calendar_title_for_type(type),
                    include_types={shell.get_collection_type_name(type)},
                    unique_id=calc_unique_calendar_id(shell, type),
                    timezone=tz
                )
            )

        entities.append(
            WasteCollectionCalendar(
                api=api,
                aggregator=CollectionAggregator([shell]),
                name=shell.calendar_title,
                exclude_types={
                    shell.get_collection_type_name(type)
                    for type in dedicated_calendar_types
                },
                unique_id=calc_unique_calendar_id(shell),
                timezone=tz
            )
        )

    async_add_entities(entities)


class WasteCollectionCalendar(CalendarEntity):
    """Calendar entity class."""

    def __init__(
        self,
        api,
        aggregator,
        name,
        unique_id: str,
        timezone: tzinfo,
        include_types=None,
        exclude_types=None,
    ):
        self._api = api
        self._aggregator = aggregator
        self._name = name
        self._include_types = include_types
        self._exclude_types = exclude_types
        self._unique_id = unique_id
        self._attr_unique_id = unique_id
        self._timezone = timezone if timezone is not None else dt_util.DEFAULT_TIME_ZONE

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
    ):
        """Return all events within specified time span."""
        events = []

        for collection in self._aggregator.get_upcoming(
            include_today=True,
            include_types=self._include_types,
            exclude_types=self._exclude_types,
        ):
            event = self._convert(collection)

            if start_date <= event.start_datetime_local <= end_date:
                events.append(event)

        return events

    def _convert(self, collection) -> CalendarEvent:
        """Convert an collection into a Home Assistant calendar event."""
        if collection.start_hour is not None and collection.end_hour is not None:
            event_date_time = datetime.combine(
                collection.date,
                time(hour=0, minute=0, second=0),
                self._timezone
            )
            return CalendarEvent(
                summary=collection.type,
                start=event_date_time + timedelta(hours=collection.start_hour),
                end=event_date_time + timedelta(hours=collection.end_hour),
            )

        return CalendarEvent(
            summary=collection.type,
            start=collection.date,
            end=collection.date + timedelta(days=1),
        )


def calc_unique_calendar_id(shell: SourceShell, type: str = None):
    return shell.unique_id + ("_" + type if type is not None else "") + "_calendar"
