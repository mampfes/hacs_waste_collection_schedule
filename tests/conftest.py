"""Pytest bootstrap for integration platform module name collisions."""

# Several architecture tests prepend the integration package directory to
# sys.path. Load the standard-library extension first so the Home Assistant
# select platform added by the device-controls feature cannot shadow it during
# later asyncio/socket imports.
import select  # noqa: F401
