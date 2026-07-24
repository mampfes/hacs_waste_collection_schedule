from unittest.mock import Mock

from custom_components.waste_collection_schedule.wcs_coordinator import WCSCoordinator


def test_cancel_scheduled_callbacks_cancels_trackers_and_delayed_fetch():
    coordinator = object.__new__(WCSCoordinator)
    first_tracker = Mock()
    second_tracker = Mock()
    delayed_fetch = Mock()
    coordinator._scheduled_callbacks = [first_tracker, second_tracker]
    coordinator._pending_fetch_cancel = delayed_fetch

    coordinator.cancel_scheduled_callbacks()

    first_tracker.assert_called_once_with()
    second_tracker.assert_called_once_with()
    delayed_fetch.assert_called_once_with()
    assert coordinator._scheduled_callbacks == []
    assert coordinator._pending_fetch_cancel is None


def test_cancel_scheduled_callbacks_is_idempotent():
    coordinator = object.__new__(WCSCoordinator)
    coordinator._scheduled_callbacks = []
    coordinator._pending_fetch_cancel = None

    coordinator.cancel_scheduled_callbacks()
    coordinator.cancel_scheduled_callbacks()

    assert coordinator._scheduled_callbacks == []
    assert coordinator._pending_fetch_cancel is None
