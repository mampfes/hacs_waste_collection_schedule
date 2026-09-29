# Carmarthenshire County Council

Support for schedules provided by [Carmarthenshire County Council](https://www.carmarthenshire.gov.wales/).

Source script for carmarthenshire.gov.wales

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: carmarthenshire_gov_wales
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
    - name: carmarthenshire_gov_wales
      args:
        uprn: 10009546468
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.
