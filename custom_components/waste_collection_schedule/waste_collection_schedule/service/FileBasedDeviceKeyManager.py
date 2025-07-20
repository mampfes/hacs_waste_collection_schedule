#!/usr/bin/env python3

import json
import logging
import os
from typing import Optional

_LOGGER = logging.getLogger(__name__)


class FileBasedDeviceKeyManager:
    """Simple file-based device key manager as fallback when HA storage isn't available."""
    
    def __init__(self, location_key: str, hass=None):
        """Initialize file-based storage manager."""
        self._location_key = location_key
        self._hass = hass
        self._storage_file = self._get_storage_file_path()
        
    def _get_storage_file_path(self) -> str:
        """Get path to storage file."""
        # Try to use HA config directory if available
        if self._hass is not None:
            try:
                config_dir = self._hass.config.config_dir
                storage_file = os.path.join(config_dir, "waste_collection_schedule_device_keys.json")
                return storage_file
            except Exception as e:
                _LOGGER.warning("Failed to get HA config directory: %s", e)
        
        # Fallback to temp directory
        import tempfile
        temp_dir = tempfile.gettempdir()
        storage_dir = os.path.join(temp_dir, "waste_collection_schedule")
        try:
            os.makedirs(storage_dir, exist_ok=True)
            storage_file = os.path.join(storage_dir, "device_keys.json")
            return storage_file
        except Exception as e:
            _LOGGER.error("Failed to create storage directory %s: %s", storage_dir, e)
            # Final fallback
            fallback_file = os.path.join(temp_dir, "wcs_device_keys.json")
            return fallback_file
    
    def get_device_key(self) -> Optional[str]:
        """Get stored device key for this location."""
        try:
            if os.path.exists(self._storage_file):
                with open(self._storage_file, 'r') as f:
                    data = json.load(f)
                    device_keys = data.get("device_keys", {})
                    result = device_keys.get(self._location_key)
                    return result
            else:
                _LOGGER.debug("File storage file does not exist: %s", self._storage_file)
        except Exception as e:
            _LOGGER.warning("Failed to read device key from file storage: %s", e)
        return None
    
    def save_device_key(self, device_key: str) -> None:
        """Save device key for this location."""
        try:
            # Load existing data
            data = {"device_keys": {}}
            if os.path.exists(self._storage_file):
                try:
                    with open(self._storage_file, 'r') as f:
                        data = json.load(f)
                except Exception:
                    # If file is corrupted, start fresh
                    pass
            
            # Ensure device_keys exists
            if "device_keys" not in data:
                data["device_keys"] = {}
            
            # Save the new key
            data["device_keys"][self._location_key] = device_key
            
            # Write back to file
            with open(self._storage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            _LOGGER.error("Failed to save device key to file storage: %s", e)