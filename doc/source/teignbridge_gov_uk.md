# Teignbridge District Council

Support for schedules provided by [Teignbridge District Council](https://www.teignbridge.gov.uk).

Source for teignbridge.gov.uk waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: teignbridge_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: teignbridge_gov_uk
      args:
        postcode: EX4 2JR
        uprn: 010032968474
```

## How to get the source arguments

Visit https://www.teignbridge.gov.uk/recycling-and-waste/forms/download-your-collection-calendar/, enter your postcode and note the UPRN from the address dropdown.
