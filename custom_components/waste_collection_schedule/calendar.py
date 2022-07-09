"""Calendar platform support for Waste Collection Schedule."""

import logging
from datetime import timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent

from custom_components.waste_collection_schedule.waste_collection_schedule.scraper import (
    Scraper,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up calendar platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    entities = []

    api = discovery_info["api"]

    for scraper in api.scrapers:
        dedicated_calendar_types = scraper.get_dedicated_calendar_types()
        global_calendar_types = scraper.get_global_calendar_types()

        if dedicated_calendar_types is not None:
            for type in dedicated_calendar_types:
                unique_id = calc_unique_calendar_id(scraper, type)

                entities.append(
                    WasteCollectionCalendar(
                        api,
                        scraper,
                        scraper.get_calendar_title_for_type(type),
                        [scraper.get_collection_type(type)],
                        unique_id,
                    )
                )

        if global_calendar_types is not None or dedicated_calendar_types is None:
            unique_id = calc_unique_calendar_id(scraper)
            entities.append(
                WasteCollectionCalendar(
                    api,
                    scraper,
                    scraper.calendar_title,
                    [
                        scraper.get_collection_type(type)
                        for type in global_calendar_types
                    ]
                    if global_calendar_types is not None
                    else None,
                    unique_id,
                )
            )

    async_add_entities(entities)


class WasteCollectionCalendar(CalendarEntity):
    """Calendar entity class."""

    def __init__(self, api, scraper, name, types, unique_id: str):
        self._api = api
        self._scraper = scraper
        self._name = name
        self._types = types
        self._unique_id = unique_id
        self._attr_unique_id = unique_id

    @property
    def name(self):
        """Return entity name."""
        return self._name

    @property
    def event(self):
        """Return next collection event."""
        collections = self._scraper.get_upcoming(
            count=1, include_today=True, types=self._types
        )

        if len(collections) == 0:
            return None
        else:
            return self._convert(collections[0])

    async def async_get_events(self, hass, start_date, end_date):
        """Return all events within specified time span."""
        collections = []
        for a in self._scraper.get_upcoming(include_today=True, types=self._types):
            if a.date >= start_date.date() and a.date <= end_date.date():
                collections.append(self._convert(a))
        return collections

    def _convert(self, collection):
        """Convert an collection into a Home Assistant calendar event."""
        return CalendarEvent(
            summary=collection.type,
            start=collection.date,
            end=collection.date + timedelta(days=1),
        )


def calc_unique_calendar_id(scraper: Scraper, type: str | None = None):
    return scraper.unique_id + ("_" + type if type is not None else "") + "_calendar"
