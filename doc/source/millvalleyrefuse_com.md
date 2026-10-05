# Mill Valley Refuse Service

Support for schedules provided by [Mill Valley Refuse Service](https://www.millvalleyrefuse.com).

Source for Mill Valley Refuse Service (MVRS), Marin County, California, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: millvalleyrefuse_com
      args:
        pickup_day: PICKUP_DAY
```

### Configuration Variables

**pickup_day**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: millvalleyrefuse_com
      args:
        pickup_day: Wednesday
```

## How to get the source arguments

No address lookup is required. Mill Valley Refuse Service publishes a single alternating-week recycling schedule for its whole service area (Mill Valley, Corte Madera, Tiburon, Belvedere, Strawberry and unincorporated Marin). Optionally set 'pickup_day' to the weekday your street is serviced so each collection lands on your actual pickup day instead of the start of the week.
