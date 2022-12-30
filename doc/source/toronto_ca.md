# City of Toronto

Support for schedules provided by [City of Toronto](https://www.toronto.ca/services-payments/recycling-organics-garbage/houses/collection-schedule/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: toronto_ca
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
    - name: toronto_ca
      args:
        street_address: 324 Weston Rd
```

## How to verify that your address works

Visit the [City of Toronto](https://www.toronto.ca/services-payments/recycling-organics-garbage/houses/collection-schedule/) page and search for your address. The string you search for there should match the string in the street_address argument.
