# Rochdale Borough Council

Support for schedules provided by [Rochdale Borough Council](https://www.rochdale.gov.uk).

Source for Rochdale Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rochdale_gov_uk
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
    - name: rochdale_gov_uk
      args:
        uprn: '10094359340'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/ by searching for your address.
