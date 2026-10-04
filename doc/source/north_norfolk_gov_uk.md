# North Norfolk District Council

Support for schedules provided by [North Norfolk District Council](https://www.north-norfolk.gov.uk/).

Source for waste collection services for North Norfolk District Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: north_norfolk_gov_uk
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
    - name: north_norfolk_gov_uk
      args:
        uprn: '100090878875'
```

## How to get the source arguments

An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
