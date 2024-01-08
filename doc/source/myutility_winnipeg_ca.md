# City of Winnipeg

Support for schedules provided by [City of Winnipeg My Utility](https://myutility.winnipeg.ca).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: myutility_winnipeg_ca
      args:
        address: STREET_ADDRESS
```

### Configuration Variables

**address**  
*(string) (required) (all capitals)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: myutility_winnipeg_ca
      args:
        address: 123 EASY ST
```

## How to verify that your address works

Visit the [My Utility Winnipeg](https://myutility.winnipeg.ca) page and search for your address under the 'Find your collection day'. Note that the address should be in all capital letters. The street type (crescent, way, landing should be a 2 letter abbreviation only i.e. CR, WY, LD). Do not append the city name or postal code.
