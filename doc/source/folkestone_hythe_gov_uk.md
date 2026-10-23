# Folkestone and Hythe District Council

Support for schedules provided by [Folkestone and Hythe District Council](https://www.folkestone-hythe.gov.uk/).

Source for Folkestone and Hythe District Council, United Kingdom.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: folkestone_hythe_gov_uk
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
    - name: folkestone_hythe_gov_uk
      args:
        uprn: 50032102
```

## How to get the source arguments

Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/).
