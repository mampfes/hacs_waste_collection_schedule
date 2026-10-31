# Using the sources without Home Assistant

The existing `waste_collection_schedule` core can be installed as a Python
package from this repository. It includes the source modules and shared
services, without installing Home Assistant or its integration layer.
Python 3.12 or newer is required.

The core stays in this repository and uses the version from the integration's
`manifest.json`. There is no separate PyPI release or independent release cycle.
Source parameters and core interfaces can change between releases; pin a tag
or commit and review changes before upgrading.

Standalone packaging is introduced on `release/3.0.0`. The 2.x releases do
not include it. Prerelease versions in the manifest are normalized to Python
package notation (for example, `3.0.0-beta.5` becomes `3.0.0b5`).

## Installation

Create a virtual environment, then install a chosen revision:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install 'waste-collection-schedule @ git+https://github.com/mampfes/hacs_waste_collection_schedule.git@<tag-or-commit>'
```

Replace `<tag-or-commit>` with a revision containing the packaging files.
For local development, use `python -m pip install -e .` from the repository root.
No `PYTHONPATH` changes or symlinks are needed.

The package installs the dependencies used for fetching and parsing schedules.
The interactive developer wizards, test runner, and provider discovery tools
are not part of the standalone interface. In particular, optional tools using
Selenium or `alive_progress` require their own dependencies when run from a
checkout. Home Assistant's persistent device-key storage is only used when the
integration initializes it; standalone sources keep device keys in memory.

## Fetching a schedule

Use the source name and arguments documented under `doc/source/`. For example,
to read an existing local ICS file:

```python
from waste_collection_schedule.source.ics import Source

source = Source(file="/absolute/path/to/input.ics")
for collection in source.fetch():
    print(collection.date, collection.type)
```

This works for the v3 `BaseSource` pipeline as well as the retained legacy
sources. Other providers follow the same pattern: import their `Source`, pass the
provider-specific arguments, and call `fetch()`. Results are `Collection`
objects with a date, waste type, and optional icon, picture, location, and
description. Exceptions from fetching should be handled by the calling
application. Scheduling, retries, and serving calendars are also the caller's
responsibility.

## Exporting to iCalendar

The repository includes [an export example](../examples/export_ics.py). Run it
from a checkout with the standalone package installed. Create `source.json`:

```json
{
  "source": "ics",
  "args": {
    "file": "/absolute/path/to/input.ics"
  }
}
```

Replace the source and arguments with those for your provider, then run:

```sh
python examples/export_ics.py source.json waste.ics
```

The example fetches once and writes all-day events with stable UIDs for the
same source, arguments, date, waste type, and location. Repeated identical
entries are emitted once. Changing the arguments changes the UIDs. Optional
locations and descriptions are preserved. A fetch failure exits with an error
before opening the output file, leaving any existing calendar in place.

To refresh a published calendar, run the example periodically with cron or a
similar scheduler and serve the resulting file using your existing web server.
Choose a reasonable fetch interval for the provider. Keep configuration files
containing credentials private.

## Checking the package

The standalone CI job builds a source distribution, builds a wheel from it,
and installs that wheel in a clean environment without Home Assistant. It then
imports all provider modules and runs a local ICS fetch/export round trip,
without contacting waste providers. To run the same smoke check locally after
installing the package:

```sh
python -m pip install packaging
python -I tests/standalone_smoke.py
```
