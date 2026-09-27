# MZV Hegau

Support for schedules provided by [MZV Hegau](https://www.mzvhegau.de).

Source for mzvhegau.de services for MZV Hegau, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mzvhegau_de
      args:
        city: CITY
```

### Configuration Variables

**city**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mzvhegau_de
      args:
        city: Engen
```

## How to get the source arguments

Enter your city/municipality shorthand in the MZV Hegau service area, e.g. Engen, Gai, GM.
