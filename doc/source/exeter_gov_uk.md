# Exeter City Council

Support for schedules provided by [Exeter City Council](https://exeter.gov.uk/).

Source for Exeter City services for Exeter City Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: exeter_gov_uk
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
    - name: exeter_gov_uk
      args:
        uprn: '100040227486'
```

## How to get the source arguments

Look up your address on the Exeter City Council 'When is my bin collected?' page; your UPRN is the number at the end of the resulting URL. Alternatively, search for your address on [Find My Address](https://www.findmyaddress.co.uk/).
