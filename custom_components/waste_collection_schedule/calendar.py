"""Calendar platform support for Waste Collection Schedule."""

import logging
from datetime import timedelta

from homeassistant.components.calendar import CalendarEventDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up calendar platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    entities = []

    api = discovery_info["api"]

    for scraper in api.scrapers:
        entities.append(WasteCollectionCalendar(api, scraper))

    async_add_entities(entities)


class WasteCollectionCalendar(CalendarEventDevice):
    """Calendar entity class."""

    def __init__(self, api, scraper):
        self._api = api
        self._scraper = scraper

    @property
    def name(self):
        """Return entity name."""
        return self._scraper.calendar_title

    @property
    def event(self):
        """Return next collection event."""
        appointments = self._scraper.get_upcoming(count=1, include_today=True)
        if len(appointments) == 0:
            return None
        else:
            return self._convert(appointments[0])

    async def async_get_events(self, hass, start_date, end_date):
        """Return all events within specified time span."""
        appointments = []
        for a in self._scraper.get_upcoming(include_today=True):
            if a.date >= start_date.date() and a.date <= end_date.date():
                appointments.append(self._convert(a))
        return appointments

    def _convert(self, appointment):
        """Convert an collection appointment into a Home Assistant calendar event."""
        return {
            "uid": f"self._scraper.calendar_title-{appointment.date.isoformat()}-{appointment.type}",
            "summary": appointment.type,
            "start": {"date": appointment.date.isoformat()},
            "end": {"date": (appointment.date + timedelta(days=1)).isoformat()},
            "allDay": True,
        }
