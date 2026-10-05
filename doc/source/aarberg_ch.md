# Aarberg

Support for schedules provided by [Aarberg](https://www.aarberg.ch/).

Source for Aarberg, Switzerland.

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

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aarberg_ch
      args:
        zone: Aarberg
```

## How to get the source arguments

The zone/area within Aarberg, e.g. Aarberg, Grafenmoos, Leimern, Mülital, Spins, Zälgli.
