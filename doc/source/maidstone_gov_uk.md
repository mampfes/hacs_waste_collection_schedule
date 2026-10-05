# Maidstone Borough Council

Support for schedules provided by [Maidstone Borough Council](https://maidstone.gov.uk).

Source for maidstone.gov.uk services for Maidstone Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: maidstone_gov_uk
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
    - name: maidstone_gov_uk
      args:
        uprn: '10022892379'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/ by searching for your address.
