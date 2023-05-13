# City of Kingston, VIC

Support for schedules provided by [City of Kingston Bins and Collections](https://www.kingston.vic.gov.au/services/rubbish-and-recycling/bins-and-collections#bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kingston_vic_gov_au
      args:
        post_code: POST_CODE
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**post_code**  
*(string) (required)*

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
    - name: kington_vic_gov_au
      args:
        post_code: "3189"
        suburb: "MOORABBIN"
        street_name: "Station Street"
        street_number: "1/1-5"
```

## How to get the source arguments

Visit the [City of Kingston Bins and Collections](https://www.kingston.vic.gov.au/services/rubbish-and-recycling/bins-and-collections#bin-day) page and search for your address. The args should exactly match the how your address is shown when you've selected your address.