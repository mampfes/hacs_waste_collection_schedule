"""Read the shared release version without importing the HA integration."""

import json
from pathlib import Path

from setuptools import setup

manifest = (
    Path(__file__).parent / "custom_components/waste_collection_schedule/manifest.json"
)
setup(version=json.loads(manifest.read_text(encoding="utf-8"))["version"])
