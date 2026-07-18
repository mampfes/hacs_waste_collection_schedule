# Stadt Verl

Support for schedules provided by [Stadt Verl](https://www.verl.de).

Source for Stadt Verl waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: verl_de
      args:
        bezirk: BEZIRK
```

### Configuration Variables

**bezirk**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: verl_de
      args:
        bezirk: 1
```

## How to get the source arguments

Your collection district number (1-5). Find yours at https://www.verl.de/rathaus/aktuelles/digitaler-umweltkalender/abfallbezirke
