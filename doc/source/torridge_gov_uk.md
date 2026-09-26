# Torridge Council

Support for schedules provided by [Torridge Council](https://torridge.gov.uk).

Source for torridge.gov.uk services for Torridge, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: torridge_gov_uk
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
    - name: torridge_gov_uk
      args:
        uprn: '10093911050'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/ by searching for your address.
