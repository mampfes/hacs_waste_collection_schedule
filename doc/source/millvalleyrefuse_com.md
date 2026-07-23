# Mill Valley Refuse Service

Support for schedules provided by [Mill Valley Refuse Service (MVRS)](https://www.millvalleyrefuse.com), serving Mill Valley, Corte Madera, Tiburon, Belvedere, Strawberry and unincorporated southern Marin County, California, USA.

MVRS publishes a single **alternating-week recycling schedule** for its entire service area as public Google Calendars (embedded on the [residential services page](https://www.millvalleyrefuse.com/residential-services)). One week is *Container Cart Recycling*, the next is *Paper Cart Recycling*, and so on, city-wide. This source reads those calendars live, so it stays in sync with whatever MVRS publishes. MVRS office-closure / holiday service notices are included automatically as an additional stream.

Garbage and compost are collected **weekly on your normal route day** and are not published in a machine-readable feed, so they are not provided by this source. Use the optional `pickup_day` argument to align the recycling entries with your route day.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: millvalleyrefuse_com
```

### Configuration Variables

**pickup_day**
*(string) (optional)*

The weekday your address is serviced (e.g. `Wednesday`). MVRS collects Monday–Friday depending on your street. When set, each alternating recycling week is reported on that weekday. When omitted, each recycling week is marked on the Sunday it begins.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: millvalleyrefuse_com
      args:
        pickup_day: Wednesday
```

## How it works

No address lookup is required — the schedule is identical across the whole MVRS service area. The source fetches MVRS's public Google Calendar ICS feeds for container recycling, paper recycling and holiday notices, collapses each alternating recycling week into a single collection, and (if `pickup_day` is set) reports it on your route weekday.
