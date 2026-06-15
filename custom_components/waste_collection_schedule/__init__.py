"""Waste Collection Schedule Component."""

from .init_ui import (  # noqa: F401
    async_migrate_entry,
    async_remove_config_entry_device,
    async_setup_entry,
    async_unload_entry,
    async_update_listener,
)
from .init_yaml import CONFIG_SCHEMA, async_setup  # noqa: F401
