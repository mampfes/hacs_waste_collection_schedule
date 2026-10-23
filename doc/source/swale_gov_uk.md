# Swale Borough Council

Support for schedules provided by [Swale Borough Council](https://swale.gov.uk).

Source for swale.gov.uk services for Swale, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: swale_gov_uk
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
    - name: swale_gov_uk
      args:
        uprn: 100062375927
        postcode: ME10 3HT
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.
