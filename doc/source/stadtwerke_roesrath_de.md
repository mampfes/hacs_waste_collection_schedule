# Neunkirchen Siegerland

Support for schedules provided by [Stadtwerke Rösrath](https://www.stadtwerke-roesrath.de/), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtwerke_roesrath_de
      args:
        street: STREET
```

### Configuration Variables

**street**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadtwerke_roesrath_de
      args:
        street: "Ahornweg"

```

## How to get the source arguments

1. Go to your calendar at [G>Abfuhrkalender - StadtWerke Rösrath](https://www.stadtwerke-roesrath.de/service/abfuhrkalender/)
2. Enter your street.
3. Copy the exact values from the textboxes street in the source configuration.

*IMPORTANT* - only streetname or part of streetname without ()
the string as street must match only 1 entry
