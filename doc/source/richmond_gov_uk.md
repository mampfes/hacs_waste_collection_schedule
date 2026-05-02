# London Borough of Richmond upon Thames

Support for schedules provided by [London Borough of Richmond upon Thames](https://www.richmond.gov.uk/), serving Richmond upon Thames, London, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: richmond_gov_uk
      args:
        uprn: "UPRN"
```

### Configuration Variables

**uprn**  
_(String | Integer) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: richmond_gov_uk
      args:
        uprn: "5061647"
```

## How to get the source argument

Get your Unique Property Reference Number (UPRN) by going to <https://www.findmyaddress.co.uk/> and entering your address details.
