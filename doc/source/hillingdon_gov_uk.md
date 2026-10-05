# London Borough of Hillingdon

Support for schedules provided by [London Borough of Hillingdon](https://www.hillingdon.gov.uk).

Source for London Borough of Hillingdon, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hillingdon_gov_uk
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
    - name: hillingdon_gov_uk
      args:
        uprn: '100021484600'
```

## How to get the source arguments

You need your Unique Property Reference Number (UPRN). An easy way to find it is by going to https://www.findmyaddress.co.uk/ and entering your address details.
