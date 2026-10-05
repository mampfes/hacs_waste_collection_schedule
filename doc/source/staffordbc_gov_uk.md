# Stafford Borough Council

Support for schedules provided by [Stafford Borough Council](https://www.staffordbc.gov.uk/).

Source for bin collection services for Stafford Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: staffordbc_gov_uk
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
    - name: staffordbc_gov_uk
      args:
        uprn: '100031780029'
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering your address details.
