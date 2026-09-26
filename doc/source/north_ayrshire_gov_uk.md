# North Ayrshire Council

Support for schedules provided by [North Ayrshire Council](https://www.north-ayrshire.gov.uk/).

Source for north-ayrshire.gov.uk services for North Ayrshire

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: north_ayrshire_gov_uk
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
    - name: north_ayrshire_gov_uk
      args:
        uprn: '126043248'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/ by searching for your address.
