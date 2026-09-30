# Blaby District Council

Support for schedules provided by [Blaby District Council](https://my.blaby.gov.uk/collections).

Recycling and refuse collection dates for Blaby District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: blaby_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: blaby_gov_uk
      args:
        uprn: 100030407500
```

## How to get the source arguments

Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/).
