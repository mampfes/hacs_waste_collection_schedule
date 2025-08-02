#!/usr/bin/env python3

import logging
from typing import Optional, Dict
from homeassistant.helpers import storage
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "waste_collection_schedule.device_keys"


class DeviceKeyStore:
    """Home Assistant Store-based device key manager."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the device key store."""
        self._hass = hass
        self._store = storage.Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: Dict[str, str] = {}
        self._loaded = False
    
    async def async_load(self) -> None:
        """Load device keys from storage."""
        try:
            data = await self._store.async_load()
            if data is not None:
                self._data = data.get("device_keys", {})
            else:
                self._data = {}
            self._loaded = True
        except Exception as e:
            _LOGGER.error("Failed to load device keys from storage: %s", e)
            self._data = {}
            self._loaded = True
    
    async def async_save(self) -> None:
        """Save device keys to storage."""
        try:
            await self._store.async_save({"device_keys": self._data})
        except Exception as e:
            _LOGGER.error("Failed to save device keys to storage: %s", e)
    
    def get_device_key(self, location_key: str) -> Optional[str]:
        """Get device key for location (sync method for worker threads)."""
        if not self._loaded:
            _LOGGER.warning("Device key store not loaded yet for location %s", location_key)
            return None
        return self._data.get(location_key)
    
    def set_device_key(self, location_key: str, device_key: str) -> None:
        """Set device key for location (sync method for worker threads)."""
        self._data[location_key] = device_key
    
    def get_all_keys(self) -> Dict[str, str]:
        """Get all device keys (for debugging/inspection)."""
        return self._data.copy()


# Global store instance
_device_key_store: Optional[DeviceKeyStore] = None


def get_device_key_store() -> Optional[DeviceKeyStore]:
    """Get the global device key store instance."""
    return _device_key_store


def initialize_device_key_store(hass: HomeAssistant) -> DeviceKeyStore:
    """Initialize the global device key store."""
    global _device_key_store
    if _device_key_store is None:
        _device_key_store = DeviceKeyStore(hass)
    return _device_key_store