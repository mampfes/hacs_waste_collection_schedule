# Abfallwirtschaft Neckar-Odenwald-Kreis (AWN)

Support for schedules provided by [Abfallwirtschaft Neckar-Odenwald-Kreis](https://www.awn-online.de/) located in Baden-Württemberg, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awn_de
      args:
        city: CITY
        street: STREET
        house_number: HNR
        address_suffix: HNR_SUFFIX
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(integer) (required)*

**address_suffix**  
*(string) (optional) (default: "")*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awn_de
      args:
        city: "Billigheim"
        street: "Marienhöhe"
        house_number: 5
        address_suffix: "A"
```

## How to get the source arguments

These values are the location you want to query for. Make sure, the writing is exactly as it is on [https://www.awn-online.de/abfuhrtermine](https://www.awn-online.de/abfuhrtermine). Typos will result in an parsing error which is printed in the log. As `house_number` expects a numeric input, address suffixes have to be provided via the `address_suffix` argument.
`address_suffix` could be for example a alpha-numeric character "A" or a additional house number like "/1".