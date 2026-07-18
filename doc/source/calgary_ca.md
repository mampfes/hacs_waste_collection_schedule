# Calgary (AB)

Support for schedules provided by [Calgary (AB)](https://www.calgary.ca).

Source for Calgary waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: calgary_ca
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: calgary_ca
      args:
        street_address: 42 AUBURN SHORES WY SE
```

## How to get the source arguments

Enter your street address in upper case, including the city quadrant (e.g. `42 AUBURN SHORES WY SE`).
