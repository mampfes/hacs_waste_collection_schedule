# Rhondda Cynon Taf County Borough Council

Support for schedules provided by [Rhondda Cynon Taf County Borough Council](https://www.rctcbc.gov.uk).

Source for rctcbc.gov.uk services for Rhondda Cynon Taf County Borough Council, Wales, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rctcbc_gov_uk
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
    - name: rctcbc_gov_uk
      args:
        uprn: '10024274791'
```

## How to get the source arguments

Find your UPRN by searching for your address on [Find My Address](https://www.findmyaddress.co.uk/).
