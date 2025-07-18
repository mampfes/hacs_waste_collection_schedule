#!/usr/bin/env python3

import asyncio
import logging
from typing import Optional, Dict, Any
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "waste_collection_schedule_device_keys"


class HAStorageDeviceKeyManager:
    """Home Assistant storage-based device key manager for WhatBinDay API."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the storage manager."""
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: Optional[Dict[str, Any]] = None
        self._load_lock = asyncio.Lock()

    async def _async_load_data(self) -> Dict[str, Any]:
        """Load data from storage."""
        if self._data is None:
            async with self._load_lock:
                if self._data is None:
                    stored_data = await self._store.async_load()
                    self._data = stored_data or {"device_keys": {}}
        return self._data

    async def async_get_device_key_for_location(self, location_key: str) -> Optional[str]:
        """Get stored device key for a specific location."""
        try:
            data = await self._async_load_data()
            return data.get("device_keys", {}).get(location_key)
        except Exception as e:
            _LOGGER.warning("Failed to load device key for location %s: %s", location_key, e)
            return None

    async def async_save_device_key_for_location(self, location_key: str, device_key: str) -> None:
        """Save device key for a specific location."""
        try:
            data = await self._async_load_data()
            if "device_keys" not in data:
                data["device_keys"] = {}
            
            data["device_keys"][location_key] = device_key
            await self._store.async_save(data)
            _LOGGER.debug("Saved device key for location %s", location_key)
        except Exception as e:
            _LOGGER.error("Failed to save device key for location %s: %s", location_key, e)

    def get_device_key_for_location(self, location_key: str) -> Optional[str]:
        """Synchronous wrapper for getting device key."""
        if self.hass.is_running:
            # Use async method if HA is running
            loop = self.hass.loop
            if loop.is_running():
                # Create a task if we're in the event loop
                task = asyncio.create_task(self.async_get_device_key_for_location(location_key))
                try:
                    # Try to get the result if it's immediately available
                    if task.done():
                        return task.result()
                    else:
                        # Schedule for later execution
                        self.hass.async_create_task(task)
                        return None
                except Exception:
                    return None
            else:
                # Run in new event loop if not in one
                return loop.run_until_complete(self.async_get_device_key_for_location(location_key))
        else:
            # HA not running, return None
            return None

    def save_device_key_for_location(self, location_key: str, device_key: str) -> None:
        """Synchronous wrapper for saving device key."""
        if self.hass.is_running:
            # Schedule the async save
            self.hass.async_create_task(
                self.async_save_device_key_for_location(location_key, device_key)
            )
        else:
            # HA not running, can't save
            _LOGGER.warning("Cannot save device key when Home Assistant is not running")


class HAStorageLocationBasedDeviceKeyManager:
    """Location-specific device key manager using HA storage."""
    
    def __init__(self, storage_manager: HAStorageDeviceKeyManager, street_number: str, 
                 street_name: str, suburb: str, post_code: str):
        """
        Initialize location-based storage manager.
        
        Args:
            storage_manager: HA storage manager instance
            street_number: Street number for location key
            street_name: Street name for location key
            suburb: Suburb for location key
            post_code: Post code for location key
        """
        self._storage = storage_manager
        self._location_key = f"{street_number}_{street_name}_{suburb}_{post_code}"
    
    def get_device_key(self) -> Optional[str]:
        """Get stored device key for this location."""
        return self._storage.get_device_key_for_location(self._location_key)
    
    def save_device_key(self, device_key: str) -> None:
        """Save device key for this location."""
        self._storage.save_device_key_for_location(self._location_key, device_key)