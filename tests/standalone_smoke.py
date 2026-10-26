"""Run against an installed wheel with python -I, without Home Assistant."""

import datetime
import importlib
import importlib.util
import json
import pkgutil
import subprocess
import sys
import tempfile
import unittest
from importlib.metadata import distribution
from pathlib import Path

from icalendar import Calendar, Event
from packaging.version import Version
from waste_collection_schedule import source
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.WhatBinDay import get_device_key_store

EXPORTER = Path(__file__).resolve().parents[1] / "examples/export_ics.py"


class StandaloneSmokeTest(unittest.TestCase):
    def test_installed_package(self):
        self.assertIsNone(importlib.util.find_spec("homeassistant"))
        package = distribution("waste-collection-schedule")
        self.assertFalse(
            any(
                "homeassistant" in requirement.lower()
                for requirement in (package.requires or [])
            )
        )
        paths = [str(path) for path in (package.files or [])]
        self.assertFalse(any(path.startswith("custom_components/") for path in paths))
        self.assertFalse(
            any(path.startswith("waste_collection_schedule/test/") for path in paths)
        )
        manifest = (
            EXPORTER.parents[1]
            / "custom_components/waste_collection_schedule/manifest.json"
        )
        self.assertEqual(
            Version(package.version),
            Version(json.loads(manifest.read_text())["version"]),
        )
        # An uninitialized HA device-key adapter must also work without HA.
        self.assertIsNone(get_device_key_store())
        for module in pkgutil.iter_modules(source.__path__):
            with self.subTest(source=module.name):
                importlib.import_module(
                    f"waste_collection_schedule.source.{module.name}"
                )

    def test_export_round_trip(self):
        ics = importlib.import_module("waste_collection_schedule.source.ics")
        self.assertTrue(issubclass(ics.Source, BaseSource))
        day = datetime.date.today() + datetime.timedelta(days=2)
        calendar = Calendar()
        calendar.add("prodid", "-//Standalone test//EN")
        calendar.add("version", "2.0")
        for number in range(2):
            event = Event()
            event.add("uid", f"input-{number}")
            event.add("dtstamp", datetime.datetime.now(datetime.UTC))
            event.add("dtstart", day)
            event.add("dtend", day + datetime.timedelta(days=1))
            event.add("summary", "Papier, Größe; recycling")
            event.add("location", "Straße 1, Hof")
            event.add("description", "First line\nSecond line")
            calendar.add_component(event)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_file = root / "input.ics"
            input_file.write_bytes(calendar.to_ical())
            config = root / "source.json"
            config.write_text(
                json.dumps({"source": "ics", "args": {"file": str(input_file)}})
            )
            output = root / "output.ics"
            command = [sys.executable, "-I", str(EXPORTER), str(config), str(output)]
            subprocess.run(command, cwd=root, check=True, capture_output=True)
            events = Calendar.from_ical(output.read_bytes()).walk("VEVENT")
            self.assertEqual(len(events), 1)
            event = events[0]
            self.assertEqual(event.decoded("dtstart"), day)
            self.assertEqual(event.decoded("dtend"), day + datetime.timedelta(days=1))
            self.assertEqual(str(event["summary"]), "Papier, Größe; recycling")
            self.assertEqual(str(event["location"]), "Straße 1, Hof")
            self.assertEqual(str(event["description"]), "First line\nSecond line")
            self.assertIsNotNone(event.decoded("dtstamp").tzinfo)
            subprocess.run(command, cwd=root, check=True, capture_output=True)
            refreshed = Calendar.from_ical(output.read_bytes()).walk("VEVENT")
            self.assertEqual(event["uid"], refreshed[0]["uid"])
            previous = output.read_bytes()
            input_file.unlink()
            result = subprocess.run(command, cwd=root, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), previous)


if __name__ == "__main__":
    unittest.main()
