# Gold Coast City Council

Support for schedules provided by [Gold Coast City Council](https://www.goldcoast.qld.gov.au/Services/Waste-recycling/Find-my-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: goldcoast_qld_gov_au
      args:
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**suburb**
*(string) (required)*

**street_name**
*(string) (required)*

**street_number**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: goldcoast_qld_gov_au
      args:
        suburb: Miami
        street_name: Henchman Ave
        street_number: 6/8
```

## How to get the source arguments

This is the address that the services are being picked up from (eg. your house!)
