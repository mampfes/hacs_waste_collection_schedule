# London Borough of Richmond upon Thames

Support for schedules provided by [London Borough of Richmond upon Thames](https://www.richmond.gov.uk/).

Source for London Borough of Richmond upon Thames

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: richmond_gov_uk
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
    - name: richmond_gov_uk
      args:
        uprn: '100022316011'
```

## How to get the source arguments

Get your Unique Property Reference Number (UPRN) by going to <https://www.findmyaddress.co.uk/> and entering your address details.
