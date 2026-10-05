# South Derbyshire District Council

Support for schedules provided by [South Derbyshire District Council](https://www.southderbyshire.gov.uk/).

Source for www.southderbyshire.gov.uk services for South Derbyshire 

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: southderbyshire_gov_uk
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
    - name: southderbyshire_gov_uk
      args:
        uprn: '100030233745'
```

## How to get the source arguments

Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/).
