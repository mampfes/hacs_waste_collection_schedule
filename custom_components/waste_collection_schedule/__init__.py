"""Waste Collection Schedule Component."""
from .init_yaml import async_setup, CONFIG_SCHEMA
from .init_ui import async_setup_entry, async_update_listener, async_unload_entry, async_migrate_entry
