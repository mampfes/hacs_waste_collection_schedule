# Stadt Verl

Support for schedules provided by [Stadt Verl](https://www.verl.de), serving the city of Verl in North Rhine-Westphalia, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: verl_de
      args:
        bezirk: 1
```

### Configuration Variables

**bezirk**
*(integer) (required)*

Your collection district number (1–5). To find your district, visit the [Abfallbezirke map](https://www.verl.de/rathaus/aktuelles/digitaler-umweltkalender/abfallbezirke) on the Verl website and locate your street.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: verl_de
      args:
        bezirk: 3
```

## How to get the arguments

1. Open [https://www.verl.de/rathaus/aktuelles/digitaler-umweltkalender/abfallbezirke](https://www.verl.de/rathaus/aktuelles/digitaler-umweltkalender/abfallbezirke).
2. Find your street on the map or in the table to determine your Abfuhrbezirk (1–5).
3. Use that number as the `bezirk` argument.
