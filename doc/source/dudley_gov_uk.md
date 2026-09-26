# Dudley Metropolitan Borough Council

Support for schedules provided by [Dudley Metropolitan Borough Council](https://dudley.gov.uk).

Source for Dudley Metropolitan Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dudley_gov_uk
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
    - name: dudley_gov_uk
      args:
        uprn: '90090715'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/ by searching for your address.
