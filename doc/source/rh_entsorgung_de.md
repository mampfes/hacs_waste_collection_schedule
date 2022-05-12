# Rhein-Hunsrück Entsorgung (RHE)

Support for schedules provided by [RHE](https://www.rh-entsorgung.de) (Rhein-Hunsrück Entsorgung) located in Rhineland-Palatinate, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rh_entsorgung_de
      args:
        city: CITY
        street: STREET
        house_number: HNR
        address_suffix: HNR_SUFFIX
```

### Configuration Variables

**city**<br>
*(string) (required)*

**street**<br>
*(string) (required)*

**house_number**<br>
*(integer) (required)*

**address_suffix**<br>
*(string) (optional) (default: "")*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rhe_de
      args:
        city: "Alterkülz"
        street: "Brühlweg"
        house_number: 1
```

## How to get the source arguments

These values are the location you want to query for. Make sure, the writing is exactly as it is on [https://www.rh-entsorgung.de/de/Service/Abfallkalender/](https://www.rh-entsorgung.de/de/Service/Abfallkalender/). Typos will result in the collection schedule for the default location *(Alterkülz, Brühlweg)*, so make sure to validate the returned schedule after setting up the integration. As `house_number` expects a numeric input, address suffixes have to be provided via the `address_suffix` argument.