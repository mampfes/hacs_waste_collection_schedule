# Haringey Council

Support for schedules provided by [Haringey Council](https://www.haringey.gov.uk/).

Source for haringey.gov.uk services for Haringey Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: haringey_gov_uk
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
    - name: haringey_gov_uk
      args:
        uprn: '100021209182'
```

## How to get the source arguments

Enter your UPRN (available from [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)).
