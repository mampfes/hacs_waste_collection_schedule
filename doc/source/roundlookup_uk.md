# Malvern Hills District Council

Support for schedules provided by [Malvern Hills District Council](https://www.malvernhills.gov.uk/).

Source for Malvern Hills District Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: roundlookup_uk
      args:
        uprn: UPRN
        council: COUNCIL
```

### Configuration Variables

**uprn**  
*(string) (required)*

**council**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: roundlookup_uk
      args:
        uprn: 100120597618
        council: Malvern Hills
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering your address details.
