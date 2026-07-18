# Abfallwirtschaft Stadt Fürth

Support for schedules provided by [Abfallwirtschaft Stadt Fürth](https://abfallwirtschaft.fuerth.eu/).

Source for Stadt Fürth.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_fuerth_eu
      args:
        id: ID
```

### Configuration Variables

**id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_fuerth_eu
      args:
        id: 96983001
```

## How to get the source arguments

Look up your address on https://abfallwirtschaft.fuerth.eu/ and copy the numeric id from the calendar export link it offers.
