# Angus Council

Support for schedules provided by [Angus Council](https://www.angus.gov.uk).

Source for Angus Council (MyAngus/Granicus)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: angus_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: angus_gov_uk
      args:
        uprn: '117097214'
        postcode: DD11 2RH
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/ by searching for your address, and enter the property's postcode.
