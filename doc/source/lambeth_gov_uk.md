# London Borough of Lambeth

Support for schedules provided by [London Borough of Lambeth](https://lambeth.gov.uk/), serving Lambeth, London, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lambeth_gov_uk
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
    - name: lambeth_gov_uk
      args:
        uprn: "5061647"
```

## How to get the source argument

Get your Unique Property Reference Number (UPRN) by going to <https://www.findmyaddress.co.uk/> and entering your address details.
