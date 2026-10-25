# Gelsia Ambiente (Giussano)

Support for schedules provided by [Gelsia Ambiente (Giussano)](https://www.gelsiambiente.it).

Source for Gelsia Ambiente waste collection schedule in Giussano.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gelsiambiente_it
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gelsiambiente_it
      args:
        zone: A
```

## How to get the source arguments

Giussano is split into zones A, B and C by street. Find your street in the zone lists on page 2 and 3 of the municipal calendar (https://www.gelsiambiente.it/servizi/calendario-dei-servizi/) and select that zone.
