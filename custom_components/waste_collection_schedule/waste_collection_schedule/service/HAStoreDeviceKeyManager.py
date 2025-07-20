#!/usr/bin/env python3

import logging
from typing import Optional
from .DeviceKeyStore import DeviceKeyStore

_LOGGER = logging.getLogger(__name__)


class HAStoreDeviceKeyManager:
    """Device key manager that uses HA Store through the DeviceKeyStore."""
    
    def __init__(self, location_key: str, store: DeviceKeyStore):
        """Initialize HA Store device key manager."""
        self._location_key = location_key
        self._store = store
    
    def get_device_key(self) -> Optional[str]:
        """Get device key from HA Store."""
        try:
            device_key = self._store.get_device_key(self._location_key)
            return device_key
        except Exception as e:
            _LOGGER.error("Failed to get device key from HA Store: %s", e)
            return None
    
    def save_device_key(self, device_key: str) -> None:
        """Save device key to HA Store."""
        try:
            self._store.set_device_key(self._location_key, device_key)
            # Note: The actual saving to disk happens later in the coordinator
        except Exception as e:
            _LOGGER.error("Failed to save device key to HA Store: %s", e)