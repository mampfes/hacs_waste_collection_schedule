"""Fetch one configured source and write an iCalendar file.

Run with the standalone package installed; see doc/standalone.md.
"""

import argparse
import datetime
import importlib
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from icalendar import Calendar, Event


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="JSON file with source and args")
    parser.add_argument("output", type=Path, help="Destination .ics file")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    source_name = config["source"]
    source_args = config.get("args", {})
    module = importlib.import_module(f"waste_collection_schedule.source.{source_name}")
    # Fetch before opening the output, so fetch errors preserve the previous file.
    collections = module.Source(**source_args).fetch()

    calendar = Calendar()
    calendar.add("prodid", "-//Waste Collection Schedule//Standalone example//EN")
    calendar.add("version", "2.0")
    identity = json.dumps([source_name, source_args], sort_keys=True)
    namespace = uuid5(NAMESPACE_URL, identity)
    timestamp = datetime.datetime.now(datetime.UTC)
    seen = set()
    for collection in sorted(collections, key=lambda c: (c.date, c.type)):
        key = (collection.date.isoformat(), collection.type, collection.location)
        uid = str(uuid5(namespace, json.dumps(key)))
        if uid in seen:
            continue
        seen.add(uid)
        event = Event()
        event.add("uid", uid)
        event.add("dtstamp", timestamp)
        event.add("dtstart", collection.date)
        # iCalendar all-day events have an exclusive end date.
        event.add("dtend", collection.date + datetime.timedelta(days=1))
        event.add("summary", collection.type)
        if collection.location:
            event.add("location", collection.location)
        if collection.description:
            event.add("description", collection.description)
        calendar.add_component(event)
    args.output.write_bytes(calendar.to_ical())


if __name__ == "__main__":
    main()
