# Strathfield Council

Support for schedules provided by [Strathfield Council](https://www.strathfield.nsw.gov.au), NSW, Australia.

The schedule is based on Strathfield Council's published waste calendar:
- **General Waste** (red lid): collected every week
- **Garden Organics** (green lid): collected fortnightly
- **Recycling** (yellow lid): collected fortnightly, alternating with Garden Organics

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: strathfield_nsw_gov_au
      args:
        collection_day: COLLECTION_DAY
```

### Configuration Variables

**collection_day**
*(string) (required)*

The day of the week your bins are collected. Must be a full weekday name (e.g. `Tuesday`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: strathfield_nsw_gov_au
      args:
        collection_day: Tuesday
```

## How to find your collection day

Your collection day is printed on your rates notice. It can also be found by contacting
[Strathfield Council](https://www.strathfield.nsw.gov.au).
