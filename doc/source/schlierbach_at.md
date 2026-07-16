# Marktgemeinde Schlierbach

Support for waste collection schedules provided by [Marktgemeinde Schlierbach](https://www.schlierbach.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: schlierbach_at
      args:
        zone: ZONE
```

### Configuration Variables

**zone**
*(string) (optional)*

Collection zone. Valid values: `"1"` (adds the 4-weekly Restabfall schedule) or `"Wohnhausanlagen"` (adds the Gelbe Tonne schedule for residential complexes). Omit to receive all events regardless of zone.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: schlierbach_at
      args:
        zone: "1"
```

## How to get the source arguments

Open <https://www.schlierbach.at/system/web/kalender.aspx?sprache=1&menuonr=225603725> and check the third column of the calendar table. Use the value shown there as your `zone` argument, or leave `zone` out to see all collection events.
