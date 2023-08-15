# City of Calgary

Support for schedules provided by [City of Calgary](https://www.calgary.ca/waste/residential/garbage-schedule.html).

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
*(string) (required) (all capitals)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: calgary_ca
      args:
        street_address: 42 AUBURN WY SE
```

## How to verify that your address works

Visit the [City of Toronto](https://www.calgary.ca/waste/residential/garbage-schedule.html) page and search for your address. Note that the address should be in all capital letters. The street type (crescent, way, landing should be a 2 letter abbreviation only i.e. CR, WY, LD). Do not append the city name or postal code.
