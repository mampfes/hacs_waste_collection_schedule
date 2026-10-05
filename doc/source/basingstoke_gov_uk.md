# Basingstoke and Deane Borough Council

Support for schedules provided by [Basingstoke and Deane Borough Council](https://basingstoke.gov.uk).

Source for basingstoke.gov.uk services for Basingstoke and Deane Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: basingstoke_gov_uk
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
    - name: basingstoke_gov_uk
      args:
        uprn: '100060234732'
```

## How to get the source arguments

Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/).
