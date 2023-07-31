# Abfallwirtschaftsbetrieb Emsland

Support for schedules provided by [Emsland Abfallwirtschaftsbetrieb](https://www.awb-emsland.de/), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_emsland_de
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
    - name: awb_emsland_de
      args:
        city: "Andervenne"
        street: "Am Gallenberg"
        house_number: 1
```

```yaml
waste_collection_schedule:
  sources:
    - name: awb_emsland_de
      args:
        city: Neubörger
        street: Aschendorfer Straße
        house_number: 1
        address_suffix: A
```

## How to get the source arguments

These values are the location you want to query for. Make sure, the writing is exactly as it is on <https://www.awb-emsland.de/service/abfuhrkalender/>. Typos will result in an parsing error which is printed in the log. As `house_number` expects a numeric input, address suffixes have to be provided via the `address_suffix` argument.
`address_suffix` could be for example a alphanumeric character "A" or a additional house number like "/1".
