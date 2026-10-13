# Pembrokeshire County Council

Support for schedules provided by [Pembrokeshire County Council](https://www.pembrokeshire.gov.uk/).

Source for pembrokeshire.gov.uk

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pembrokeshire_gov_uk
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
    - name: pembrokeshire_gov_uk
      args:
        uprn: '100100283349'
```

## How to get the source arguments

To get your UPRN go to [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) and search for your address.
