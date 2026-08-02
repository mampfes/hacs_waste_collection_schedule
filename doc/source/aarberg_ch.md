# Aarberg

Support for schedules provided by [Aarberg](https://www.aarberg.ch/de/abfallwirtschaft/abfallkalender/), serving Aarberg, Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aarberg_ch
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)*

Name of the collection zone within the municipality of Aarberg. Supported values:
`Aarberg`, `Grafenmoos`, `Leimern`, `Mülital`, `Spins`, `Zälgli`

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aarberg_ch
      args:
        zone: Aarberg
```

## How to get the source arguments

Visit [https://www.aarberg.ch/de/abfallwirtschaft/abfallkalender/](https://www.aarberg.ch/de/abfallwirtschaft/abfallkalender/) and use the "Zone" filter drop-down to find the name of the zone your address belongs to. Use that exact name (e.g. `Aarberg`, `Grafenmoos`, `Leimern`, `Mülital`, `Spins`, `Zälgli`) as the `zone` argument.
