# Bradford Metropolitan District Council

Support for schedules provided by [Bradford Metropolitan District Council](https://bradford.gov.uk).

Source for Bradford.gov.uk services for Bradford Metropolitan Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bradford_gov_uk
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
    - name: bradford_gov_uk
      args:
        uprn: '100051250665'
```

## How to get the source arguments

Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/).
